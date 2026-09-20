"""Constants and themes for the Thai Dam Classification dashboard."""

STATUS_THEMES = {
    "drought": {
        "color": "#eab308",
        "bg_light": "#fefce8",
        "border": "#fef08a",
        "label": "น้ำน้อย เสี่ยงแล้ง",
        "label_short": "เสี่ยงน้ำแล้ง",
        "en": "Drought Risk",
    },
    "normal": {
        "color": "#16a34a",
        "bg_light": "#f0fdf4",
        "border": "#bbf7d0",
        "label": "ปกติ",
        "label_short": "ปกติ",
        "en": "Normal",
    },
    "flood": {
        "color": "#dc2626",
        "bg_light": "#fef2f2",
        "border": "#fecaca",
        "label": "น้ำมากเสี่ยงน้ำล้น",
        "label_short": "เสี่ยงน้ำล้น",
        "en": "Flood Risk",
    },
}

DAM_LOCATIONS = {
    # ภาคเหนือ
    "เขื่อนแม่กวงอุดมธารา": {"province": "เชียงใหม่", "region": "ภาคเหนือ"},
    "เขื่อนกิ่วลม": {"province": "ลำปาง", "region": "ภาคเหนือ"},
    "เขื่อนกิ่วคอหมา": {"province": "ลำปาง", "region": "ภาคเหนือ"},
    "เขื่อนแควน้อยบำรุงแดน": {"province": "พิษณุโลก", "region": "ภาคเหนือ"},
    "เขื่อนแม่มอก": {"province": "สุโขทัย", "region": "ภาคเหนือ"},
    "เขื่อนภูมิพล": {"province": "ตาก", "region": "ภาคเหนือ"},
    "เขื่อนสิริกิติ์": {"province": "อุตรดิตถ์", "region": "ภาคเหนือ"},
    "เขื่อนแม่งัดสมบูรณ์ชล": {"province": "เชียงใหม่", "region": "ภาคเหนือ"},

    # ภาคตะวันออกเฉียงเหนือ
    "เขื่อนห้วยหลวง": {"province": "อุดรธานี", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนน้ำอูน": {"province": "สกลนคร", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนลำปาว": {"province": "กาฬสินธุ์", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนลำตะคอง": {"province": "นครราชสีมา", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนลำพระเพลิง": {"province": "นครราชสีมา", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนมูลบน": {"province": "นครราชสีมา", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนลำแชะ": {"province": "นครราชสีมา", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนลำนางรอง": {"province": "บุรีรัมย์", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนน้ำพุง": {"province": "สกลนคร", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนจุฬาภรณ์": {"province": "ชัยภูมิ", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนอุบลรัตน์": {"province": "ขอนแก่น", "region": "ภาคตะวันออกเฉียงเหนือ"},
    "เขื่อนสิรินธร": {"province": "อุบลราชธานี", "region": "ภาคตะวันออกเฉียงเหนือ"},

    # ภาคกลาง
    "เขื่อนป่าสักชลสิทธิ์": {"province": "ลพบุรี", "region": "ภาคกลาง"},
    "เขื่อนทับเสลา": {"province": "อุทัยธานี", "region": "ภาคกลาง"},
    "เขื่อนกระเสียว": {"province": "สุพรรณบุรี", "region": "ภาคกลาง"},

    # ภาคตะวันออก
    "เขื่อนขุนด่านปราการชล": {"province": "นครนายก", "region": "ภาคตะวันออก"},
    "เขื่อนคลองสียัด": {"province": "ฉะเชิงเทรา", "region": "ภาคตะวันออก"},
    "เขื่อนบางพระ": {"province": "ชลบุรี", "region": "ภาคตะวันออก"},
    "เขื่อนหนองปลาไหล": {"province": "ระยอง", "region": "ภาคตะวันออก"},
    "เขื่อนประแสร์": {"province": "ระยอง", "region": "ภาคตะวันออก"},
    "เขื่อนนฤบดินทรจินดา": {"province": "ปราจีนบุรี", "region": "ภาคตะวันออก"},

    # ภาคตะวันตก
    "เขื่อนศรีนครินทร์": {"province": "กาญจนบุรี", "region": "ภาคตะวันตก"},
    "เขื่อนวชิราลงกรณ": {"province": "กาญจนบุรี", "region": "ภาคตะวันตก"},

    # ภาคใต้
    "เขื่อนปราณบุรี": {"province": "ประจวบคีรีขันธ์", "region": "ภาคใต้"},
    "เขื่อนแก่งกระจาน": {"province": "เพชรบุรี", "region": "ภาคใต้"},
    "เขื่อนรัชชประภา": {"province": "สุราษฎร์ธานี", "region": "ภาคใต้"},
    "เขื่อนบางลาง": {"province": "ยะลา", "region": "ภาคใต้"},
}


def get_dam_location(dam_name: str, dam_data=None) -> tuple:
    """Return (province, region) for a given dam name."""
    clean_name = str(dam_name).strip() if dam_name else ""
    if clean_name in DAM_LOCATIONS:
        info = DAM_LOCATIONS[clean_name]
        return info["province"], info["region"]

    # Fuzzy match if prefix is missing or different
    for k, v in DAM_LOCATIONS.items():
        if k in clean_name or clean_name in k:
            return v["province"], v["region"]

    # Fallback to dam_data if available
    prov = "ไม่ระบุ"
    reg = "ไม่ระบุ"
    if dam_data is not None:
        try:
            prov = dam_data.get("province") or prov
            reg = dam_data.get("region") or reg
        except Exception:
            pass
    return prov, reg


