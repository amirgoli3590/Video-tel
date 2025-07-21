import requests

MERCHANT_ID = 'YOUR_ZARINPAL_MERCHANT_ID'
CALLBACK_URL = 'https://yourdomain.com/payment_callback'

def create_payment_link(user_id):
    url = "https://api.zarinpal.com/pg/v4/payment/request.json"
    data = {
        "merchant_id": MERCHANT_ID,
        "amount": 10000,
        "callback_url": f"{CALLBACK_URL}?user_id={user_id}",
        "description": "خرید اشتراک ماهانه ربات",
        "metadata": {"mobile": "", "email": ""}
    }
    try:
        response = requests.post(url, json=data)
        resp_json = response.json()
        if resp_json.get("data") and resp_json["data"].get("authority"):
            authority = resp_json["data"]["authority"]
            return f"https://www.zarinpal.com/pg/StartPay/{authority}"
        else:
            return None
    except:
        return None

def verify_payment(authority):
    url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
    data = {
        "merchant_id": MERCHANT_ID,
        "authority": authority,
        "amount": 10000
    }
    try:
        response = requests.post(url, json=data)
        resp_json = response.json()
        if resp_json.get("data") and resp_json["data"].get("code") == 100:
            return True
        return False
    except:
        return False
