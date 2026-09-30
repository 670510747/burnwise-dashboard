# BurnWise Dashboard

แดชบอร์ดแสดงผลการวิเคราะห์การเผา/ไถกลบตอซังข้าว อำเภอท่าตะโก จังหวัดนครสวรรค์ (GeoHackathon 2026)

## รันในเครื่องตัวเอง

```bash
pip install -r requirements.txt
streamlit run app.py
```

เปิดเบราว์เซอร์ที่ `http://localhost:8501`

## Deploy ผ่าน Streamlit Community Cloud (ฟรี)

1. สร้าง repo ใหม่บน GitHub แล้ว push โฟลเดอร์นี้ทั้งหมดขึ้นไป (ต้องมีไฟล์ `app.py`, `requirements.txt`, โฟลเดอร์ `data/` และ `.streamlit/config.toml`)
2. เข้า [share.streamlit.io](https://share.streamlit.io) ล็อกอินด้วย GitHub
3. กด **New app** → เลือก repo และ branch ที่ push ไว้ → ตั้ง Main file path เป็น `app.py`
4. กด **Deploy** รอสักครู่จะได้ลิงก์สาธารณะมาแชร์ได้ทันที

## โครงสร้างไฟล์

```
├── app.py                          # โค้ดหลักของแดชบอร์ด
├── requirements.txt                # ไลบรารีที่ต้องติดตั้ง
├── .streamlit/config.toml          # ธีมสี
└── data/
    ├── burnwise_master_plots.csv   # ข้อมูลระดับแปลง (~48,000 แปลง)
    ├── burnwise_score_panel.csv    # สรุป Tier รายตำบล
    └── burnwise_tambon_overview.csv
```

## อัปเดตข้อมูลใหม่

แทนที่ไฟล์ 3 ไฟล์ใน `data/` ด้วยผลลัพธ์ใหม่จาก notebook (ชื่อไฟล์และชื่อคอลัมน์ต้องตรงเดิม) แล้ว push ขึ้น GitHub — Streamlit Cloud จะ redeploy ให้อัตโนมัติ
