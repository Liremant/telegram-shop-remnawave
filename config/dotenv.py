import os
from dotenv import load_dotenv, find_dotenv, set_key
from typing import Dict, Union, Optional
import secrets
import string


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
    def __init__(self, env_config: Optional[EnvConfig] = None):
        self.env_config = env_config or EnvConfig()

    def _format_rate(self, rate_value: Union[str, int, float]) -> str:
        if rate_value is None:
            return "0"
        currency = os.getenv("RATE_CURRENCY", "RUB")
        if currency == "RUB":
            return f"{rate_value}₽"
        elif currency:
            return f"{rate_value} {currency}"
        return str(rate_value)

    def get_rates(self) -> Dict[str, Dict[str, str]]:
        rates = {}
        rate_1_value = os.getenv("RATE")
        rate_1_name = os.getenv("RATE_NAME", "Тариф 1")
        rate_1_desc = os.getenv("RATE_DESC", "")

        if rate_1_value is None:
            raise ValueError("RATE is not set in environment")

        rates["rate_1"] = {
            "value": self._format_rate(rate_1_value),
            "name": rate_1_name,
            "desc": rate_1_desc,
        }

        for i in range(2, 10):
            rate_key = f"RATE_{i}"
            rate_name_key = f"RATE{i}_NAME"
            rate_desc_key = f"RATE{i}_DESC"

            rate_value = os.getenv(rate_key)
            rate_name = os.getenv(rate_name_key, f"Тариф {i}")
            rate_desc = os.getenv(rate_desc_key, "")

            if rate_value is not None:
                rates[f"rate_{i}"] = {
                    "value": self._format_rate(rate_value),
                    "name": rate_name,
                    "desc": rate_desc,
                }

        return rates

    def get_rate_by_number(self, rate_number: int) -> Optional[Dict[str, str]]:
        rates = self.get_rates()
        return rates.get(f"rate_{rate_number}")

    def get_all_rate_values(self) -> Dict[str, str]:
        rates = self.get_rates()
        return {key: data["value"] for key, data in rates.items()}

    def get_all_rate_names(self) -> Dict[str, str]:
        rates = self.get_rates()
        return {key: data["name"] for key, data in rates.items()}

    def get_all_rate_descs(self) -> Dict[str, str]:
        rates = self.get_rates()
        return {key: data["desc"] for key, data in rates.items()}
