QUESTIONS = [
    "نام و نام خانوادگی:",
    "سن دقیق:",
    "قد (بر حسب سانتی‌متر):",
    "وزن فعلی (بر حسب کیلوگرم):",
    # ... بقیه سوالات (۳۷ مورد)
]

def get_question(index):
    return QUESTIONS[index] if index < len(QUESTIONS) else None
