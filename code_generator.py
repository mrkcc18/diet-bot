import random
from datetime import datetime

def generate_user_code(full_name: str) -> str:
    now = datetime.now()
    initials = ''.join([word[0] for word in full_name.split()[:2]]).upper()
    factor = str(random.randint(1, 9))
    year = str(now.year)[-1]
    date_code = now.strftime("%m%d%H")
    return f"{initials}{factor}{year}{date_code}"
