from domain.price_tg_repository import PriceMessangerRepository
from telethon import TelegramClient
from _secrets import telegram_api_id, telegram_api_hash


class PriceTGRepository(PriceMessangerRepository):

    async def send(self, price):
        async with TelegramClient('anon', telegram_api_id, telegram_api_hash) as client:
            me = await client.get_me()
            await client.send_message(me.id, 'Hello, myself!')