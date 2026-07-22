def translate_status(status_text):
    status_lower = str(status_text).lower()
    if "flood" in status_lower:
        return "น้ำล้น (Flood)"
    elif "drought" in status_lower:
        return "น้ำแล้ง (Drought)"
    else:
        return "ปกติ (Normal)"
