class Locale:
    def __init__(self, user_lang=None):
        self.user_lang = user_lang  # добавляешь поддержку языка
        self.translations = {
            "en": {
                "greeting": "Hello! Welcome to the vpn shop!",
                "choose_rate": "Choose a plan",
                "buy_sub": "Buy a subscription",
                "show_sub": "Show subscription",
                "back": "⬅️ Back",
                "cancel": "❌ Cancel",
                "confirm": "✅ Confirm",
                "rate_selected": "You have selected:",
                "confirm_purchase": "✅ Buy this plan",
                "change_rate": "🔄 Choose another plan",
                "confirm_question": "Confirm your purchase:",
                "error_loading_rates": "Error loading plans",
                "rate_not_found": "Plan not found",
                "choose_payment": "Choose payment method:",
                "pay_card": "💳 Bank Card",
                "pay_crypto": "₿ Cryptocurrency",
                "pay_stars": "⭐ Stars",
                "sub": "Subscription:",
                "active": "✅ Active",
                "expired": "❌ Expired",
                "no_subscription": "You don't have an active subscription",
                "loading": "⏳ Loading...",
                "success": "✅ Success!",
                "error": "❌ Error",
                "try_again": "🔄 Try again",
                "GB": "GB",
                "sub_url": "Subscription url",
                "traffic_used": "Traffic used",
                "traffic_limit": "Traffic limit",
                "status": "Status",
                "topup": "Top-up ballance",
                "info_ballance": "Your ballance:",
                "buy_rate": "Buy rate:",
                "rate_value": "Price:",
                "rate_description": "Description",
                "rate_period": "Period:",
                "payment_description": "VPN subscription payment",
                "thanks_for_purchase": "Thanks for purchase!",
                "enter_amount": "Enter amount to top up (in RUB):",
                "invalid_amount": "Invalid amount",
                "amount_too_large": "Amount is too large",
                "invalid_amount_format": "Invalid amount format",
                "payment_created": "Payment created",
                "amount": "Amount",
                "expires_in": "Expires in 1 hour",
                "pay_by_this_link": "Pay by this link",
                "payment_creation_error": "Payment creation error",
                "user_not_found": "User not found"
            },
            "ru": {
                "greeting": "Привет! Добро пожаловать в магазин vpn!",
                "choose_rate": "Выберите тариф",
                "buy_sub": "Купить подписку",
                "show_sub": "Показать подписку",
                "back": "⬅️ Назад",
                "cancel": "❌ Отмена",
                "confirm": "✅ Подтвердить",
                "rate_selected": "Вы выбрали:",
                "confirm_purchase": "✅ Купить этот тариф",
                "change_rate": "🔄 Выбрать другой тариф",
                "confirm_question": "Подтвердите покупку:",
                "error_loading_rates": "Ошибка загрузки тарифов",
                "rate_not_found": "Тариф не найден",
                "choose_payment": "Выберите способ оплаты:",
                "pay_card": "💳 Банковская карта",
                "pay_crypto": "₿ Криптовалюта",
                "pay_stars": "⭐ Звезды",
                "active": "✅ Активна",
                "expires": "❌ Истекла",
                "no_subscription": "У вас нет активной подписки",
                "loading": "⏳ Загрузка...",
                "success": "✅ Успешно!",
                "error": "❌ Ошибка",
                "try_again": "🔄 Попробовать снова",
                "GB": "ГБ",
                "sub": "Подписка",
                "sub_url": "Ссылка на подписку",
                "traffic_used": "Использовано",
                "traffic_limit": "Лимит трафика",
                "status": "Статус",
                "topup": "Пополнить баланс",
                "info_ballance": "Ваш баланс:",
                "buy_rate": "Приобрести тариф:",
                "rate_value": "Стоимость:",
                "rate_description": "Описание:",
                "rate_period": "Длительность:",
                "payment_description": "Оплата VPN подписки",
                "thanks_for_purchase": "Спасибо за покупку!",
                "enter_amount": "Введите сумму для пополнения (в рублях):",
                "invalid_amount": "Неверная сумма",
                "amount_too_large": "Слишком большая сумма",
                "invalid_amount_format": "Неверный формат суммы",
                "payment_created": "Платеж создан",
                "amount": "Сумма",
                "expires_in": "Истекает через 1 час",
                "pay_by_this_link": "Оплатить по этой ссылке",
                "payment_creation_error": "Ошибка создания платежа",
                "user_not_found": "Пользователь не найден"
            },
        }

    def get_language(self):
        """Возвращает установленный язык"""
        return self.user_lang or "en"
    
    def set_language(self, lang):
        """Устанавливает язык"""
        self.user_lang = lang

    def get(self, key, message=None):
        user_lang = "en"

        if self.user_lang:
            user_lang = self.user_lang
        elif message:
            if hasattr(message, "message") and hasattr(message.message, "from_user"):
                user_lang = getattr(message.message.from_user, "language_code", "en")
            elif hasattr(message, "from_user") and hasattr(
                message.from_user, "language_code"
            ):
                user_lang = message.from_user.language_code

        translations = self.translations.get(user_lang, self.translations["en"])
        return translations.get(key, key)

    def add_translation(self, lang: str, key: str, value: str):
        if lang not in self.translations:
            self.translations[lang] = {}
        self.translations[lang][key] = value

    def get_supported_languages(self):
        return list(self.translations.keys())

    def get_all_keys(self):
        all_keys = set()
        for lang_dict in self.translations.values():
            all_keys.update(lang_dict.keys())
        return sorted(list(all_keys))