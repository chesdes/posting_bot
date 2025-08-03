import asyncio
import logging
import sys
from aiogram import Dispatcher
from app.handlers import router
from app.init_bot import bot
from app.auto_posting import ticker

async def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(ticker())
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())