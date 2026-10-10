import streamlit as st
from views.icons import svg_icon


def render_footer():
    st.markdown(f"""
    <footer id="section-about" class="dashboard-footer">
        <div class="footer-title">
            {svg_icon("info", 16, "#64748b")}
            <span>เกี่ยวกับระบบและแหล่งข้อมูล (Credits & Information)</span>
        </div>
        <div class="footer-content">
            <span>• <b>แหล่งที่มาของข้อมูล:</b> เชื่อมโยงข้อมูลสถานการณ์น้ำรายวันจาก <a href="https://app.rid.go.th/reservoir/api/document/dam/" target="_blank" rel="noopener noreferrer" style="color:#0284c7; text-decoration:underline; font-weight:600;">API</a> สาธารณะของ <b>ศูนย์ปฏิบัติการน้ำอัจฉริยะ กรมชลประทาน</b></span>
            <span class="footer-sep">|</span>
            <span>• <b>แบบจำลองการพยากรณ์:</b> พัฒนาขึ้นโดยใช้เทคนิคการเรียนรู้ของเครื่อง (Machine Learning: Weka Framework)</span>
        </div>
        <div class="footer-disclaimer">
            หมายเหตุ: ระบบนี้จัดทำขึ้นเพื่อการศึกษา
        </div>
    </footer>
    """, unsafe_allow_html=True)
