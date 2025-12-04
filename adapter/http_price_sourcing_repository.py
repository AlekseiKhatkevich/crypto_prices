import decimal
from typing import Dict

import httpx
from pydantic import RootModel

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
            limits=httpx.Limits(max_connections=5),
            event_hooks={'response': [self.raise_on_4xx_5xx]},
            transport=httpx.AsyncHTTPTransport(retries=2),
        )

    @staticmethod
    async def raise_on_4xx_5xx(response) -> None:
        response.raise_for_status()

    async def fetch(self, price):
        response = await self.client.get(
                self.base_url,
                params={'ids': price.standard_name, 'vs_currencies': settings.vs_currency},
            )
        validated = PricesResponse.model_validate(response.json())
        current_price = validated.root[price.standard_name].root[settings.vs_currency]
        price.current = current_price

        return price

    async def _finalize(self):
        await self.client.aclose()


repository: HTTPCryptoPriceSourcingRepository
ModuleSingletonAssigner(HTTPCryptoPriceSourcingRepository, 'repository').assign()