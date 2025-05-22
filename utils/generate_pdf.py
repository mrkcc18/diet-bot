from fpdf import FPDF
import os

def generate_pdf(user_code, name, answers_dict):
    os.makedirs("data/pdfs", exist_ok=True)
    filename = f"data/pdfs/{user_code}.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "utils/fonts/DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)

    pdf.cell(200, 10, txt=f"کد کاربر: {user_code}", ln=True, align='R')
    pdf.cell(200, 10, txt=f"نام: {name}", ln=True, align='R')
    pdf.ln(10)

    for question, answer in answers_dict.items():
        pdf.multi_cell(0, 10, f"{question}\n{answer}", align='R')
        pdf.ln(1)

    pdf.output(filename)
    return filename
