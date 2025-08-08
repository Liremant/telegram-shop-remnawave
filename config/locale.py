class Locale:
    def __init__(self):
        self.translations = {
            'en': {
                'greeting': 'Hello\\! Welcome to the vpn shop\\!',
                'choose_rate': 'Choose a plan',
                'buy_sub': 'Buy a subscription',
                'show_sub': 'Show subscription'
            },
            'ru': {
                'greeting': 'Привет\\! Добро пожаловать в магазин vpn\\!',
                'choose_rate': 'Выберите тариф',
                'buy_sub': 'Купить подписку',
                'show_sub': 'Показать подписку'
            }
        }
    
    def get(self, key, message=None):
        if message and hasattr(message.from_user, 'language_code'):
            user_lang = message.from_user.language_code
        else:
            user_lang = 'en'  
        
        translations = self.translations.get(user_lang, self.translations['en'])
        return translations.get(key, key)