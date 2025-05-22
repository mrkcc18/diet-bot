import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from database import init_db, add_user
from code_generator import generate_code  # این را بعداً می‌سازیم

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update, context):
    user = update.message.from_user
    unique_code = generate_code(user.first_name)  # تولید کد یکتا
    add_user(user.id, user.first_name, unique_code)  # ذخیره در دیتابیس
    
    await update.message.reply_text(
        f"سلام {user.first_name}!\n"
        f"کد پیگیری شما: {unique_code}\n"
        "لطفاً به سوالات رژیم‌گیری پاسخ دهید."
    )

def main():
    init_db()  # ایجاد دیتابیس در اولین اجرا
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
