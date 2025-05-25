import os
from fpdf import FPDF

def generate_pdf(user_code: str, name: str, answers: dict) -> str:
    print("📄 شروع ساخت PDF...")

    try:
        pdf = FPDF()
        pdf.add_page()

        # تنظیم فونت فارسی
        font_path = "utils/fonts/DejaVuSans.ttf"
        if not os.path.exists(font_path):
            print("❌ فونت یافت نشد:", font_path)
            return ""

        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", "", 14)

        # عنوان
        pdf.set_right_margin(10)
        pdf.set_left_margin(10)
        pdf.cell(0, 10, txt=f"فرم رژیم غذایی - {name}", ln=True, align="C")
        pdf.ln(10)

        # پاسخ‌ها
        pdf.set_font("DejaVu", "", 12)
        for question, answer in answers.items():
            pdf.multi_cell(0, 10, f"{question}\n{answer}", align="R")
            pdf.ln(2)

        # مسیر خروجی
        output_dir = "data/pdfs"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{user_code}.pdf")

        print("📤 مسیر ذخیره‌سازی:", output_path)
        pdf.output(output_path)

        print(f"[PDF CREATED] {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ خطا در ساخت PDF: {str(e)}")
        return ""
