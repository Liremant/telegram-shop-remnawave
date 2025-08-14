from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from keyboards.user_keyboards import (
    main_menu_kb,
    rates_kb,
    payment_methods_kb,
    crypto_button,
    show_months
)
from config.locale import Locale, escape_markdown_v2
from config.dotenv import RateConfig, EnvConfig
import logging
from database.req import create_user,get_user_by_telegram_id
from api.user_manager import UserManager
from api.cryptobot import CryptoBotWebhook
from remnawave import RemnawaveSDK
import json
from aiogram.utils.text_decorations import markdown_decoration as md

logger = logging.getLogger("__main__")
user_router = Router()


@user_router.message(CommandStart())
async def start(message: Message, locale: Locale):
    greeting = locale.get("greeting", message)
    logger.info(
        f"user {message.from_user.username} started bot. id={message.from_user.id}"
    )
    user = await create_user(
        username=message.from_user.username,
        name=message.from_user.full_name,
        telegram_id=message.from_user.id,
    )
    if user:
        logger.info("user added into db")
    else:
        logger.info("user already in db")
    await message.answer(greeting, reply_markup=main_menu_kb(locale))


@user_router.callback_query(F.data == "buy_sub")
async def buy_sub(callback: CallbackQuery, locale: Locale):
    choose_rate = locale.get("choose_rate", callback.message)
    await callback.answer()
    await callback.message.answer(choose_rate, reply_markup=rates_kb(locale))
    logger.info(
        f"buy_sub button touched, id:{callback.from_user.id} username:{callback.from_user.username}"
    )


@user_router.callback_query(F.data.startswith("select_rate_"))
async def choose_months(callback: CallbackQuery, locale: Locale):
    rate_id = int(callback.data.replace("select_rate_", ""))
    await callback.answer()
    await callback.message.answer(locale.get("choose_months"), reply_markup=show_months(rate_id,locale))



    
@user_router.callback_query(F.data.startswith("select_months_"))
async def confirm_purchase(callback: CallbackQuery, locale: Locale):
    await callback.answer()
    config = RateConfig()
    _, _, rate_number, months = callback.data.split("_")
    confirm_purchase_locale = locale.get("confirm_purchase", callback.message)
    rate_data = config.get_rate_by_number(rate_number)
    if rate_data:
        prices = escape_markdown_v2(
            f"{locale.get('buy_rate')}{rate_data['name']}\n{locale.get('rate_value')}{int(rate_data['value'])*months}\n{locale.get('rate_description')}{rate_data['desc']}\n{locale.get('rate_period')}{months}"
        )
    else:
        prices = "Rate not found"
    await callback.message.answer(
        f"{confirm_purchase_locale}\n\n{prices}",
        reply_markup=payment_methods_kb(locale, rate_number,months)
    )


@user_router.callback_query(F.data.startswith("pay_crypto"))
async def generate_invoice(callback: CallbackQuery, locale: Locale):
    rates = RateConfig()
    
    client = CryptoBotWebhook()
    _, _, rate_key, months = callback.data.split("_")
    value = rates.get_value_by_number(rate_key)

    invoice_data = client.cr_invoice(
        amount=int(value)*months,
        period=months,
        expires_in=3600,
        user_id=await get_user_by_telegram_id(callback.from_user.id),
        locale=locale
    )
    if invoice_data and invoice_data.get("ok"):
        text = md.quote(f'{locale.get("pay_by_this_link")}')
        pay_link = invoice_data["result"]["pay_url"]
        logger.info(
            f"Invoice successfully created:{json.dumps(invoice_data, indent=4)} Payment URL: {invoice_data['result']['pay_url']}"
        )
        await callback.message.answer(
            text, reply_markup=crypto_button(locale, pay_link)
        )






@user_router.callback_query(F.data == "show_sub")
async def show_sub(callback: CallbackQuery, remnawave: RemnawaveSDK, locale: Locale):
    user = UserManager(remnawave)
    ans = await user.get_subscription(str(callback.from_user.id))
    logger.debug(f"subscrption get from api:{ans}")
    answer = ""
    for i, subscription in enumerate(ans):
        expires = subscription.expire_at
        used_traffic = f"{subscription.used_traffic_bytes / 1024**3:.2f} GB"
        traffic_limit = (
            f"{subscription.traffic_limit_bytes / 1024**3:.2f} GB"
            if subscription.traffic_limit_bytes > 0
            else "∞"
        )
        sub_url = subscription.subscription_url

        status_map = {"ACTIVE": "active", "EXPIRED": "expired", "DISABLED": "disabled"}
        status = status_map.get(subscription.status.value, "unknown")

        answer += f"{locale.get('sub')} {i+1}\n{locale.get('expires')}\\: {expires}\n{locale.get('sub_url')}\\: {sub_url}\n{locale.get('traffic_used')}\\: {used_traffic}\n{locale.get('traffic_limit')}\\: {traffic_limit}\n{locale.get('status')}\\: {status}\n\n"
    try:
        await callback.message.answer(escape_markdown_v2(answer))
    except Exception as e:
        logger.error(f"err: {e}")