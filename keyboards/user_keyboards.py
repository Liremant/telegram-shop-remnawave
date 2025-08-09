from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.dotenv import BaseConfig
from typing import Optional, Dict, Any


def main_menu_kb(locale):
    buttons = [
        [
            InlineKeyboardButton(
                text=locale.get('buy_sub'),
                callback_data="buy_sub"
            ),
            InlineKeyboardButton(
                text=locale.get('show_sub'),
                callback_data="show_sub"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rates_kb(locale, config: Optional[BaseConfig] = None):

    if config is None:
        config = BaseConfig()
    
    try:
        rates = config.get_rates()
        buttons = []
        

        for rate_key, rate_data in rates.items():

            button_text = f"{rate_data['name']} - {rate_data['value']}"

            callback_data = f"select_{rate_key}"
            
            button = InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )

            buttons.append([button])
        

        back_button = InlineKeyboardButton(
            text=locale.get('back') if hasattr(locale, 'get') and callable(locale.get) else '⬅️ Назад',
            callback_data="back_to_main"
        )
        buttons.append([back_button])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    except ValueError as e:

        error_button = InlineKeyboardButton(
            text=locale.get('error_loading_rates') if hasattr(locale, 'get') and callable(locale.get) else 'Ошибка загрузки тарифов',
            callback_data="error_rates"
        )
        back_button = InlineKeyboardButton(
            text=locale.get('back') if hasattr(locale, 'get') and callable(locale.get) else '⬅️ Назад',
            callback_data="back_to_main"
        )
        return InlineKeyboardMarkup(inline_keyboard=[[error_button], [back_button]])


def rates_kb_compact(locale, config: Optional[BaseConfig] = None, rates_per_row: int = 1):

    if config is None:
        config = BaseConfig()
    
    try:
        rates = config.get_rates()
        buttons = []
        current_row = []
        
        for rate_key, rate_data in rates.items():
            button_text = f"{rate_data['name']}\n{rate_data['value']}"
            callback_data = f"select_{rate_key}"
            
            button = InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )
            
            current_row.append(button)
            
            if len(current_row) >= rates_per_row:
                buttons.append(current_row)
                current_row = []
        
        if current_row:
            buttons.append(current_row)
        
        back_button = InlineKeyboardButton(
            text=locale.get('back') if hasattr(locale, 'get') and callable(locale.get) else '⬅️ Назад',
            callback_data="back_to_main"
        )
        buttons.append([back_button])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    except ValueError as e:
        return rates_kb(locale, config)  


def rate_confirmation_kb(locale, rate_key: str, rate_data: Dict[str, str]):

    confirm_text = (locale.get('confirm_purchase') 
                   if hasattr(locale, 'get') and callable(locale.get) 
                   else f'✅ Купить {rate_data["name"]}')
    
    change_text = (locale.get('change_rate') 
                  if hasattr(locale, 'get') and callable(locale.get) 
                  else '🔄 Выбрать другой тариф')
    
    cancel_text = (locale.get('cancel') 
                  if hasattr(locale, 'get') and callable(locale.get) 
                  else '❌ Отмена')
    
    buttons = [
        [
            InlineKeyboardButton(
                text=confirm_text,
                callback_data=f"confirm_purchase_{rate_key}"
            )
        ],
        [
            InlineKeyboardButton(
                text=change_text,
                callback_data="buy_sub"
            ),
            InlineKeyboardButton(
                text=cancel_text,
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_methods_kb(locale, rate_key: str):

    pay_card_text = (locale.get('pay_card') 
                    if hasattr(locale, 'get') and callable(locale.get) 
                    else '💳 Банковская карта')
    
    pay_crypto_text = (locale.get('pay_crypto') 
                      if hasattr(locale, 'get') and callable(locale.get) 
                      else '₿ Криптовалюта')
    
    pay_stars_text = (locale.get('pay_stars') 
                    if hasattr(locale, 'get') and callable(locale.get) 
                    else '🥝 Stars')
    
    back_text = (locale.get('back') 
                if hasattr(locale, 'get') and callable(locale.get) 
                else '⬅️ Назад')
    
    buttons = [
        [
            InlineKeyboardButton(
                text=pay_card_text,
                callback_data=f"pay_card_{rate_key}"
            ),
            InlineKeyboardButton(
                text=pay_crypto_text,
                callback_data=f"pay_crypto_{rate_key}"
            )
        ],
        [
            InlineKeyboardButton(
                text=pay_stars_text,
                callback_data=f"pay_stars_{rate_key}"
            )
        ],
        [
            InlineKeyboardButton(
                text=back_text,
                callback_data="buy_sub"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rates_kb_dict_locale(locale_dict: Dict[str, str], config: Optional[BaseConfig] = None):

    if config is None:
        config = BaseConfig()
    
    try:
        rates = config.get_rates()
        buttons = [] 
        
        for rate_key, rate_data in rates.items():
            button_text = f"{rate_data['name']} - {rate_data['value']}"
            callback_data = f"select_{rate_key}"
            
            button = InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )
            buttons.append([button])
        
        back_button = InlineKeyboardButton(
            text=locale_dict.get('back', '⬅️ Назад'),
            callback_data="back_to_main"
        )
        buttons.append([back_button])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    except ValueError as e:
        error_button = InlineKeyboardButton(
            text=locale_dict.get('error_loading_rates', 'Ошибка загрузки тарифов'),
            callback_data="error_rates"
        )
        back_button = InlineKeyboardButton(
            text=locale_dict.get('back', '⬅️ Назад'),
            callback_data="back_to_main"
        )
        return InlineKeyboardMarkup(inline_keyboard=[[error_button], [back_button]])



