import decimal
from typing import Dict

import httpx
from pydantic import BaseModel, RootModel

from domain.price_sourcing_repository import CryptoPriceSourcingRepository
from settings import settings
from utils.singletone import ModuleSingletonAssigner

__all__ = (
    'repository',
)


class PriceInfo(BaseModel):
    usd: decimal.Decimal

class PricesResponse(RootModel[Dict[str, PriceInfo]]):
    pass


class HTTPCryptoPriceSourcingRepository(CryptoPriceSourcingRepository):
    def __init__(self, base_url: str = settings.api_base_url) -> None:
        self.base_url = base_url
        self.client = httpx.AsyncClient()


    async def fetch(self, price):
        response = await self.client.get(
                self.base_url,
                params={'ids': price.standard_name, 'vs_currencies': settings.vs_currency},
            )
        validated = PricesResponse.model_validate(response.json())
        current_price = getattr(validated.root[price.standard_name], settings.vs_currency)
        price.current = current_price

        return price


repository: HTTPCryptoPriceSourcingRepository
ModuleSingletonAssigner(HTTPCryptoPriceSourcingRepository, 'repository').assign()