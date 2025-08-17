import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config.dotenv import EnvConfig
from config.locale import Locale
from middleware import LocaleMiddleware
from handlers.user_handlers import user_router
from database.db import init_db
from initialize_remnawave import create_remnawave_client

from api.cryptobot import setup_crypto_webhook

dp = Dispatcher()


def setup_logging():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
    )
    for logger_name in [
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "httpx",
        "httpcore",
        "urllib3",
        "asyncio",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)
    return logging.getLogger(__name__)


logger = setup_logging()


async def setup_bot():
    logger.info("bot initializing...")
    config = EnvConfig()
    telegram_token = config.get_telegram_token()
    bot = Bot(
        token=telegram_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
        
    dp.workflow_data["bot"] = bot
    
    remnawave = create_remnawave_client()
    if asyncio.iscoroutine(remnawave):
        remnawave = await remnawave
    try:
        dp.workflow_data["remnawave"] = remnawave
    except Exception:
        setattr(dp, "remnawave", remnawave)
    locale = Locale()
    middleware = LocaleMiddleware(locale)
    dp.include_router(user_router)
    dp.update.outer_middleware(middleware)
    await init_db()
    return bot, config


async def cleanup_bot(bot):
    try:
        await bot.delete_webhook()
    except Exception:
        pass
    try:
        await bot.session.close()
    except Exception:
        try:
            await bot.close()
        except Exception:
            pass


async def run_polling(bot):
    logger.info("starting polling...")
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        pass
    finally:
        await cleanup_bot(bot)


async def run_webhook(bot, config):
    app = web.Application()
    app["bot"] = bot
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=config.get_webhook_secret()
    ).register(app, path=config.get_webhook_path())

    setup_application(app, dp, bot=bot)

    setup_crypto_webhook(app)

    webhook_url = f"{config.get_webhook_url()}{config.get_webhook_path()}"
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=False,
        secret_token=config.get_webhook_secret(),
    )
    logger.info(f"webhook set: {webhook_url}")

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, config.get_webhook_host(), config.get_webhook_port())

    logger.info(
        f"starting webhook server on {config.get_webhook_host()}:{config.get_webhook_port()}"
    )
    await site.start()

    shutdown_event = asyncio.Event()

    def signal_handler():
        shutdown_event.set()

    if hasattr(asyncio, "get_running_loop"):
        loop = asyncio.get_running_loop()
        import signal

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

    try:
        await shutdown_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("shutting down webhook server...")
        await cleanup_bot(bot)
        await runner.cleanup()


async def main():
    bot, config = await setup_bot()
    try:
        if config.get_use_webhook():
            await run_webhook(bot, config)
        else:
            await run_polling(bot)
    except KeyboardInterrupt:
        logger.info("received keyboard interrupt")
    except Exception as e:
        logger.exception(f"unexpected error: {e}")
    finally:
        logger.info("bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
