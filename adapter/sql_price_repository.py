from typing import AsyncIterator, Awaitable

import sqlalchemy as sa

from database import CryptoPriceORM
from database.alchemy import db
from domain.price_db_repository import CryptoPriceRepository

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

    async def add(self, price) -> Awaitable[CryptoPriceORM]:
        # orm_price = self.model.from_dto()
        async with self.db.async_session as session:
            await session.add(price)
            await session.commit()
        return price

    async def __aiter__(self) -> AsyncIterator[CryptoPriceORM] :
        all_targets = await self.all()
        for target in all_targets:
            yield target.to_dto(target)
