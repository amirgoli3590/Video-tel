from telebot import types

ADMIN_ID = 7536757725

def admin_handler(bot, message, db, save_db):
    chat_id = message.chat.id
    bot.send_message(chat_id, "به پنل مدیریت خوش آمدید!\n"
                              "از دستورات زیر استفاده کنید:\n"
                              "/add_category نام_دسته\n"
                              "/add_episode نام_دسته نام_قسمت file_id\n"
                              "/list_categories\n"
                              "/list_episodes نام_دسته\n"
                              "/remove_category نام_دسته\n"
                              "/remove_episode نام_دسته نام_قسمت")

@bot.message_handler(commands=['add_category'])
def add_category(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        _, category_name = message.text.split(maxsplit=1)
        if category_name in db['categories']:
            bot.send_message(message.chat.id, f"دسته‌بندی '{category_name}' قبلاً وجود دارد.")
            return
        db['categories'][category_name] = {}
        save_db(db)
        bot.send_message(message.chat.id, f"دسته‌بندی '{category_name}' با موفقیت اضافه شد.")
    except:
        bot.send_message(message.chat.id, "فرمت دستور اشتباه است.\nمثال:\n/add_category سریال_جدید")

@bot.message_handler(commands=['add_episode'])
def add_episode(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            bot.send_message(message.chat.id, "فرمت دستور اشتباه است.\nمثال:\n/add_episode خاتون قسمت1 file_id")
            return
        _, category_name, episode_name, file_id = parts
        if category_name not in db['categories']:
            bot.send_message(message.chat.id, f"دسته‌بندی '{category_name}' وجود ندارد.")
            return
        db['categories'][category_name][episode_name] = file_id
        save_db(db)
        bot.send_message(message.chat.id, f"قسمت '{episode_name}' به دسته‌بندی '{category_name}' اضافه شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"خطا در افزودن قسمت: {e}")

@bot.message_handler(commands=['list_categories'])
def list_categories(message):
    if message.chat.id != ADMIN_ID:
        return
    categories = list(db['categories'].keys())
    if categories:
        text = "دسته‌بندی‌ها:\n" + "\n".join(categories)
    else:
        text = "هیچ دسته‌بندی وجود ندارد."
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['list_episodes'])
def list_episodes(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        _, category_name = message.text.split(maxsplit=1)
        episodes = db['categories'].get(category_name)
        if not episodes:
            bot.send_message(message.chat.id, f"دسته‌بندی '{category_name}' وجود ندارد یا خالی است.")
            return
        text = f"قسمت‌های دسته‌بندی '{category_name}':\n" + "\n".join(episodes.keys())
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "فرمت دستور اشتباه است.\nمثال:\n/list_episodes خاتون")

@bot.message_handler(commands=['remove_category'])
def remove_category(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        _, category_name = message.text.split(maxsplit=1)
        if category_name not in db['categories']:
            bot.send_message(message.chat.id, f"دسته‌بندی '{category_name}' وجود ندارد.")
            return
        del db['categories'][category_name]
        save_db(db)
        bot.send_message(message.chat.id, f"دسته‌بندی '{category_name}' حذف شد.")
    except:
        bot.send_message(message.chat.id, "فرمت دستور اشتباه است.\nمثال:\n/remove_category خاتون")

@bot.message_handler(commands=['remove_episode'])
def remove_episode(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        _, category_name, episode_name = message.text.split(maxsplit=2)
        if category_name not in db['categories']:
            bot.send_message(message.chat.id, f"دسته‌بندی '{category_name}' وجود ندارد.")
            return
        if episode_name not in db['categories'][category_name]:
            bot.send_message(message.chat.id, f"قسمت '{episode_name}' در دسته‌بندی '{category_name}' وجود ندارد.")
            return
        del db['categories'][category_name][episode_name]
        save_db(db)
        bot.send_message(message.chat.id, f"قسمت '{episode_name}' از دسته‌بندی '{category_name}' حذف شد.")
    except:
        bot.send_message(message.chat.id, "فرمت دستور اشتباه است.\nمثال:\n/remove_episode خاتون قسمت1")
