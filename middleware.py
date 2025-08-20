from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, Update
from database.req import UserRequests
from config.locale import Locale


class LocaleMiddleware(BaseMiddleware):
    def __init__(self, default_lang: str = "en"):
        super().__init__()
        self.default_lang = default_lang

    async def __call__(self, handler, event: TelegramObject, data: dict):
        tg_id = None
        lang = None

        if isinstance(event, Message) and event.from_user:
            tg_id = event.from_user.id
            lang = event.from_user.language_code
        elif isinstance(event, CallbackQuery) and event.from_user:
            tg_id = event.from_user.id
            lang = event.from_user.language_code
        elif isinstance(event, Update):
            if event.message and event.message.from_user:
                tg_id = event.message.from_user.id
                lang = event.message.from_user.language_code
            elif event.callback_query and event.callback_query.from_user:
                tg_id = event.callback_query.from_user.id
                lang = event.callback_query.from_user.language_code

        if tg_id and not lang:
            user = await UserRequests().get_user_by_telegram_id(tg_id)
            lang = user.locale if user and user.locale else self.default_lang

        if not lang:
            lang = self.default_lang

        data["locale"] = Locale(lang)
        return await handler(event, data)
