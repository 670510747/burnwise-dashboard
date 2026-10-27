"""BurnWise · ตรรกะของหน้า "จากแปลงแดงสู่มาตรการ" (pandas/numpy เท่านั้น ทดสอบได้โดยไม่ต้องมี Streamlit)

หลักการ
- แปลง "แดง" = display_status เป็นตรวจพบสัญญาณเผา และ burn_pct >= RED_MIN (ตรงกับเกณฑ์ Tier แดงใน notebook)
- ส่วนที่ยังไม่มีข้อมูลจริงในรอบนี้ (จุดรับซื้อที่ยืนยันแล้ว, ข้อมูลครัวเรือน) ใช้ค่าจำลองเชิงสาธิต
  ตามที่เมนเทอ Monitoring Session 2 อนุญาต: ต้องติดป้าย "จำลอง" ทุกที่ที่แสดง และห้ามนำไปใช้เป็นผลของโครงการ
- ค่าจำลองสุ่มแบบคงที่ต่อ plot_id (ผลไม่เปลี่ยนเมื่อกรอง/รีเฟรช)
- ถ้าไฟล์จริงมี access_gap_index อยู่แล้ว จะใช้ค่าจริงนั้นแทนค่าจำลองเสมอ
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RED_MIN = 50.0          # burn_pct >= 50 = แดง (เกณฑ์เดียวกับ notebook G)
YELLOW_MIN = 10.0       # 10 <= burn_pct < 50 = เหลือง (ยังไม่แน่ใจ ซ่อนเป็นค่าเริ่มต้น)
W_DIST, W_SIZE, W_INCOME = 0.5, 0.3, 0.2   # น้ำหนักทดลองเดียวกับ notebook H
DIST_CAP_KM = 40.0
DETOUR = 1.3            # ตัวคูณเส้นตรง -> ระยะถนนโดยประมาณ (สาธิตเท่านั้น)

LANE_HELP = "ช่วยก่อน"
LANE_CHECK = "ตรวจก่อนใช้มาตรการ"

# จุดรับซื้อ/โรงงานจาก notebook เซลล์ H — ทั้งหมดยังเป็น unverified
FACILITIES = [
    ("รวมผลใบโอเพาเวอร์", "โรงไฟฟ้าชีวมวล", 15.7196, 100.0872),
    ("KTIS 3", "โรงงานน้ำตาล + ชีวมวล", 15.3773, 100.2419),
    ("ไทยส่งเสริม โรงสีไฟ", "โรงสีข้าว", 15.6357, 100.4804),
    ("โรงงานน้ำตาลรวมผล", "โรงงานน้ำตาล", 15.7917, 100.0863),
    ("โรงสีไพเกียรติรุ่งเรือง", "โรงสีข้าว", 15.6533, 100.5698),
    ("TRUE ENERGY นครสวรรค์", "โรงไฟฟ้าชีวมวล", 15.8617, 100.5842),
    ("เกษตรไทยไบโอเพาเวอร์", "โรงไฟฟ้าชีวมวล", 15.2865, 100.419),
    ("ลานรับซื้อ ดอนคา", "จุดรับซื้อผลผลิตเกษตร", 15.6512, 100.558),
    ("KTBE", "ชีวมวล/เอทานอล", 15.2842, 100.4173),
    ("นครสวรรค์ ไบโอแก๊ส", "ก๊าซชีวภาพ", 15.7485, 100.321),
]
FACILITY_DF = pd.DataFrame(FACILITIES, columns=["name", "type", "lat", "lon"])

MEASURE_HELP_DIST = "จุดรับซื้อเคลื่อนที่ / อุดหนุนค่าขนส่งเศษวัสดุ"
MEASURE_HELP_SIZE = "รถไถขนาดเล็ก / รวมกลุ่มแปลงเล็กใช้เครื่องจักรร่วมกัน"
MEASURE_HELP_INCOME = "เงินอุดหนุนแบบมีเงื่อนไข + โควตาคิวเช่าเครื่องจักรรัฐราคาพิเศษ"
MEASURE_CHECK = "ตรวจภาคสนามยืนยัน → สื่อสาร/จูงใจ → (ขั้นสุดท้าย) ระงับสนับสนุนบางส่วน"


def stable_uniform(ids: pd.Series, salt: str) -> np.ndarray:
    """ค่า 0..1 คงที่ต่อ plot_id + salt (ไม่ขึ้นกับลำดับแถวหรือตัวกรอง)"""
    keys = ids.astype(str) + "|" + salt
    h = pd.util.hash_pandas_object(keys, index=False).to_numpy(dtype="uint64")
    return (h % np.uint64(1_000_003)).astype("float64") / 1_000_003.0


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dl = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def nearest_facility(lat: np.ndarray, lon: np.ndarray, facilities: pd.DataFrame = FACILITY_DF):
    """ระยะเส้นตรง (กม.) และชื่อจุดที่ใกล้ที่สุด; แถวที่ไม่มีพิกัดได้ NaN"""
    lat = np.asarray(lat, dtype="float64")
    lon = np.asarray(lon, dtype="float64")
    d = np.full((len(lat), len(facilities)), np.nan)
    for j, (flat, flon) in enumerate(zip(facilities["lat"], facilities["lon"])):
        d[:, j] = haversine_km(lat, lon, flat, flon)
    ok = ~np.isnan(d).all(axis=1)
    dist = np.full(len(lat), np.nan)
    idx = np.zeros(len(lat), dtype=int)
    if ok.any():
        idx[ok] = np.nanargmin(d[ok], axis=1)
        dist[ok] = d[ok, idx[ok]]
    names = np.where(ok, facilities["name"].to_numpy()[idx], "")
    return dist, names


def circle_latlon(lat: float, lon: float, km: float, n: int = 72):
    """วงกลม buffer เป็นรายการ lat/lon (ปิดวง) สำหรับวาดบนแผนที่"""
    ang = np.linspace(0, 2 * np.pi, n + 1)
    dlat = km / 111.32
    dlon = km / (111.32 * np.cos(np.radians(lat)))
    return (lat + dlat * np.sin(ang)).tolist(), (lon + dlon * np.cos(ang)).tolist()


def tier_of(burn_pct: pd.Series) -> pd.Series:
    t = pd.Series("เขียว", index=burn_pct.index, dtype="object")
    t[burn_pct >= YELLOW_MIN] = "เหลือง"
    t[burn_pct >= RED_MIN] = "แดง"
    t[burn_pct.isna()] = "ไม่ทราบ"
    return t


def officer_counts(plots: pd.DataFrame) -> dict:
    """ตัวเลข 3-4 ตัวที่เจ้าหน้าที่ใช้ได้จริง (ไม่ใช่ตัวเลขเทคนิค)"""
    st_ = plots["display_status"]
    burn = plots["burn_pct"]
    detected = st_.eq("ตรวจพบสัญญาณเผา")
    return {
        "total": int(len(plots)),
        "no_visit": int(st_.eq("ไม่เข้าเกณฑ์ตรวจพบ").sum()),
        "red": int((detected & (burn >= RED_MIN)).sum()),
        "yellow": int((detected & (burn >= YELLOW_MIN) & (burn < RED_MIN)).sum()),
        "unknown": int(st_.eq("ข้อมูลไม่เพียงพอ").sum()),
    }


def build_red_table(plots: pd.DataFrame, gap_threshold: float = 0.5, include_yellow: bool = False) -> pd.DataFrame:
    """ตารางแปลงแดง (และเหลืองถ้าขอ) พร้อม Access Gap, เหตุผล, กลุ่ม (lane) และมาตรการ

    คืนคอลัมน์เพิ่ม: tier, burn_area_rai, dist_km, dist_source, nearest_facility, size_gap, income_gap,
    gap, gap_source, reason, lane, measure, sim_owner_age, sim_education, sim_has_machine, is_simulated
    """
    d = plots["display_status"].eq("ตรวจพบสัญญาณเผา") & plots["burn_pct"].ge(YELLOW_MIN if include_yellow else RED_MIN)
    df = plots.loc[d].copy()
    if df.empty:
        return df
    df["tier"] = tier_of(df["burn_pct"])
    df["burn_area_rai"] = df["plot_area_rai"] * df["burn_pct"] / 100.0

    # --- ระยะทาง: ใช้ค่าจริงถ้ามี ไม่งั้นประมาณจากเส้นตรง × DETOUR ไปจุดที่ยังไม่ยืนยัน (จำลอง)
    sim_dist, fac_name = nearest_facility(df["centroid_lat"].to_numpy(), df["centroid_lon"].to_numpy())
    sim_dist = sim_dist * DETOUR
    miss = np.isnan(sim_dist)  # ไม่มีพิกัด → สุ่มคงที่ 3–35 กม. (จำลอง)
    sim_dist[miss] = 3 + 32 * stable_uniform(df["plot_id"], "dist")[miss]
    real = df["distance_to_collection_km"].to_numpy(dtype="float64")
    use_real = ~np.isnan(real)
    df["dist_km"] = np.where(use_real, real, sim_dist)
    df["dist_source"] = np.where(use_real, "จริง", "จำลอง")
    df["nearest_facility"] = np.where(use_real, "", fac_name)
    dist_gap = np.clip(df["dist_km"].to_numpy() / DIST_CAP_KM, 0, 1)

    # --- ขนาดแปลง: เล็ก = เข้าถึงยาก (อันดับเปอร์เซ็นไทล์ภายในชุดนี้ ไม่ขึ้นกับสเกลหน่วย)
    df["size_gap"] = 1 - df["plot_area_rai"].rank(pct=True, method="average").to_numpy()
    # --- รายได้ตำบล: ต่ำ = เข้าถึงยาก; ถ้าไม่มีค่าจริง ใช้ค่าสุ่มจำลอง
    inc = df["tambon_income_baht_year"]
    inc_gap = 1 - inc.rank(pct=True, method="average")
    inc_sim = pd.Series(stable_uniform(df["plot_id"], "income"), index=df.index)
    df["income_gap"] = inc_gap.where(inc.notna(), inc_sim)
    df["income_source"] = np.where(inc.notna(), "จริง", "จำลอง")

    calc = W_DIST * dist_gap + W_SIZE * df["size_gap"].to_numpy() + W_INCOME * df["income_gap"].to_numpy()
    real_gap = df["access_gap_index"].to_numpy(dtype="float64")
    use_real_gap = ~np.isnan(real_gap)
    df["gap"] = np.where(use_real_gap, real_gap, calc)
    df["gap_source"] = np.where(use_real_gap, "จริง", "จำลองบางส่วน")

    comp = pd.DataFrame({"ไกลจุดรับซื้อ": W_DIST * dist_gap, "แปลงเล็ก": W_SIZE * df["size_gap"].to_numpy(),
                         "รายได้ตำบลต่ำ": W_INCOME * df["income_gap"].to_numpy()}, index=df.index)
    df["reason"] = comp.idxmax(axis=1)

    # --- ข้อมูลครัวเรือนจำลอง 3 ตัวแปร (ตามคำแนะนำเมนเทอ: 2–4 ตัวแปรก็พอ)
    u_age = stable_uniform(df["plot_id"], "age")
    u_edu = stable_uniform(df["plot_id"], "edu")
    u_mach = stable_uniform(df["plot_id"], "mach")
    df["sim_owner_age"] = (35 + 40 * u_age).round().astype(int)
    df["sim_education"] = np.select([u_edu < 0.55, u_edu < 0.88], ["ประถม", "มัธยม"], default="อนุปริญญาขึ้นไป")
    df["sim_has_machine"] = u_mach < 0.2
    df["is_simulated"] = True

    df["lane"] = np.where(df["gap"] >= gap_threshold, LANE_HELP, LANE_CHECK)
    measure = np.full(len(df), MEASURE_CHECK, dtype=object)
    helping = df["lane"].eq(LANE_HELP).to_numpy()
    by_reason = df["reason"].map({"ไกลจุดรับซื้อ": MEASURE_HELP_DIST, "แปลงเล็ก": MEASURE_HELP_SIZE,
                                  "รายได้ตำบลต่ำ": MEASURE_HELP_INCOME}).to_numpy(dtype=object)
    measure[helping] = by_reason[helping]
    df["measure_demo"] = measure
    if "tier" in df and include_yellow:
        df.loc[df["tier"].eq("เหลือง"), "measure_demo"] = "ยังไม่แน่ใจ — รอภาพเพิ่ม/ตรวจซ้ำก่อนกำหนดมาตรการ"
        df.loc[df["tier"].eq("เหลือง"), "lane"] = "รอตรวจซ้ำ"
    return df


def priority_list(table: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    """รายชื่อแปลงที่ควรไปตรวจก่อน: แปลงแดงเรียงตามพื้นที่ที่ถูกเผาจริง (ไร่) มากสุดก่อน"""
    red = table[table["tier"].eq("แดง")] if "tier" in table else table
    out = red.sort_values(["burn_area_rai", "plot_area_rai"], ascending=False).head(n).copy()
    out.insert(0, "ลำดับ", range(1, len(out) + 1))
    return out


def lane_summary(table: pd.DataFrame) -> pd.DataFrame:
    red = table[table["tier"].eq("แดง")]
    if red.empty:
        return pd.DataFrame(columns=["lane", "n", "area_rai", "mean_gap", "mean_dist", "mean_size"])
    g = red.groupby("lane").agg(n=("plot_id", "size"), area_rai=("plot_area_rai", "sum"), burn_area_rai=("burn_area_rai", "sum"),
                                 mean_gap=("gap", "mean"), mean_dist=("dist_km", "mean"), mean_size=("plot_area_rai", "mean"))
    return g.reset_index()


def pick_examples(table: pd.DataFrame):
    """เลือกตัวอย่างแปลงแดง 2 แปลงสำหรับเล่าเรื่อง: A = ช่วยก่อน (gap สูงสุดในกลุ่มที่มีพื้นที่เผาปานกลางขึ้นไป),
    B = ตรวจก่อนใช้มาตรการ (แปลงใหญ่ gap ต่ำ) ถ้าไม่มีกลุ่มใดกลุ่มหนึ่งคืน None"""
    red = table[table["tier"].eq("แดง")]
    if red.empty:
        return None, None
    help_ = red[red["lane"].eq(LANE_HELP)]
    check = red[red["lane"].eq(LANE_CHECK)]
    a = None
    if not help_.empty:
        pool = help_[help_["burn_area_rai"] >= help_["burn_area_rai"].median()]
        a = (pool if not pool.empty else help_).sort_values("gap", ascending=False).iloc[0]
    b = None
    if not check.empty:
        b = check.sort_values(["plot_area_rai", "gap"], ascending=[False, True]).iloc[0]
    return a, b
