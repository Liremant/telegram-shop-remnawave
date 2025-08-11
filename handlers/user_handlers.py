from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from keyboards.user_keyboards import main_menu_kb, rates_kb, payment_methods_kb
from config.locale import Locale , escape_markdown_v2
from config.dotenv import RateConfig
import logging
from database.req import create_user
from api.user_manager import UserManager
from remnawave import RemnawaveSDK

logger = logging.getLogger('__main__')
user_router = Router()


@user_router.message(CommandStart())
async def start(message: Message, locale: Locale):
    greeting = locale.get('greeting', message)
    logger.info(f'user {message.from_user.username} started bot. id={message.from_user.id}')
    user = await create_user(username=message.from_user.username, name=message.from_user.full_name,telegram_id=message.from_user.id)
    if user:
        logger.info('user added into db')
    else:
        logger.info('user already in db')
    await message.answer(greeting, reply_markup=main_menu_kb(locale))

@user_router.callback_query(F.data == 'buy_sub')
async def buy_sub(callback: CallbackQuery, locale: Locale):
    choose_rate = locale.get('choose_rate', callback.message)
    await callback.answer()  
    await callback.message.answer(choose_rate, reply_markup=rates_kb(locale))
    logger.info(f'buy_sub button touched, id:{callback.from_user.id} username:{callback.from_user.username}')
@user_router.callback_query(F.data.startswith('select_rate_'))
async def confirm_purchase(callback: CallbackQuery, locale: Locale):
    await callback.answer()
    config = RateConfig()
    rate_key = callback.data.replace('select_rate_', '')
    rate_number = int(rate_key)
    confirm_purchase_locale = locale.get('confirm_purchase', callback.message)
    rate_data = config.get_rate_by_number(rate_number)
    if rate_data:
        prices = escape_markdown_v2(f"{rate_data['name']} - {rate_data['value']}\n\n{rate_data['desc']}")
    else:
        prices = "Rate not found"
    await callback.message.answer(f"{confirm_purchase_locale}\n\n{prices}", reply_markup=payment_methods_kb(locale, rate_key))

@user_router.message(Command("sub"))
async def generate_sub(message: Message,remnawave: RemnawaveSDK):
    user = UserManager(remnawave)
    print(f"{message.from_user.id},{message.from_user.username}")
    ans = await user.create_or_get_user(telegram_id=message.from_user.id,tg_username=message.from_user.username)
    await message.answer(ans,parse_mode=None)