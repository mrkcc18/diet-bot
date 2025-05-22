import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from code_generator import generate_user_code
from database import save_user_info

logging.basicConfig(level=logging.INFO)

ASK_NAME = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! به ربات رژیم غذایی خوش اومدی.\nلطفاً نام و نام خانوادگی‌تو وارد کن:")
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text
    code = generate_user_code(full_name)
    
    context.user_data["name"] = full_name
    context.user_data["code"] = code

    save_user_info(code, full_name)
    
    await update.message.reply_text(f"✅ ثبت‌نام انجام شد!\nکد یکتای شما: {code}")
    await update.message.reply_text("بزن بریم سراغ سوالات... (در مرحله بعد اضافه می‌شه)")
    return ConversationHandler.END

def main():
    import os
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()

