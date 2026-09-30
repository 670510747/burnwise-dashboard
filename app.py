import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="BurnWise — แดชบอร์ดพื้นที่นำร่องท่าตะโก",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DESIGN TOKENS
# ============================================================
COLOR_CREAM      = "#FAF6EE"
COLOR_CARD       = "#FFFDF8"
COLOR_INK        = "#2B2A25"
COLOR_INK_SOFT   = "#6B6558"
COLOR_GREEN      = "#3A8B62"   # เขียว = ไถกลบ / ปฏิบัติดี
COLOR_GREEN_SOFT = "#E4EBDD"
COLOR_AMBER      = "#F0A143"   # เหลือง = มีเงื่อนไข
COLOR_AMBER_SOFT = "#F6E9CF"
COLOR_EMBER      = "#C8463D"   # แดง = สัญญาณเผา (สีไฟ ไม่ใช่สีตกแต่ง)
COLOR_EMBER_SOFT = "#F5DCCB"
COLOR_GREY       = "#A9A09B"   # ข้อมูลไม่เพียงพอ
COLOR_GREY_SOFT  = "#EAE6DA"

TIER_COLORS = {
    "เขียว": COLOR_GREEN,
    "เหลือง": COLOR_AMBER,
    "แดง": COLOR_EMBER,
    "ข้อมูลไม่เพียงพอ": COLOR_GREY,
}
TIER_ORDER = ["เขียว", "เหลือง", "แดง", "ข้อมูลไม่เพียงพอ"]

# ============================================================
# GLOBAL CSS — fonts, cards, sidebar, tables
# ============================================================
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap');
:root {color-scheme: light;}
html,body,.stApp,.stApp * {font-family:'Noto Sans Thai',sans-serif;}
.stApp,[data-testid="stAppViewContainer"] {background:linear-gradient(180deg,#fff9f5 0%,#ffffff 340px);color:#422c28;}
[data-testid="stHeader"] {background:#fff9f5;}
.block-container {max-width:1240px;padding-top:1.2rem;padding-bottom:3.5rem;}
.stApp h1,.stApp h2,.stApp h3,.stApp h4 {color:#552b29;letter-spacing:-.02em;}
.stApp h1 {font-size:clamp(28px,3vw,43px);font-weight:700;}
.st-key-topbar {background:#fff;border:1px solid #f4dfd7;border-radius:22px;padding:18px 24px;margin:12px 0 20px;box-shadow:0 12px 32px rgba(173,68,42,.07);}
.brand {font-size:25px;font-weight:700;color:#a73532;line-height:1.45;}
.brand small {display:block;font-size:11px;letter-spacing:1.7px;color:#bf6d47;font-weight:700;}
.st-key-topbar [data-testid="stRadio"] > div {gap:6px;flex-wrap:wrap;justify-content:flex-end;}
.st-key-topbar [data-testid="stRadio"] label {border-radius:12px;padding:7px 13px;background:#fff4ed;border:1px solid #f5dfd3;color:#653e32;min-height:42px;}
.st-key-topbar [data-testid="stRadio"] label:has(input:checked) {background:#ba3d36;border-color:#ba3d36;color:white;}
.st-key-topbar [data-testid="stRadio"] label p {color:inherit;font-weight:600;white-space:nowrap;font-size:13px;}
.st-key-topbar [data-testid="stRadio"] label [data-testid="stMarkdownContainer"] {color:inherit;}
.st-key-filters {background:#fff;border:1px solid #f1ded2;border-radius:20px;padding:16px 20px;margin-bottom:18px;box-shadow:0 8px 24px rgba(151,64,45,.05);}
.st-key-filters [data-testid="stWidgetLabel"] p {font-weight:600;color:#683c32;}
[data-testid="stMultiSelect"] > div > div {background:#fff;border-color:#e7cbbd;color:#422c28;}
[data-testid="stMultiSelect"] span[data-baseweb="tag"] {background:#ffede2;color:#872e29;}
.kpi-card {background:#fff;border:1px solid #f3ded0;border-radius:20px;padding:23px;min-height:155px;box-shadow:0 10px 30px rgba(160,75,42,.07);border-top:4px solid #e56a43;}
.kpi-label {color:#765b51;font-size:13px;font-weight:600;min-height:26px;}
.kpi-value {color:#a93430;font-size:35px;font-weight:700;font-variant-numeric:tabular-nums;margin:5px 0;}
.kpi-sub,.caption-muted {color:#7d665d;font-size:12px;}
[class*="st-key-card_"] {background:#fff;border:1px solid #f2e0d6;border-radius:22px;padding:20px;margin:8px 0 18px;box-shadow:0 10px 28px rgba(160,75,42,.06);}
.stApp [data-testid="stDataFrame"] {border:1px solid #f1ded2;border-radius:16px;overflow:hidden;}
.stButton button,.stDownloadButton button {border-radius:12px;background:#b93c35;border:1px solid #b93c35;color:#fff;font-weight:600;}
.stButton button:hover,.stDownloadButton button:hover {background:#df603d;color:#fff;border-color:#df603d;}
.stApp hr {border-color:#f1dfd6;}
@media(max-width:800px){.block-container{padding:1rem}.st-key-topbar{padding:14px}.brand{font-size:21px}.st-key-topbar [data-testid="stRadio"] > div{justify-content:flex-start}.kpi-value{font-size:28px}}
</style>""",unsafe_allow_html=True)

# ============================================================
# DATA LOADING
# ============================================================
DATA_DIR = Path(__file__).resolve().parent / "data"

@st.cache_data
def load_data():
    tables = []
    for name in ["burnwise_master_plots.csv", "burnwise_score_panel.csv", "burnwise_tambon_overview.csv"]:
        path = DATA_DIR / name
        if not path.is_file():
            raise ValueError(f"ไม่พบไฟล์ data/{name} กรุณาอัปโหลด CSV ลงโฟลเดอร์ data")
        try:
            table = pd.read_csv(path, encoding="utf-8-sig")
        except pd.errors.EmptyDataError:
            raise ValueError(f"ไฟล์ data/{name} ว่าง กรุณาอัปโหลดไฟล์ผลลัพธ์จริงจาก notebook") from None
        if table.empty:
            raise ValueError(f"ไฟล์ data/{name} มีหัวตารางแต่ไม่มีแถวข้อมูล")
        tables.append(table)
    required = [
        {"plot_id", "tambon_name", "plot_area_rai", "burn_pct", "tillage_pct", "valid_observation_pct", "tier", "priority_group", "distance_to_collection_km", "access_gap_index", "needs_verification", "centroid_lat", "centroid_lon"},
        {"tambon_name"},
        {"tambon_name", "burn_pct (%)", "tillage_pct (%)"},
    ]
    for table, columns in zip(tables, required):
        missing = columns - set(table.columns)
        if missing:
            raise ValueError("CSV ขาดคอลัมน์: " + ", ".join(sorted(missing)))
    return tuple(tables)

try:
    plots, score_panel, tambon_overview = load_data()
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(str(exc))
    st.stop()

st.caption("ผลเบื้องต้น: สีแดงไม่ได้ยืนยันว่าเผา และสีเขียวไม่ได้ยืนยันว่าไถกลบ ต้องตรวจสอบหลักฐานก่อนใช้กำหนดมาตรการ")

# ============================================================
# SIDEBAR — nav + global filters
# ============================================================
with st.container(key="topbar"):
    left, right = st.columns([1, 3], vertical_alignment="center")
    left.markdown('<div class="brand">🔥 BurnWise<small>THA TAKO · FIELD INSIGHTS</small></div>',unsafe_allow_html=True)
    page = right.radio("หน้า", ["ภาพรวม", "แปลงรายพื้นที่", "แผนที่", "เกี่ยวกับโครงการ"], horizontal=True, label_visibility="collapsed")
with st.container(key="filters"):
    st.markdown("**เลือกพื้นที่และกลุ่มแปลง**")
    left, right = st.columns(2)
    tambon_options = sorted(plots["tambon_name"].dropna().unique().tolist())
    selected_tambons = left.multiselect("ตำบล", tambon_options, default=tambon_options)
    selected_tiers = right.multiselect("กลุ่มสี", TIER_ORDER, default=TIER_ORDER)

filtered = plots[
    plots["tambon_name"].isin(selected_tambons) & plots["tier"].isin(selected_tiers)
]

# ============================================================
# HELPER — KPI card renderer
# ============================================================
def kpi_card(label, value, sub=""):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PAGE: ภาพรวม (Overview)
# ============================================================
if page == "ภาพรวม":
    st.markdown("# ภาพรวมพื้นที่นำร่อง")
    st.markdown(
        f"<p class='caption-muted'>แสดงผล {len(filtered):,} แปลง จากทั้งหมด {len(plots):,} แปลง "
        f"ครอบคลุม {filtered['tambon_name'].nunique()} ตำบล</p>",
        unsafe_allow_html=True,
    )

    total_area = filtered["plot_area_rai"].sum()
    n_green = (filtered["tier"] == "เขียว").sum()
    n_urgent = (filtered["priority_group"].astype(str).str.contains("เร่งด่วน")).sum()
    n_pending = (filtered["tier"] == "ข้อมูลไม่เพียงพอ").sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("จำนวนแปลงทั้งหมด", f"{len(filtered):,}", "แปลง")
    with c2:
        kpi_card("พื้นที่รวม", f"{total_area:,.0f}", "ไร่")
    with c3:
        kpi_card("แปลงกลุ่มเขียว", f"{n_green:,}", f"{n_green/max(len(filtered),1)*100:.1f}% ของแปลงที่แสดง")
    with c4:
        kpi_card("ต้องช่วยเหลือเร่งด่วน", f"{n_urgent:,}", "ตามเกณฑ์ Priority เบื้องต้น")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.1, 1])

    with col_left:
        st.markdown("#### การกระจายตัวของ Tier")
        tier_counts = filtered["tier"].value_counts().reindex(TIER_ORDER).fillna(0).reset_index()
        tier_counts.columns = ["tier", "count"]
        fig = px.bar(
            tier_counts, x="tier", y="count", color="tier",
            color_discrete_map=TIER_COLORS, category_orders={"tier": TIER_ORDER},
        )
        fig.update_layout(
            showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_family="Noto Sans Thai", font_color="#553d34", xaxis_title=None, yaxis_title="จำนวนแปลง",
            margin=dict(t=10, b=10, l=10, r=10), height=340,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            "<p class='caption-muted'>'ข้อมูลไม่เพียงพอ' เป็นสถานะจาก notebook ต้องตรวจสอบเกณฑ์และเวอร์ชันข้อมูล "
            "แยกออกจากกลุ่มแดงโดยตั้งใจ ไม่ใช่การนับว่าเผา</p>", unsafe_allow_html=True,
        )
        

    with col_right:
        st.markdown("---")
        st.markdown("#### มาตรการที่เสนอ")
        pg_counts = filtered["priority_group"].value_counts().reset_index()
        pg_counts.columns = ["priority_group", "count"]
        fig2 = px.pie(
            pg_counts, names="priority_group", values="count", hole=0.55,
            color_discrete_sequence=[COLOR_EMBER, COLOR_GREY, COLOR_AMBER, COLOR_GREEN, "#8A9B6E"],
        )
        fig2.update_traces(textposition="inside", textinfo="percent")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_family="Noto Sans Thai", font_color="#553d34",
            margin=dict(t=10, b=10, l=10, r=10), height=340,
            legend=dict(orientation="h", yanchor="bottom", y=-0.5, font=dict(size=10)),
        )
        st.plotly_chart(fig2, use_container_width=True)
        

    st.markdown("---")
    st.markdown("#### เปรียบเทียบสัญญาณจากภาพรายตำบล")
    tov = tambon_overview[tambon_overview["tambon_name"].isin(selected_tambons)].copy()
    tov_melt = tov.melt(
        id_vars="tambon_name", value_vars=["burn_pct (%)", "tillage_pct (%)"],
        var_name="ประเภท", value_name="เปอร์เซ็นต์",
    )
    tov_melt["ประเภท"] = tov_melt["ประเภท"].map({
        "burn_pct (%)": "สัญญาณเผา", "tillage_pct (%)": "พืชพรรณลดลง ไม่เข้าเกณฑ์เผา"
    })
    fig3 = px.bar(
        tov_melt, x="tambon_name", y="เปอร์เซ็นต์", color="ประเภท", barmode="group",
        color_discrete_map={"สัญญาณเผา": COLOR_EMBER, "พืชพรรณลดลง ไม่เข้าเกณฑ์เผา": COLOR_GREEN},
    )
    fig3.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_family="Noto Sans Thai", font_color="#553d34", xaxis_title=None, yaxis_title="% ของพื้นที่เกษตร",
        margin=dict(t=10, b=10, l=10, r=10), height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig3, use_container_width=True)
    

# ============================================================
# PAGE: แปลงรายพื้นที่ (Plot-level table)
# ============================================================
elif page == "แปลงรายพื้นที่":
    st.markdown("# ข้อมูลรายแปลง")
    st.markdown(f"<p class='caption-muted'>{len(filtered):,} แปลง (กรองตามตำบลและกลุ่มสีด้านบน)</p>", unsafe_allow_html=True)

    search = st.text_input("ค้นหา plot_id", "")
    table_df = filtered.copy()
    if search:
        table_df = table_df[table_df["plot_id"].astype(str).str.contains(search, case=False, na=False, regex=False)]

    display_cols = [
        "plot_id", "tambon_name", "plot_area_rai", "burn_pct", "tillage_pct",
        "valid_observation_pct", "tier", "priority_group",
        "distance_to_collection_km", "access_gap_index", "needs_verification",
    ]
    st.dataframe(
        table_df[display_cols].sort_values("plot_area_rai", ascending=False),
        use_container_width=True, height=520,
    )

    csv_bytes = table_df[display_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇ ดาวน์โหลดตารางที่กรองแล้ว (CSV)", csv_bytes,
        file_name="burnwise_filtered_plots.csv", mime="text/csv",
    )

# ============================================================
# PAGE: แผนที่ (Map)
# ============================================================
elif page == "แผนที่":
    st.markdown("# แผนที่การกระจายตัวของแปลง")

    map_df = filtered.dropna(subset=["centroid_lat", "centroid_lon"])
    MAX_POINTS = 8000
    if len(map_df) > MAX_POINTS:
        st.info(f"แสดงตัวอย่างสุ่ม {MAX_POINTS:,} จุด จากทั้งหมด {len(map_df):,} จุด เพื่อความเร็วในการแสดงผล — กรองตำบล/Tier ให้แคบลงเพื่อดูครบทุกจุด")
        map_df = map_df.sample(MAX_POINTS, random_state=42)

    fig_map = px.scatter_mapbox(
        map_df, lat="centroid_lat", lon="centroid_lon", color="tier",
        color_discrete_map=TIER_COLORS, category_orders={"tier": TIER_ORDER},
        hover_data=["plot_id", "tambon_name", "burn_pct", "tillage_pct"],
        zoom=10.5, height=620, opacity=0.65,
    )
    fig_map.update_layout(
        mapbox_style="carto-positron",
        margin=dict(t=0, b=0, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.0),
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ============================================================
# PAGE: เกี่ยวกับโครงการ (About)
# ============================================================
else:
    st.markdown("# เกี่ยวกับ BurnWise")
    st.markdown("---")
    st.markdown("""
BurnWise วิเคราะห์สัญญาณเผาและการลดลงของพืชพรรณระดับแปลง จากภาพถ่ายดาวเทียม Sentinel-2
เพื่อจัดลำดับความเร่งด่วนในการให้เงินอุดหนุนเกษตรกรที่เข้าไม่ถึงทางเลือกแทนการเผา

**พื้นที่นำร่อง:** อำเภอท่าตะโก จังหวัดนครสวรรค์ (10 ตำบล)

**ขั้นตอนหลัก:**
1. คำนวณ dNBR เทียบภาพก่อน-หลังฤดูเก็บเกี่ยว
2. หา threshold แยกเผา/ไม่เผา จากค่าเฉลี่ย dNBR ที่จุดความร้อน FIRMS จริง
3. ตัดขอบเขตแปลงด้วย Fields of The World (FTW)
4. คำนวณ Access Gap Index จากระยะทางถึงจุดรับซื้อชีวมวลและข้อมูลเศรษฐกิจ-สังคม
    """)
    

    st.markdown("---")
    st.markdown("#### ข้อจำกัดที่ควรรู้ก่อนอ่านผล")
    st.markdown("""
- **"ข้อมูลไม่เพียงพอ"** ไม่ใช่ "ไม่เผา" — คือแปลงที่สัญญาณดาวเทียมยังไม่ชัดพอจะสรุป
- **Threshold การเผา** ปรับเทียบจากจุดความร้อน FIRMS ที่มีจำนวนจำกัดในพื้นที่นำร่อง
- **ขอบเขตแปลงจาก FTW** มาจากโมเดลทำนาย ไม่ใช่ทะเบียนที่ดินจริง
- **needs_verification** ระบุแปลงที่ควรตรวจสอบภาคสนามซ้ำก่อนใช้ตัดสินใจเชิงนโยบายจริง
    """)
    
