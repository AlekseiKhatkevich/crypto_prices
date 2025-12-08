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


    @staticmethod
    async def update_price(price):
        return await http_repository.fetch(price)

    async def check_trigger(self, price: CryptoPrice):
        if ((price.movement_direction.DOWN and price.last_saved > price.target <= price.current) or
                (price.movement_direction.UP and price.last_saved < price.target <= price.current)):
            price.is_active = False
            # await self.telegram_queue.put(price)


    async def fetch_web_data_consumer(self, id):
        while True:
            try:
                price = await self.fetch_queue.get() if not self.main_end_event.is_set() else self.fetch_queue.get_nowait()
                print(f'{id=}, fetch_web_data_consumer::Got price {price}')
                await self.update_price(price)
                await self.check_trigger(price)
                # await self.save_db_queue.put(price)
                self.fetch_queue.task_done()
            except (asyncio.CancelledError, asyncio.queues.QueueEmpty) as exc:
                print(f'{id=}, fetch_web_data_consumer:: Exiting, reason - {exc}')
                self.fetch_end_event.set()
                break

    # async def save_data_in_db_consumer(self, id):
    #     while True:
    #         price = await self.save_db_queue.get()
    #         if price is None:
    #             self.save_db_queue.task_done()
    #             print(f'save_data_in_db_consumer::Got None form a queue. Finishing...')
    #             break
    #         else:
    #             print(f'{id=}save_data_in_db_consumer:: Got price to save it db {price}')
    #             await self.targets_repo.add(price)
    #             self.save_db_queue.task_done()


    async def main_producer(self):
        async for price in self.targets_repo:
            await self.fetch_queue.put(price)
            print(f'main_producer::Put price {price} in queue')
        # await self.fetch_queue.put(None)
        self.main_end_event.set()
        print(f'main_producer::Set main event. All done!')

    async def execute(self):
        await asyncio.gather(
            self.main_producer(),
            *[self.fetch_web_data_consumer(id) for id in range(3)],
            # *[self.save_data_in_db_consumer(id) for id in range(3)],
        )



