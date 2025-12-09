from typing import TYPE_CHECKING
import os
from telethon import TelegramClient

from _secrets import telegram_api_hash, telegram_api_id
from domain.price_tg_repository import PriceMessangerRepository

if TYPE_CHECKING:
    from domain.price import CryptoPrice


class PriceTGRepository(PriceMessangerRepository):

    async def send(self, price: 'CryptoPrice') -> None:
        async with TelegramClient('anon', telegram_api_id, telegram_api_hash) as client:
            me = await client.get_me()
            message = (f'Цена на {price.standard_name.upper()} пересекла таргет {price.target}. {os.linesep}'
                       f'Текущая цена {price.current}.')
            await client.send_message(me.id, message)