import dataclasses
import importlib
import uuid
from functools import cache
from typing import Any, Type, TypeVar, Generic

__all__ = (
    'settings',
)

@dataclasses.dataclass(frozen=True)
class ProjectSettings:
    vote_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    db_addr: str = 'sqlite+aiosqlite:///crypto_price_db.db'


settings: ProjectSettings

T = TypeVar('T')

class ModuleSingletonAssigner(Generic[T]):
    def __init__(self, obj: Type[T], attr_name: str) -> None:
        self.obj = obj
        self.attr_name = attr_name

    @cache
    def _build_obj(self) -> T:
        return self.obj()

    def _module_level_getattr(self, name: str) -> T | Any:
        if name == self.attr_name:
            return self._build_obj()
        elif name in __all__:
            import importlib
            return importlib.import_module('.' + name, __name__)
        else:
            raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

    def assign(self) -> None:
        mod = importlib.import_module('settings')
        mod.__getattr__ = self._module_level_getattr

ModuleSingletonAssigner(ProjectSettings, 'settings').assign()