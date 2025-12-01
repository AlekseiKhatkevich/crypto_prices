import importlib
import inspect
from functools import cache
from typing import Any, Generic, Type, TypeVar

__all__ = (
    'ModuleSingletonAssigner',
)

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
        caller_frame = inspect.currentframe().f_back
        caller_module = inspect.getmodule(caller_frame)
        caller_name = caller_module.__name__ if caller_module is not None else None
        mod = importlib.import_module(caller_name)
        mod.__getattr__ = self._module_level_getattr
