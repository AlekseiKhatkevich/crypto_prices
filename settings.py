import dataclasses


@dataclasses.dataclass(frozen=True)
class ProjectSettings:
    db_addr: str =  'sqlite+aiosqlite:///crypto_price_db.db'