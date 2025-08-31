from datetime import datetime, timedelta
from remnawave.models import (
    UpdateUserRequestDto,
    CreateUserRequestDto,
    TelegramUserResponseDto,
    UserResponseDto,
)
import uuid
import logging
import base64
import json
import hmac
import hashlib
from aiohttp import web

from config.locale import Locale

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserManager:
    def __init__(self, remnawave_client):
        self.client = remnawave_client

    def generate_username(self):
        u = uuid.uuid4()
        b64 = base64.urlsafe_b64encode(u.bytes).rstrip(b"=").decode("ascii")
        return b64

    async def create_user(self, telegram_id, months, limit_bytes):
        username = self.generate_username()

        user_data = CreateUserRequestDto(
            username=username,
            expire_at=datetime.utcnow() + timedelta(days=int(months) * 30),
            telegram_id=telegram_id,
            activate_all_inbounds=True,
            traffic_limit_bytes=limit_bytes,
            traffic_limit_strategy="MONTH",
        )

        created_user: UserResponseDto = await self.client.users.create_user(
            body=user_data
        )
        logger.info(f"user created:{created_user}")
        return created_user

    async def renew_subscription(self, tg_id: int, days: int):
        user = await self.create_or_get_user(tg_id)
        new_expires = datetime.utcnow() + timedelta(days=days)
        update_data = UpdateUserRequestDto(
            is_active=True, subscription_expires_at=new_expires
        )
        logger.info(
            f"Updating subscription for user {user.id}, new expiration: {new_expires}"
        )
        updated_user = await self.client.users.update_user(user.id, update_data)
        logger.info(f"Subscription updated for user {user.id}")
        return updated_user

    async def get_subscription(self, telegram_id: str):
        try:
            logger.info(f"trying to get user by telgram id:{telegram_id}")
            response: TelegramUserResponseDto = (
                await self.client.users.get_users_by_telegram_id(telegram_id)
            )
            logger.info(response)
            return response
        except Exception as e:
            logger.error(f"error while getting user:{e}")


logger = logging.getLogger(__name__)


class PanelWebhookHandler:
    def __init__(self, bot, user_manager, webhook_secret):
        self.bot = bot
        self.user_manager = user_manager
        self.webhook_secret = webhook_secret
        self.default_lang = "ru"
        logger.info("Remnawave webhook initialize")

    def _verify_signature(self, body: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            return True

        if isinstance(body, bytes):
            original_body = body.decode("utf-8")
        else:
            original_body = str(body)

        computed_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            original_body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        logger.info(f"Received: {signature}")
        logger.info(f"Computed: {computed_signature}")

        return hmac.compare_digest(computed_signature, signature)

    def _get_user_locale(self, tg_id: int) -> str:
        # default locale while WIP
        return self.default_lang

    async def _send_notification(self, tg_id: int, message: str):
        try:
            await self.bot.send_message(tg_id, message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send notification to {tg_id}: {e}")

    async def handle_webhook(self, request):
        body = await request.read()
        signature = request.headers.get("X-Remnawave-Signature", "")

        if not self._verify_signature(body, signature):
            return web.Response(status=403, text="Invalid signature")

        try:
            data = json.loads(body.decode())
        except Exception as e:
            logger.error(e)
            return web.Response(status=400, text="Invalid JSON")

        event = data.get("name") or data.get("event")
        user_data = data.get("payload") or data.get("data", {})

        if isinstance(user_data, dict) and "user" in user_data:
            user_data = user_data["user"]

        tg_id = user_data.get("telegramId")
        if not tg_id:
            return web.Response(status=200, text="No telegram ID")

        tg_id = int(tg_id)

        if event == "user.expired":
            await self._handle_expired(tg_id, user_data)
        elif event in [
            "user.expires_in_72_hours",
            "user.expires_in_48_hours",
            "user.expires_in_24_hours",
        ]:
            await self._handle_expiring(tg_id, user_data, event)

        logger.info(f"Processed webhook event: {event} for user {tg_id}")
        return web.Response(status=200, text="OK")

    async def _handle_expired(self, tg_id: int, user_data: dict):
        lang = self._get_user_locale(tg_id)
        locale = Locale(lang)

        expire_date = (
            user_data.get("expireAt", "")[:10] if user_data.get("expireAt") else ""
        )

        message = (
            f"⚠️ <b>{locale.get('sub_expired')}</b>\n\n"
            f"{locale.get('expiry_date')}{expire_date}\n"
            f"{locale.get('renew_subscription')}"
        )
        await self._send_notification(tg_id, message)

    async def _handle_expiring(self, tg_id: int, user_data: dict, event: str):
        lang = self._get_user_locale(tg_id)
        locale = Locale(lang)

        hours = {
            "user.expires_in_72_hours": 72,
            "user.expires_in_48_hours": 48,
            "user.expires_in_24_hours": 24,
        }[event]

        expire_date = (
            user_data.get("expireAt", "")[:10] if user_data.get("expireAt") else ""
        )

        message = (
            f"⏰ <b>{locale.get('sub_expires_soon')}</b>\n\n"
            f"{locale.get('hours before')}{hours}\n"
            f"{locale.get('expire_date')}{expire_date}\n"
            f"{locale.get('dont_forget_renew')}"
        )
        await self._send_notification(tg_id, message)
