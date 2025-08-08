import os
from dotenv import load_dotenv

class BaseConfig:
    def __init__(self, env_file=".env"):
        load_dotenv(env_file)

    def get_telegram_token(self):
        token = os.getenv("BOT_TOKEN")
        if token is None:
            raise ValueError("BOT_TOKEN is not set in the environment. Check your .env file.")
        return token

    def get_rate_1(self, rate_1, default=None):
        rate = os.getenv(rate_1, default)
        if os.getenv('RATE_CURRENCY') == 'RUB':
            return f'{str(rate)}₽'
        return rate 

    def get_rates_2_3(self, rate_2=None, rate_3=None, default=0):
        rates = {}
        if rate_2:
            rates["rate_2"] = os.getenv(rate_2, default)
        if rate_3:
            rates["rate_3"] = os.getenv(rate_3, default)
        return rates