import os
from dotenv import load_dotenv, find_dotenv, set_key
from typing import Dict, Optional
import secrets
import string
import logging

logger = logging.getLogger(__name__)


class EnvConfig:
    def __init__(self, env_file=".env"):
        load_dotenv(env_file)

    def get_telegram_token(self) -> str:
        token = os.getenv("BOT_TOKEN")
        if token is None:
            raise ValueError(
                "BOT_TOKEN is not set in the environment. Check your .env file."
            )
        return token

    def get_remnawave_data(self):
        token = os.getenv("REMNAWAVE_TOKEN")
        panel_url = os.getenv("PANEL_URL")

        return token, panel_url

    def get_cryptobot_data(self):
        token = os.getenv("CRYPTOBOT_TOKEN")
        currency = os.getenv("RATE_CURRENCY", "RUB")

        return token, currency

    def get_use_webhook(self) -> bool:
        return os.getenv("USE_WEBHOOK", "false").lower() == "true"

    def get_webhook_url(self) -> str:
        url = os.getenv("WEBHOOK_URL", "")
        if not url and self.get_use_webhook():
            raise ValueError("WEBHOOK_URL must be set when using webhooks")
        return url

    def get_webhook_path(self) -> str:
        return os.getenv("WEBHOOK_PATH", "/webhook")

    def get_webhook_secret(self) -> str:
        return os.getenv("WEBHOOK_SECRET", "your_secret_token_here")

    def get_webhook_host(self) -> str:
        return os.getenv("WEBHOOK_HOST", "0.0.0.0")

    def get_webhook_port(self) -> int:
        return int(os.getenv("WEBHOOK_PORT", "8080"))

    def get_currency(self):
        return os.getenv("RATE_CURRENCY")

    def get_ref_percent(self):
        return int(os.getenv("REF_PERCENT"))


class GetDatabase:
    @staticmethod
    def generate_password(length: int = 24) -> str:
        return "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
        )

    def get_postgresql_data(self) -> str:
        load_dotenv()
        passwd = os.getenv("PSQL_PASSWD")
        if not passwd:
            passwd = self.generate_password()
            env_file = find_dotenv() or ".env"
            set_key(env_file, "PSQL_PASSWD", passwd)
            print(f"Generated and saved new password to .env: {passwd}")

        user = os.getenv("PSQL_USER", "admin")
        host = os.getenv("PSQL_HOST", "localhost")
        port = os.getenv("PSQL_PORT", "5432")
        db = os.getenv("PSQL_DB", "users")
        return passwd, user, host, port, db


class RateConfig:
    def _format_rate(self) -> str:
        currency = os.getenv("RATE_CURRENCY", "RUB")
        if currency == "RUB":
            return "₽"
        elif currency:
            return currency

    def get_rates(self) -> Dict[str, Dict[str, str]]:
        rates = {}
        rate_1_value = int(os.getenv("RATE"))
        rate_1_limit = os.getenv("RATE_LIMIT")
        rate_1_desc = os.getenv("RATE_DESC")

        logger.info(type(rate_1_value))

        if rate_1_value is None:
            raise ValueError("RATE is not set in environment")

        rates["rate_1"] = {
            "value": rate_1_value,
            "currency": self._format_rate(),
            "limit": rate_1_limit,
            "desc": rate_1_desc
        }

        for i in range(2, 10):
            rate_key = f"RATE_{i}"
            rate_limit = f'RATE{i}_LIMIT'
            rate_dsc = f'RATE{i}_DESC'
            
            rate_value = os.getenv(rate_key)
            rate_lmt = os.getenv(rate_limit)
            rate_desc = os.getenv(rate_dsc)
            if rate_value is not None:
                rates[f"rate_{i}"] = {
                    "value": rate_value,
                    "currency": self._format_rate(),
                    "limit": rate_lmt,
                    "desc": rate_desc
                }

        return rates

    def get_rate_by_number(self, rate_number: int) -> Optional[Dict[str, str]]:
        rates = self.get_rates()
        return rates.get(f"rate_{rate_number}")

    def get_all_rate_values(self) -> Dict[str, str]:
        rates = self.get_rates()
        return {key: data["value"] for key, data in rates.items()}

    def get_all_rate_limits(self) -> Dict[str, str]:
        rates = self.get_rates()
        return {key: data["limit"] for key, data in rates.items()}

    def get_all_rate_descs(self) -> Dict[str, str]:
        rates = self.get_rates()
        return {key: data["desc"] for key, data in rates.items()}

    def get_value_by_number(self, rate_number: int) -> Optional[str]:
        load_dotenv()
        key = "RATE" if int(rate_number) == 1 else f"RATE_{rate_number}"
        rate_value = os.getenv(key)

        if rate_value is None:
            logger.error(f"key not found:{key}")
            return None

        if rate_value is None:
            logger.info("БЛЯТЬ МЫ В ДЕРЬМЕ")
            return None

        return rate_value

    def get_minimal_amount(self):
        return os.getenv("MINIMAL_AMOUNT", default=100)
