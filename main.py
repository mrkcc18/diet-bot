import os
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)
from questions import questions
from utils.save_json import save_response_json
from utils.database import save_to_db
from utils.code_generator import generate_user_code
from utils.generate_pdf import generate_pdf

ASKING = range(1)

user_data_map = {}

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
            f"🔖 کد پیگیری: {user_code}\n"
            f"👤 نام: {name}\n\n"
        )
        body = "\n\n".join([
            f"━━━━━━━━━━━━━━\n🟦 *{q.strip()}*\n🟩 {a.strip()}" for q, a in answers.items()
        ])

        summary = header + body

        await update.message.reply_text(summary, parse_mode="Markdown")
        await update.message.reply_text(
            "📸 *لطفاً همین حالا تصویر رسید پرداخت خود را ارسال کنید.*\n"
            "🕒 بدون ارسال رسید، فرایند بررسی و دریافت رژیم آغاز نمی‌شود.",
            parse_mode="Markdown"
        )

        context.user_data["waiting_for_payment"] = True
        return ASKING

async def handle_file_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_payment"):
        return

    user_code = context.user_data.get("user_code")
    name = context.user_data["answers"].get("نام و نام خانوادگی:")
    summary = (
        f"📋 *خلاصه پاسخ‌های کاربر:*\n"
        f"🔖 کد پیگیری: {user_code}\n"
        f"👤 نام: {name}\n\n"
    )
    summary += "\n\n".join([
        f"━━━━━━━━━━━━━━\n🟦 *{q.strip()}*\n🟩 {a.strip()}" for q, a in context.user_data["answers"].items()
    ])

    admin_id = int(os.getenv("ADMIN_ID"))

    await update.message.reply_text("✅ رسید دریافت شد. در حال ارسال به مدیر برای تایید...")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید رسید", callback_data=f"verify:{user_code}"),
            InlineKeyboardButton("📤 ارسال رژیم", callback_data=f"submit:{user_code}")
        ]
    ])

    await context.bot.send_message(chat_id=admin_id, text=summary, parse_mode="Markdown", reply_markup=keyboard)

    if update.message.document:
        await context.bot.forward_message(chat_id=admin_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
    elif update.message.photo:
        await context.bot.forward_message(chat_id=admin_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)

    json_path = f"data/responses/{user_code}.json"
    if os.path.exists(json_path):
        input_file = InputFile(open(json_path, "rb"), filename=os.path.basename(json_path))
        await context.bot.send_document(chat_id=admin_id, document=input_file, caption=f"📁 فایل JSON اطلاعات کاربر {user_code}")
        print(f"[JSON SENT] {json_path}")
    else:
        print(f"[JSON MISSING] {json_path}")

    pdf_path = generate_pdf(user_code, name, context.user_data["answers"])
    if os.path.exists(pdf_path):
        await context.bot.send_document(chat_id=admin_id, document=InputFile(pdf_path), caption=f"📄 فایل PDF اطلاعات {user_code}")
        await context.bot.send_document(chat_id=update.effective_user.id, document=InputFile(pdf_path), caption="📄 خلاصه اطلاعات شما (PDF)")
        print(f"[PDF SENT] {pdf_path}")
    else:
        print(f"[PDF MISSING] {pdf_path}")

    user_data_map[user_code] = update.effective_user.id
    print(f"[PAYMENT FORWARDED TO ADMIN] by {user_code}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = os.getenv("ADMIN_ID")

    if str(query.from_user.id) != str(admin_id):
        await context.bot.send_message(chat_id=query.from_user.id, text="⛔ فقط مدیر می‌تواند از این کلیدها استفاده کند.")
        return

    action, user_code = query.data.split(":")

    if action == "verify":
        await context.bot.send_message(chat_id=user_data_map[user_code], text="✅ رسید شما دریافت و تایید شد.")
        await context.bot.send_message(chat_id=query.from_user.id, text=f"✅ رسید مربوط به {user_code} تایید شد.")
        print(f"[VERIFIED] {user_code}")

    elif action == "submit":
        json_path = f"data/responses/{user_code}.json"
        if not os.path.exists(json_path):
            await context.bot.send_message(chat_id=query.from_user.id, text="❌ اطلاعاتی برای این کد یافت نشد.")
            return

        with open(json_path, "r") as f:
            data = json.load(f)

        user_id = data.get("telegram_user_id")
        if not user_id:
            await context.bot.send_message(chat_id=query.from_user.id, text="❌ شناسه کاربر یافت نشد.")
            return

        await context.bot.send_message(chat_id=user_id, text="📄 رژیم غذایی شما آماده است:")
        await context.bot.send_message(chat_id=user_id, text="⚠️ رژیم در این نسخه به‌صورت دستی توسط مدیر تولید شده است.")
        await context.bot.send_message(chat_id=query.from_user.id, text=f"✅ رژیم برای کاربر {user_code} ارسال شد.")
        print(f"[DIET SENT] to {user_id}")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Your Telegram ID is: {update.effective_user.id}")

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
            ASKING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer),
                MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file_forward),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("myid", get_id))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
