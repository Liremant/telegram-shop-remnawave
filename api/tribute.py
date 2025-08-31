import json
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any
from aiohttp import web
from aiogram import Bot
from config.locale import Locale
from database.req import UserRequests

logger = logging.getLogger(__name__)


class TributeWebhookHandler:
    def __init__(self, bot: Bot, remnawave_sdk, secret_key: Optional[str] = None):
        self.bot = bot
        self.remnawave = remnawave_sdk
        self.secret_key = secret_key

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        if not self.secret_key:
            logger.warning("Tribute secret key не настроен")
            return False

        if not signature:
            logger.warning("Отсутствует заголовок trbt-signature")
            return False

        try:
            expected_sig = hmac.new(
                self.secret_key.encode("utf-8"), payload, hashlib.sha256
            ).hexdigest()

            is_valid = hmac.compare_digest(expected_sig, signature)

            if not is_valid:
                logger.warning("Неверная подпись webhook")

            return is_valid

        except Exception as e:
            logger.error(f"Ошибка при верификации подписи: {e}")
            return False

    async def handle_donation(self, payload_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            telegram_user_id = payload_data.get("telegram_user_id")
            amount = payload_data.get("amount")
            currency = payload_data.get("currency", "USD")
            message = payload_data.get("message", "")
            donation_request_id = payload_data.get("donation_request_id")
            donation_name = payload_data.get("donation_name", "")
            anonymously = payload_data.get("anonymously", False)

            if not telegram_user_id or not amount or not donation_request_id:
                logger.error("Отсутствуют обязательные поля")
                return {"status": "error", "reason": "missing_required_fields"}

            try:
                user = UserRequests()
                us = await user.get_user_by_telegram_id(telegram_user_id)
                user_lang = us.locale if us else "ru"
                locale = Locale(user_lang)
            except Exception as e:
                logger.error(f"Ошибка получения пользователя {telegram_user_id}: {e}")
                locale = Locale("ru")

            try:
                amount_cents = int(amount)
                amount_dollars = amount_cents / 100.0
            except (ValueError, TypeError):
                logger.error(f"Неверный формат суммы: {amount}")
                return {"status": "error", "reason": "invalid_amount"}

            donor_name = (
                locale.get("anonymous_donor")
                if anonymously
                else locale.get("supporter")
            )

            logger.info(
                f"Tribute donation: user={telegram_user_id}, amount={amount_dollars} {currency}"
            )

            notification_text = self._format_donation_message(
                donor_name, amount_dollars, currency, message, donation_name, locale
            )

            try:
                await self.bot.send_message(
                    chat_id=telegram_user_id, text=notification_text, parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")

            await self._process_donation_rewards(telegram_user_id, amount_dollars)

            return {"status": "ok"}

        except Exception as e:
            logger.exception(f"Ошибка обработки доната: {e}")
            return {"status": "error", "reason": "processing_failed"}

    def _format_donation_message(
        self,
        donor_name: str,
        amount: float,
        currency: str,
        message: str,
        donation_name: str,
        locale: Locale,
    ) -> str:
        msg = "💰 <b>Новый донат</b>\n\n"
        msg += f"🎯 {donation_name}\n" if donation_name else ""
        msg += f"👤 От: <b>{donor_name}</b>\n"
        msg += f"💵 Сумма: <b>{amount} {currency}</b>\n"

        if message.strip():
            msg += f"💬 Сообщение: <i>{message}</i>\n"

        return msg

    async def _process_donation_rewards(self, user_id: int, amount: float):
        try:
            days_to_add = int(amount)
            if days_to_add > 0:
                logger.info(f"Добавлено {days_to_add} дней пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при обработке вознаграждений: {e}")

    async def handle_webhook(self, request: web.Request) -> web.Response:
        try:
            raw_body = await request.read()

            signature = request.headers.get("trbt-signature", "")

            if not self.verify_signature(raw_body, signature):
                logger.warning("Неверная подпись Tribute webhook")
                return web.json_response(
                    {"status": "error", "reason": "invalid_signature"}, status=401
                )

            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                return web.json_response(
                    {"status": "error", "reason": "invalid_json"}, status=400
                )

            event_name = payload.get("name")
            payload_data = payload.get("payload", {})

            if event_name == "new_donation":
                result = await self.handle_donation(payload_data)
                status_code = 200 if result["status"] == "ok" else 400
                return web.json_response(result, status=status_code)
            else:
                logger.warning(f"Неизвестный тип события: {event_name}")
                return web.json_response(
                    {"status": "error", "reason": "unknown_event_type"}, status=400
                )

        except Exception as e:
            logger.exception(f"Критическая ошибка webhook: {e}")
            return web.json_response(
                {"status": "error", "reason": "internal_error"}, status=500
            )
