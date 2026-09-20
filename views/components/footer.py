"""Footer component rendering data credits and educational disclaimer."""

import streamlit as st
from views.icons import svg_icon


def render_footer():
    """Render the dashboard data credits and educational disclaimer note."""
    st.markdown(f"""
    <div id="section-about" style="scroll-margin-top: 80px; margin-top: 28px; margin-bottom: 24px; background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
        <div style="display:flex; align-items:center; gap:8px; font-weight:700; color:#0f172a; font-size:1.0rem; margin-bottom:10px;">
            {svg_icon("info", 20, "#0284c7")} <span>เกี่ยวกับระบบและแหล่งข้อมูล (Credits & Information)</span>
        </div>
        <div style="font-size:0.85rem; color:#475569; line-height:1.7;">
            • <b>แหล่งที่มาของข้อมูล:</b> เชื่อมโยงข้อมูลสถานการณ์น้ำรายวันจาก <a href="https://app.rid.go.th/reservoir/api/document/dam/" target="_blank" rel="noopener noreferrer" style="color:#0284c7; text-decoration:underline; font-weight:600;">API</a> สาธารณะของ <b>ศูนย์ปฏิบัติการน้ำอัจฉริยะ กรมชลประทาน</b><br>
            • <b>แบบจำลองการพยากรณ์:</b> พัฒนาขึ้นโดยใช้เทคนิคการเรียนรู้ของเครื่อง (Machine Learning: Weka Framework)<br>
            • <b>หมายเหตุ:</b> ระบบนี้จัดทำขึ้นเพื่อการศึกษา มิได้มีวัตถุประสงค์เพื่อใช้เป็นข้อมูลตัดสินใจเชิงปฏิบัติการในภาวะวิกฤตอย่างเป็นทางการ
        </div>
    </div>
    """, unsafe_allow_html=True)
