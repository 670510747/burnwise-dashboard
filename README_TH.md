# BurnWise Plot Workbook

## ใช้งานในเครื่อง

เปิด Terminal ในโฟลเดอร์นี้แล้วรัน:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

ข้อมูลจริงอยู่ใน `data/` แล้ว ไม่ต้องอัปโหลดข้อมูลที่หน้าเว็บ ไม่มีข้อมูล demo ปะปน

## แทนที่เว็บ Streamlit เดิม

นำ `app.py`, `requirements.txt`, โฟลเดอร์ `data/`, `assets/` และ `.streamlit/` รวมถึง `.gitattributes` ขึ้น repository เดิม โดยวาง app.py ที่ root ตาม main file เดิม ให้ Streamlit ติดตั้ง dependencies ใหม่แล้วเปิดเว็บตรวจ ผลงานนี้ไม่ได้ push GitHub หรือ deploy ให้แล้ว

## สิ่งที่เปลี่ยนจาก app 2.py

- ตารางรายแปลงเป็นหน้าหลัก แสดง 50 แถวต่อหน้าและเลื่อนดูตารางได้
- ใช้ข้อมูลภาพเพียงพอเป็นค่าเริ่มต้น เลือกทั้งหมดหรือรอภาพได้
- กรองตำบล สถานะ รหัสแปลง และเรียงตามขนาดแปลง/สัญญาณ/coverage
- รหัสแปลงกดได้ เปิดรายละเอียดในหน้าเดียวกันโดยเก็บ filter ใน URL
- รายละเอียดแสดง signal, coverage, สถานะ logistics, เหตุผลตรวจ และ GISTDA เมื่อมี
- พิกัดเป็น centroid เท่านั้น มีลิงก์ Google Maps ไม่อ้างเป็นขอบเขตหรือทางเข้าแปลง
- สลับ English/ไทย และ light/dark/black & white แยกตาม session
- ฟอนต์ไทยแนบใน assets พร้อม OFL license ไม่ต้องโหลดฟอนต์จากเว็บขณะใช้งาน
- CSV และ Excel export ตามตัวกรอง รวม download รายแปลง
- ตัวเลขทั้งหมด/ภาพเพียงพอ/รอภาพอยู่เสมอ ไม่มีการลบ Unknown ออกจากข้อมูลหลัก
- ไม่มีกราฟเป็นหน้าหลัก ผลเทียบผลิตภัณฑ์อยู่ในส่วนเปิดอ่านเพิ่มเติม
- รายงาน 5 discrepancy และ ground truth ที่ยังไม่มีอย่างชัดเจน

## ความหมายข้อมูล

Burn signal = เข้าเกณฑ์ปัจจุบัน, No burn signal = ไม่เข้าเกณฑ์ตรวจพบ, insufficient imagery = ยังจัดสถานะไม่ได้ ค่า Access Gap ที่หายไม่แทนด้วยศูนย์ ชุดนี้เป็นผลมกราคม 2026 ที่มีภาพเพียงพอ 1,229/47,316 แปลง จึงยังสรุปทั้งอำเภอไม่ได้

## การทดสอบและข้อจำกัด

ตรวจด้วย Streamlit AppTest และ Chromium ในเครื่อง: โหลดข้อมูลจริง, filter, ภาษา/ธีม และเปิดรายละเอียดแปลง ไม่มีการรัน Earth Engine ใหม่ ไม่ใช่ spreadsheet editor: ตารางใช้ดูและคัดกรอง ไม่เขียน label กลับไปยังข้อมูลหลัก ฟอนต์ Noto Sans Thai ใช้ SIL Open Font License ตามไฟล์ assets/OFL-NotoSansThai.txt

เมื่ออัปเดตข้อมูล ต้องเปลี่ยนไฟล์ทั้ง bundle จาก run เดียวกันแล้ว restart/clear cache อย่านำ master ใหม่ปน validation เก่า ไฟล์ .gz เป็น binary ตาม .gitattributes

## API reference

https://docs.streamlit.io/develop/api-reference/text/st.html
https://docs.streamlit.io/develop/api-reference/caching-and-state/st.query_params

Font source: https://github.com/google/fonts/tree/main/ofl/notosansthai
