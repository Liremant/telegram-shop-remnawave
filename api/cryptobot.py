from aiohttp import web
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.update import Update
import logging
from config.dotenv import EnvConfig
import database.req as rq

logger = logging.getLogger(__name__)


class CryptoBotWebhook:
    def __init__(self):
        self.config = EnvConfig()
        self.token, self.currency = self.config.get_cryptobot_data()
        self.crypto = AioCryptoPay(token=self.token, network=Networks.TEST_NET)
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.crypto.pay_handler()
        async def invoice_paid(update: Update, app) -> None:
            logger.info(update)
    
    async def cr_invoice(self, amount: float, period: str, locale,expires_in: int,user_id) -> str:
        invoice = await self.crypto.create_invoice(
            amount=amount,
            description=f"{locale.get('payment_description')}:",
            hidden_message=locale.get('thanks_for_purchase'),
            paid_btn_name='callback',
            expires_in=expires_in
        )
        rq.create_invoice(status='pending',user_id=user_id,platform='cryptobot',rate=amount)
        return invoice.bot_invoice_url
    
    async def close_session(self):
        await self.crypto.close()
    
    def setup_routes(self, app: web.Application):
        app.add_routes([web.post('/crypto-secret-path', self.crypto.get_updates)])
        app.on_shutdown.append(lambda app: self.close_session())


def setup_crypto_webhook(app: web.Application):
    crypto_webhook = CryptoBotWebhook()
    crypto_webhook.setup_routes(app)
    return crypto_webhook