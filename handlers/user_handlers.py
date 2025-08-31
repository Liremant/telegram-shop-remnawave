from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from keyboards.user_keyboards import (
    main_menu_kb,
    rates_kb,
    payment_methods_kb,
    crypto_button,
    show_months,
    topup_balance,
    build_subscription_detail_keyboard,
    build_subscriptions_keyboard,
    confirm_pay,
    sub_kb,
    back_kb,
)
from config.locale import Locale
from config.dotenv import RateConfig, EnvConfig
import logging
from database.req import (
    UserRequests,
    InvoiceRequests,
    ReferralLinkRequests,
    SublinkRequests,
)
from services.user_service import UserService, ReferralService, PaymentService
from api.user_manager import UserManager
from api.cryptobot import CryptoBotWebhook
from remnawave import RemnawaveSDK
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import base58
from decimal import Decimal

logger = logging.getLogger("__main__")
user_router = Router()


class PaymentStates(StatesGroup):
    waiting_amount = State()


@user_router.message(CommandStart())
async def start(message: Message, locale: Locale, command: CommandObject, **kwargs):
    greeting = locale.get("greeting")
    logger.info(
        f"user {message.from_user.username} started bot. id={message.from_user.id}"
    )
    client = UserService()
    status, user = await client.create_or_get_user(
        name=message.from_user.full_name,
        telegram_id=message.from_user.id,
        userlang=message.from_user.language_code,
        username=message.from_user.username,
    )
    logger.info(f"status:{status},user:{user}")
    if status and command.args:
        ref = ReferralService()
        logger.info(f"{command.args}")
        await ref.create_or_get_referral(
            cryptid=command.args,
            uid=user.id,
            full_name=message.from_user.full_name,
            locale=locale,
            username=message.from_user.username,
            user_tgid=message.from_user.id,
            bot=kwargs.get("bot"),
        )
    await message.answer(greeting, reply_markup=main_menu_kb(locale))


@user_router.callback_query(F.data == "back_to_main")
async def restart(callback: CallbackQuery, locale: Locale):
    callback.answer()
    greeting = locale.get("greeting")
    logger.info(
        f"user {callback.message.from_user.username} started bot. id={callback.message.from_user.id}"
    )
    client = UserRequests
    user = await client.create_user(
        username=callback.message.from_user.username,
        name=callback.message.from_user.full_name,
        telegram_id=callback.message.from_user.id,
        locale=callback.message.from_user.language_code,
    )
    if user:
        logger.info("user added into db")
    else:
        logger.info("user already in db")
    await callback.message.edit_text(greeting, reply_markup=main_menu_kb(locale))


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
    months = int(months)
    logger.info(f"rate_numer:{rate_number},months:{months}")
    confirm_purchase_locale = locale.get("confirm_purchase")
    rate_data = config.get_rate_by_number(rate_number)
    if rate_data:
        prices = f"{locale.get('buy_rate')}{rate_data['limit']}\n{locale.get('rate_value')}{rate_data['value'] * months}\n{locale.get('rate_description')}{rate_data['desc']}\n{locale.get('rate_period')}{months}"
    else:
        prices = "Rate not found"
    await callback.message.edit_text(
        f"{confirm_purchase_locale}\n\n{prices}",
        reply_markup=confirm_pay(locale, rate_number, months),
    )


@user_router.callback_query(F.data == "show_sub")
async def show_sub(callback: CallbackQuery, remnawave: RemnawaveSDK, locale: Locale):
    await callback.answer()
    user = UserManager(remnawave)
    try:
        ans = await user.get_subscription(str(callback.from_user.id))
        logger.info(f"subscrption get from api:{ans}")
        answer = locale.get("sub_list")
        usr = UserRequests()
        uid = await usr.get_user_by_telegram_id(callback.from_user.id)
        uid = uid.id

        await callback.message.edit_text(
            answer, reply_markup=await build_subscriptions_keyboard(ans, uid=uid)
        )
    except Exception as e:
        ans = f'{locale.get("no_sub")}'
        logger.error(f"err: {e}")
        await callback.message.edit_text(ans, reply_markup=back_kb(locale))


@user_router.callback_query(F.data.startswith("sub_info:"))
async def show_subscription_info(
    callback: CallbackQuery, locale: Locale, remnawave: RemnawaveSDK
):
    await callback.answer()
    data_parts = callback.data.split(":")
    subid = int(data_parts[1])
    raw_status = data_parts[2]
    used_gb = data_parts[3]
    limit_gb = data_parts[4]

    rq = SublinkRequests()
    sub = await rq.get_sublink_by_id(subid)
    expire_at = sub.expires_at

    status_map = {
        "ACTIVE": f"🟢 {locale.get('active')}",
        "EXPIRED": f"🟡 {locale.get('expired')}",
        "LIMITED": f"🟡 {locale.get('limited')}",
        "DISABLED": f"🔴 {locale.get('disabled')}",
    }
    expire_date = expire_at.strftime("%d.%m.%Y %H:%M")
    status = status_map.get(raw_status)
    info_text = f"""📊 <b>{locale.get('subscription')}</b>
🚦 <b>{locale.get('status')}:</b> {status}
📈 <b>{locale.get('traffic_used')}:</b> {used_gb} GB
📊 <b>{locale.get('traffic_limit')}:</b> {limit_gb} GB
📅 <b>{locale.get('expires')}:</b> {expire_date}
🔗 <b>{locale.get('sub_url')}:</b>
<code>{sub.link}</code>"""

    await callback.message.answer(
        info_text, reply_markup=await build_subscription_detail_keyboard(sub.link)
    )


@user_router.callback_query(F.data == "show_balance")
async def show_balance(callback: CallbackQuery, locale: Locale):
    await callback.answer()
    user = UserRequests()
    ans = await user.get_user_by_telegram_id(callback.from_user.id)
    await callback.message.edit_text(
        f"{locale.get('info_balance')}{ans.balance}", reply_markup=topup_balance(locale)
    )


@user_router.callback_query(F.data == "topup_balance")
async def choose_pay_type(callback: CallbackQuery, locale: Locale):
    await callback.answer()
    await callback.message.edit_text(
        locale.get("choose_payment"), reply_markup=payment_methods_kb(locale)
    )


@user_router.callback_query(F.data.startswith("pay_rate:"))
async def pay_rate(callback: CallbackQuery, locale: Locale, remnawave: RemnawaveSDK):
    await callback.answer()
    ps = PaymentService()
    payment, ballance = await ps.service_pay_rate(
        tgid=callback.from_user.id, callbackdata=callback.data
    )
    """     rq = UserRequests()
    rt = RateConfig()
    sb = SublinkRequests()
    submanager = UserManager(remnawave)
    rate_number = callback.data.split(":")[1]
    months = callback.data.split(":")[2]
    usr = await rq.get_user_by_telegram_id(callback.from_user.id)
    rate_data = rt.get_rate_by_number(rate_number)
    value = Decimal(str(rate_data["value"]))
    limit = int(rate_data["limit"])
    limit_bytes = limit * 1024**3 """

    """ if usr.balance >= value:
        await rq.update_user(user_id=usr.id, balance=usr.balance - value)
        sub = await submanager.create_user(callback.from_user.id, months, limit_bytes)
        await sb.create_sublink(
            link=sub.subscription_url,
            expires_at=sub.expire_at,
            username=sub.username,
            user_id=usr.id,
            limit_gb=sub.traffic_limit_bytes / 1024**3,
            status=sub.status,
        )
        logger.info(f"sublink created:{sub.subscription_url}")

        )

    else:
        await callback.message.edit_text(
            f'{locale.get("not_enough_money")}:{usr.balance}'
    ) """
    if payment:
        await callback.message.edit_text(
            f'{locale.get("sub_bought")}\n{locale.get("new_balance")}{ballance}\n{locale.get("sub_already_in_subs")}',
            callback_data=sub_kb(locale),
        )
    else:
        await callback.message.edit_text(f'{locale.get("not_enough_money")}:{ballance}')


@user_router.callback_query(F.data == "pay_crypto")
async def pay_crypto_start(callback: CallbackQuery, locale: Locale, state: FSMContext):
    await callback.answer()
    await state.set_state(PaymentStates.waiting_amount)

    await callback.message.edit_text(locale.get("enter_amount"))
    logger.info(f"User {callback.from_user.id} started crypto payment process")


@user_router.message(PaymentStates.waiting_amount)
async def process_amount_and_create_invoice(
    message: Message,
    locale: Locale,
    state: FSMContext,
    cryptobot: CryptoBotWebhook,
    **kwargs,
):
    try:
        amount = float(message.text.replace(",", "."))
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
        logger.info(f"user_id:{user.id}")
        bot = kwargs.get("bot")
        me = await bot.get_me()
        bot_username = f"https://t.me/{me.username}"

        invoice = await cryptobot.create_invoice(
            amount=amount,
            locale=locale,
            bot_username=bot_username,
            user_id=user_id,
            tg_id=message.from_user.id,
        )
        invreq = InvoiceRequests()
        await invreq.create_invoice(
            status="pending", user_id=user_id, platform="cryptobot", amount=amount
        )
        await message.answer(
            locale.get("pay_crypto"),
            reply_markup=crypto_button(locale, invoice.bot_invoice_url),
        )
    except Exception as e:
        logger.exception(f"error:{e}")


@user_router.callback_query(F.data == "show_refferals")
async def show_refs(callback: CallbackQuery, locale: Locale, **kwargs):
    env = EnvConfig()
    percent = env.get_ref_percent()
    await callback.answer()
    bot = kwargs.get("bot")
    me = await bot.get_me()
    tg_id = callback.from_user.id
    cryptedid = base58.b58encode_int(tg_id).decode()
    reflink = f"https://t.me/{me.username}?start={cryptedid}"
    ans = f"""{locale.get("refheader")}

{locale.get("your_reflink")} {reflink}
{locale.get("ref_percent")} {percent}%
    """
    user = UserRequests()
    owner_id = await user.get_user_by_telegram_id(tg_id)
    try:
        refs = ReferralLinkRequests()
        referrals = await refs.get_referral_links_by_owner_id(owner_id=owner_id)

        for ref in referrals:
            ans += f"""• {ref.full_name}
            """
    except Exception as e:
        logger.debug(e)
    await callback.message.edit_text(ans)
