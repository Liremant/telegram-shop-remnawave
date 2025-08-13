from fastapi import FastAPI, Request
from aiocryptopay import AioCryptoPay

app = FastAPI()
crypto = AioCryptoPay(token="твой_токен")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    if data.get('update_type') == 'invoice_paid':
        invoice_id = data['payload']['invoice_id']
        print(f"Оплачен инвойс: {invoice_id}")
        
    return {"status": "ok"}