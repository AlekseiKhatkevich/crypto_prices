import contextlib
import decimal
from typing import Dict
from http import HTTPStatus
import httpx
from pydantic import RootModel
from utils.logging import log
from domain.price_sourcing_repository import CryptoPriceSourcingRepository
from settings import settings
from utils.singletone import ModuleSingletonAssigner
from utils.weakref import Finalizable

__all__ = (
    'repository',
)


class PriceInfo(RootModel[Dict[str, decimal.Decimal]]):
    pass


class PricesResponse(RootModel[Dict[str, PriceInfo]]):
    pass


class HTTPCryptoPriceSourcingRepository(Finalizable, CryptoPriceSourcingRepository):
    def __init__(self, base_url: str = settings.api_base_url) -> None:
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            http2=True,
            limits=httpx.Limits(max_connections=10),
            transport=httpx.AsyncHTTPTransport(retries=2),
        )

    async def fetch(self, price):
        response = await self.client.get(
                self.base_url,
                params={'ids': price.standard_name, 'vs_currencies': settings.vs_currency},
            )
        if response.status_code == HTTPStatus.OK:
            validated = PricesResponse.model_validate(response.json())
            current_price = validated.root[price.standard_name].root[settings.vs_currency]
            price.current = current_price
        elif response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            await log.awarning(f'Price "{price}" http fetch. Got 429, skipping...')
            return price

        response.raise_for_status()

        return price

    async def _finalize(self) -> None:
        with contextlib.suppress(Exception):
            await self.client.aclose()

    def __call__(self, *args, **kwargs) -> 'HTTPCryptoPriceSourcingRepository':
        return self


repository: HTTPCryptoPriceSourcingRepository
ModuleSingletonAssigner(HTTPCryptoPriceSourcingRepository, 'repository').assign()