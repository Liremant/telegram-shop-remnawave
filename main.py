import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config.dotenv import EnvConfig
from middleware import LocaleMiddleware
from handlers.user_handlers import user_router
from database.db import init_db
from remnawave import RemnawaveSDK

from api.user_manager import PanelWebhookHandler 

from api.cryptobot import CryptoBotWebhook

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

    token, currency = config.get_cryptobot_data()
    cryptobot = CryptoBotWebhook(token, currency, bot)
    dp.workflow_data["cryptobot"] = cryptobot
    logger.info("cryptobot setup ended")

    remnawave_token, panel_url = config.get_remnawave_data()
    remnawave = RemnawaveSDK(base_url=panel_url, token=remnawave_token)
    if asyncio.iscoroutine(remnawave):
        remnawave = await remnawave
    dp.workflow_data["remnawave"] = remnawave
    logger.info("remnawave setup ended")

    middleware = LocaleMiddleware()
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


    
async def run_webhook(bot, config):
    app = web.Application()

    cryptobot = dp.workflow_data["cryptobot"]
    remnawave = dp.workflow_data["remnawave"]
    
    webhook_handler = PanelWebhookHandler(
        bot, 
        remnawave,
        config.get_remna_secret()
    )

    webpath,cryptowebhook,remnawavewebhook = config.get_webhook_path()

    logger.info(f"webhook_path: {webpath}")
    logger.info(f"crypto path will be: {webpath}{cryptowebhook}")
    logger.info(f"panel path will be:{webpath}{remnawavewebhook}")
    app.add_subapp(f"{webpath}{cryptowebhook}", cryptobot.app)
    
    async def panel_webhook_route(request):
        return await webhook_handler.handle_webhook(request)
    
    app.router.add_post(f"{webpath}{remnawavewebhook}", panel_webhook_route)
    
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=config.get_webhook_secret()
    ).register(app, path=webpath)


    setup_application(app, dp, bot=bot)

    webhook_url = f"{config.get_webhook_url()}{webpath}"
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
        await run_webhook(bot, config)
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