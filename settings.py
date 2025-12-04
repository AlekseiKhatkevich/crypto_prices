import dataclasses


from utils.singletone import ModuleSingletonAssigner

__all__ = (
    'settings',
)

@dataclasses.dataclass(frozen=True)
class ProjectSettings:
    db_addr: str = 'sqlite+aiosqlite:///crypto_price_db.db'
    api_base_url = 'https://api.coingecko.com/api/v3/simple/price'
    vs_currency = 'usd'


settings: ProjectSettings
ModuleSingletonAssigner(ProjectSettings, 'settings').assign()
