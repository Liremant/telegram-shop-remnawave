import asyncio
import logging
import os
from contextlib import asynccontextmanager
import hmac

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from config.dotenv import EnvConfig
from config.locale import Locale
from middleware import LocaleMiddleware
from handlers.user_handlers import user_router
from database.db import init_db
from initialize_remnawave import create_remnawave_client

dp = Dispatcher()

def setup_logging():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
    )
    for logger_name in ["sqlalchemy", "sqlalchemy.engine", "sqlalchemy.pool", "httpx", "httpcore", "urllib3", "asyncio"]:
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
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
    )
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


async def run_polling(bot):
    logger.info("starting polling...")
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        pass
    finally:
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
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        webhook_url = f"{config.get_webhook_url()}{config.get_webhook_path()}"
        try:
            await bot.set_webhook(
                url=webhook_url,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True,
                secret_token=config.get_webhook_secret(),
            )
            logger.info(f"webhook set: {webhook_url}")
            yield
        except Exception as e:
            logger.exception(e)
            yield
        finally:
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

    def verify_telegram_secret(request: Request, expected_secret: str):
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not token or not hmac.compare_digest(token, expected_secret):
            client = "unknown"
            try:
                client = request.client[0] if request.client else "unknown"
            except Exception:
                client = "unknown"
            logger.warning("unauthorized webhook access attempt from %s", client)
            raise HTTPException(status_code=401, detail="Unauthorized")

    app = FastAPI(lifespan=lifespan)

    @app.post(config.get_webhook_path())
    async def webhook_handler(request: Request):
        try:
            verify_telegram_secret(request, config.get_webhook_secret())
            json_data = await request.json()
            update = Update.model_validate(json_data, context={"bot": bot})
            await dp.feed_update(bot, update)
            return JSONResponse(status_code=200, content={"ok": True})
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(e)
            return JSONResponse(status_code=500, content={"ok": False})

    logger.info("starting webhook server...")
    uvicorn_config = uvicorn.Config(
        app=app,
        host=config.get_webhook_host(),
        port=config.get_webhook_port(),
        log_config=None,
    )
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


async def main():
    bot, config = await setup_bot()
    if config.get_use_webhook():
        await run_webhook(bot, config)
    else:
        await run_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
