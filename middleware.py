from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

class LocaleMiddleware(BaseMiddleware):
    def __init__(self, locale):
        super().__init__()
        self.locale = locale
    
    async def __call__(self, handler, event: TelegramObject, data: dict):
        data['locale'] = self.locale  
        return await handler(event, data)