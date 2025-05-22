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

# تعریف یک حالت برای شروع و ادامه پرسش‌ها
ASKING = range(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answers"] = {}
    context.user_data["current_q"] = 0

    await update.message.reply_text("سلام! بریم سراغ فرم رژیم غذایی ✍️")
    await update.message.reply_text(questions[0])
    return ASKING

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_q = context.user_data["current_q"]
    context.user_data["answers"][questions[current_q]] = update.message.text

    current_q += 1
    if current_q < len(questions):
        context.user_data["current_q"] = current_q
        await update.message.reply_text(questions[current_q])
        return ASKING
    else:
        # همه سوالات پاسخ داده شده
        summary = "\n\n".join(
            [f"{q}\n{a}" for q, a in context.user_data["answers"].items()]
        )
        await update.message.reply_text("✅ فرم شما کامل شد. این خلاصه‌ی پاسخ‌های شماست:\n\n")
        await update.message.reply_text(summary)

        # در مرحله بعدی می‌تونیم ذخیره‌سازی JSON / SQLite / PDF انجام بدیم
        return ConversationHandler.END

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

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()

