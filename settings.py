import dataclasses


from utils.singletone import ModuleSingletonAssigner

__all__ = (
    'settings',
)

@dataclasses.dataclass(frozen=True)
class ProjectSettings:
    db_addr: str = 'sqlite+aiosqlite:///crypto_price_db.db'


settings: ProjectSettings
ModuleSingletonAssigner(ProjectSettings, 'settings').assign()
