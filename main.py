import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from database import init_db, add_user, save_answers
from questions import QUESTIONS

TOKEN = os.getenv("TELEGRAM_TOKEN")
app = Application.builder().token(TOKEN).build()

user_sessions = {}

async def start(update, context):
    user = update.message.from_user
    user_id = user.id
    
    # تولید کد یکتا (ساده شده)
    unique_code = f"{user.first_name[:2]}{user.id%1000}"
    
    add_user(user_id, user.first_name, unique_code)
    user_sessions[user_id] = {
        'current_question': 0,
        'answers': {},
        'unique_code': unique_code
    }
    
    await update.message.reply_text(
        f"سلام {user.first_name}!\n"
        f"کد پیگیری شما: {unique_code}\n"
        f"سوال 1: {QUESTIONS[0]}"
    )

async def handle_message(update, context):
    user_id = update.message.from_user.id
    if user_id not in user_sessions:
        await update.message.reply_text("لطفاً با دستور /start شروع کنید.")
        return
    
    session = user_sessions[user_id]
    current_q = session['current_question']
    session['answers'][current_q] = update.message.text
    
    next_q = current_q + 1
    if next_q < len(QUESTIONS):
        session['current_question'] = next_q
        await update.message.reply_text(f"سوال {next_q+1}: {QUESTIONS[next_q]}")
    else:
        save_answers(user_id, session['answers'])
        await update.message.reply_text(
            "✅ پاسخ‌های شما ثبت شد!\n"
            f"کد پیگیری: {session['unique_code']}"
        )
        del user_sessions[user_id]

def main():
    init_db()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تنظیمات بهینه برای Render
    app.run_polling(
        drop_pending_updates=True,
        close_loop=False,
        timeout=20
    )

if __name__ == "__main__":
    main()
