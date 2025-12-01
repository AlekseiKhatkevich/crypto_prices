import abc
from typing import Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from .price import CryptoPrice



class CryptoPriceSourcingRepository(abc.ABC):
    @abc.abstractmethod
    async def fetch(self, price: 'CryptoPrice') -> Awaitable['CryptoPrice']:
        pass
