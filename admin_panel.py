from telebot import types

def admin_handler(bot, message, db, save_db):
    chat_id = message.chat.id

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ افزودن دسته‌بندی", "➖ حذف دسته‌بندی")
    markup.row("📁 افزودن قسمت", "🗑 حذف قسمت")
    markup.row("📋 نمایش دسته‌بندی‌ها", "📤 ارسال پیام همگانی")
    markup.row("🔙 خروج پنل مدیریت")

    bot.send_message(chat_id, "پنل مدیریت\nیک گزینه انتخاب کنید:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_admin_option, bot, db, save_db)

def process_admin_option(message, bot, db, save_db):
    text = message.text
    chat_id = message.chat.id

    if text == "➕ افزودن دسته‌بندی":
        msg = bot.send_message(chat_id, "نام دسته‌بندی را وارد کنید:")
        bot.register_next_step_handler(msg, add_category, bot, db, save_db)
    elif text == "➖ حذف دسته‌بندی":
        msg = bot.send_message(chat_id, "نام دسته‌بندی را برای حذف وارد کنید:")
        bot.register_next_step_handler(msg, delete_category, bot, db, save_db)
    elif text == "📁 افزودن قسمت":
        msg = bot.send_message(chat_id, "نام دسته‌بندی را وارد کنید:")
        bot.register_next_step_handler(msg, add_episode_category, bot, db, save_db)
    elif text == "🗑 حذف قسمت":
        msg = bot.send_message(chat_id, "نام دسته‌بندی را وارد کنید:")
        bot.register_next_step_handler(msg, delete_episode_category, bot, db, save_db)
    elif text == "📋 نمایش دسته‌بندی‌ها":
        categories = "\n".join(db.get("categories", {}).keys())
        bot.send_message(chat_id, f"دسته‌بندی‌ها:\n{categories}")
        admin_handler(bot, message, db, save_db)
    elif text == "📤 ارسال پیام همگانی":
        msg = bot.send_message(chat_id, "متن پیام همگانی را وارد کنید:")
        bot.register_next_step_handler(msg, send_broadcast, bot, db)
    elif text == "🔙 خروج پنل مدیریت":
        bot.send_message(chat_id, "از پنل مدیریت خارج شدید.", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(chat_id, "گزینه نامعتبر است.")
        admin_handler(bot, message, db, save_db)

def add_category(message, bot, db, save_db):
    cat_name = message.text.strip()
    if cat_name in db["categories"]:
        bot.send_message(message.chat.id, "این دسته‌بندی قبلاً وجود دارد.")
    else:
        db["categories"][cat_name] = {}
        save_db(db)
        bot.send_message(message.chat.id, f"دسته‌بندی '{cat_name}' اضافه شد.")
    admin_handler(bot, message, db, save_db)

def delete_category(message, bot, db, save_db):
    cat_name = message.text.strip()
    if cat_name in db["categories"]:
        del db["categories"][cat_name]
        save_db(db)
        bot.send_message(message.chat.id, f"دسته‌بندی '{cat_name}' حذف شد.")
    else:
        bot.send_message(message.chat.id, "چنین دسته‌بندی‌ای وجود ندارد.")
    admin_handler(bot, message, db, save_db)

def add_episode_category(message, bot, db, save_db):
    cat_name = message.text.strip()
    if cat_name not in db["categories"]:
        bot.send_message(message.chat.id, "چنین دسته‌بندی‌ای وجود ندارد.")
        admin_handler(bot, message, db, save_db)
        return
    msg = bot.send_message(message.chat.id, "نام قسمت را وارد کنید:")
    bot.register_next_step_handler(msg, add_episode_name, bot, db, save_db, cat_name)

def add_episode_name(message, bot, db, save_db, cat_name):
    episode_name = message.text.strip()
    msg = bot.send_message(message.chat.id, "file_id ویدیو را وارد کنید:")
    bot.register_next_step_handler(msg, add_episode_file_id, bot, db, save_db, cat_name, episode_name)

def add_episode_file_id(message, bot, db, save_db, cat_name, episode_name):
    file_id = message.text.strip()
    db["categories"][cat_name][episode_name] = file_id
    save_db(db)
    bot.send_message(message.chat.id, f"قسمت '{episode_name}' به دسته‌بندی '{cat_name}' اضافه شد.")
    admin_handler(bot, message, db, save_db)

def delete_episode_category(message, bot, db, save_db):
    cat_name = message.text.strip()
    if cat_name not in db["categories"]:
        bot.send_message(message.chat.id, "چنین دسته‌بندی‌ای وجود ندارد.")
        admin_handler(bot, message, db, save_db)
        return
    msg = bot.send_message(message.chat.id, "نام قسمت را برای حذف وارد کنید:")
    bot.register_next_step_handler(msg, delete_episode_name, bot, db, save_db, cat_name)

def delete_episode_name(message, bot, db, save_db, cat_name):
    episode_name = message.text.strip()
    if episode_name in db["categories"][cat_name]:
        del db["categories"][cat_name][episode_name]
        save_db(db)
        bot.send_message(message.chat.id, f"قسمت '{episode_name}' از دسته‌بندی '{cat_name}' حذف شد.")
    else:
        bot.send_message(message.chat.id, "چنین قسمتی وجود ندارد.")
    admin_handler(bot, message, db, save_db)

def send_broadcast(message, bot, db):
    text = message.text
    count = 0
    for uid in db["users"]:
        try:
            bot.send_message(int(uid), text)
            count += 1
        except:
            continue
    bot.send_message(message.chat.id, f"پیام به {count} کاربر ارسال شد.")
    admin_handler(bot, message, db, None)
