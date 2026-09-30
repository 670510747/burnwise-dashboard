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
COLOR_GREEN      = "#2F5233"   # เขียว = ไถกลบ / ปฏิบัติดี
COLOR_GREEN_SOFT = "#E4EBDD"
COLOR_AMBER      = "#C98A1A"   # เหลือง = มีเงื่อนไข
COLOR_AMBER_SOFT = "#F6E9CF"
COLOR_EMBER      = "#C1440E"   # แดง = สัญญาณเผา (สีไฟ ไม่ใช่สีตกแต่ง)
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
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: {COLOR_INK};
    }}
    .stApp {{
        background-color: {COLOR_CREAM};
    }}
    h1, h2, h3, .display-font {{
        font-family: 'Fraunces', serif !important;
        color: {COLOR_INK} !important;
        font-weight: 600 !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {COLOR_GREEN};
        border-right: 1px solid #23401F;
    }}
    section[data-testid="stSidebar"] * {{
        color: #F5F1E6 !important;
    }}
    section[data-testid="stSidebar"] .stRadio label {{
        font-size: 0.95rem;
    }}
    div[data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    .kpi-card {{
        background: {COLOR_CARD};
        border: 1px solid #E9E1CE;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 2px 10px rgba(43, 42, 37, 0.06);
        height: 100%;
    }}
    .kpi-label {{
        font-size: 0.82rem;
        color: {COLOR_INK_SOFT};
        margin-bottom: 0.3rem;
        font-weight: 500;
    }}
    .kpi-value {{
        font-family: 'Fraunces', serif;
        font-size: 2rem;
        font-weight: 600;
        line-height: 1.1;
    }}
    .kpi-sub {{
        font-size: 0.78rem;
        color: {COLOR_INK_SOFT};
        margin-top: 0.3rem;
    }}
    .section-card {{
        background: {COLOR_CARD};
        border: 1px solid #E9E1CE;
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        box-shadow: 0 2px 10px rgba(43, 42, 37, 0.06);
        margin-bottom: 1.2rem;
    }}
    .tag {{
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
    }}
    .caption-muted {{
        color: {COLOR_INK_SOFT};
        font-size: 0.85rem;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA LOADING
# ============================================================
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    plots = pd.read_csv(DATA_DIR / "burnwise_master_plots.csv")
    score_panel = pd.read_csv(DATA_DIR / "burnwise_score_panel.csv")
    tambon_overview = pd.read_csv(DATA_DIR / "burnwise_tambon_overview.csv")
    return plots, score_panel, tambon_overview

plots, score_panel, tambon_overview = load_data()

# ============================================================
# SIDEBAR — nav + global filters
# ============================================================
with st.sidebar:
    st.markdown("## 🔥 BurnWise")
    st.markdown(
        "<div style='opacity:0.85; font-size:0.85rem; margin-top:-0.6rem;'>"
        "อำเภอท่าตะโก จังหวัดนครสวรรค์</div>", unsafe_allow_html=True
    )
    st.markdown("---")

    page = st.radio(
        "เมนู",
        ["ภาพรวม", "แปลงรายพื้นที่", "แผนที่", "เกี่ยวกับโครงการ"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**ตัวกรอง**")
    tambon_options = sorted(plots["tambon_name"].unique().tolist())
    selected_tambons = st.multiselect(
        "ตำบล", tambon_options, default=tambon_options
    )
    tier_options = TIER_ORDER
    selected_tiers = st.multiselect(
        "Tier", tier_options, default=tier_options
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem; opacity:0.75;'>"
        "ข้อมูลจากภาพถ่ายดาวเทียม Sentinel-2 · GeoHackathon 2026"
        "</div>", unsafe_allow_html=True
    )

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
        kpi_card("แปลงปฏิบัติดี (เขียว)", f"{n_green:,}", f"{n_green/max(len(filtered),1)*100:.1f}% ของแปลงที่แสดง")
    with c4:
        kpi_card("ต้องช่วยเหลือเร่งด่วน", f"{n_urgent:,}", "เผา + เข้าถึงยาก")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.1, 1])

    with col_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### การกระจายตัวของ Tier")
        tier_counts = filtered["tier"].value_counts().reindex(TIER_ORDER).fillna(0).reset_index()
        tier_counts.columns = ["tier", "count"]
        fig = px.bar(
            tier_counts, x="tier", y="count", color="tier",
            color_discrete_map=TIER_COLORS, category_orders={"tier": TIER_ORDER},
        )
        fig.update_layout(
            showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_family="Inter", xaxis_title=None, yaxis_title="จำนวนแปลง",
            margin=dict(t=10, b=10, l=10, r=10), height=340,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            "<p class='caption-muted'>'ข้อมูลไม่เพียงพอ' คือแปลงที่สัญญาณเผา+ไถกลบรวมกันต่ำเกินกว่าจะสรุปได้ "
            "แยกออกจากกลุ่มแดงโดยตั้งใจ ไม่ใช่การนับว่าเผา</p>", unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### มาตรการที่เสนอ")
        pg_counts = filtered["priority_group"].value_counts().reset_index()
        pg_counts.columns = ["priority_group", "count"]
        fig2 = px.pie(
            pg_counts, names="priority_group", values="count", hole=0.55,
            color_discrete_sequence=[COLOR_EMBER, COLOR_GREY, COLOR_AMBER, COLOR_GREEN, "#8A9B6E"],
        )
        fig2.update_traces(textposition="inside", textinfo="percent")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_family="Inter",
            margin=dict(t=10, b=10, l=10, r=10), height=340,
            legend=dict(orientation="h", yanchor="bottom", y=-0.5, font=dict(size=10)),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### เปรียบเทียบสัดส่วนเผา / ไถกลบ รายตำบล")
    tov = tambon_overview[tambon_overview["tambon_name"].isin(selected_tambons)].copy()
    tov_melt = tov.melt(
        id_vars="tambon_name", value_vars=["burn_pct (%)", "tillage_pct (%)"],
        var_name="ประเภท", value_name="เปอร์เซ็นต์",
    )
    tov_melt["ประเภท"] = tov_melt["ประเภท"].map({
        "burn_pct (%)": "เผา", "tillage_pct (%)": "ไถกลบ"
    })
    fig3 = px.bar(
        tov_melt, x="tambon_name", y="เปอร์เซ็นต์", color="ประเภท", barmode="group",
        color_discrete_map={"เผา": COLOR_EMBER, "ไถกลบ": COLOR_GREEN},
    )
    fig3.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_family="Inter", xaxis_title=None, yaxis_title="% ของพื้นที่เกษตร",
        margin=dict(t=10, b=10, l=10, r=10), height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: แปลงรายพื้นที่ (Plot-level table)
# ============================================================
elif page == "แปลงรายพื้นที่":
    st.markdown("# ข้อมูลรายแปลง")
    st.markdown(f"<p class='caption-muted'>{len(filtered):,} แปลง (กรองตามตำบล/Tier จากแถบด้านซ้าย)</p>", unsafe_allow_html=True)

    search = st.text_input("ค้นหา plot_id", "")
    table_df = filtered.copy()
    if search:
        table_df = table_df[table_df["plot_id"].astype(str).str.contains(search, case=False, na=False)]

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
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("""
BurnWise ตรวจจับพฤติกรรมการเผา-ไถกลบตอซังข้าวระดับแปลง จากภาพถ่ายดาวเทียม Sentinel-2
เพื่อจัดลำดับความเร่งด่วนในการให้เงินอุดหนุนเกษตรกรที่เข้าไม่ถึงทางเลือกแทนการเผา

**พื้นที่นำร่อง:** อำเภอท่าตะโก จังหวัดนครสวรรค์ (10 ตำบล)

**ขั้นตอนหลัก:**
1. คำนวณ dNBR เทียบภาพก่อน-หลังฤดูเก็บเกี่ยว
2. หา threshold แยกเผา/ไม่เผา จากค่าเฉลี่ย dNBR ที่จุดความร้อน FIRMS จริง
3. ตัดขอบเขตแปลงด้วย Fields of The World (FTW)
4. คำนวณ Access Gap Index จากระยะทางถึงจุดรับซื้อชีวมวลและข้อมูลเศรษฐกิจ-สังคม
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### ข้อจำกัดที่ควรรู้ก่อนอ่านผล")
    st.markdown("""
- **"ข้อมูลไม่เพียงพอ"** ไม่ใช่ "ไม่เผา" — คือแปลงที่สัญญาณดาวเทียมยังไม่ชัดพอจะสรุป
- **Threshold การเผา** ปรับเทียบจากจุดความร้อน FIRMS ที่มีจำนวนจำกัดในพื้นที่นำร่อง
- **ขอบเขตแปลงจาก FTW** มาจากโมเดลทำนาย ไม่ใช่ทะเบียนที่ดินจริง
- **needs_verification** ระบุแปลงที่ควรตรวจสอบภาคสนามซ้ำก่อนใช้ตัดสินใจเชิงนโยบายจริง
    """)
    st.markdown('</div>', unsafe_allow_html=True)
