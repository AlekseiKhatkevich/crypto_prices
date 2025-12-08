import datetime
import decimal

from sqlalchemy import CheckConstraint, FetchedValue, Index, func, text, true
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import ORMBase
from domain.price import CryptoPrice, CryptoPriceMovementDirection

__all__ = (
    'CryptoPriceORM',
)


class CryptoPriceORM(ORMBase):
    __tablename__ = 'cryptoprice'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        comment='id.',
        nullable=False,
    )
    target: Mapped[decimal.Decimal] = mapped_column(
        comment='Таргет цены криптоактива.',
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(
        comment='Тикер.',
        nullable=False,
    )
    standard_name: Mapped[str] = mapped_column(
        comment='Стандартное название для апи получения.',
        nullable=False,
    )
    movement_direction: Mapped[CryptoPriceMovementDirection] = mapped_column(
        comment='Направление движения цены.',
        nullable=False,
    )
    last_saved: Mapped[decimal.Decimal] = mapped_column(
        comment='Последняя сохраненная цена.',
    )
    is_active: Mapped[bool] = mapped_column(
        comment='Признак активности таргета.',
        server_default=true(),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.Now(),
        nullable=False,
        comment='Время создания.',
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        onupdate=func.Now(),
        comment='Время обновления.',
        server_onupdate=FetchedValue(for_update=True),
    )

    __table_args__ = (
        Index(
            'name_target_uq',
            'ticker', 'target',
            unique=True,
            sqlite_where=text('is_active = True'),
        ),
        CheckConstraint(text('target > 0'), name='target_gt_0_check', ),
        CheckConstraint(text('last_saved > 0'), name='last_saved_gt_0_check', ),
    )

    def __repr__(self):
        return f'{self.target} for {self.ticker}'

    @staticmethod
    def to_dto(price: 'CryptoPriceORM') -> CryptoPrice:
        return CryptoPrice(
            id=price.id,
            standard_name=price.standard_name,
            target=price.target,
            movement_direction=price.movement_direction,
            last_saved=price.last_saved,
            current=None,
            is_active=price.is_active,
            ticker=price.ticker,
        )

    @classmethod
    def from_dto(cls, price: 'CryptoPrice') -> 'CryptoPriceORM':
        return cls(
            id=price.id,
            standard_name=price.standard_name,
            target=price.target,
            movement_direction=price.movement_direction,
            last_saved=price.current,
            is_active=price.is_active,
            ticker=price.ticker,
            updated_at=func.NOW(),
        )
