from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config.dotenv import EnvConfig
from config.locale import Locale
from middleware import LocaleMiddleware
from handlers.user.user_handlers import user_router
from database.db import init_db
import asyncio
import logging
import os

dp = Dispatcher()


def setup_logging():

    if not os.path.exists("logs"):
        os.makedirs("logs")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
    )
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    logging.getLogger("aiogram").setLevel(logging.ERROR)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.getLogger("asyncio").setLevel(logging.WARNING)
    return logging.getLogger(__name__)


logger = setup_logging()


async def main() -> None:

    logger.info("bot initializing...")
    config = EnvConfig()
    telegram_token = config.get_telegram_token()
    bot = Bot(
        token=telegram_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
    )
    locale = Locale()
    middleware = LocaleMiddleware(locale)

    dp.include_router(user_router)
    dp.update.outer_middleware(middleware)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(main())
