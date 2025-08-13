import requests
import json



class CryptoPayAPIClient:
    def __init__(self, api_token: str, base_url: str = "https://testnet-pay.crypt.bot/api/"):
        if not api_token:
            raise ValueError("API token cannot be empty.")
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            "Crypto-Pay-API-Token": self.api_token,
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, data: dict):
        url = f"{self.base_url}{method}"
        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status() 
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
            if response is not None:
                print(f"Status code: {response.status_code}")
                print(f"Server response: {response.text}")
            return None

    def create_invoice(
        self,
        asset: str,
        amount: float,
        description: str = None,
        hidden_message: str = None,
        paid_btn_name: str = None,
        paid_btn_url: str = None,
        payload: str = None,
        allow_comments: bool = True,
        allow_anonymous: bool = True,
        expires_in: int = None,
        currency_type: str = "crypto",
        fiat: str = None,
        accepted_assets: str = None,
        swap_to: str = None
    ):
        data = {
            "asset": asset,
            "amount": amount,
            "currency_type": currency_type,
        }

        if description: data["description"] = description
        if hidden_message: data["hidden_message"] = hidden_message
        if paid_btn_name: data["paid_btn_name"] = paid_btn_name
        if paid_btn_url: data["paid_btn_url"] = paid_btn_url
        if payload: data["payload"] = payload
        if not allow_comments: data["allow_comments"] = allow_comments
        if not allow_anonymous: data["allow_anonymous"] = allow_anonymous
        if expires_in: data["expires_in"] = expires_in
        if fiat: data["fiat"] = fiat
        if accepted_assets: data["accepted_assets"] = accepted_assets
        if swap_to: data["swap_to"] = swap_to

        

        return self._make_request("createInvoice", data)


    def get_invoices(
        self,
        asset: str = None,
        fiat: str = None,
        invoice_ids: str = None,
        status: str = None,
        offset: int = None,
        count: int = None
    ):
        data = {}
        if asset: data["asset"] = asset
        if fiat: data["fiat"] = fiat
        if invoice_ids: data["invoice_ids"] = invoice_ids
        if status: data["status"] = status
        if offset: data["offset"] = offset
        if count: data["count"] = count

        return self._make_request("getInvoices", data)

