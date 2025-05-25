import os
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

def reshape(text):
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def generate_pdf(user_code: str, name: str, answers: dict) -> str:
    print("📄 شروع ساخت PDF...")

    pdf = FPDF()
    pdf.add_page()

    font_path = "utils/fonts/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        print("❌ فونت یافت نشد:", font_path)
        return ""

    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", "", 14)
    pdf.set_right_margin(10)
    pdf.set_left_margin(10)

    # عنوان
    title = f"فرم رژیم غذایی - {name}"
    pdf.cell(0, 10, reshape(title), ln=True, align="C")
    pdf.ln(8)

    # بدنه
    for question, answer in answers.items():
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 8, reshape(f"🔹 {question}"), align="R")
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 8, reshape(f"🟢 {answer}"), align="R")
        pdf.ln(2)

    output_dir = "data/pdfs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{user_code}.pdf")
    pdf.output(output_path)

    print(f"[PDF CREATED] {output_path}")
    return output_path
