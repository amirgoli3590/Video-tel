import telebot
import json
import datetime
import threading
import time
from telebot import types
from admin_panel import admin_handler
from zarinpal import create_payment_link, verify_payment

TOKEN = 'توکن_ربات_تو_اینجا'
CHANNEL_ID = '@نام_کانال_خصوصی_تو'
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

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    if uid == str(ADMIN_ID):
        admin_handler(bot, message, db, save_db)
        return

    if uid not in db['users']:
        add_new_user(uid, message.from_user.username)
        bot.send_message(uid, "🌹 خوش آمدی به ربات ما!")
    else:
        bot.send_message(uid, "👋 خوش آمدی دوباره!\nبرای دیدن دسته‌بندی‌ها دکمه 📁 دسته‌بندی‌ها را بزن.")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 خرید اشتراک", "📁 دسته‌بندی‌ها")
    bot.send_message(uid, "لطفا یکی از گزینه‌ها را انتخاب کن:", reply_markup=markup)

def add_new_user(uid, username):
    db['users'][uid] = {
        'username': username,
        'subscription': False,
        'payment_authority': '',
        'notified': False
    }
    save_db(db)

@bot.message_handler(func=lambda m: m.text == "🛒 خرید اشتراک")
def buy_subscription(message):
    uid = str(message.chat.id)
    link = create_payment_link(uid)
    db['users'][uid]['payment_authority'] = link.sp  # توجه کن اینجا باید اصلاح بشه طبق ساختار لینک
    save_db(db)
    bot.send_message(uid, f"برای خرید اشتراک روی لینک زیر کلیک کن:\n{link.url}")

@bot.message_handler(func=lambda m: m.text == "📁 دسته‌بندی‌ها")
def show_categories(message):
    uid = str(message.chat.id)
    if not db['categories']:
        bot.send_message(uid, "فعلا هیچ دسته‌بندی‌ای موجود نیست.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in db['categories']:
        markup.row(category)
    markup.row("بازگشت")
    bot.send_message(uid, "دسته‌بندی‌ها:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in db['categories'])
def show_series(message):
    uid = str(message.chat.id)
    category = message.text
    series = db['categories'][category]

    if not series:
        bot.send_message(uid, "فعلا هیچ قسمتی در این دسته‌بندی نیست.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for serie in series:
        markup.row(serie)
    markup.row("بازگشت")
    bot.send_message(uid, f"قسمت‌های دسته‌بندی {category}:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in s for s in [serie for cat in db['categories'].values() for serie in cat]))
def send_video(message):
    uid = str(message.chat.id)
    video_name = message.text

    # جستجو در تمام دسته‌ها و قسمت‌ها برای پیدا کردن فایل ایدی
    for category, series in db['categories'].items():
        if video_name in series:
            file_id = series[video_name]
            bot.send_video(uid, file_id)
            return
    bot.send_message(uid, "قسمت پیدا نشد.")

if __name__ == '__main__':
    bot.infinity_polling()
