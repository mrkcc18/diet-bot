from fpdf import FPDF
import os

def generate_pdf(user_code: str, name: str, answers: dict) -> str:
    output_dir = "data/pdfs"
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{user_code}.pdf")

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "utils/fonts/DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", "", 14)

    pdf.cell(0, 10, f"کد کاربر: {user_code}", ln=True, align="R")
    pdf.cell(0, 10, f"نام: {name}", ln=True, align="R")
    pdf.ln(5)

    pdf.set_font("DejaVu", "", 12)
    for q, a in answers.items():
        pdf.multi_cell(0, 10, f"{q}\n{a}", align="R")
        pdf.ln(1)

    pdf.output(pdf_path)
    return pdf_path
