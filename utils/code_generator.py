import random

def generate_user_code(name: str) -> str:
    return str(random.randint(100000, 999999))
