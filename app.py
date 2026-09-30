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
COLOR_GREEN      = "#4DD4A4"   # เขียว = ไถกลบ / ปฏิบัติดี
COLOR_GREEN_SOFT = "#E4EBDD"
COLOR_AMBER      = "#F3BB55"   # เหลือง = มีเงื่อนไข
COLOR_AMBER_SOFT = "#F6E9CF"
COLOR_EMBER      = "#F27C7C"   # แดง = สัญญาณเผา (สีไฟ ไม่ใช่สีตกแต่ง)
COLOR_EMBER_SOFT = "#F5DCCB"
COLOR_GREY       = "#9C9484"   # ข้อมูลไม่เพียงพอ
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
:root {color-scheme: dark;}
.stApp,[data-testid="stAppViewContainer"] {background:radial-gradient(circle at 90% 0%,#192f47,transparent 40%),radial-gradient(circle at 0% 60%,#242039,transparent 40%),#0d1220;color:#edf3fa;font-family:'Noto Sans Thai',sans-serif;}
.stApp h1,.stApp h2,.stApp h3,.stApp h4 {color:#f2f6ff;font-family:'Noto Sans Thai',sans-serif;}
.block-container {max-width:1320px;padding-top:2rem;padding-bottom:4rem;}
[data-testid="stSidebar"] {background:#121c2e;}
.st-key-topbar {background:#152036;border:1px solid #30425d;border-radius:24px;padding:18px 22px;margin-bottom:24px;}
.st-key-topbar button {border-radius:14px;}
.brand {font-size:25px;font-weight:700;color:#f3f7ff;line-height:1.5;}
.brand small {display:block;font-size:11px;letter-spacing:2px;color:#65d5cf;}
[class*="st-key-card_"] {background:linear-gradient(140deg,#1c2941,#151e31);border:1px solid #30425d;border-radius:24px;padding:22px;margin:10px 0 20px;}
.kpi-card {background:linear-gradient(140deg,#20314b,#172238);border:1px solid #344966;border-radius:24px;padding:24px;min-height:150px;box-shadow:0 12px 28px #00000020;}
.kpi-label {color:#b3c1d5;font-size:13px;min-height:24px;}
.kpi-value {color:#f7faff;font-size:36px;font-weight:700;font-variant-numeric:tabular-nums;margin:8px 0;}
.kpi-sub,.caption-muted {color:#a7bad0;font-size:12px;}
.stButton button,.stDownloadButton button {border-radius:14px;}
.stButton button[kind="primary"] {background:linear-gradient(110deg,#257e88,#5372bd);border:0;}
[data-testid="stWidgetLabel"] p {color:#dce6f3;}
@media(max-width:700px){.kpi-value{font-size:28px}.block-container{padding:1rem}.brand{font-size:20px}}
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
if "burnwise_page" not in st.session_state:
    st.session_state.burnwise_page = "ภาพรวม"
with st.container(key="topbar"):
    nav = st.columns([1.5, 1, 1.2, 1, 1.3])
    nav[0].markdown('<div class="brand">BurnWise<small>THA TAKO · FIELD INSIGHTS</small></div>',unsafe_allow_html=True)
    for col, label in zip(nav[1:], ["ภาพรวม", "แปลงรายพื้นที่", "แผนที่", "เกี่ยวกับโครงการ"]):
        if col.button(label, use_container_width=True, type="primary" if st.session_state.burnwise_page == label else "secondary"):
            st.session_state.burnwise_page = label
            st.rerun()
page = st.session_state.burnwise_page
with st.expander("เลือกพื้นที่และกลุ่มแปลง", expanded=True):
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
        st.markdown("---")
        st.markdown("#### การกระจายตัวของ Tier")
        tier_counts = filtered["tier"].value_counts().reindex(TIER_ORDER).fillna(0).reset_index()
        tier_counts.columns = ["tier", "count"]
        fig = px.bar(
            tier_counts, x="tier", y="count", color="tier",
            color_discrete_map=TIER_COLORS, category_orders={"tier": TIER_ORDER},
        )
        fig.update_layout(
            showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_family="Noto Sans Thai", font_color="#dce6f3", xaxis_title=None, yaxis_title="จำนวนแปลง",
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
            paper_bgcolor="rgba(0,0,0,0)", font_family="Noto Sans Thai", font_color="#dce6f3",
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
        font_family="Noto Sans Thai", font_color="#dce6f3", xaxis_title=None, yaxis_title="% ของพื้นที่เกษตร",
        margin=dict(t=10, b=10, l=10, r=10), height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig3, use_container_width=True)
    

# ============================================================
# PAGE: แปลงรายพื้นที่ (Plot-level table)
# ============================================================
elif page == "แปลงรายพื้นที่":
    st.markdown("# ข้อมูลรายแปลง")
    st.markdown(f"<p class='caption-muted'>{len(filtered):,} แปลง (กรองตามตำบล/Tier จากแถบด้านซ้าย)</p>", unsafe_allow_html=True)

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
        mapbox_style="carto-darkmatter",
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
    
