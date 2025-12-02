import datetime
import decimal

from sqlalchemy import FetchedValue, Identity, Index, func, true
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from domain.price import CryptoPriceMovementDirection

__all__ = (
    'CryptoPriceORM',
)




class CryptoPriceORM(DeclarativeBase):
    __tablename__ = 'cryptoprice'

    id: Mapped[int] = mapped_column(
        Identity(always=True),
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
            sqlite_where='is_active = True',
        ),
    )

    def __repr__(self):
        return f'{self.target} for {self.ticker}'
