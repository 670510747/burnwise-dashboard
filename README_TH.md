# BurnWise REVIEWED(4) — คงหน้าตาเดิม อัปเดตผลรอบใหม่

ใช้ CSS เดิมทุกตัวจาก app 2.py คงธีม การ์ด เมนู sidebar และคอลัมน์

## ใช้ทันที
นำ app.py, requirements.txt, .gitattributes, .streamlit/ และ data/ ใน ZIP นี้วางที่ root ของ repository
เปิดหน้าภาพรวม คุณภาพข้อมูล ผลประเมิน และเกี่ยวกับโครงการได้ทันทีโดยไม่ต้องอัปโหลด
ผลสรุปอ้างอิง notebook REVIEWED(4) และ CSV audit ที่แนบ ไม่ได้รัน Earth Engine ใหม่
ตารางรายเดือนกุมภาพันธ์–พฤษภาคมนำมาจาก saved HTML outputs O3.7/O3.17
ค่า GISTDA area และ BW/GISTDA ratio ใน output มีทศนิยม 3 ตำแหน่ง จึงระบุไว้บนเว็บ
เมตริกมกราคมคำนวณจาก TN/FP/FN/TP จำนวนเต็มที่บันทึกใน O2.4

## เปิดรายละเอียดรายแปลง — ไม่ต้องรันส่วนหลักใหม่
ไฟล์แนบครั้งนี้ยังไม่มี master CSV ใหม่ จึงไม่ใส่ master รอบเก่าในชุดนี้
แตก ZIP ไว้ในเครื่อง เช่น D:/BurnWise_Reviewed4
ที่ท้าย notebook REVIEWED(4) ใน kernel เดิมที่รันเสร็จแล้ว เพิ่มเซลล์:

%run -i "D:/BurnWise_Reviewed4/export_web_bundle.py"

แก้เฉพาะ path ให้ตรงตำแหน่งไฟล์จริง สคริปต์อ่านตัวแปร master_plots, THRESHOLD และช่วงเวลาใน kernel ที่มีอยู่
สคริปต์ตรวจจำนวน 47,311 แปลงและสถานะ Burn 3,403 / No Burn 38,787 / ข้อมูลไม่พอ 5,121
สร้าง ZIP ชื่อ burnwise_reviewed4_web_export.zip ใน working directory ของ notebook
นำไฟล์ทั้งหมดใน ZIP นั้นวางที่ root ของ repo แล้ว Reboot แอป
จะมี master ใหม่และ manifest พร้อม SHA256 ที่ตรงกัน เปิดตารางรายแปลงได้โดยอัตโนมัติ
ไม่มีการเรียก Earth Engine จากสคริปต์ส่งออกนี้
หากเปลี่ยนผลรันอีกครั้ง ให้ปรับ snapshot/summary เป็นรอบเดียวกันก่อนส่งออก

ห้ามคัดลอก master เก่าใส่ data/ เพราะ threshold และจำนวนแปลงเปลี่ยนแล้ว เว็บตรวจ hash ก่อนเปิด
อย่าแก้ manifest เพื่อข้ามการตรวจ หาก kernel ไม่ตรงกันต้องใช้ผลรันที่ถูกชุด

## ผลรอบใหม่
- pre 2025-10-01 ถึงก่อน 2026-01-01: 26 scenes / 22 unique UTC days
- post มกราคม 2026: 13 scenes / 12 unique UTC days
- threshold 0.20999151812466055, Positive-dNBR Otsu experimental baseline
- ภาพเพียงพอ 42,190 / 47,311 = 89.18%; รอภาพ 5,121
- ผลเทียบ GISTDA 41,447 แปลง: TN 27,726 FP 2,093 FN 10,387 TP 1,241
- Precision 37.22%, Recall 10.67%, F1 16.59%; satellite product agreement ไม่ใช่ independent ground truth
- ตารางกับ raster ต่างเกิน 2 pp 23 แปลง ป้ายเปลี่ยน 14 แปลง
- May baseline coverage 7.52%; method review และ GISTDA lineage ยังไม่ปิด
- O3.16 ต่างเพียง 0.0625 ไร่จาก inclusive/strict NDVI ไม่ได้รับรองความเหมือนกันของทุกเดือน
- O3.14 sensitivity เป็นการคำนวณแยก ห้ามแทน baseline

## รันในเครื่อง
pip install -r requirements.txt
streamlit run app.py

ยังไม่ได้ deploy ไปยังเว็บออนไลน์
