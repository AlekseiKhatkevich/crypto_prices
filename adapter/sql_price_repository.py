from typing import AsyncIterator, Awaitable, TYPE_CHECKING

import sqlalchemy as sa

from database import CryptoPriceORM
from database.alchemy import db
from domain.price_db_repository import CryptoPriceRepository

if TYPE_CHECKING:
    from domain.price import CryptoPrice

__all__ = (
    'SQLPriceRepository',
)

class SQLPriceRepository(CryptoPriceRepository):
    model = CryptoPriceORM
    db = db

    async def all(self) -> Awaitable[list[CryptoPriceORM]]:
        async with self.db.async_session as session:
            res = await session.scalars(
                sa.select(self.model).where(self.model.is_active == sa.true())
            )
            return res.all()

    async def add(self, price: 'CryptoPrice') -> Awaitable['CryptoPrice']:
        orm_price = self.model.from_dto(price)
        async with self.db.async_session as session:
            await session.merge(orm_price)
            await session.commit()
        return price

    async def __aiter__(self) -> AsyncIterator['CryptoPrice'] :
        for target in await self.all():
            yield target.to_dto(target)
