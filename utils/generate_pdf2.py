# utils/generate_pdf2.py
# -*- coding: utf-8 -*-
"""
سازنده‌ی PDF فارسی (راست‌چین) با fpdf2 + arabic_reshaper + python-bidi

تابع اصلی:
    create_pdf(payload: dict, out_path: str) -> str

ساختار payload پیشنهادی:
payload = {
    "title": "گزارش نمونه",
    "user": "کاربر",
    "items": [
        {"name": "وعده ۱", "kcal": 350},
        {"name": "وعده ۲", "kcal": 480},
        {"name": "مجموع",  "kcal": 830},
    ],
    "date": "2025-10-04",
}

خروجی:
    مسیر فایل PDF ساخته‌شده را برمی‌گرداند (str). اگر لازم بود، پوشه‌ی مقصد را می‌سازد.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, List

from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display


# ـــــــــــــــــــــــــــــ تنظیمات فونت ـــــــــــــــــــــــــــــ
# دو مسیر پیش‌فرض؛ اگر متفاوت است، اصلاح کن.
REPO_ROOT = Path(__file__).resolve().parents[1]
FONT_PATHS = {
    "regular": REPO_ROOT / "assets" / "fonts" / "DejaVuSans.ttf",
    "bold":    REPO_ROOT / "assets" / "fonts" / "DejaVuSans-Bold.ttf",
}

# امکان override از طریق ENV
FONT_PATH_REGULAR_ENV = os.getenv("PDF_FONT_REGULAR_PATH")
FONT_PATH_BOLD_ENV = os.getenv("PDF_FONT_BOLD_PATH")
if FONT_PATH_REGULAR_ENV:
    FONT_PATHS["regular"] = Path(FONT_PATH_REGULAR_ENV)
if FONT_PATH_BOLD_ENV:
    FONT_PATHS["bold"] = Path(FONT_PATH_BOLD_ENV)


# ـــــــــــــــــــــــــــــ ابزار متن فارسی ـــــــــــــــــــــــــــــ
def fa(text: Any) -> str:
    """
    تبدیل متن فارسی/عربی به نمای راست‌به‌چپ قابل‌نمایش در PDF.
    هر چیزی که str نیست، ابتدا به str تبدیل می‌شود.
    """
    s = "" if text is None else str(text)
    if not s:
        return ""
    reshaped = arabic_reshaper.reshape(s)
    return get_display(reshaped)


# ـــــــــــــــــــــــــــــ کلاس PDF ـــــــــــــــــــــــــــــ
class RTLFPDF(FPDF):
    """
    FPDF با چند کمک‌تابع برای متن راست‌چین.
    """
    def header(self):
        # هدر ساده؛ اگر خواستی آرم/لوگو اضافه کن.
        self.set_font("DejaVu", "B", 14)
        # جای هدر را سمت راست صفحه در نظر می‌گیریم
        self.cell(0, 10, fa(self.title_text or ""), new_x="LMARGIN", new_y="NEXT", align="R")
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 9)
        page_text = fa(f"صفحه {self.page_no()}")
        self.cell(0, 10, page_text, align="C")

    def add_rtl_text(self, txt: str, size: int = 12, bold: bool = False, ln: bool = True):
        self.set_font("DejaVu", "B" if bold else "", size)
        self.cell(0, 8, fa(txt), new_x="LMARGIN", new_y="NEXT" if ln else "TOP", align="R")

    def add_kv(self, key: str, value: str, size: int = 11):
        """
        یک خط کلید/مقدار راست‌چین (مثلا: تاریخ: 2025-10-04)
        """
        self.set_font("DejaVu", "", size)
        line = f"{key}: {value}"
        self.cell(0, 7, fa(line), new_x="LMARGIN", new_y="NEXT", align="R")

    def add_table(self, rows: List[Dict[str, Any]], headers: List[str], col_widths: List[int] | None = None):
        """
        جدول راست‌چین ساده. headers به ترتیبِ rows[i].keys() نیست؛ خودت تعیین کن.
        rows: لیست dict با کلیدهای هم‌نام با headers (اما از لحاظ محتوا آزاد).
        """
        if not rows:
            return

        if col_widths is None:
            # سه ستون پیش‌فرض با نسبت تقریبی
            usable = self.w - self.l_margin - self.r_margin
            col_widths = [int(usable * 0.65), int(usable * 0.35)]

        # سرستون‌ها
        self.set_font("DejaVu", "B", 11)
        self.set_fill_color(245, 245, 245)
        # چاپ از راست به چپ: ابتدا آخرین ستون
        for i in range(len(headers) - 1, -1, -1):
            self.cell(col_widths[i if i < len(col_widths) else -1], 8, fa(headers[i]), border=1, align="C", fill=True)
        self.ln()

        # ردیف‌ها
        self.set_font("DejaVu", "", 11)
        for row in rows:
            # فرض: headers تعریف‌کننده ترتیب‌اند
            for i in range(len(headers) - 1, -1, -1):
                key = headers[i]
                val = row.get(key, "")
                # اعداد را به صورت ساده چاپ می‌کنیم (می‌توانی قالب‌بندی کنی)
                if isinstance(val, (int, float)):
                    txt = f"{val}"
                else:
                    txt = str(val)
                self.cell(col_widths[i if i < len(col_widths) else -1], 8, fa(txt), border=1, align="R")
            self.ln()


def _ensure_fonts(pdf: RTLFPDF):
    """
    ثبت فونت‌های یونیکد؛ اگر پیدا نشود، ارور واضح می‌دهیم.
    """
    reg = FONT_PATHS["regular"]
    bold = FONT_PATHS["bold"]
    if not reg.exists() or not bold.exists():
        raise FileNotFoundError(
            "فونت‌های یونیکد یافت نشدند. این فایل‌ها را اضافه کن:\n"
            f"- {reg}\n- {bold}\n"
            "یا مسیرها را با ENVهای PDF_FONT_REGULAR_PATH / PDF_FONT_BOLD_PATH بده."
        )
    pdf.add_font("DejaVu", "", str(reg), uni=True)
    pdf.add_font("DejaVu", "B", str(bold), uni=True)


# ـــــــــــــــــــــــــــــ سازنده‌ی PDF ـــــــــــــــــــــــــــــ
def create_pdf(payload: Dict[str, Any], out_path: str) -> str:
    """
    فایل PDF را می‌سازد و مسیر خروجی را برمی‌گرداند.
    """
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    title = payload.get("title", "گزارش")
    user_name = payload.get("user", "کاربر")
    date_str = payload.get("date", "")
    items = payload.get("items", [])  # انتظار: [{ "name": "...", "kcal": 123 }, ...]

    pdf = RTLFPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.title_text = title

    _ensure_fonts(pdf)

    pdf.add_page()

    # عنوان
    pdf.add_rtl_text(title, size=16, bold=True)

    # متادیتا
    if date_str:
        pdf.add_kv("تاریخ", date_str)
    if user_name:
        pdf.add_kv("کاربر", user_name)

    pdf.ln(2)

    # جدول آیتم‌ها (اگر موجود)
    if items:
        # تبدیل به ردیف‌های ساده با کلیدهای هم‌نام با headers
        rows = []
        total_kcal = 0
        for it in items:
            name = it.get("name", "")
            kcal = it.get("kcal", "")
            try:
                total_kcal += float(kcal)
            except Exception:
                pass
            rows.append({"name": name, "kcal": kcal})

        headers = ["name", "kcal"]  # ترتیب منطقی: [نام، کالری]
        pdf.add_table(rows=rows, headers=headers, col_widths=None)

        pdf.ln(2)
        # جمع کل اگر محاسبه شد
        if total_kcal:
            pdf.add_rtl_text(f"جمع کالری: {int(total_kcal)}", size=12, bold=True)

    # یادداشت پایانی (اختیاری)
    note = payload.get("note")
    if note:
        pdf.ln(3)
        pdf.add_rtl_text("یادداشت:", size=12, bold=True)
        pdf.set_font("DejaVu", "", 11)
        # برای متن چندخطی از multi_cell استفاده می‌کنیم؛ راست‌چین با تبدیل fa
        pdf.multi_cell(0, 7, fa(note), align="R")

    # ذخیره
    pdf.output(str(out_file))
    return str(out_file)
