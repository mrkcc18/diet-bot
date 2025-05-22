import random
from datetime import datetime

def generate_user_code(name: str) -> str:
    now = datetime.now()
    initials = ''.join([word[0] for word in name.split()[:2]]).upper()
    factor = str(random.randint(1, 9))
    code = f"{initials}{factor}{now.strftime('%y%m%d%H')}"
    return code
