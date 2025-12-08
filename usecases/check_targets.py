import asyncio

from adapter.http_price_sourcing_repository import repository as http_repository
from adapter.sql_price_repository import SQLPriceRepository
from domain.price import CryptoPrice


# DI !
QUEUE_MAXSIZE = 3

class CheckTargetsUseCase:

    def __init__(self, targets_repo = http_repository, sql_repo=SQLPriceRepository):
        self.targets_repo = targets_repo()
        self.sql_repo = sql_repo()
        self.fetch_queue = asyncio.Queue(QUEUE_MAXSIZE)
        self.telegram_queue = asyncio.Queue(QUEUE_MAXSIZE)
        self.save_db_queue = asyncio.Queue(QUEUE_MAXSIZE)

        self.main_end_event = asyncio.Event()
        self.fetch_end_event = asyncio.Event()
        self.save_in_db_end_event = asyncio.Event()
        self.tg_end_event = asyncio.Event()

    async def send_to_tg_consumer(self, _id):
        async for price in self._get_price_from_queue(
                self.telegram_queue,
                self.fetch_end_event,
                self.tg_end_event ,
                _id,
                name='send_to_tg_consumer',
        ):
            print(f'{_id=} send_to_tg_consumer:: Sending price {price} to telegram bot.')
            self.telegram_queue.task_done()


    async def check_trigger(self, price: CryptoPrice):
        if ((price.movement_direction.DOWN and price.last_saved > price.target >= price.current) or
                (price.movement_direction.UP and price.last_saved < price.target <= price.current)):
            price.is_active = False
            await self.telegram_queue.put(price)


    @staticmethod
    async def _get_price_from_queue(queue, prev_event, current_event, _id, name):
        """
        1) С таймаутом в 1 сек мы пытаемся получить задачу из очереди пока продюсер не закончил работу.
        2) Как только продюсер закончил работу prev_event.is_set() == True, мы переходим в режим get_nowait,
        в котором мы просто берем все задачи из очереди пока они не закончатся.
        3) Задачи заканчиваются и мы устанавливаем эвент текущего контекста в True, что говорит о том что везде,
        где этот консьюмер является продьюсером мы сигнализируем об окончании работы.
        4) Завершаем работу консьюмера.
        """
        while True:
            try:
                if not prev_event.is_set():
                    price = await asyncio.wait_for(queue.get(), timeout=1.0)
                else:
                    price = queue.get_nowait()
                print(f'{_id=}, {queue}::Got price {price}')
            except asyncio.TimeoutError:
                continue
            except (asyncio.CancelledError, asyncio.queues.QueueEmpty):
                print(f'{_id=}, {name}::Exiting, all done.')
                if current_event is not None:
                    current_event.set()
                break
            else:
                yield price

    async def fetch_web_data_consumer(self, _id):
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

    async def save_data_in_db_consumer(self, _id):
        async for price in self._get_price_from_queue(
                self.save_db_queue,
                self.fetch_end_event,
                self.save_in_db_end_event,
                _id,
                name='save_data_in_db_consumer',
        ):
            await self.sql_repo.add(price)
            self.save_db_queue.task_done()


    async def main_producer(self):
        async for price in self.sql_repo:
            await self.fetch_queue.put(price)
            print(f'main_producer::Put price {price} in queue')
        self.main_end_event.set()
        print(f'main_producer::Set main event. All done!')

    async def execute(self):
        await asyncio.gather(
            self.main_producer(),
            *[self.fetch_web_data_consumer(_id) for _id in range(3)],
            *[self.save_data_in_db_consumer(_id) for _id in range(3)],
            *[self.send_to_tg_consumer(_id) for _id in range(3)],
        )



