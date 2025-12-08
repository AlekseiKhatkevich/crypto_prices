import abc
from typing import AsyncIterator, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from .price import CryptoPrice



class CryptoPriceRepository(abc.ABC):
    @abc.abstractmethod
    async def add(self, price: 'CryptoPrice') -> Awaitable['CryptoPrice']:
        pass

    @abc.abstractmethod
    async def __aiter__(self) -> AsyncIterator['CryptoPrice']:
        pass
