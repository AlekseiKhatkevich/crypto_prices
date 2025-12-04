from domain.price import CryptoPrice
from adapter.sql_price_repository import SQLPriceRepository

class CheckTargetsUseCase:
    targets_repo = SQLPriceRepository


    async def execute(self):
        pass

    async def all_targets(self):
        pass
