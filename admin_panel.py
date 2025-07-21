import telebot
from telebot import types

def admin_handler(bot, message, db, save_db):
    uid = str(message.chat.id)

    @bot.message_handler(commands=['add_category'])
    def add_category_cmd(msg):
        if str(msg.chat.id) != uid:
            return
        bot.send_message(uid, "لطفا نام دسته‌بندی جدید را وارد کنید:")
        bot.register_next_step_handler_by_chat_id(uid, add_category_step)

    def add_category_step(msg):
        category_name = msg.text
        if category_name in db['categories']:
            bot.send_message(uid, "این دسته‌بندی قبلا وجود دارد.")
        else:
            db['categories'][category_name] = {}
            save_db(db)
            bot.send_message(uid, f"دسته‌بندی {category_name} اضافه شد.")
        bot.send_message(uid, "برای افزودن قسمت‌ها، دستور /add_series را ارسال کنید.")

    @bot.message_handler(commands=['add_series'])
    def add_series_cmd(msg):
        if str(msg.chat.id) != uid:
            return
        bot.send_message(uid, "نام دسته‌بندی که می‌خواهید قسمت به آن اضافه کنید را وارد کنید:")
        bot.register_next_step_handler_by_chat_id(uid, add_series_category_step)

    def add_series_category_step(msg):
        category_name = msg.text
        if category_name not in db['categories']:
            bot.send_message(uid, "دسته‌بندی وجود ندارد.")
            return
        bot.send_message(uid, "نام قسمت را وارد کنید:")
        bot.register_next_step_handler_by_chat_id(uid, lambda m: add_series_step(m, category_name))

    def add_series_step(msg, category_name):
        series_name = msg.text
        bot.send_message(uid, "file_id قسمت را وارد کنید:")
        bot.register_next_step_handler_by_chat_id(uid, lambda m: add_series_file_id_step(m, category_name, series_name))

    def add_series_file_id_step(msg, category_name, series_name):
        file_id = msg.text
        db['categories'][category_name][series_name] = file_id
        save_db(db)
        bot.send_message(uid, f"قسمت {series_name} به دسته‌بندی {category_name} اضافه شد.")

    bot.send_message(uid, "پنل مدیریت فعال شد. دستورات:\n/add_category - افزودن دسته‌بندی\n/add_series - افزودن قسمت")
