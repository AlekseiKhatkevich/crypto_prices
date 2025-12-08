import contextlib

from domain.price import CryptoPrice, CryptoPriceMovementDirection
from adapter.sql_price_repository import SQLPriceRepository
from adapter.http_price_sourcing_repository import repository as http_repository
import asyncio
# DI !


class CheckTargetsUseCase:
    targets_repo = SQLPriceRepository()

    def __init__(self, targets_repo = SQLPriceRepository):
        self.targets_repo = targets_repo()
        self.fetch_queue = asyncio.Queue(maxsize=3)
        self.telegram_queue = asyncio.Queue(maxsize=3)
        self.save_db_queue = asyncio.Queue(maxsize=3)

        self.main_end_event = asyncio.Event()
        self.fetch_end_event = asyncio.Event()
        self.save_in_db_end_event = asyncio.Event()


    async def check_trigger(self, price: CryptoPrice):
        if ((price.movement_direction.DOWN and price.last_saved > price.target >= price.current) or
                (price.movement_direction.UP and price.last_saved < price.target <= price.current)):
            price.is_active = False
            await self.telegram_queue.put(price)


    @staticmethod
    async def _get_price_from_queue(queue, prev_event, current_event, id):
        while True:
            try:
                if not prev_event.is_set():
                    price = await asyncio.wait_for(queue.get(), timeout=1.0)
                else:
                    price = queue.get_nowait()
                print(f'{id=}, {queue}::Got price {price}')
            except asyncio.TimeoutError:
                continue
            except (asyncio.CancelledError, asyncio.queues.QueueEmpty):
                print(f'{id=}, {queue}::Exiting, all done.')
                current_event.set()
                break
            else:
                yield price

    async def fetch_web_data_consumer(self, id):
        async for price in self._get_price_from_queue(
                self.fetch_queue,
                self.main_end_event,
                self.fetch_end_event,
                id,
        ):
            await http_repository.fetch(price)
            await self.check_trigger(price)
            await self.save_db_queue.put(price)
            self.fetch_queue.task_done()

    async def save_data_in_db_consumer(self, id):
        async for price in self._get_price_from_queue(
                self.save_db_queue,
                self.fetch_end_event,
                self.save_in_db_end_event,
                id,
        ):
            await self.targets_repo.add(price)
            self.save_db_queue.task_done()


    async def main_producer(self):
        async for price in self.targets_repo:
            await self.fetch_queue.put(price)
            print(f'main_producer::Put price {price} in queue')
        self.main_end_event.set()
        print(f'main_producer::Set main event. All done!')

    async def execute(self):
        await asyncio.gather(
            self.main_producer(),
            *[self.fetch_web_data_consumer(id) for id in range(3)],
            *[self.save_data_in_db_consumer(id) for id in range(3)],
        )



