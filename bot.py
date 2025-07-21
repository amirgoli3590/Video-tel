import telebot
import json
import datetime
import threading
import time
from admin_panel import admin_handler
from zarinpal import create_payment_link, verify_payment

TOKEN = '7621509071:AAGQQFbqxI5hvJBRoYEhGvicmT9P0dJSi_U'
ADMIN_ID = 7536757725
DB_FILE = 'database.json'

bot = telebot.TeleBot(TOKEN)

# Load & Save DB
def load_db():
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"users": {}, "categories": {}}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

db = load_db()

# Check subscription
def has_access(user_id):
    user = db['users'].get(str(user_id))
    if not user:
        return False
    expire_str = user.get('subscription_expiry')
    if not expire_str:
        return False
    expire_date = datetime.datetime.strptime(expire_str, '%Y-%m-%d')
    return datetime.datetime.now() <= expire_date

# Notify users 1 day before expiry
def notify_expiring_users():
    while True:
        now = datetime.datetime.now()
        changed = False
        for uid, user in db['users'].items():
            expire_str = user.get('subscription_expiry')
            if expire_str:
                expire_date = datetime.datetime.strptime(expire_str, '%Y-%m-%d')
                if (expire_date - now).days == 1 and not user.get('notified'):
                    try:
                        bot.send_message(int(uid), "⏳ اشتراک شما فردا منقضی می‌شود. لطفاً تمدید کنید ✅")
                        user['notified'] = True
                        changed = True
                    except:
                        pass
        if changed:
            save_db(db)
        time.sleep(86400)  # check daily

threading.Thread(target=notify_expiring_users, daemon=True).start()

# Store user's current category
user_states = {}

def set_user_state(user_id, category):
    user_states[user_id] = category

def get_user_state(user_id):
    return user_states.get(user_id)

# Delete video message after delay
def delete_message_later(chat_id, message_id, delay=30):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "⏳ ویدیو ۳۰ ثانیه روی ربات بود و الان حذف شد، لطفا سیو کنید.")
    except:
        pass

# Handle /start command
@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = str(message.chat.id)
    if uid == str(ADMIN_ID):
        admin_handler(bot, message, db, save_db)
        return
    if uid not in db['users']:
        start_date = datetime.datetime.now()
        expire_date = start_date + datetime.timedelta(days=7)
        db['users'][uid] = {
            "username": message.from_user.username,
            "subscription": "free",
            "subscription_expiry": expire_date.strftime('%Y-%m-%d'),
            "notified": False
        }
        save_db(db)
        bot.send_message(message.chat.id, "🎉 خوش آمدید! ۷ روز اشتراک رایگان دارید.")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📂 دسته‌بندی‌ها", "🛒 خرید اشتراک")
    bot.send_message(message.chat.id, "از منو انتخاب کنید:", reply_markup=markup)

# Show categories
@bot.message_handler(func=lambda m: m.text == "📂 دسته‌بندی‌ها")
def show_categories(message):
    uid = str(message.chat.id)
    if not has_access(uid):
        bot.send_message(message.chat.id, "⛔ اشتراک شما منقضی شده. لطفاً اشتراک خود را تمدید کنید.")
        return
    categories = list(db['categories'].keys())
    if not categories:
        bot.send_message(message.chat.id, "📂 هنوز دسته‌بندی‌ای اضافه نشده.")
        return
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in categories:
        markup.row(cat)
    markup.row("🔙 بازگشت")
    bot.send_message(message.chat.id, "📂 یک دسته‌بندی انتخاب کنید:", reply_markup=markup)

# Show episodes in category
@bot.message_handler(func=lambda m: m.text in db['categories'].keys())
def show_episodes(message):
    uid = str(message.chat.id)
    category = message.text
    set_user_state(uid, category)
    episodes = db['categories'][category]
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for ep in episodes.keys():
        markup.row(ep)
    markup.row("🔙 بازگشت")
    bot.send_message(message.chat.id, f"🎬 قسمت‌های {category}:", reply_markup=markup)

# Send video on episode selection
@bot.message_handler(func=lambda m: True)
def send_video(message):
    uid = str(message.chat.id)
    if message.text == "🔙 بازگشت":
        start_handler(message)
        return

    if not has_access(uid):
        bot.send_message(message.chat.id, "⛔ اشتراک شما منقضی شده. لطفاً اشتراک خود را تمدید کنید.")
        return

    category = get_user_state(uid)
    if not category:
        bot.send_message(message.chat.id, "لطفاً ابتدا یک دسته‌بندی انتخاب کنید.")
        return

    episodes = db['categories'].get(category, {})
    video_file_id = episodes.get(message.text)
    if not video_file_id:
        bot.send_message(message.chat.id, "قسمت انتخابی وجود ندارد. لطفاً مجدداً تلاش کنید.")
        return

    sent_msg = bot.send_video(message.chat.id, video_file_id)
    threading.Thread(target=delete_message_later, args=(message.chat.id, sent_msg.message_id)).start()

# Handle purchase button
@bot.message_handler(func=lambda m: m.text == "🛒 خرید اشتراک")
def buy_subscription(message):
    uid = str(message.chat.id)
    link, authority = create_payment_link(uid)
    db['users'][uid]['payment_authority'] = authority
    save_db(db)
    bot.send_message(message.chat.id, f"💳 برای خرید اشتراک روی لینک زیر کلیک کنید:\n{link}")

# Payment verification webhook or polling (باید توی zarinpal.py باشه)

# Admin panel command
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        admin_handler(bot, message, db, save_db)
    else:
        bot.send_message(message.chat.id, "⚠️ شما دسترسی به پنل مدیریت ندارید.")

if __name__ == "__main__":
    print("🤖 ربات آنلاین است...")
    bot.infinity_polling()
