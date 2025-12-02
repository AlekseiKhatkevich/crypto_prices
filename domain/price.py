import dataclasses
import decimal
import enum
from typing import Awaitable, TYPE_CHECKING

from utils.enums import CaseInsensitiveMixin

if TYPE_CHECKING:
    from .price_db_repository import CryptoPriceRepository
    from .price_sourcing_repository import CryptoPriceSourcingRepository


class CryptoPriceMovementDirection(CaseInsensitiveMixin, enum.StrEnum):
    DOWN = 'down'
    UP = 'up'


@dataclasses.dataclass
class CryptoPrice:
    ticker: str
    target: decimal.Decimal
    movement_direction: CryptoPriceMovementDirection
    id: int | None = None
    last_saved: decimal.Decimal | None = None
    current:decimal.Decimal | None = None
    is_active: bool = True


    async def save_in_db(self, db_repository: 'CryptoPriceRepository', ) -> Awaitable['CryptoPrice']:
        return await db_repository.add(self)

    async def fetch_current_value(
            self,
            sourcing_repository: 'CryptoPriceSourcingRepository',
    ) -> Awaitable['CryptoPrice']:
        return await sourcing_repository.fetch(self)