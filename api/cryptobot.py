from aiohttp import web
from aiocryptopay import AioCryptoPay, Networks
from aiocryptopay.models.update import Update
import logging
import asyncio
from config.dotenv import EnvConfig
import database.req as rq
import json
from config.locale import Locale

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
            logger.info(f"Invoice paid: {update}")
            
            try:

                await rq.InvoiceRequests.update_invoice(
                    invoice_id=update.payload.invoice_id,
                    status="paid"
                )
                logger.info(f"Invoice {update.payload.invoice_id} marked as paid")
                
                if update.payload.payload:
                    try:
                        payload_data = json.loads(update.payload.payload)
                        user_id = payload_data.get("user_id")
                        user_lang = payload_data.get("user_lang", "en")
                        amount = payload_data.get("amount", update.payload.amount)
                        
                        if user_id:
                            try:
                                user = await rq.UserRequests.get_user_by_id(user_id)
                                if not user:
                                    logger.error(f"User with id {user_id} not found")
                                    return

                                locale = Locale(user_lang)
                                success_text = locale.get("success")
                                message = f"{success_text}\n💰 +{amount}₽"
                                
                                bot = app["bot"]
                                await bot.send_message(user.telegram_id, message)
                                
                                logger.info(f"Payment success notification should be sent to user {user.telegram_id}")
                                
                            except Exception as e:
                                logger.error(f"Failed to send notification: {e}")
                                                
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse payload: {e}")
                
            except Exception as e:
                logger.error(f"Failed to update invoice status: {e}")
            return True

    
    async def _create_invoice_internal(
        self, crypto_instance, amount: float, locale, expires_in: int, user_id, btn_url=None
    ):
        user_lang = getattr(locale, 'user_lang', 'en') if hasattr(locale, 'user_lang') else 'en'
        
        invoice = await crypto_instance.create_invoice(
            currency_type='fiat',
            amount=amount,
            fiat=self.currency,
            description=f"{locale.get('payment_description')}",
            hidden_message=locale.get("thanks_for_purchase"),
            paid_btn_name="callback",
            expires_in=expires_in,
            paid_btn_url=btn_url,
            lang=user_lang,
            accepted_assets=['USDT', 'TON']
        )
        
        await rq.InvoiceRequests.create_invoice(
            status="pending", 
            user_id=user_id, 
            platform="cryptobot", 
            rate=amount
        )
        
        return invoice

    async def create_invoice(self, amount: float, locale, expires_in: int, user_id, btn_url=None):
        try:
            invoice = await self._create_invoice_internal(
                self.crypto, amount, locale, expires_in, user_id, btn_url
            )
            
            return {
                "ok": True,
                "result": {
                    "pay_url": invoice.bot_invoice_url,
                    "invoice_id": invoice.invoice_id,
                    "amount": amount
                }
            }
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return {"ok": False, "error": {"name": str(e), "code": "INVOICE_CREATION_ERROR"}}

    async def create_invoice_with_new_session(self, amount: float, locale, expires_in: int, user_id, btn_url=None):
        try:
            async with CryptoBotManager() as crypto:
                invoice = await self._create_invoice_internal(
                    crypto, amount, locale, expires_in, user_id, btn_url
                )
                
                return {
                    "ok": True,
                    "result": {
                        "pay_url": invoice.bot_invoice_url,
                        "invoice_id": invoice.invoice_id,
                        "amount": amount
                    }
                }
        except Exception as e:
            logger.error(f"Error creating invoice with new session: {e}")
            return {"ok": False, "error": {"name": str(e), "code": "INVOICE_CREATION_ERROR"}}

    async def close_session(self):
        try:
            if self.crypto and hasattr(self.crypto, '_session'):
                session = getattr(self.crypto, '_session', None)
                if session and not session.closed:
                    await asyncio.sleep(0.1)
                    await session.close()
                    await asyncio.sleep(0.1)
                logger.info("CryptoBot session closed successfully")
        except Exception as e:
            logger.warning(f"Non-critical error closing CryptoBot session: {e}")

    def setup_routes(self, app: web.Application):
        app.add_routes([web.post("/crypto-secret-path", self.crypto.get_updates)])
        
        async def cleanup_handler(app):
            await self.close_session()
        
        app.on_cleanup.append(cleanup_handler)


def setup_crypto_webhook(app: web.Application):
    crypto_webhook = CryptoBotWebhook()
    crypto_webhook.setup_routes(app)
    return crypto_webhook


class CryptoBotManager:
    def __init__(self):
        self.config = EnvConfig()
        self.token, self.currency = self.config.get_cryptobot_data()
        self.crypto = None

    async def __aenter__(self):
        self.crypto = AioCryptoPay(token=self.token, network=Networks.TEST_NET)
        return self.crypto

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.crypto:
            try:
                await self.crypto.close()
            except Exception as e:
                logger.debug(f'fucking ssl error:{e}')
                pass


