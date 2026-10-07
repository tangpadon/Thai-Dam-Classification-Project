"""
โมดูลฟังก์ชันตัวช่วย (Utility Functions)
รวบรวมฟังก์ชันแปลงค่าตัวเลข, วันที่ภาษาไทย, การประเมินระดับสถานการณ์น้ำ,
และการจัดเตรียมข้อมูลเขื่อนสำหรับส่งต่อไปยังโมเดลพยากรณ์และหน้าจอ
"""

import math
from typing import Any, Optional, Dict, Tuple
import pandas as pd
from views.constants import STATUS_THEMES


# 1. การประเมินระดับสถานะน้ำและธีมสี (Risk Classification & Themes)

def classify_by_percent(pct: Optional[float]) -> str:
    """
    จำแนกระดับความเสี่ยงตามร้อยละความจุเก็บกักของเขื่อน:
    - น้อยกว่า 30%: น้ำแล้งวิกฤต (drought)
    - มากกว่า 80%: เสี่ยงน้ำล้น (flood)
    - 30% ถึง 80%: ปกติ (normal)
    (มีระบบป้องกัน Error กรณีค่าว่าง/None โดยจะคืนค่า 'normal' เสมอ)
    """
    if pct is None:
        return "normal"
    try:
        pct_f = float(pct)
        if math.isnan(pct_f):
            return "normal"
        if pct_f < 30.0:
            return "drought"
        elif pct_f > 80.0:
            return "flood"
        return "normal"
    except (TypeError, ValueError):
        return "normal"


def get_status_theme(status_key: str) -> Dict[str, str]:
    """ดึงข้อมูลสี, ข้อความภาษาไทย, และไอคอนตามระดับสถานการณ์น้ำ"""
    return STATUS_THEMES.get(status_key, STATUS_THEMES["normal"])


# 2. การแปลงค่าและจัดรูปแบบตัวเลข (Number Parsing & Formatting)

def to_num(val: Any) -> Optional[float]:
    """แปลงค่าเป็น float อย่างปลอดภัย หากเป็นค่าว่างหรือไม่ใช่ตัวเลขจะส่งกลับ None"""
    if val is None:
        return None
    try:
        return float(str(val).replace(',', '').strip())
    except (TypeError, ValueError):
        return None


def fmt_num(val: Any, decimals: int = 2) -> str:
    """แปลงตัวเลขเป็นข้อความพร้อมเครื่องหมายจุลภาคคั่นหลักพัน เช่น 12,345.67"""
    if val is None:
        return "-"
    try:
        val_f = float(str(val).replace(',', '').strip())
        return f"{val_f:,.{decimals}f}"
    except (TypeError, ValueError):
        return str(val)


def calc_storage_percent(volume: Any, capacity: Any) -> Optional[float]:
    """คำนวณร้อยละความจุเก็บกักจาก (ปริมาตรน้ำ / ความจุอ่าง) * 100 อย่างปลอดภัย"""
    vol = to_num(volume)
    cap = to_num(capacity)
    if vol is not None and cap is not None and cap > 0:
        return (vol / cap) * 100.0
    return None



# 3. การจัดรูปแบบวันที่ภาษาไทย (Date Formatting)

def format_date_th(dt) -> str:
    """แปลงวันที่เป็นภาษาไทยแบบเต็ม เช่น '20 มีนาคม 2568'"""
    months_th = [
        "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    return f"{dt.day} {months_th[dt.month]} {dt.year + 543}"


def format_date_th_short(dt) -> str:
    """แปลงวันที่เป็นภาษาไทยแบบย่อ เช่น '20 มี.ค. 2568'"""
    months_short = [
        "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
        "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
    ]
    return f"{dt.day} {months_short[dt.month]} {dt.year + 543}"


# 4. การจัดเตรียมข้อมูลเขื่อน (Dam Data Preparation)

def prepare_dam_data(raw_dam_data: Any, data_date: Any = None) -> Tuple[Dict[str, Any], bool, Any]:
    """
    จัดเตรียมข้อมูลเขื่อนให้สมบูรณ์สำหรับแสดงผลและส่งเข้าโมเดลพยากรณ์:
    1. ตรวจสอบว่าวันนี้มีค่า Input หรือไม่ (percent_storage หรือ volume)
    2. ถ้าวันนี้ไม่มีข้อมูล (หรือเป็น None/0) ให้ดึงข้อมูลเมื่อวานมาใช้เป็น Fallback
    3. คำนวณร้อยละความจุสำรองจาก (volume / capacity) * 100 กรณี percent_storage ขาดหาย
    
    คืนค่า: (dam_data_dict, is_fallback, fallback_date)
    """
    dam_dict = dict(raw_dam_data)

    pct_raw = to_num(dam_dict.get('percent_storage'))
    vol_raw = to_num(dam_dict.get('volume'))
    has_input = (pct_raw is not None and pct_raw > 0) or (vol_raw is not None and vol_raw > 0)

    is_fallback = False
    fallback_date = None

    # หากวันนี้ไม่มีค่า Input ให้ดึงข้อมูลจากวันก่อนหน้า (เมื่อวาน)
    if not has_input:
        from core.db import get_yesterday_valid_data
        dam_id = dam_dict.get('id') or dam_dict.get('dam_id')
        y_data = get_yesterday_valid_data(dam_id, current_date=data_date)
        if y_data:
            if y_data.get('percent_storage') is not None:
                dam_dict['percent_storage'] = float(y_data['percent_storage'])
            if y_data.get('volume') is not None:
                dam_dict['volume'] = float(y_data['volume'])
            if y_data.get('inflow') is not None:
                dam_dict['inflow'] = float(y_data['inflow'])
            if y_data.get('outflow') is not None:
                dam_dict['outflow'] = float(y_data['outflow'])
            is_fallback = True
            fallback_date = y_data.get('record_date')

    # คำนวณร้อยละความจุเก็บกักสำรอง หากไม่มีค่า percent_storage แต่มี volume และ capacity
    current_pct = to_num(dam_dict.get('percent_storage')) or 0.0
    if current_pct <= 0:
        calculated_pct = calc_storage_percent(dam_dict.get('volume'), dam_dict.get('capacity'))
        if calculated_pct is not None:
            dam_dict['percent_storage'] = calculated_pct

    return dam_dict, is_fallback, fallback_date



# Aliases สำหรับรองรับโค้ดเก่า
_classify_by_percent = classify_by_percent
_get_status_theme = get_status_theme
_fmt_num = fmt_num
_to_num = to_num
_format_date_th = format_date_th
_format_date_th_short = format_date_th_short
