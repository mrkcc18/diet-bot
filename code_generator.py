from datetime import datetime
import random

def generate_code(name):
    initials = ''.join([word[0] for word in name.split()[:2]]).upper()
    random_digit = str(random.randint(1, 9))
    date_part = datetime.now().strftime("%d%m%H")
    return f"{initials}{random_digit}{date_part}"
