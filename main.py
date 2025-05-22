
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters
)
from questions import questions
from utils.save_json import save_response_json
from utils.database import save_to_db
from utils.code_generator import generate_user_code
from utils.generate_pdf import generate_pdf

ASKING = range(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answers"] = {}
    context.user_data["current_q"] = 0
    context.user_data["user_code"] = None
    context.user_data["waiting_for_payment"] = False

    await update.message.reply_text("سلام! بریم سراغ فرم رژیم غذایی ✍️")
    await update.message.reply_text(questions[0])
    return ASKING

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_payment"):
        return  # منتظر رسید هستیم، پس سوالی نباید پرسیده بشه

    current_q = context.user_data["current_q"]
    context.user_data["answers"][questions[current_q]] = update.message.text

    current_q += 1
    if current_q < len(questions):
        context.user_data["current_q"] = current_q
        await update.message.reply_text(questions[current_q])
        return ASKING
    else:
        # فرم تمام شد
        answers = context.user_data["answers"]
        name = answers.get("نام و نام خانوادگی:")
        user_code = generate_user_code(name)
        context.user_data["user_code"] = user_code

        data = {
            "user_code": user_code,
            "name": name,
            "answers": answers,
        }

        json_path = save_response_json(user_code, data)
        save_to_db(user_code, name, json_path)
        pdf_path = generate_pdf(user_code, name, answers)
        print(f"[PDF CREATED] {pdf_path}")

        summary = "\n\n".join([f"{q}\n{a}" for q, a in answers.items()])
        await update.message.reply_text(f"✅ فرم شما کامل شد. خلاصه پاسخ‌ها:\n\n{summary}")
        await update.message.reply_text(f"📌 کد پیگیری شما: {user_code}")
        await update.message.reply_text("لطفاً تصویر رسید پرداخت خود را ارسال کنید 💳")

        context.user_data["waiting_for_payment"] = True
        return ASKING

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_payment"):
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    user_code = context.user_data.get("user_code")
    if not user_code:
        await update.message.reply_text("کد شما یافت نشد. لطفاً فرم را دوباره پر کنید.")
        return

    os.makedirs("data/payments", exist_ok=True)
    payment_path = f"data/payments/{user_code}.jpg"
    await file.download_to_drive(payment_path)

    await update.message.reply_text("✅ رسید شما دریافت شد، منتظر بررسی مدیر باشید.")
    print(f"[PAYMENT RECEIVED] {payment_path}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرم متوقف شد ❌")
    return ConversationHandler.END

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()

