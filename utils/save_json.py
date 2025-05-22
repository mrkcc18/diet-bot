import json
import os
from datetime import datetime

def save_response_json(user_code, data):
    os.makedirs("data/responses", exist_ok=True)
    filename = f"data/responses/{user_code}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filename
