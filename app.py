"""BurnWise dashboard: CSV display only; no Earth Engine credentials required."""
from pathlib import Path
from html import escape
import io
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="BurnWise · ท่าตะโก", page_icon="🔥", layout="wide")
BASE = Path(__file__).resolve().parent
RED, ORANGE, GREY = "#B93C35", "#E56A43", "#B9C2CC"
STATUS = {"Burn": "ตรวจพบสัญญาณเผา", "No Burn": "ไม่เข้าเกณฑ์ตรวจพบ", "Unknown": "ข้อมูลไม่เพียงพอ"}
CSS = '''<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap');
html,body,[class*="st-"]{font-family:'Noto Sans Thai',sans-serif;}
.stApp{background:#FFF9F5;color:#422C28;}
[data-testid="stHeader"]{background:#FFF9F5;}
.block-container{max-width:1440px;padding:1.6rem 2.5rem 3rem;}
h1,h2,h3{color:#422C28!important;letter-spacing:-.02em;}
h1{font-size:2.1rem!important;}
.brand{font-size:28px;font-weight:700;color:#B93C35;line-height:1.1;}
.brand small{display:block;font-size:10px;letter-spacing:1.4px;color:#7D665D;margin-top:8px;}
.st-key-navigation{background:white;border:1px solid #F1DED2;border-radius:18px;padding:18px 22px;margin-bottom:18px;}
.st-key-navigation [data-testid="stRadio"]>div{gap:8px;justify-content:flex-end;}
.st-key-navigation [data-testid="stRadio"] label{padding:8px 14px;border-radius:12px;}
.st-key-navigation [data-testid="stRadio"] label:has(input:checked){background:#FFF0E7;color:#B93C35;}
.st-key-filters{background:#fff;border:1px solid #F1DED2;border-radius:18px;padding:12px 18px;margin:12px 0 20px;}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-color:#F1DED2!important;border-radius:18px!important;background:#fff;}
.metric{background:#fff;border:1px solid #F1DED2;border-radius:18px;padding:20px;min-height:145px;}
.metric .label{color:#7D665D;font-size:13px;border-left:4px solid var(--accent);padding-left:12px;}
.metric .value{font-size:34px;font-weight:700;color:var(--accent);margin:10px 0 4px;}
.metric .note{font-size:12px;color:#7D665D;}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid #F1DED2;}
.stButton button[kind="primary"],.stDownloadButton button[kind="primary"]{background:#B93C35;border-color:#B93C35;color:#fff;}
button{border-radius:10px!important;}
[data-baseweb="tag"]{background:#FFF0E7!important;color:#8F2D2B!important;}
@media(max-width:800px){.block-container{padding:1rem}.metric{padding:15px;min-height:135px}.metric .value{font-size:28px}.st-key-navigation [data-testid="stRadio"]>div{justify-content:flex-start;}}
</style>'''
st.markdown(CSS, unsafe_allow_html=True)


def read_csv(source):
    """Keep leading zeroes in IDs and report empty/broken files cleanly."""
    try:
        frame = pd.read_csv(source, encoding="utf-8-sig", dtype={"plot_id": "string", "tambon_id": "string"})
    except pd.errors.EmptyDataError:
        raise ValueError("CSV ว่าง: ส่งออกไฟล์จาก notebook ใหม่ก่อนนำมาใช้") from None
    except (UnicodeDecodeError, pd.errors.ParserError):
        raise ValueError("อ่าน CSV ไม่ได้ กรุณาส่งออกเป็น UTF-8 CSV จาก notebook") from None
    frame.columns = frame.columns.astype(str).str.strip()
    if frame.empty:
        raise ValueError("CSV มีเฉพาะหัวตาราง แต่ยังไม่มีข้อมูลแปลง")
    return frame


def prepare(frame):
    frame = frame.copy()
    required = {"plot_id", "tambon_name", "plot_area_rai", "burn_pct"}
    missing = required - set(frame)
    if missing:
        raise ValueError("CSV ขาดคอลัมน์: " + ", ".join(sorted(missing)))
    if frame["plot_id"].isna().any() or frame["plot_id"].astype(str).str.strip().eq("").any() or frame["plot_id"].duplicated().any():
        raise ValueError("plot_id ต้องมีค่าครบและไม่ซ้ำ กรุณาตรวจไฟล์ต้นทาง")
    if frame["tambon_name"].isna().any():
        raise ValueError("พบแปลงไม่มีชื่อตำบล กรุณาตรวจการเชื่อมข้อมูลต้นทาง")
    numeric = ["plot_area_rai", "burn_pct", "valid_observation_pct", "unknown_pct", "distance_to_collection_km", "access_gap_index", "centroid_lat", "centroid_lon", "tambon_income_baht_year"]
    for col in numeric:
        if col not in frame:
            frame[col] = np.nan
        original = frame[col]
        frame[col] = pd.to_numeric(original, errors="coerce")
        if (original.notna() & frame[col].isna()).any() or np.isinf(frame[col]).any():
            raise ValueError(f"คอลัมน์ {col} มีค่าที่ไม่ใช่ตัวเลข กรุณาตรวจ CSV")
    for col, lo, hi in [("burn_pct", 0, 100), ("valid_observation_pct", 0, 100), ("unknown_pct", 0, 100), ("access_gap_index", 0, 1), ("centroid_lat", -90, 90), ("centroid_lon", -180, 180)]:
        if ((frame[col] < lo) | (frame[col] > hi)).any():
            raise ValueError(f"{col} ต้องอยู่ในช่วง {lo}–{hi} กรุณาตรวจการคำนวณต้นทาง")
    if (frame["plot_area_rai"] < 0).any() or frame["plot_area_rai"].isna().any() or (frame["distance_to_collection_km"] < 0).any():
        raise ValueError("พื้นที่แปลงต้องมีค่าครบ และพื้นที่/ระยะทางต้องไม่ติดลบ")
    if "burn_status" in frame:
        if not frame["burn_status"].isin(STATUS).all():
            raise ValueError("burn_status ต้องเป็น Burn, No Burn หรือ Unknown เท่านั้น")
        mode = "modern"
        frame["display_status"] = frame["burn_status"].map(STATUS)
    elif "tier" in frame:
        if not frame["tier"].isin(["เขียว", "เหลือง", "แดง", "ข้อมูลไม่เพียงพอ"]).all():
            raise ValueError("tier มีค่าที่ไม่รู้จัก กรุณาตรวจ CSV")
        mode = "legacy"
        frame["display_status"] = frame["tier"].map({"เขียว": "Tier เขียว (เดิม)", "เหลือง": "Tier เหลือง (เดิม)", "แดง": "Tier แดง (เดิม)", "ข้อมูลไม่เพียงพอ": "ข้อมูลไม่เพียงพอ"})
    else:
        raise ValueError("ต้องมี burn_status จากโค้ดล่าสุด หรือ tier จากไฟล์เดิม เว็บจะไม่เดาสถานะเอง")
    for col in ["exclusion_reason", "priority_group", "needs_verification"]:
        if col not in frame:
            frame[col] = ""
    values = frame["needs_verification"].fillna("").astype(str).str.strip()
    frame["review_flag"] = ~values.str.lower().isin(["", "false", "0", "0.0", "none", "nan"])
    frame["review_flag"] |= frame["display_status"].eq("ข้อมูลไม่เพียงพอ") | frame["exclusion_reason"].fillna("").astype(str).str.strip().ne("")
    return frame, mode


def chart_style(fig, height=350):
    fig.update_layout(template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(family="Noto Sans Thai, sans-serif", color="#422C28"), height=height, margin=dict(l=10, r=10, t=20, b=10), legend=dict(title=None, orientation="h", y=-.22), hoverlabel=dict(bgcolor="white"))
    fig.update_xaxes(gridcolor="#F7EAE4")
    fig.update_yaxes(gridcolor="#F7EAE4")
    return fig


def csv_bytes(frame):
    return frame.to_csv(index=False).encode("utf-8-sig")


def metric(label, value, note, color=RED):
    st.markdown(f'<div class="metric" style="--accent:{color}"><div class="label">{escape(label)}</div><div class="value">{escape(str(value))}</div><div class="note">{escape(note)}</div></div>', unsafe_allow_html=True)


def status_chart(frame):
    counts = pd.crosstab(frame["tambon_name"], frame["display_status"]).reindex(columns=order, fill_value=0)
    counts.index.name = "tambon_name"
    pct = counts.div(counts.sum(axis=1), axis=0).mul(100)
    table = pct.reset_index().melt(id_vars="tambon_name", var_name="สถานะ", value_name="สัดส่วน (%)")
    actual = counts.reset_index().melt(id_vars="tambon_name", var_name="สถานะ", value_name="จำนวนแปลง")
    table = table.merge(actual, on=["tambon_name", "สถานะ"], validate="one_to_one")
    fig = px.bar(table, x="สัดส่วน (%)", y="tambon_name", color="สถานะ", orientation="h", color_discrete_map=colors, category_orders={"สถานะ": order}, hover_data={"จำนวนแปลง": True, "สัดส่วน (%)": ":.1f"}, labels={"tambon_name": ""}, barmode="stack")
    return chart_style(fig, max(340, len(counts) * 35 + 110)), counts


def show_map(frame, limit=12000):
    located = frame.dropna(subset=["centroid_lat", "centroid_lon"])
    if located.empty:
        st.info("ยังไม่มี centroid_lat / centroid_lon สำหรับแสดงแผนที่")
        return
    sampled = located if len(located) <= limit else located.sample(limit, random_state=42)
    fig = px.scatter_map(sampled, lat="centroid_lat", lon="centroid_lon", color="display_status", color_discrete_map=colors, category_orders={"display_status": order}, hover_name="plot_id", hover_data={"tambon_name": True, "burn_pct": ":.1f", "distance_to_collection_km": ":.2f", "centroid_lat": False, "centroid_lon": False}, zoom=10, center={"lat": located["centroid_lat"].median(), "lon": located["centroid_lon"].median()}, map_style="open-street-map", labels={"display_status": "สถานะ", "burn_pct": "สัญญาณเผา (%)", "distance_to_collection_km": "ระยะทาง (กม.)", "tambon_name": "ตำบล"})
    fig.update_traces(marker=dict(size=7, opacity=.7))
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=0, b=0), legend=dict(title=None, orientation="h"))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"จุดกึ่งกลางแปลง {len(sampled):,} / {len(located):,} จุดที่มีพิกัด · ขาดพิกัด {len(frame)-len(located):,} แปลง · ไม่ใช่ขอบเขตแปลง" + (" · สุ่มเพื่อให้แผนที่โหลดเร็ว; ตัวเลขสรุปใช้ข้อมูลครบ" if len(sampled) < len(located) else ""))


def show_scatter(frame):
    eligible = frame[~frame["display_status"].eq("ข้อมูลไม่เพียงพอ")].dropna(subset=["burn_pct", "access_gap_index"])
    if eligible.empty:
        st.info("ยังไม่มีแปลงที่มีสถานะและค่า burn_pct / access_gap_index ครบ")
        return
    sampled = eligible if len(eligible) <= 6000 else eligible.sample(6000, random_state=42)
    fig = px.scatter(sampled, x="access_gap_index", y="burn_pct", color="display_status", color_discrete_map=colors, hover_name="plot_id", hover_data=["tambon_name"], opacity=.55, labels={"access_gap_index": "Access Gap (0–1)", "burn_pct": "สัดส่วนสัญญาณเผา (%)", "display_status": "สถานะ"})
    fig.update_traces(marker=dict(size=5))
    fig.update_xaxes(range=[0, 1]); fig.update_yaxes(range=[0, 100])
    st.plotly_chart(chart_style(fig, 430), width="stretch")
    st.caption(f"แสดง {len(sampled):,} / {len(eligible):,} แปลงที่มีค่าครบและไม่อยู่กลุ่มข้อมูลไม่พอ · ใช้สำรวจความสัมพันธ์ ไม่ใช้ยืนยันสาเหตุ")


def demo_data():
    # Deliberately synthetic; selected by the user only. No export to project CSV.
    rng = np.random.default_rng(42)
    n = 600
    status = rng.choice(list(STATUS), n, p=[.23, .52, .25])
    burn = np.where(status == "Burn", rng.uniform(10, 90, n), rng.uniform(0, 9, n))
    burn[status == "Unknown"] = np.nan
    return pd.DataFrame({"plot_id": [f"DEMO-{i:04}" for i in range(n)], "tambon_name": rng.choice(["ต.ท่าตะโก", "ต.ดอนคา", "ต.ทำนบ", "ต.พนมรอก"], n), "plot_area_rai": rng.uniform(.5, 20, n), "burn_status": status, "burn_pct": burn, "valid_observation_pct": np.where(status == "Unknown", rng.uniform(10, 70, n), rng.uniform(80, 100, n)), "centroid_lat": rng.uniform(15.5, 15.8, n), "centroid_lon": rng.uniform(100.3, 100.6, n), "access_gap_index": rng.uniform(0, 1, n), "distance_to_collection_km": rng.uniform(0, 25, n), "exclusion_reason": np.where(status == "Unknown", "ข้อมูลจำลอง: coverage ไม่พอ", ""), "needs_verification": status == "Unknown"})


with st.sidebar:
    st.markdown("### ข้อมูลของโครงการ")
    st.caption("ใส่ CSV ใน data/ บน GitHub หรืออัปโหลดเพื่อดูในเซสชันนี้")
    uploaded = st.file_uploader("ตารางแปลง burnwise_master_plots.csv", type=["csv"], key="plots_upload")
    optional_overview = st.file_uploader("ภาพรวมตำบล (ไม่จำเป็น)", type=["csv"], key="overview_upload")
    demo = st.toggle("ทดลองหน้าตาด้วยข้อมูลจำลอง", value=False)
    period = st.text_input("ช่วงศึกษาที่ระบุใน notebook", placeholder="เช่น พ.ย. 2568 – ม.ค. 2569")
    st.caption("ชื่อช่วงศึกษาใช้แสดงประกอบเท่านั้น ไม่ได้กรองวันที่ใน CSV")

with st.container(key="navigation"):
    brand, nav = st.columns([1, 3], vertical_alignment="center")
    brand.markdown('<div class="brand">🔥 BurnWise<small>THA TAKO · FIELD INSIGHTS</small></div>', unsafe_allow_html=True)
    page = nav.radio("หน้าเว็บ", ["ภาพรวม", "สำรวจแปลง", "คุณภาพข้อมูล", "เกี่ยวกับโครงการ"], horizontal=True, label_visibility="collapsed")

path = BASE / "data" / "burnwise_master_plots.csv"
try:
    if demo:
        raw = demo_data(); source_name = "ข้อมูลจำลอง"
    elif uploaded is not None:
        raw = read_csv(io.BytesIO(uploaded.getvalue())); source_name = uploaded.name
    elif path.is_file():
        raw = read_csv(path); source_name = "data/burnwise_master_plots.csv"
    else:
        st.title("เริ่มต้นใช้งาน BurnWise")
        st.info("อัปโหลด burnwise_master_plots.csv ทางซ้าย หรือเพิ่มไฟล์นี้ในโฟลเดอร์ data ของ GitHub")
        st.markdown("เปิด **ทดลองหน้าตาด้วยข้อมูลจำลอง** เพื่อดูหน้าเว็บก่อนนำข้อมูลจริงเข้ามา")
        st.stop()
    plots, mode = prepare(raw)
except (ValueError, OSError) as exc:
    st.error(str(exc)); st.stop()

if mode == "modern":
    order = list(STATUS.values()); colors = dict(zip(order, [RED, ORANGE, GREY]))
else:
    order = ["Tier เขียว (เดิม)", "Tier เหลือง (เดิม)", "Tier แดง (เดิม)", "ข้อมูลไม่เพียงพอ"]
    colors = dict(zip(order, ["#3A8B62", "#EDA340", RED, GREY]))
if demo:
    st.warning("ข้อมูลจำลองทั้งหมด: ใช้ตรวจหน้าตาเว็บเท่านั้น ตัวเลขและพิกัดไม่ใช่ผลของโครงการ")
elif mode == "legacy":
    st.warning("ไฟล์นี้ใช้ Tier เดิมจากสัดส่วนไถกลบ: แสดงกลุ่มตามต้นทาง ไม่แปลงเป็น Burn / No Burn · valid_observation_pct เดิมอาจเป็นผลรวมเผา+ไถกลบ จึงยังใช้ยืนยัน coverage ไม่ได้")
else:
    st.caption("ผลจากดาวเทียมเบื้องต้น · No Burn = ไม่เข้าเกณฑ์ตรวจพบ ไม่ใช่หลักฐานยืนยันว่าไม่เผาหรือไถกลบ")
st.caption(f"แหล่งข้อมูล: {source_name}" + (f" · ช่วงศึกษา: {period}" if period else " · ยังไม่ได้ระบุช่วงศึกษา"))

with st.container(key="filters"):
    a, b = st.columns(2)
    names = sorted(plots["tambon_name"].unique())
    selected_names = a.multiselect("ตำบล", names, default=names)
    selected_status = b.multiselect("สถานะ", order, default=order)
f = plots[plots["tambon_name"].isin(selected_names) & plots["display_status"].isin(selected_status)].copy()
if f.empty:
    st.info("ไม่มีแปลงตรงกับตัวกรอง กรุณาเลือกตำบลหรือสถานะเพิ่ม"); st.stop()

export_cols = [c for c in f.columns if c not in ["display_status", "review_flag"]]
st.download_button("↓ ดาวน์โหลดแปลงที่เลือก", csv_bytes(f[export_cols]), "burnwise_filtered_plots.csv", "text/csv", type="primary")

if page == "ภาพรวม":
    st.title("ภาพรวมพื้นที่นำร่อง")
    st.caption(f"อำเภอท่าตะโก · {len(f):,} จาก {len(plots):,} แปลง · {f['tambon_name'].nunique()} ตำบล · พื้นที่รวม {f['plot_area_rai'].sum():,.1f} ไร่")
    if mode == "modern":
        cards = [("แปลงทั้งหมด", len(f), "แปลงในตัวกรอง", RED)] + [(label, int(f["display_status"].eq(label).sum()), f"{f['display_status'].eq(label).mean()*100:.1f}% ของแปลงที่เลือก", colors[label]) for label in order]
    else:
        cards = [("แปลงทั้งหมด", len(f), "แปลงในตัวกรอง", RED), ("พื้นที่รวม (ไร่)", f"{f['plot_area_rai'].sum():,.0f}", "ผลรวมพื้นที่แปลงตาม CSV", ORANGE), ("Tier แดง (เดิม)", int(f["display_status"].eq("Tier แดง (เดิม)").sum()), "กลุ่มจากตรรกะเดิม ไม่ยืนยันว่าเผา", RED), ("ข้อมูลไม่เพียงพอ", int(f["display_status"].eq("ข้อมูลไม่เพียงพอ").sum()), "แยกจากกลุ่มที่จัดสถานะได้", "#566370")]
    for col, (label, value, note, color) in zip(st.columns(4), cards):
        with col: metric(label, f"{value:,}" if isinstance(value, int) else value, note, "#566370" if color == GREY else color)
    left, right = st.columns([1.1, 1])
    with left, st.container(border=True):
        st.subheader("สถานะรายตำบล")
        st.caption("สัดส่วนจำนวนแปลงในตัวกรอง รวมกลุ่มข้อมูลไม่พอ")
        fig, counts = status_chart(f); st.plotly_chart(fig, width="stretch")
        st.download_button("ดาวน์โหลดจำนวนแปลงรายตำบล", csv_bytes(counts.reset_index()), "burnwise_tambon_counts.csv", "text/csv")
    with right, st.container(border=True):
        st.subheader("สัดส่วนสัญญาณเผารายตำบล")
        overview = None
        overview_path = BASE / "data" / "burnwise_tambon_overview.csv"
        if not demo and (optional_overview is not None or overview_path.is_file()):
            try:
                overview = read_csv(io.BytesIO(optional_overview.getvalue()) if optional_overview else overview_path)
                if not {"tambon_name", "burn_pct (%)"}.issubset(overview):
                    raise ValueError("ภาพรวมตำบลต้องมี tambon_name และ burn_pct (%)")
                if overview["tambon_name"].duplicated().any():
                    raise ValueError("ตารางภาพรวมตำบลมีชื่อตำบลซ้ำ")
                overview["burn_pct (%)"] = pd.to_numeric(overview["burn_pct (%)"], errors="raise")
                if not overview["burn_pct (%)"].dropna().between(0, 100).all():
                    raise ValueError("burn_pct (%) ต้องอยู่ในช่วง 0–100")
                overview = overview[overview["tambon_name"].isin(selected_names)].dropna(subset=["burn_pct (%)"])
            except (ValueError, OSError) as exc:
                st.warning(f"ไม่แสดงภาพรวมตำบล: {exc}"); overview = None
        if overview is not None and not overview.empty:
            fig = px.bar(overview.sort_values("burn_pct (%)"), x="burn_pct (%)", y="tambon_name", orientation="h", color_discrete_sequence=[RED], labels={"tambon_name": "", "burn_pct (%)": "สัดส่วนพื้นที่ (%)"})
            st.plotly_chart(chart_style(fig), width="stretch")
            st.caption("ใช้ตารางภาพรวมจาก notebook ตามตำบลที่เลือก · ไม่เปลี่ยนตามตัวกรองสถานะแปลง · ฐานพื้นที่ต่างจากกราฟจำนวนแปลง")
            st.dataframe(overview, hide_index=True, width="stretch")
        else:
            mean_burn = f[~f["display_status"].eq("ข้อมูลไม่เพียงพอ")].groupby("tambon_name", as_index=False)["burn_pct"].mean().dropna()
            if mean_burn.empty:
                st.info("ยังไม่มีค่าสัญญาณเผาในแปลงที่จัดสถานะได้")
            else:
                fig = px.bar(mean_burn.sort_values("burn_pct"), x="burn_pct", y="tambon_name", orientation="h", color_discrete_sequence=[RED], labels={"tambon_name": "", "burn_pct": "ค่าเฉลี่ยต่อแปลง (%)"})
                st.plotly_chart(chart_style(fig), width="stretch")
            st.caption("ค่าเฉลี่ย burn_pct ต่อแปลงที่ไม่อยู่กลุ่มข้อมูลไม่พอ · ไม่ใช่สัดส่วนพื้นที่เผาทั้งตำบล · เพิ่ม CSV ภาพรวมเพื่อแสดงผลระดับพื้นที่")
    left, right = st.columns([1.2, 1])
    with left, st.container(border=True):
        st.subheader("แผนที่พื้นที่ศึกษา"); show_map(f)
    with right, st.container(border=True):
        st.subheader("สัญญาณเผา × Access Gap"); show_scatter(f)
    with st.container(border=True):
        st.subheader("แปลงที่ควรตรวจสอบเพิ่มเติม")
        review = f[f["review_flag"]]
        st.caption(f"{len(review):,} แปลง · รวมสถานะข้อมูลไม่พอ เหตุผลคัดออก หรือธงตรวจสอบจากต้นทาง · ตัวอย่าง 100 แถวแรก")
        st.dataframe(review[["plot_id", "tambon_name", "display_status", "burn_pct", "valid_observation_pct", "exclusion_reason", "needs_verification"]].head(100), hide_index=True, width="stretch")

elif page == "สำรวจแปลง":
    st.title("สำรวจแปลงรายพื้นที่")
    query = st.text_input("ค้นหารหัสแปลง", placeholder="พิมพ์ส่วนหนึ่งของ plot_id")
    review_only = st.checkbox("แสดงเฉพาะแปลงที่ควรตรวจสอบเพิ่มเติม")
    explored = f[f["plot_id"].astype(str).str.contains(query, regex=False, case=False)]
    if review_only: explored = explored[explored["review_flag"]]
    st.caption(f"พบ {len(explored):,} แปลง · ตารางแสดงไม่เกิน 1,000 แถวแรก")
    show_map(explored)
    cols = ["plot_id", "tambon_name", "display_status", "plot_area_rai", "burn_pct", "valid_observation_pct", "distance_to_collection_km", "access_gap_index", "exclusion_reason"]
    st.dataframe(explored[cols].head(1000), hide_index=True, width="stretch")
    st.download_button("ดาวน์โหลดผลค้นหาทั้งหมด", csv_bytes(explored[export_cols]), "burnwise_search.csv", "text/csv")
    if not explored.empty:
        ids = explored["plot_id"].tolist()[:1000]
        choice = st.selectbox("ดูรายละเอียดแปลง (จาก 1,000 แถวแรก)", ids)
        row = explored[explored["plot_id"].eq(choice)].iloc[0]
        with st.container(border=True):
            st.subheader(str(choice))
            st.write(f"**ตำบล:** {row['tambon_name']} · **สถานะ:** {row['display_status']}")
            st.dataframe(pd.DataFrame({"รายการ": export_cols, "ค่า": ["—" if pd.isna(row[c]) else str(row[c]) for c in export_cols]}), hide_index=True, width="stretch")

elif page == "คุณภาพข้อมูล":
    st.title("คุณภาพข้อมูลและจุดที่ต้องตรวจสอบ")
    unknown = f[f["display_status"].eq("ข้อมูลไม่เพียงพอ")]
    a, b, c = st.columns(3)
    with a: metric("ข้อมูลไม่เพียงพอ", f"{len(unknown):,}", "แปลงที่ยังไม่ควรสรุปสถานะ", "#566370")
    with b: metric("ไม่มีระยะทางถนน", f"{f['distance_to_collection_km'].isna().sum():,}", "ไม่แทนระยะทางที่หายด้วยศูนย์", ORANGE)
    with c: metric("ไม่มี Access Gap", f"{f['access_gap_index'].isna().sum():,}", "ตรวจข้อมูลประกอบก่อนจัดลำดับ", RED)
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("Coverage" if mode == "modern" else "สัดส่วน valid_observation_pct เดิม")
        valid = f.dropna(subset=["valid_observation_pct"])
        if valid.empty: st.info("ไม่มีข้อมูล valid_observation_pct")
        else:
            fig = px.histogram(valid, x="valid_observation_pct", nbins=20, color_discrete_sequence=[ORANGE], labels={"valid_observation_pct": "สัดส่วน (%)"})
            if mode == "modern": fig.add_vline(x=80, line_dash="dash", line_color=RED, annotation_text="เกณฑ์โค้ดหลัก 80%")
            st.plotly_chart(chart_style(fig), width="stretch")
        st.caption(f"ไม่มีค่า {f['valid_observation_pct'].isna().sum():,} แปลง" + (" · ในไฟล์เดิมค่านี้อาจเป็นเผา+ไถกลบ ไม่ใช่พื้นที่ที่มีภาพใช้ได้" if mode == "legacy" else " · กราฟไม่เปลี่ยนสถานะที่บันทึกใน CSV"))
    with right, st.container(border=True):
        st.subheader("เหตุผลที่ต้องตรวจสอบ")
        reasons = f.loc[f["review_flag"], "exclusion_reason"].fillna("").astype(str).str.strip().replace("", "ธงตรวจสอบ/สถานะข้อมูลไม่พอ แต่ไม่มีเหตุผลคัดออก")
        counts = reasons.value_counts().rename_axis("เหตุผล").reset_index(name="จำนวนแปลง")
        st.dataframe(counts, hide_index=True, width="stretch")
    st.info("GISTDA เป็นส่วนเปรียบเทียบเพิ่มเติม: เว็บนี้ไม่ต้องรอไฟล์รอยเผา หากช่วงอ้างอิงไม่ครบ ให้เว้นผลประเมินส่วนนั้นไว้")
    st.markdown("ผล FIRMS ที่เคยทดสอบ 2/2 จุดที่อ่านภาพได้ มีตัวอย่างน้อย และไม่มีตัวอย่างยืนยันไม่เผา จึงยังไม่ใช้สรุปความแม่นยำทั้งโครงการ")

else:
    st.title("เกี่ยวกับ BurnWise")
    with st.container(border=True):
        st.subheader("ข้อมูลสำหรับสำรวจและช่วยเหลือพื้นที่")
        st.write("BurnWise รวบรวมสัญญาณจากดาวเทียม ขอบเขตแปลง และการเข้าถึงจุดรวบรวม เพื่อช่วยสำรวจพื้นที่นำร่องอำเภอท่าตะโก")
        st.write("เว็บนี้อ่านผล CSV ที่คำนวณแล้วจาก notebook ไม่ได้คำนวณ Earth Engine ใหม่ ไม่ได้เปลี่ยน threshold หรือจัดสถานะแปลงใหม่")
        st.markdown("**แหล่งข้อมูลในกระบวนการ:** Sentinel-2, FIRMS, Fields of The World, ขอบเขต DOPA, โครงข่ายถนน OpenStreetMap และข้อมูลรายได้ระดับตำบลที่ทีมเลือกใช้")
        st.markdown("**ข้อจำกัด:** สัญญาณเผาไม่ใช่หลักฐานยืนยันรายบุคคล · No Burn ไม่ยืนยันว่าไถกลบ · รายได้ตำบลไม่ใช่รายได้เจ้าของแปลง · Access Gap เป็นดัชนีประกอบการสำรวจ")
        st.caption("ภาพรวมจำนวนแปลงคำนวณใหม่จากตารางหลัก เพื่อหลีกเลี่ยง Score Panel จากคนละรอบประมวลผล")

st.divider()
st.caption("BurnWise · ท่าตะโก · ตรวจสอบข้อมูลและหลักฐานภาคสนามก่อนใช้กำหนดมาตรการ")
