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


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserManager:
    def __init__(self, remnawave_client):
        self.client = remnawave_client

    def generate_username(self):
        u = uuid.uuid4()
        b64 = base64.urlsafe_b64encode(u.bytes).rstrip(b"=").decode("ascii")
        return b64

    async def create_user(self, telegram_id,months,limit_bytes):
        username = self.generate_username()

        user_data = CreateUserRequestDto(
            username=username,
            expire_at=datetime.utcnow() + timedelta(days=int(months)*30),
            telegram_id=telegram_id,
            activate_all_inbounds=True,
            traffic_limit_bytes=limit_bytes,
            traffic_limit_strategy="MONTH"
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
