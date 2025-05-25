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

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید رسید", callback_data=f"verify:{user_code}"),
            InlineKeyboardButton("📤 ارسال رژیم", callback_data=f"submit:{user_code}")
        ]
    ])

    # ارسال خلاصه اطلاعات همراه با دکمه‌ها به مدیر
    await context.bot.send_message(
        chat_id=admin_id,
        text=summary,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

    # فوروارد تصویر یا فایل رسید از چت مشتری به مدیر
    if update.message.document:
        await context.bot.forward_message(
            chat_id=admin_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )
    elif update.message.photo:
        await context.bot.forward_message(
            chat_id=admin_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )

    # ارسال فایل JSON به مدیر
    json_path = f"data/responses/{user_code}.json"
    if os.path.exists(json_path):
        await context.bot.send_document(
            chat_id=admin_id,
            document=InputFile(open(json_path, "rb"), filename=os.path.basename(json_path)),
            caption=f"📁 فایل JSON اطلاعات کاربر {user_code}"
        )
        print(f"[JSON SENT] {json_path}")
    else:
        print(f"[JSON MISSING] {json_path}")

    # تولید و ارسال فایل PDF به مدیر و کاربر
    pdf_path = generate_pdf(user_code, name, context.user_data["answers"])
    if os.path.exists(pdf_path):
        await context.bot.send_document(
            chat_id=admin_id,
            document=InputFile(open(pdf_path, "rb"), filename=os.path.basename(pdf_path)),
            caption=f"📄 فایل PDF اطلاعات {user_code}"
        )
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=InputFile(open(pdf_path, "rb"), filename=os.path.basename(pdf_path)),
            caption="📄 خلاصه اطلاعات شما (PDF)"
        )
        print(f"[PDF SENT] {pdf_path}")
    else:
        print(f"[PDF MISSING] {pdf_path}")

    # ثبت آیدی کاربر برای پاسخ‌دهی بعدی
    user_data_map[user_code] = update.effective_user.id
    print(f"[PAYMENT FORWARDED TO ADMIN] by {user_code}")
