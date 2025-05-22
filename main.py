import os
from telegram import Update, InputFile
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
        return

    current_q = context.user_data["current_q"]
    context.user_data["answers"][questions[current_q]] = update.message.text

    current_q += 1
    if current_q < len(questions):
        context.user_data["current_q"] = current_q
        await update.message.reply_text(questions[current_q])
        return ASKING
    else:
        answers = context.user_data["answers"]
        name = answers.get("نام و نام خانوادگی:")
        user_code = generate_user_code(name)
        context.user_data["user_code"] = user_code

        data = {
            "user_code": user_code,
            "name": name,
            "answers": answers,
            "telegram_user_id": update.effective_user.id
        }

        json_path = save_response_json(user_code, data)
        save_to_db(user_code, name, json_path)
        pdf_path = generate_pdf(user_code, name, answers)
        context.user_data["pdf_path"] = pdf_path

        await update.message.reply_text(f"✅ فرم شما کامل شد. کد پیگیری شما: {user_code}\nلطفاً تصویر رسید پرداخت را ارسال کنید.")
        context.user_data["waiting_for_payment"] = True
        return ASKING

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_payment"):
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    user_code = context.user_data.get("user_code")
    name = context.user_data["answers"].get("نام و نام خانوادگی:")
    pdf_path = context.user_data.get("pdf_path")
    summary = "\n\n".join([f"{q}\n{a}" for q, a in context.user_data["answers"].items()])

    os.makedirs("data/payments", exist_ok=True)
    payment_path = f"data/payments/{user_code}.jpg"
    await file.download_to_drive(payment_path)

    await update.message.reply_text("✅ رسید دریافت شد. در حال ارسال به مدیر برای تایید...")

    admin_id = int(os.getenv("ADMIN_ID"))
    await context.bot.send_message(chat_id=admin_id, text=f"📥 اطلاعات جدید دریافت شد\nکد: {user_code}\nنام: {name}")
    await context.bot.send_message(chat_id=admin_id, text=f"📋 خلاصه پاسخ‌ها:\n\n{summary}")
    if os.path.exists(pdf_path):
        await context.bot.send_document(chat_id=admin_id, document=InputFile(pdf_path))
    if os.path.exists(payment_path):
        await context.bot.send_document(chat_id=admin_id, document=InputFile(payment_path), caption="🧾 تصویر رسید پرداخت")

    print(f"[PAYMENT RECEIVED + ADMIN NOTIFIED] {payment_path}")

async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = os.getenv("ADMIN_ID")
    if str(update.effective_user.id) != str(admin_id):
        await update.message.reply_text("⛔ فقط مدیر می‌تواند پرداخت‌ها را تأیید کند.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("❗ لطفاً کد کاربر را به صورت `/verify <code>` وارد کنید.")
        return

    user_code = context.args[0]
    receipt_path = f"data/payments/{user_code}.jpg"

    if not os.path.exists(receipt_path):
        await update.message.reply_text("❌ رسیدی برای این کد یافت نشد.")
        return

    await update.message.reply_text(f"✅ رسید مربوط به {user_code} تأیید شد.")
    print(f"[VERIFIED] {user_code}")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Your Telegram ID is: {update.effective_user.id}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرم متوقف شد ❌")
    return ConversationHandler.END

async def submit_diet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = os.getenv("ADMIN_ID")
    if str(update.effective_user.id) != str(admin_id):
        await update.message.reply_text("⛔ فقط مدیر می‌تواند رژیم را ارسال کند.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("❗ لطفاً کد کاربر را به صورت `/submit_diet <code>` وارد کنید.")
        return

    user_code = context.args[0]
    json_path = f"data/responses/{user_code}.json"
    pdf_path = f"data/pdfs/{user_code}.pdf"

    if not os.path.exists(json_path):
        await update.message.reply_text("❌ اطلاعاتی برای این کد یافت نشد.")
        return

    import json
    with open(json_path, "r") as f:
        data = json.load(f)

    user_id = data.get("telegram_user_id")
    if not user_id:
        await update.message.reply_text("❌ شناسه کاربر یافت نشد.")
        return

    if os.path.exists(pdf_path):
        await context.bot.send_message(chat_id=user_id, text="📄 رژیم غذایی شما آماده است:")
        await context.bot.send_document(chat_id=user_id, document=InputFile(pdf_path))
        await update.message.reply_text(f"✅ رژیم برای کاربر {user_code} ارسال شد.")
        print(f"[DIET SENT] to {user_id}")
    else:
        await update.message.reply_text("❌ فایل رژیم یافت نشد.")

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
    app.add_handler(CommandHandler("verify", verify_payment))
    app.add_handler(CommandHandler("submit_diet", submit_diet))
    app.add_handler(CommandHandler("myid", get_id))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()


