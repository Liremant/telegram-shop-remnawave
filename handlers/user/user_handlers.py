from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from keyboards.user_keyboards import main_menu_kb, get_rates
from config.locale import Locale
userRouter = Router()

@userRouter.message(CommandStart())
async def start(message: Message, locale: Locale):
    greeting = locale.get('greeting', message)
    await message.answer(greeting, reply_markup=main_menu_kb())

@userRouter.callback_query(F.data == 'buy_sub')
async def buy_sub(callback: CallbackQuery, locale: Locale):
    choose_rate = locale.get('choose_rate', callback.message)
    await callback.answer()  
    await callback.message.answer(choose_rate, reply_markup=get_rates())