import asyncio
import decimal
from typing import AsyncGenerator, TYPE_CHECKING, cast

from adapter import PriceTGRepository
from utils.logging import log
from adapter.http_price_sourcing_repository import repository as http_repository
from adapter.sql_price_repository import SQLPriceRepository
from domain.price import CryptoPrice

if TYPE_CHECKING:
    from domain.price_sourcing_repository import CryptoPriceSourcingRepository
    from domain.price_db_repository import CryptoPriceRepository
    from domain.price_tg_repository import PriceMessangerRepository


QUEUE_MAXSIZE = 3

class CheckTargetsUseCase:
    def __init__(
            self,
            targets_repo:'CryptoPriceSourcingRepository' = http_repository,
            sql_repo: 'CryptoPriceRepository'=SQLPriceRepository(),
            tg_repo: 'PriceMessangerRepository' = PriceTGRepository(),
    ) -> None:
        self.targets_repo  = targets_repo
        self.sql_repo = sql_repo
        self.tg_repo = tg_repo

        self.fetch_queue = asyncio.Queue(QUEUE_MAXSIZE)
        self.telegram_queue = asyncio.Queue(QUEUE_MAXSIZE)
        self.save_db_queue = asyncio.Queue(QUEUE_MAXSIZE)

        self.main_end_event = asyncio.Event()
        self.fetch_end_event = asyncio.Event()
        self.save_in_db_end_event = asyncio.Event()
        self.tg_end_event = asyncio.Event()

    async def send_to_tg_consumer(self, _id: int) -> None:
        async for price in self._get_price_from_queue(
                self.telegram_queue,
                self.fetch_end_event,
                self.tg_end_event ,
                _id,
                name='send_to_tg_consumer',
        ):
            await self.tg_repo.send(price)
            await log.ainfo(f'Sending price {price} to telegram bot.', id=_id, price=price)
            self.telegram_queue.task_done()

    async def check_trigger(self, price: CryptoPrice) -> None:
        last_saved = cast(decimal.Decimal, price.last_saved)
        current = cast(decimal.Decimal, price.current)
        target =  price.target
        if ((price.movement_direction.DOWN and last_saved > target >= current) or
                (price.movement_direction.UP and last_saved < target <= current)):
            price.is_active = False
            await self.telegram_queue.put(price)
            await log.ainfo(
                f'check_trigger:: Condition has triggered.',
                target=price.target, price=price.current, price_id=price.id
            )

    @staticmethod
    async def _get_price_from_queue(
            queue: asyncio.Queue,
            prev_event: asyncio.Event,
            current_event: asyncio.Event,
            _id: int,
            name: str,
    ) -> AsyncGenerator[CryptoPrice, None]:
        """
        1) С тайм-аутом в 1 сек мы пытаемся получить задачу из очереди пока продюсер не закончил работу.
        2) Как только продюсер закончил работу prev_event.is_set() == True, мы переходим в режим get_nowait,
        в котором мы просто берем все задачи из очереди пока они не закончатся.
        3) Задачи заканчиваются и мы устанавливаем эвент текущего контекста в True, что говорит о том что везде,
        где этот консьюмер является продюсером мы сигнализируем об окончании работы.
        4) Завершаем работу консьюмера.
        """
        local_log = log.bind(id=_id, name=name)
        while True:
            try:
                if not prev_event.is_set():
                    price = await asyncio.wait_for(queue.get(), timeout=1.0)
                else:
                    price = queue.get_nowait()
                await local_log.ainfo(f'Got price {price}')
            except asyncio.TimeoutError:
                continue
            except (asyncio.CancelledError, asyncio.queues.QueueEmpty):
                await local_log.ainfo('Exiting, all done.')
                if current_event is not None:
                    current_event.set()
                break
            else:
                yield price

    async def fetch_web_data_consumer(self, _id: int) -> None:
        async for price in self._get_price_from_queue(
                self.fetch_queue,
                self.main_end_event,
                self.fetch_end_event,
                _id,
                name='fetch_web_data_consumer',
        ):
            await http_repository.fetch(price)
            await self.check_trigger(price)
            await self.save_db_queue.put(price)
            self.fetch_queue.task_done()

    async def save_data_in_db_consumer(self, _id: int) -> None:
        async for price in self._get_price_from_queue(
                self.save_db_queue,
                self.fetch_end_event,
                self.save_in_db_end_event,
                _id,
                name='save_data_in_db_consumer',
        ):
            await self.sql_repo.add(price)
            self.save_db_queue.task_done()
            await log.ainfo(f'Saved price {price} in db.', consumer='save_data_in_db_consumer', id=_id)


    async def main_producer(self) -> None:
        log_local = log.bind(producer='main_producer')
        async for price in self.sql_repo:
            await self.fetch_queue.put(price)
            await log_local.ainfo(f'Put price {price} in queue.')
        self.main_end_event.set()
        await log_local.ainfo(f'Set main event. All done!')

    async def execute(self) -> None:
        await asyncio.gather(
            self.main_producer(),
            *[self.fetch_web_data_consumer(_id) for _id in range(QUEUE_MAXSIZE)],
            *[self.save_data_in_db_consumer(_id) for _id in range(QUEUE_MAXSIZE)],
            *[self.send_to_tg_consumer(_id) for _id in range(QUEUE_MAXSIZE)],
        )
