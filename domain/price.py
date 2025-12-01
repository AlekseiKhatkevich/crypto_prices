import dataclasses
import decimal
import enum

class CryptoPriceMovementDirection(enum.StrEnum):
    DOWN = 'down'
    UP = 'up'


@dataclasses.dataclass
class CryptoPrice:
    target: decimal.Decimal
    movement_direction: CryptoPriceMovementDirection
    id: int | None = None
    last_saved: decimal.Decimal | None = None
    current:decimal.Decimal | None = None
    is_active: bool = True
    is_fired: bool = False
