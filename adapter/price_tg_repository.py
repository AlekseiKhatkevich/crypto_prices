import os
from pyexpat.errors import messages
from typing import TYPE_CHECKING

from telethon import TelegramClient

from _secrets import telegram_api_hash, telegram_api_id, telegram_bot_token
from domain.price_tg_repository import PriceMessangerRepository

if TYPE_CHECKING:
    from domain.price import CryptoPrice


class PriceTGRepository(PriceMessangerRepository):

    async def send(self, price: 'CryptoPrice') -> None:
        message = (f'Цена на {price.standard_name.upper()} пересекла таргет {price.target}. {os.linesep}'
                       f'Текущая цена {price.current}.')
        bot = await TelegramClient('bot', telegram_api_id, telegram_api_hash).start(bot_token=telegram_bot_token)
        await bot.send_message(5282738353, message=message)