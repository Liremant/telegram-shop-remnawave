from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb():
    buttons = [
        [
            InlineKeyboardButton(text="Купить", callback_data="buy_sub"),
            InlineKeyboardButton(text="Показать мою подписку", callback_data="show_sub")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def get_rates():
  buttons = [
    [
      InlineKeyboardButton(text=locale.get)
    ]
  ]
  