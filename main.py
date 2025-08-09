from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config.dotenv import BaseConfig
from config.locale import Locale
from middleware import LocaleMiddleware
from handlers.user.user_handlers import user_router
import asyncio


dp = Dispatcher()


async def main() -> None:
    config = BaseConfig()
    telegram_token = (config.get_telegram_token()) 
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
    asyncio.run(main())
