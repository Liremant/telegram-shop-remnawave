from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards.user_keyboards import main_menu_kb, rates_kb, payment_methods_kb
from config.locale import Locale , escape_markdown_v2
from config.dotenv import RateConfig
import logging
from database.req import get_all_users

logger = logging.getLogger('__main__')

admin_router = Router()

@admin_router.message(Command="admin")
async def admin_menu(message: Message):
    await message.answer("hi its admin menu im very lazy to code it lmao")