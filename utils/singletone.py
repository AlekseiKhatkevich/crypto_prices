import asyncio
import importlib
import inspect
import weakref
from functools import cache
from typing import Any, Generic, Type, TypeVar, no_type_check

from utils.weakref import Finalizable

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
        built_obj = self.obj()
        if isinstance(built_obj, Finalizable):
            weakref.finalize(built_obj, lambda: asyncio.run(built_obj._finalize()))
        return built_obj

    def _module_level_getattr(self, name: str) -> T | Any:
        if name == self.attr_name:
            return self._build_obj()
        elif name in __all__:
            import importlib
            return importlib.import_module('.' + name, __name__) # ty: ignore[invalid-argument-type]
        else:
            raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

    @no_type_check
    def assign(self) -> None:
        caller_frame = inspect.currentframe().f_back
        caller_module = inspect.getmodule(caller_frame)
        caller_name = caller_module.__name__
        mod = importlib.import_module(caller_name)
        mod.__getattr__ = self._module_level_getattr
