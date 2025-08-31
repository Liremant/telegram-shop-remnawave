import logging
from typing import Dict, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database.req as rq
from config.dotenv import RateConfig
from config.locale import Locale


def back_kb(locale):
    buttons = [
        InlineKeyboardButton(
            text=(
                locale.get("back")
                if hasattr(locale, "get") and callable(locale.get)
                else "⬅️ Назад"
            ),
            callback_data="back_to_main",
        )
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def main_menu_kb(locale):
    buttons = [
        [InlineKeyboardButton(text=locale.get("buy_sub"), callback_data="buy_sub")],
        [
            InlineKeyboardButton(text=locale.get("show_sub"), callback_data="show_sub"),
        ],
        [
            InlineKeyboardButton(
                text=locale.get("show_balance"), callback_data="show_balance"
            )
        ],
        [
            InlineKeyboardButton(
                text=locale.get("referral_button"), callback_data="show_refferals"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sub_kb(locale):
    bttns = [
        [InlineKeyboardButton(text=locale.get("show_sub"), callback_data="show_sub")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=bttns)


def topup_balance(locale):
    buttons = [
        [InlineKeyboardButton(text=locale.get("topup"), callback_data="topup_balance")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rates_kb(locale, config: Optional[RateConfig] = None):
    if config is None:
        config = RateConfig()

    try:
        rates = config.get_rates()
        buttons = []

        for rate_key, rate_data in rates.items():
            button_text = f"{rate_data['limit']} - {rate_data['value']}"
            callback_data = f"select_{rate_key}"

            button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
            buttons.append([button])

        back_button = InlineKeyboardButton(
            text=(
                locale.get("back")
                if hasattr(locale, "get") and callable(locale.get)
                else "⬅️ Назад"
            ),
            callback_data="back_to_main",
        )
        buttons.append([back_button])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    except ValueError as e:
        logging.error(e)
        error_button = InlineKeyboardButton(
            text=(
                locale.get("error_loading_rates")
                if hasattr(locale, "get") and callable(locale.get)
                else "Ошибка загрузки тарифов"
            ),
            callback_data="error_rates",
        )
        back_button = InlineKeyboardButton(
            text=(
                locale.get("back")
                if hasattr(locale, "get") and callable(locale.get)
                else "⬅️ Назад"
            ),
            callback_data="back_to_main",
        )
        return InlineKeyboardMarkup(inline_keyboard=[[error_button], [back_button]])


def rates_kb_compact(
    locale, config: Optional[RateConfig] = None, rates_per_row: int = 1
):
    if config is None:
        config = RateConfig()

    try:
        rates = config.get_rates()
        buttons = []
        current_row = []

        for rate_key, rate_data in rates.items():
            button_text = f"{rate_data['limit']}\n{rate_data['value']}"
            callback_data = f"select_{rate_key}"

            button = InlineKeyboardButton(text=button_text, callback_data=callback_data)

            current_row.append(button)

            if len(current_row) >= rates_per_row:
                buttons.append(current_row)
                current_row = []

        if current_row:
            buttons.append(current_row)

        back_button = InlineKeyboardButton(
            text=(
                locale.get("back")
                if hasattr(locale, "get") and callable(locale.get)
                else "⬅️ Назад"
            ),
            callback_data="back_to_main",
        )
        buttons.append([back_button])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    except ValueError as e:
        logging.error(e)
        return rates_kb(
            locale,
            config,
        )


def rate_confirmation_kb(locale, rate_key: str, rate_data: Dict[str, str]):
    confirm_text = (
        locale.get("confirm_purchase")
        if hasattr(locale, "get") and callable(locale.get)
        else f"✅ Купить {rate_data['limit']}"
    )

    change_text = (
        locale.get("change_rate")
        if hasattr(locale, "get") and callable(locale.get)
        else "🔄 Выбрать другой тариф"
    )

    cancel_text = (
        locale.get("cancel")
        if hasattr(locale, "get") and callable(locale.get)
        else "❌ Отмена"
    )

    buttons = [
        [
            InlineKeyboardButton(
                text=confirm_text, callback_data=f"confirm_purchase_{rate_key}"
            )
        ],
        [
            InlineKeyboardButton(text=change_text, callback_data="buy_sub"),
            InlineKeyboardButton(text=cancel_text, callback_data="back_to_main"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_methods_kb(locale):
    pay_card_text = (
        locale.get("pay_card")
        if hasattr(locale, "get") and callable(locale.get)
        else "💳 Банковская карта"
    )

    pay_crypto_text = (
        locale.get("pay_crypto")
        if hasattr(locale, "get") and callable(locale.get)
        else "₿ Криптовалюта"
    )

    pay_stars_text = (
        locale.get("pay_stars")
        if hasattr(locale, "get") and callable(locale.get)
        else "🥝 Stars"
    )

    back_text = (
        locale.get("back")
        if hasattr(locale, "get") and callable(locale.get)
        else "⬅️ Назад"
    )

    buttons = [
        [
            InlineKeyboardButton(text=pay_card_text, callback_data="pay_card"),
            InlineKeyboardButton(
                text=pay_crypto_text,
                callback_data="pay_crypto",
            ),
        ],
        [InlineKeyboardButton(text=pay_stars_text, callback_data="pay_stars")],
        [InlineKeyboardButton(text=back_text, callback_data="buy_sub")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def crypto_button(locale, pay_link):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=locale.get("pay"), url=pay_link)]]
    )
    return keyboard


def confirm_pay(locale, rate_id, months):
    buttons = [
        [
            InlineKeyboardButton(
                text=locale.get("pay"), callback_data=f"pay_rate:{rate_id}:{months}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rates_kb_dict_locale(
    locale_dict: Dict[str, str], config: Optional[RateConfig] = None
):
    if config is None:
        config = RateConfig()

    try:
        rates = config.get_rates()
        buttons = []

        for rate_key, rate_data in rates.items():
            button_text = f"{rate_data['limit']} - {rate_data['value']}"
            callback_data = f"select_{rate_key}"

            button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
            buttons.append([button])

        back_button = InlineKeyboardButton(
            text=locale_dict.get("back", "⬅️ Назад"), callback_data="back_to_main"
        )
        buttons.append([back_button])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    except ValueError as e:
        logging.exception(e)
        error_button = InlineKeyboardButton(
            text=locale_dict.get("error_loading_rates", "Ошибка загрузки тарифов"),
            callback_data="error_rates",
        )
        back_button = InlineKeyboardButton(
            text=locale_dict.get("back", "⬅️ Назад"), callback_data="back_to_main"
        )
        return InlineKeyboardMarkup(inline_keyboard=[[error_button], [back_button]])


def show_months(rate_id, locale):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale.get("1_month"),
                    callback_data=f"select_months_{rate_id}_1",
                )
            ],
            [
                InlineKeyboardButton(
                    text=locale.get("3_month"),
                    callback_data=f"select_months_{rate_id}_3",
                )
            ],
            [
                InlineKeyboardButton(
                    text=locale.get("6_month"),
                    callback_data=f"select_months_{rate_id}_6",
                )
            ],
            [
                InlineKeyboardButton(
                    text=locale.get("12_month"),
                    callback_data=f"select_months_{rate_id}_12",
                )
            ],
        ]
    )
    return kb


async def build_subscriptions_keyboard(user_response, uid):
    builder = InlineKeyboardBuilder()
    sublink = rq.SublinkRequests()
    subscriptions = (
        user_response.root if hasattr(user_response, "root") else user_response
    )
    userreq = rq.UserRequests()
    usr = await userreq.get_user_by_id(uid)
    user_lang = usr.locale
    locale = Locale(user_lang)

    for i, subscription in enumerate(subscriptions):
        used_gb = f"{subscription.used_traffic_bytes / 1024**3:.2f}"
        limit_gb = (
            f"{subscription.traffic_limit_bytes / 1024**3:.2f}"
            if subscription.traffic_limit_bytes > 0
            else "∞"
        )
        status_emoji = "🟢" if subscription.status.value == "ACTIVE" else "🔴"
        button_text = f"{status_emoji} {used_gb}/{limit_gb} {locale.get('GB')}"

        sub = await sublink.get_sublink_by_link(subscription.subscription_url)
        print(f"Looking for: {subscription.subscription_url}")
        print(f"Found sub: {sub}")
        if sub:
            await sublink.update_sublink(
                sublink_id=sub.id,
                used_gb=used_gb,
                limit_gb=limit_gb,
                status=subscription.status.value,
            )
        else:
            logging.error("WTF")
        builder.add(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"sub_info:{sub.id}:{subscription.status.value}:{used_gb}:{limit_gb}:{subscription.expire_at}",
            )
        )
    total_subs = len(subscriptions)
    if total_subs <= 5:
        builder.adjust(1)
    elif total_subs <= 10:
        builder.adjust(2)
    elif total_subs <= 15:
        builder.adjust(3)
    else:
        builder.adjust(4)

    return builder.as_markup()


async def build_subscription_detail_keyboard(subscription_url):

    builder = InlineKeyboardBuilder()
    sublink = rq.SublinkRequests
    sl = await sublink.get_sublink_by_link(subscription_url)
    uid = sl.user_id
    userreq = rq.UserRequests()
    usr = await userreq.get_user_by_id(uid)
    lang = usr.locale
    locale = Locale(lang)

    builder.add(InlineKeyboardButton(text=locale.get("open_sub"), url=f"{sl.link}"))

    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_subs"))

    builder.adjust(2, 1)

    return builder.as_markup()
