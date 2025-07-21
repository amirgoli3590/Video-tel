from flask import Flask, request
import json
import datetime

app = Flask(__name__)

DB_FILE = 'database.json'

def load_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"users": {}, "categories": {}}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

@app.route('/payment_callback', methods=['GET'])
def payment_callback():
    db = load_db()
    user_id = request.args.get('user_id')
    authority = request.args.get('Authority')
    status = request.args.get('Status')

    if status == 'OK':
        # اینجا باید با زرین پال ارتباط برقرار کنی و پرداخت رو تایید کنی
        # این فقط یک نمونه ساده است؛ حتما verify_payment رو در zarinpal.py داشته باش
        from zarinpal import verify_payment
        if verify_payment(authority):
            user = db['users'].get(user_id)
            if user:
                new_expire = datetime.datetime.now() + datetime.timedelta(days=30)
                user['expire_date'] = new_expire.strftime('%Y-%m-%d')
                user['notified'] = False
                save_db(db)
                return "پرداخت موفق و اشتراک فعال شد. ممنون از خرید شما."
            else:
                return "کاربر یافت نشد."
        else:
            return "پرداخت تایید نشد."
    else:
        return "پرداخت ناموفق بود یا لغو شد."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
