import logging
import database.req as rq
import base58
from config.dotenv import RateConfig
from decimal import Decimal

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        self.client = rq.UserRequests()

    async def create_or_get_user(self, name, telegram_id, userlang, username=None):

        usr = await self.client.get_user_by_telegram_id(telegram_id)
        if usr:
            logger.info("user found in db,returning...")
            return False, usr
        else:
            logger.info("user not found!creating...")
            usr = await self.client.create_user(
                username=username, name=name, telegram_id=telegram_id, locale=userlang
            )
            logger.info(f"user created!tgid={telegram_id}")
            return True, usr


class ReferralService:
    def __init__(self):
        self.ref = rq.ReferralLinkRequests()

    async def create_or_get_referral(
        self, cryptid, bot, user_id, user_tgid, full_name, locale, username=None
    ):

        owner_tgid = base58.b58decode_int(cryptid)
        owner = await self.ref.get_user_by_telegram_id(owner_tgid)
        owner_id = owner.id
        refuser = await self.ref.get_user_by_id(user_id)
        user = await self.ref.get_referral_link_by_user_id(refuser.id)
        if user:
            return user
        else:
            refuser = await self.ref.create_referral(
                owner_id=owner_id,
                user_id=user_id,
                user_tgid=user_tgid,
                user_full_name=full_name,
            )

            if username:
                ans = (
                    f"{locale.get('referral_connected')}\n• {full_name}\n• @{username}"
                )
            else:
                ans = f"{locale.get('referral_connected')}\n• {full_name}"

            logger.info(f"referral created!from:{owner_tgid},ref:{user_tgid}")
            await bot.send_message(chat_id=owner_tgid, text=f"{ans}")
            return refuser


class PaymentService:
    def __init__(self):
        self.user_requests = rq.UserRequests()
        self.sublink_requests = rq.SublinkRequests()
        self.rateConfig = RateConfig()

    async def service_pay_rate(
        self,
        tgid,
        callbackdata,
    ):
        rate_number = callbackdata.split(":")[1]
        months = callbackdata.split(":")[2]
        usr = await self.user_requests.get_user_by_telegram_id(tgid)
        rate_data = self.rateConfig.get_rate_by_number(rate_number)
        value = Decimal(str(rate_data["value"]))
        limit = int(rate_data["limit"])
        limit_bytes = limit * 1024**3
        if usr.balance >= value:
            await self.user_requests.update_user(
                user_id=usr.id, balance=usr.balance - value
            )
            sub = await self.sublink_requests.create_user(tgid, months, limit_bytes)
            await self.sublink_requests.create_sublink(
                link=sub.subscription_url,
                expires_at=sub.expire_at,
                username=sub.username,
                user_id=usr.id,
                limit_gb=sub.traffic_limit_bytes / 1024**3,
                status=sub.status,
            )
            logger.info(f"sublink created:{sub.subscription_url}")
            return True, usr.balance - value

        else:
            return False, usr.balance
