import abc


__all__ = (
    'Finalizable',
)

class Finalizable(abc.ABC):

    @abc.abstractmethod
    async def _finalize(self) -> None:
        pass