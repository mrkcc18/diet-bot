import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from database import init_db, add_user, save_answers
from code_generator import generate_code
from questions import get_question

TOKEN = os.getenv("TELEGRAM_TOKEN")
user_sessions = {}

async def start(update, context):
    user = update.message.from_user
    user_id = user.id
    
    # تولید کد یکتا
    unique_code = generate_code(user.first_name)
    
    # ذخیره اطلاعات اولیه کاربر
    add_user(user_id, user.first_name, unique_code)
    
    # شروع پرسش‌ها
    user_sessions[user_id] = {
        'unique_code': unique_code,
        'current_question': 0,
        'answers': {}
    }
    
    await update.message.reply_text(
        f"سلام {user.first_name}!\n"
        f"کد پیگیری شما: {unique_code}\n"
        "لطفاً به سوالات زیر پاسخ دهید:\n\n"
        f"سوال ۱: {get_question(0)}"
    )

async def handle_answer(update, context):
    user_id = update.message.from_user.id
    if user_id not in user_sessions:
        await update.message.reply_text("لطفاً ابتدا دستور /start را وارد کنید.")
        return
    
    session = user_sessions[user_id]
    current_q = session['current_question']
    
    # ذخیره پاسخ
    session['answers'][current_q] = update.message.text
    
    # ارسال سوال بعدی
    next_question = current_q + 1
    if next_question < len(get_question.__self__.QUESTIONS):
        session['current_question'] = next_question
        await update.message.reply_text(f"سوال {next_question + 1}: {get_question(next_question)}")
    else:
        # پایان پرسش‌ها
        save_answers(user_id, session['answers'])
        await update.message.reply_text(
            "✅ پاسخ‌های شما با موفقیت ثبت شد!\n"
            "کارشناسان ما در حال طراحی رژیم اختصاصی شما هستند.\n"
            f"کد پیگیری: {session['unique_code']}"
        )
        del user_sessions[user_id]

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))
    
    app.run_polling()

if __name__ == "__main__":
    main()
