from fpdf import FPDF
import os

def generate_pdf(user_code: str, name: str, answers: dict) -> str:
    print("📄 شروع ساخت PDF...")

    font_path = "utils/fonts/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        print("❌ فونت یافت نشد:", font_path)
        return ""

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", "", 12)
    pdf.set_right_margin(10)
    pdf.set_left_margin(10)

    pdf.cell(0, 10, txt=f"فرم رژیم غذایی - {name}", ln=True, align="C")
    pdf.ln(10)

    for question, answer in answers.items():
        pdf.multi_cell(0, 10, f"{question}\n{answer}", align="R")
        pdf.ln(2)

    output_path = f"data/pdfs/{user_code}.pdf"
    os.makedirs("data/pdfs", exist_ok=True)
    pdf.output(output_path)

    if os.path.exists(output_path):
        print(f"[PDF CREATED] {output_path}")
        return output_path
    else:
        print("[PDF NOT CREATED]")
        return ""
