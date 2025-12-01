import dataclasses
import uuid

from utils.singletone import ModuleSingletonAssigner

__all__ = (
    'settings',
)

@dataclasses.dataclass(frozen=True)
class ProjectSettings:
    vote_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    db_addr: str = 'sqlite+aiosqlite:///crypto_price_db.db'


settings: ProjectSettings
ModuleSingletonAssigner(ProjectSettings, 'settings').assign()