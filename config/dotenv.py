import os
from dotenv import load_dotenv
from typing import Dict, Union, Optional


class BaseConfig:
    def __init__(self, env_file=".env"):
        load_dotenv(env_file)
    
    def get_telegram_token(self) -> str:
        token = os.getenv("BOT_TOKEN")
        if token is None:
            raise ValueError("BOT_TOKEN is not set in the environment. Check your .env file.")
        return token
    
    def _format_rate(self, rate_value: Union[str, int, float]) -> str:

        if rate_value is None:
            return "0"
        
        currency = os.getenv('RATE_CURRENCY', 'RUB')
        if currency == 'RUB':
            return f'{rate_value}₽'
        elif currency:
            return f'{rate_value} {currency}'
        return str(rate_value)
    
    def get_rates(self) -> Dict[str, Dict[str, str]]:
        rates = {}

        rate_1_value = os.getenv("RATE")
        rate_1_name = os.getenv("RATE_NAME", "Тариф 1")
        
        if rate_1_value is None:
            raise ValueError("RATE is not set in environment")
        
        rates["rate_1"] = {
            "value": self._format_rate(rate_1_value),
            "name": rate_1_name
        }
        
        for i in range(2, 10):
            rate_key = f"RATE_{i}"
            rate_name_key = f"RATE{i}_NAME"
            
            rate_value = os.getenv(rate_key)
            rate_name = os.getenv(rate_name_key, f"Тариф {i}") 
            
            if rate_value is not None:
                rates[f"rate_{i}"] = {
                    "value": self._format_rate(rate_value),
                    "name": rate_name
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


