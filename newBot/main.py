from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import time

bot = Bot(token='5205054173:AAHFth95nXtAqEkjxUz37aWQSPbF9U-coLw')

dp = Dispatcher(bot)


@dp.message_handler(content_types=['text'])
async def func(msg):
    await msg.answer(msg.text)


executor.start_polling(dp, skip_updates=True)
