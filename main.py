# main.py — Python Telegram Bot 20.x (Long Polling for Render Worker)
import os
import logging
from datetime import datetime
from pathlib import Path

from telegram import Update, InputFile
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ───────────── Logging ─────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("diet-bot-polling")

# ───────────── ENV ─────────────
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN را در Environment تنظیم کن.")

# ───────────── مسیرهای ذخیره ─────────────
DATA_DIR = Path("data")
PAYMENTS_DIR = DATA_DIR / "payments"
PDFS_DIR = DATA_DIR / "pdfs"
for p in [DATA_DIR, PAYMENTS_DIR, PDFS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# ───────────── ایمپورت اختیاری PDF ─────────────
try:
    # باید فایل utils/generate_pdf2.py و تابع create_pdf(payload, out_path) را داشته باشی
    from utils.generate_pdf2 import create_pdf
except Exception:  # noqa: E722
    create_pdf = None
    logger.warning("utils.generate_pdf2.create_pdf در دسترس نیست؛ /pdf غیرفعال می‌ماند.")

# ───────────── Helpers ─────────────
def is_admin(user_id: int) -> bool:
    return ADMIN_ID != 0 and user_id == ADMIN_ID

async def send_typing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_chat:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, action=ChatAction.TYPING
            )
    except Exception as e:
        logger.debug("send_typing error: %s", e)

# ───────────── Handlers ─────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing(update, context)
    await update.message.reply_text(
        "سلام! 👋\n"
        "بات روی Render با حالت Polling فعاله ✅\n\n"
        "دستورات:\n"
        "• /help — راهنما\n"
        "• /pdf — تست ساخت PDF (اگر فعال باشد)\n"
        "رسید/فایل را بفرست؛ برای ادمین به‌صورت document ارسال می‌کنم."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_typing(update, context)
    await update.message.reply_text(
        "راهنما 📘\n"
        "— عکس یا PDF بفرست؛ من به‌صورت «document» برای ADMIN فوروارد می‌کنم.\n"
        "— /pdf برای ساخت PDF نمونه (نیازمند utils/generate_pdf2.py و فونت یونیکد).\n"
    )

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هر نوع فایل/عکس دریافت شد → ذخیره لوکال → ارسال برای ADMIN به‌صورت document."""
    await send_typing(update, context)
    user = update.effective_user

    file_id = None
    filename = None

    if update.message.photo:
        photo = update.message.photo[-1]
        file_id = photo.file_id
        filename = f"receipt_{user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg"
    elif update.message.document:
        doc = update.message.document
        file_id = doc.file_id
        filename = doc.file_name or f"document_{user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    else:
        await update.message.reply_text("فایلی تشخیص داده نشد. عکس یا PDF ارسال کن.")
        return

    try:
        tg_file = await context.bot.get_file(file_id)
        local_path = PAYMENTS_DIR / filename
        await tg_file.download_to_drive(str(local_path))
        logger.info("Saved incoming file to %s", local_path)
    except Exception as e:
        logger.exception("Download failed: %s", e)
        await update.message.reply_text("دانلود فایل ناموفق بود.")
        return

    try:
        if ADMIN_ID == 0:
            await update.message.reply_text(
                "فایل ذخیره شد ✅\n"
                "توجه: ADMIN_ID تنظیم نشده؛ برای ارسال به ادمین، ENV را ست کن."
            )
        else:
            caption = f"رسید جدید از {user.full_name or user.id} (user_id={user.id})"
            await context.bot.send_document(
                chat_id=ADMIN_ID,
                document=InputFile(str(local_path)),
                caption=caption,
            )
            await update.message.reply_text("رسیدت رسید ✅ (برای ادمین ارسال شد)")
    except Exception as e:
        logger.exception("Forward to admin failed: %s", e)
        await update.message.reply_text("ارسال برای ادمین ناموفق بود.")

async def generate_pdf_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if create_pdf is None:
        await update.message.reply_text("ماژول PDF فعال نیست (utils/generate_pdf2.py را اضافه کن).")
        return

    await send_typing(update, context)
    payload = {
        "title": "گزارش نمونه",
        "user": update.effective_user.full_name if update.effective_user else "کاربر",
        "items": [
            {"name": "وعده ۱", "kcal
