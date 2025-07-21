import telebot
import json
import datetime
import threading
import time
from telebot import types
from admin_panel import admin_handler
from zarinpal import create_payment_link, verify_payment

TOKEN = '7621509071:AAGQQFbqxI5hvJBRoYEhGvicmT9P0dJSi_U'
CHANNEL_ID = '@amiramir3590'
ADMIN_ID = 7536757725
DB_FILE = 'database.json'

bot = telebot.TeleBot(TOKEN)

def load_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"users": {}, "categories": {}}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

db = load_db()

def has_access(user_id):
    user = db['users'].get(str(user_id))
    if not user:
        return False
    expire_str = user.get('expire_date')
    if not expire_str:
        return False
    expire_date = datetime.datetime.strptime(expire_str, "%Y-%m-%d")
    return datetime.datetime.now() <= expire_date

def add_new_user(user_id, username):
    start_date = datetime.datetime.now()
    expire_date = start_date + datetime.timedelta(days=7)
    db['users'][str(user_id)] = {
        "username": username,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "expire_date": expire_date.strftime("%Y-%m-%d"),
        "notified": False
    }
    save_db(db)

def delete_message_after(chat_id, message_id, seconds=30):
    def task():
        time.sleep(seconds)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=task).start()

def notify_expiring_users():
    while True:
        now = datetime.datetime.now()
        for uid, user in db['users'].items():
            expire_date = datetime.datetime.strptime(user['expire_date'], '%Y-%m-%d')
            days_left = (expire_date - now).days
            if days_left == 1 and not user.get('notified', False):
                try:
                    bot.send_message(uid, "⏳ اشتراک شما فردا منقضی می‌شود. لطفاً به موقع تمدید کنید.")
                    db['users'][uid]['notified'] = True
                    save_db(db)
                except:
                    pass
        time.sleep(86400)

threading.Thread(target=notify_expiring_users, daemon=True).start()

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    if uid == str(ADMIN_ID):
        admin_handler(bot, message, db, save_db)
        return
    if uid not in db['users']:
        add_new_user(uid, message.from_user.username or "")
        bot.send_message(uid,
            "سلام عزیزم 🌹\nخوش آمدی به ربات ما!\nشما 7 روز دسترسی رایگان داری.\nلطفا فیلم‌ها رو تا ۳۰ ثانیه بعد ذخیره کن.\nبرای دیدن دسته‌بندی‌ها دکمه '📂 دسته‌بندی‌ها' رو بزن.")
    else:
        bot.send_message(uid,
            "👋 خوش آمدی دوباره!\nبرای دیدن دسته‌بندی‌ها دکمه '📂 دسته‌بندی‌ها' رو بزن.")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📂 دسته‌بندی‌ها", "🛒 خرید اشتراک")
    bot.send_message(uid, "لطفا یکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🛒 خرید اشتراک")
def buy_subscription(message):
    uid = str(message.chat.id)
    link = create_payment_link(uid)
    db['users'][uid]['payment_authority'] = link.split('/')[-1]  # ذخیره کد پرداخت برای بررسی بعدی
    save_db(db)
    bot.send_message(uid,
        f"برای خرید اشتراک ماهانه ۱۰ هزار تومان روی لینک زیر کلیک کنید:\n{link}\nبعد از پرداخت اشتراک شما فعال می‌شود.")

@bot.message_handler(func=lambda m: m.text == "📂 دسته‌بندی‌ها")
def show_categories(message):
    uid = str(message.chat.id)
    if not has_access(uid):
        bot.send_message(uid, "⛔ اشتراک شما منقضی شده است. لطفاً اشتراک خریداری کنید.")
        return
    if not db['categories']:
        bot.send_message(uid, "📂 هنوز دسته‌بندی‌ای ثبت نشده.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in db['categories']:
        markup.row(cat)
    markup.row("🔙 بازگشت")
    bot.send_message(uid, "دسته‌بندی‌ها:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in db['categories'])
def show_episodes(message):
    uid = str(message.chat.id)
    category = message.text
    episodes = db['categories'][category]
    if not episodes:
        bot.send_message(uid, "📂 این دسته‌بندی هنوز قسمت ندارد.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for ep in episodes:
        markup.row(ep)
    markup.row("🔙 بازگشت")
    bot.send_message(uid, f"قسمت‌های دسته‌بندی {category}:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in eps for eps in db['categories'].values()))
def send_video(message):
    uid = str(message.chat.id)
    if not has_access(uid):
        bot.send_message(uid, "⛔ اشتراک شما منقضی شده است.")
        return
    video_name = message.text
    file_id = None
    for cat, eps in db['categories'].items():
        if video_name in eps:
            file_id = eps[video_name]
            break
    if not file_id:
        bot.send_message(uid, "⚠️ فایل پیدا نشد.")
        return
    msg = bot.send_video(uid, file_id)
    bot.send_message(uid, "🎥 فیلم تا ۳۰ ثانیه دیگر حذف می‌شود، لطفاً ذخیره کنید.")
    delete_message_after(uid, msg.message_id, 30)

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت")
def go_back(message):
    start(message)

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.chat.id == ADMIN_ID:
        admin_handler(bot, message, db, save_db)
    else:
        bot.send_message(message.chat.id, "⚠️ شما دسترسی به پنل مدیریت ندارید.")

print("ربات شروع به کار کرد...")
bot.infinity_polling()
