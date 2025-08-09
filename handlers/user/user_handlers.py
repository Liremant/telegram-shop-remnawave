from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from keyboards.user_keyboards import main_menu_kb, rates_kb, payment_methods_kb
from config.locale import Locale , escape_markdown_v2
from config.dotenv import BaseConfig 
userRouter = Router()

@userRouter.message(CommandStart())
async def start(message: Message, locale: Locale):
    greeting = locale.get('greeting', message)
    await message.answer(greeting, reply_markup=main_menu_kb(locale))

@userRouter.callback_query(F.data == 'buy_sub')
async def buy_sub(callback: CallbackQuery, locale: Locale):
    choose_rate = locale.get('choose_rate', callback.message)
    await callback.answer()  
    await callback.message.answer(choose_rate, reply_markup=rates_kb(locale))

@userRouter.callback_query(F.data.startswith('select_rate_'))
async def confirm_purchase(callback: CallbackQuery, locale: Locale):
    callback.answer()
    config = BaseConfig()
    rate_key = callback.data.replace('select_rate_', '')
    rate_number = int(rate_key)
    confirm_purchase_locale = locale.get('confirm_purchase',callback.message)
    rate_data = config.get_rate_by_number(rate_number)
    if rate_data:
        prices = escape_markdown_v2(f"{rate_data['name']} - {rate_data['value']}")
    else:
        prices = "Rate not found"
    await callback.message.answer(f"{confirm_purchase_locale}\n\n{prices}", reply_markup=payment_methods_kb(locale, rate_key))

# @userRouter.callback_query(F.data.startswith('pay_card_'))
