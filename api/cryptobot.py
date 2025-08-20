from aiohttp.web import Application, run_app
from aiosend import CryptoPay, TESTNET
from aiosend.types import Invoice
from aiosend.webhook import AiohttpManager
import logging
from keyboards.user_keyboards import back_kb
from database.req import InvoiceRequests, UserRequests, ReferralLinkRequests
from config.locale import Locale
from config.dotenv import EnvConfig
from decimal import Decimal

logger = logging.getLogger("__name__")


class CryptoBotWebhook:
    def __init__(self, token: str, currency: str, bot):
        self.app = Application()
        self.currency = currency
        if self.currency == "RUB":
            self.myfiat = "₽"
        else:
            self.myfiat = self.currency
        self.bot = bot
        self.cp = CryptoPay(
            token, webhook_manager=AiohttpManager(self.app, "/handler"), network=TESTNET
        )
        self._setup_handlers()
        logger.info("cryptobot setup ended")

    def _setup_handlers(self):
        @self.cp.webhook()
        async def handler(invoice: Invoice) -> None:
            await self.handle_payment(invoice)

    async def handle_payment(self, invoice: Invoice):
        user_id, tg_id = invoice.payload.split("_", 1)
        user_id = int(user_id)
        tg_id = int(tg_id)
        logger.info(
            f"Received {invoice.amount} {invoice.fiat} by user:{user_id},tgid={tg_id}"
        )
        amount = invoice.amount
        user = await UserRequests().get_user_by_id(user_id)
        lang = user.locale
        locale = Locale(lang)
        await self.bot.send_message(
            chat_id=tg_id,
            text=f"{locale.get('success_message')}\n+{amount}{self.myfiat}",
            reply_markup=back_kb(locale),
        )
        await self._update_data(user_id, invoice, amount)

    async def create_invoice(self, amount: float, locale, bot_username, user_id, tg_id):
        invoice = await self.cp.create_invoice(
            amount=amount,
            currency_type="fiat",
            fiat=self.currency,
            paid_btn_name="callback",
            paid_btn_url=bot_username,
            accepted_assets=["USDT", "TON"],
            expires_in=3600,
            payload=f"{user_id}_{tg_id}",
        )
        logger.info(f"invoice link: {invoice.bot_invoice_url}")
        return invoice

    async def run(self):
        await run_app(self.app)

    async def _update_data(self, user_id, invoice, amount):
        try:
            invreq = InvoiceRequests()
            usrreq = UserRequests()
            refreq = ReferralLinkRequests()
            env = EnvConfig()

            user = await usrreq.get_user_by_id(user_id=user_id)
            balance = float(user.balance)

            referral = await refreq.get_referral_link_by_user_id(user.id)
            if referral:
                ownref = await refreq.get_referral_link_by_user_id(user_id=user_id)
                ownid = ownref.owner_id
                percent = env.get_ref_percent()

                usid = await usrreq.get_user_by_id(ownid)
                ownref_tgid = usid.telegram_id
                user_lang = usid.locale
                locale = Locale(user_lang)

                referre_fee = usid.balance + Decimal(str(percent / 100 * amount))
                logger.info(f"{percent},{percent / 100},{percent / 100 * amount}")

                await usrreq.update_user(
                    user_id=ownid, balance=usid.balance + referre_fee
                )
                await self.bot.send_message(
                    chat_id=ownref_tgid,
                    text=f"{locale.get('percent_by_referral')}{percent}{self.myfiat}",
                )
                logger.info(
                    f"referral bonus payed from {user.id},@{user.username} in {percent / 100 * amount} value"
                )

            await invreq.update_invoice(invoice_id=invoice.invoice_id, status="payed")
            await usrreq.update_user(user_id=user_id, balance=balance + amount)
        except Exception as e:
            logger.error(e)
            pass
        logger.info(f"user ballance sucessfuly updated:{balance + amount}")
