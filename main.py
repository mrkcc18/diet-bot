
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

        header = (
            f"📋 *خلاصه پاسخ‌های شما:*\n"
            f"🔖 کد پیگیری: `{user_code}`\n"
            f"👤 نام: {name}\n\n"
        )
        body = "\n\n".join([
            f"━━━━━━━━━━━━━━\n🟦 *{q.strip()}*\n🟩 `{a.strip()}`" for q, a in answers.items()
        ])

        summary = header + body

        await update.message.reply_text("✅ فرم شما کامل شد. لطفاً تصویر رسید پرداخت را ارسال کنید.")
        await update.message.reply_text(summary, parse_mode="Markdown")

        context.user_data["waiting_for_payment"] = True
        return ASKING

async def handle_file_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_payment"):
        return

    user_code = context.user_data.get("user_code")
    name = context.user_data["answers"].get("نام و نام خانوادگی:")
    summary = (
        f"📋 *خلاصه پاسخ‌های کاربر:*\n"
        f"🔖 کد پیگیری: `{user_code}`\n"
        f"👤 نام: {name}\n\n"
    )
    summary += "\n\n".join([
        f"━━━━━━━━━━━━━━\n🟦 *{q.strip()}*\n🟩 `{a.strip()}`" for q, a in context.user_data["answers"].items()
    ])

    admin_id = int(os.getenv("ADMIN_ID"))

    await update.message.reply_text("✅ رسید دریافت شد. در حال ارسال به مدیر برای تایید...")

    await context.bot.send_message(chat_id=admin_id, text=summary, parse_mode="Markdown")

    if update.message.document:
        await context.bot.forward_message(chat_id=admin_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
    elif update.message.photo:
        await context.bot.forward_message(chat_id=admin_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)

    print(f"[PAYMENT FORWARDED TO ADMIN] by {user_code}")

async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = os.getenv("ADMIN_ID")
    if str(update.effective_user.id) != str(admin_id):
        await update.message.reply_text("⛔ فقط مدیر می‌تواند پرداخت‌ها را تأیید کند.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("❗ لطفاً کد کاربر را به صورت `/verify <code>` وارد کنید.")
        return

    user_code = context.args[0]
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

    await context.bot.send_message(chat_id=user_id, text="📄 رژیم غذایی شما آماده است:")
    await context.bot.send_message(chat_id=user_id, text="⚠️ رژیم در این نسخه به‌صورت دستی توسط مدیر تولید شده است.")
    await update.message.reply_text(f"✅ رژیم برای کاربر {user_code} ارسال شد.")
    print(f"[DIET SENT] to {user_id}")

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer),
                MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file_forward),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
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
