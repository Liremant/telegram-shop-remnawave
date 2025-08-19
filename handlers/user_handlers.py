from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from keyboards.user_keyboards import (
    main_menu_kb,
    rates_kb,
    payment_methods_kb,
    crypto_button,
    show_months,
    topup_balance
)
from config.locale import Locale
from config.dotenv import RateConfig, EnvConfig
import logging
from database.req import UserRequests, InvoiceRequests, ReferralLinkRequests
from api.user_manager import UserManager
from api.cryptobot import CryptoBotWebhook
from remnawave import RemnawaveSDK
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import base58

logger = logging.getLogger("__main__")
user_router = Router()


class PaymentStates(StatesGroup):
    waiting_amount = State()

@user_router.message(CommandStart())
async def start(message: Message, locale: Locale,command: CommandObject,**kwargs    ):



    greeting = locale.get("greeting")
    logger.info(
        f"user {message.from_user.username} started bot. id={message.from_user.id}"
    )
    client = UserRequests
    tgid = message.from_user.id
    name = message.from_user.full_name
    if message.from_user.username:
        username = message.from_user.username
        user = await client.create_user(
        username=username,
        name=name,
        telegram_id=tgid,
        locale=message.from_user.language_code
    )
    else:
        user = await client.create_user(
        name=message.from_user.full_name,
        telegram_id=message.from_user.id,
        locale=message.from_user.language_code
    )
    if user:
        logger.info("user added into db")
        if command.args:
            
            crypted_id = command.args  
            ownref_tgid = base58.b58decode_int(crypted_id)
            ownref = await client.get_user_by_telegram_id(ownref_tgid)
            bot = kwargs.get('bot')
            ref = ReferralLinkRequests
            usr = await client.get_user_by_telegram_id(message.from_user.id)
            user_id = usr.id
            ownref_user_id = ownref.id
            refferal = await ref.create_referral_link(
                owner_id=ownref_user_id,
                user_id=user_id,
                user_tgid=tgid,
                user_full_name=name
            )
            if refferal:
                if username:
                    await bot.send_message(
                        chat_id=ownref_tgid,
                        text=f'{locale.get("referral_connected")}\n{name} ',
                    )
                else:
                    await bot.send_message(
                        chat_id=ownref_tgid,
                        text=f'{locale.get("referral_connected")}\n• {name}• {username} ',
                    )

    else:
        logger.info("user already in db")

    await message.answer(greeting, reply_markup=main_menu_kb(locale))


@user_router.callback_query(F.data == "back_to_main")
async def restart(callback: CallbackQuery, locale: Locale):
    callback.answer()
    greeting = locale.get("greeting")
    logger.info(f"user {callback.message.from_user.username} started bot. id={callback.message.from_user.id}")
    client = UserRequests
    user = await client.create_user(
        username=callback.message.from_user.username,
        name=callback.message.from_user.full_name,
        telegram_id=callback.message.from_user.id,
        locale=callback.message.from_user.language_code
    )
    if user:
        logger.info("user added into db")
    else:
        logger.info("user already in db")
    await callback.message.answer(greeting, reply_markup=main_menu_kb(locale))


@user_router.callback_query(F.data == "buy_sub")
async def buy_sub(callback: CallbackQuery, locale: Locale):
    choose_rate = locale.get("choose_rate")
    await callback.answer()
    await callback.message.edit_text(choose_rate, reply_markup=rates_kb(locale))
    logger.info(
        f"buy_sub button touched, id:{callback.from_user.id} username:{callback.from_user.username}"
    )


@user_router.callback_query(F.data.startswith("select_rate_"))
async def choose_months(callback: CallbackQuery, locale: Locale):
    rate_id = int(callback.data.replace("select_rate_", ""))
    await callback.answer()
    await callback.message.edit_text(
        locale.get("choose_months"), reply_markup=show_months(rate_id, locale)
    )


@user_router.callback_query(F.data.startswith("select_months_"))
async def confirm_purchase(callback: CallbackQuery, locale: Locale):
    await callback.answer()
    config = RateConfig()
    _, _, rate_number, months = callback.data.split("_")
    confirm_purchase_locale = locale.get("confirm_purchase")
    rate_data = config.get_rate_by_number(rate_number)
    if rate_data:
        prices =f"{locale.get('buy_rate')}{rate_data['name']}\n{locale.get('rate_value')}{int(rate_data['value'])*months}\n{locale.get('rate_description')}{rate_data['desc']}\n{locale.get('rate_period')}{months}"
    else:
        prices = "Rate not found"
    await callback.message.edit_text(
        f"{confirm_purchase_locale}\n\n{prices}",
        reply_markup=payment_methods_kb(locale, rate_number, months),
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
        await callback.answer()
        await callback.message.edit_text(answer)
    except Exception as e:
        logger.error(f"err: {e}")


@user_router.callback_query(F.data == "show_balance")
async def show_balance(callback: CallbackQuery, locale: Locale):
    await callback.answer()
    user = UserRequests()
    ans = await user.get_user_by_telegram_id(callback.from_user.id)
    await callback.message.edit_text(
        f'{locale.get("info_balance")}{ans.balance}', reply_markup=topup_balance(locale)
    )

@user_router.callback_query(F.data == "topup_balance")
async def choose_pay_type(callback : CallbackQuery,locale: Locale):
    await callback.answer()
    await callback.message.edit_text(locale.get('choose_payment'),reply_markup=payment_methods_kb(locale))


@user_router.callback_query(F.data == "pay_crypto")
async def pay_crypto_start(callback: CallbackQuery, locale: Locale, state: FSMContext):
    await callback.answer()
    await state.set_state(PaymentStates.waiting_amount)
    
    await callback.message.edit_text(
        locale.get("enter_amount")
    )
    logger.info(f"User {callback.from_user.id} started crypto payment process")

@user_router.message(PaymentStates.waiting_amount)
async def process_amount_and_create_invoice(message: Message, locale: Locale, state: FSMContext,cryptobot: CryptoBotWebhook ,**kwargs):
    try:
        amount = float(message.text.replace(',', '.'))
        config = RateConfig()
        minamount = config.get_minimal_amount()
        if amount < float(minamount):
            await message.answer(locale.get("invalid_amount"))
            return
            
        if amount > 50000:
            await message.answer(locale.get("amount_too_large"))
            return
            
    except ValueError:
        await message.answer(locale.get("invalid_amount_format"))
        return
    
    await state.clear()
    
    try:
        
        user = await UserRequests.get_user_by_telegram_id(message.from_user.id)
        user_id = user.id
        logger.info(f'user_id:{user.id}')
        bot = kwargs.get('bot')
        me = await bot.get_me()
        bot_username = f'https://t.me/{me.username}'

        invoice = await cryptobot.create_invoice(
            amount=amount,
            locale=locale,
            bot_username=bot_username,
            user_id=user_id,
            tg_id=message.from_user.id
            )
        invreq = InvoiceRequests()
        await invreq.create_invoice(
            status='pending',
            user_id=user_id,
            platform='cryptobot',
            amount=amount
        )
        await message.answer(locale.get('pay_crypto'),reply_markup=crypto_button(locale,invoice.bot_invoice_url))
    except Exception as e:
        logger.exception(f'error:{e}')


@user_router.callback_query(F.data == 'show_refferals')
async def show_refs(callback: CallbackQuery,locale: Locale,**kwargs):
    env = EnvConfig()
    percent = env.get_ref_percent()
    await callback.answer()
    bot = kwargs.get('bot')
    me = await bot.get_me()
    tg_id = callback.from_user.id
    cryptedid = base58.b58encode_int(tg_id).decode()
    reflink = f'https://t.me/{me.username}?start={cryptedid}'
    ans=f'''{locale.get('refheader')}

{locale.get('your_reflink')} {reflink}
{locale.get('ref_percent')} {percent}%
    '''
    user = UserRequests()
    owner_id = await user.get_user_by_telegram_id(tg_id)
    try:
        refs = ReferralLinkRequests()
        referrals = await refs.get_referral_links_by_owner_id(owner_id=owner_id)
        
        for ref in referrals:
            ans+=f'''• {ref.full_name}
            '''
    except Exception as e:
        logger.debug(e)
    await callback.message.answer(ans)