import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="BurnWise · Tha Tako Field Insights",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# DESIGN TOKENS — ตรงกับเทมเพลต BurnWise_Desktop_Overview.svg / Explore.svg
# ============================================================
BG          = "#FFF9F5"
CARD        = "#FFFFFF"
BORDER      = "#F1DED2"
TAG_BG      = "#FFF0E7"
INK         = "#422C28"
INK_MUTED   = "#7D665D"
RED         = "#B93C35"   # Burn
ORANGE      = "#E56A43"   # No Burn (ไม่เข้าเกณฑ์ตรวจพบ)
GREY_TEXT   = "#566370"   # ข้อมูลไม่เพียงพอ
GREY_BG     = "#F2F4F6"
GREY_BORDER = "#B9C2CC"

STATUS_COLORS = {"Burn": RED, "No Burn": ORANGE, "ข้อมูลไม่เพียงพอ": GREY_BORDER}
STATUS_LABELS = {"Burn": "ตรวจพบสัญญาณเผา", "No Burn": "ไม่เข้าเกณฑ์ตรวจพบ", "ข้อมูลไม่เพียงพอ": "ข้อมูลไม่เพียงพอ"}
STATUS_ORDER = ["Burn", "No Burn", "ข้อมูลไม่เพียงพอ"]

TIER_COLORS = {"Green": "#3F8B5C", "Yellow": "#D9A441", "Red": RED, "Unknown": GREY_BORDER}
TIER_ORDER = ["Green", "Yellow", "Red", "Unknown"]

PAGES = ["ภาพรวม", "สำรวจแปลง", "คุณภาพข้อมูล", "เกี่ยวกับโครงการ"]

REQUIRED_COLS = {
    "plot_id", "tambon_name", "burn_status", "burn_pct",
    "valid_observation_pct", "exclusion_reason",
}

# ============================================================
# CSS
# ============================================================
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&family=Sarabun:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {{ font-family: 'Noto Sans Thai', 'Sarabun', sans-serif; color: {INK}; }}
    .stApp {{ background-color: {BG}; }}
    #MainMenu, footer, header[data-testid="stHeader"] {{ background: transparent; }}

    h1, h2, h3 {{ color: {INK} !important; font-weight: 700 !important; }}

    .bw-nav {{
        display: flex; align-items: center; justify-content: space-between;
        background: {CARD}; border-bottom: 1px solid {BORDER};
        padding: 14px 8px; margin: -1rem -1rem 1.2rem -1rem;
    }}
    .bw-logo {{ display: flex; align-items: center; gap: 12px; }}
    .bw-logo-mark {{
        width: 38px; height: 38px; border-radius: 11px; background: {RED};
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 18px;
    }}
    .bw-logo-text {{ line-height: 1.1; }}
    .bw-logo-title {{ font-size: 20px; font-weight: 700; color: {RED}; }}
    .bw-logo-sub {{ font-size: 8px; font-weight: 600; color: {INK_MUTED}; letter-spacing: 0.08em; }}

    .bw-banner {{
        background: {TAG_BG}; border-radius: 10px; padding: 10px 16px;
        color: {RED}; font-size: 13px; font-weight: 500; margin-bottom: 1.2rem;
    }}

    .bw-card {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 18px;
        padding: 1.3rem 1.4rem; margin-bottom: 1.1rem;
    }}
    .kpi-card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 18px;
        padding: 1.1rem 1.3rem; height: 100%; border-left: 5px solid var(--accent, {RED}); }}
    .kpi-label {{ font-size: 0.82rem; color: {INK_MUTED}; font-weight: 500; margin-bottom: 0.5rem; }}
    .kpi-value {{ font-size: 2.1rem; font-weight: 700; line-height: 1.1; color: var(--accent, {RED}); }}
    .kpi-sub {{ font-size: 0.78rem; color: {INK_MUTED}; margin-top: 0.4rem; }}

    .pill {{ display: inline-block; padding: 0.2rem 0.75rem; border-radius: 999px; font-size: 0.78rem; font-weight: 500; }}
    .caption-muted {{ color: {INK_MUTED}; font-size: 0.85rem; }}

    div[role="radiogroup"] {{ gap: 6px; }}
    div[role="radiogroup"] label {{
        background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
        padding: 8px 16px !important; margin: 0 !important;
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================
# DEMO DATA — ใช้เมื่อยังไม่มี CSV จริงใน data/ (ธนาคารตัวเลขอ้างอิงจากเทมเพลต)
# ============================================================
@st.cache_data
def make_demo_data(seed=42, n=12000):
    rng = np.random.default_rng(seed)
    tambons = ["ท่าตะโก", "ดอนคา", "ทำนบ", "พนมรอก", "หนองหลวง",
               "สายลำโพง", "วังใหญ่", "พนมเศษ", "วังมหากร", "หัวถนน"]
    tambon_name = rng.choice(tambons, size=n)

    status = rng.choice(STATUS_ORDER, size=n, p=[0.23, 0.52, 0.25])
    burn_pct = np.where(
        status == "Burn", rng.uniform(10, 95, n),
        np.where(status == "No Burn", rng.uniform(0, 9.9, n), np.nan)
    )
    valid_obs = np.where(status == "ข้อมูลไม่เพียงพอ", rng.uniform(10, 79, n), rng.uniform(80, 100, n))
    exclusion_reason = np.where(
        status == "ข้อมูลไม่เพียงพอ",
        rng.choice(["ภาพใช้ได้ไม่พอ (< 80%)", "แปลงเล็กกว่า 0.1 ไร่", "ไม่มีพิกเซลเกษตรในแปลง"], size=n),
        None,
    )
    tier = np.select(
        [status == "No Burn", (status == "Burn") & (burn_pct < 50), (status == "Burn") & (burn_pct >= 50), status == "ข้อมูลไม่เพียงพอ"],
        ["Green", "Yellow", "Red", "Unknown"],
        default="Unknown",
    )
    access_gap = np.clip(rng.normal(0.55, 0.18, n), 0.02, 0.99)
    distance_km = np.clip(rng.exponential(6, n), 0.1, 28)
    needs_verification = np.where(
        (status == "Burn") & (np.abs(np.nan_to_num(burn_pct) - 10) <= 3),
        "ตรวจสอบซ้ำ: สัดส่วน Burn ใกล้เกณฑ์", None
    )

    df = pd.DataFrame({
        "plot_id": [f"DEMO-{i:05d}" for i in range(n)],
        "tambon_id": pd.factorize(tambon_name)[0] + 1,
        "tambon_name": tambon_name,
        "plot_area_rai": np.round(rng.gamma(2, 2.5, n), 2),
        "burn_pct": np.round(burn_pct, 1),
        "burn_status": status,
        "burn_tier": tier,
        "valid_observation_pct": np.round(valid_obs, 1),
        "unknown_pct": np.round(100 - valid_obs, 1),
        "exclusion_reason": exclusion_reason,
        "centroid_lat": rng.uniform(15.58, 15.84, n),
        "centroid_lon": rng.uniform(100.33, 100.60, n),
        "distance_to_collection_km": np.round(distance_km, 1),
        "access_gap_index": np.round(access_gap, 3),
        "needs_verification": needs_verification,
    })
    return df


# ============================================================
# DATA LOADING — ใช้ CSV จริงถ้ามี ไม่งั้น fallback เป็นข้อมูลตัวอย่าง
# ============================================================
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    plots_path = DATA_DIR / "burnwise_master_plots.csv"
    if plots_path.exists():
        df = pd.read_csv(plots_path)
        missing = REQUIRED_COLS - set(df.columns)
        if missing:
            raise ValueError(
                f"burnwise_master_plots.csv ขาดคอลัมน์ที่จำเป็น: {sorted(missing)} "
                f"— ต้อง export จากส่วน J ของ BurnWise_Team_Merged_with_Charts.ipynb เวอร์ชันล่าสุด"
            )
        if df["plot_id"].isna().any() or df["plot_id"].duplicated().any():
            raise ValueError("plot_id ว่างหรือซ้ำในไฟล์ CSV — ตรวจตารางหลักก่อนอัปโหลด")
        return df, False
    return make_demo_data(), True


try:
    plots, is_demo = load_data()
except ValueError as e:
    st.error(f"โหลดข้อมูลไม่สำเร็จ: {e}")
    st.stop()

# ============================================================
# TOP NAV
# ============================================================
st.markdown(f"""
<div class="bw-nav">
    <div class="bw-logo">
        <div class="bw-logo-mark">🔥</div>
        <div class="bw-logo-text">
            <div class="bw-logo-title">BurnWise</div>
            <div class="bw-logo-sub">THA TAKO · FIELD INSIGHTS</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

page = st.radio("เมนู", PAGES, horizontal=True, label_visibility="collapsed")

if is_demo:
    st.markdown(
        '<div class="bw-banner">เทมเพลตตัวอย่าง · ตัวเลข กราฟ และแผนที่เป็นข้อมูลจำลอง '
        'ยังไม่เชื่อมไฟล์ผลลัพธ์จริง — วาง burnwise_master_plots.csv ไว้ในโฟลเดอร์ data/ '
        'เพื่อแสดงผลจริง</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# HELPERS
# ============================================================
def kpi_card(label, value, sub, accent):
    st.markdown(f"""
    <div class="kpi-card" style="--accent: {accent};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def status_pill(status):
    color = {"Burn": RED, "No Burn": ORANGE, "ข้อมูลไม่เพียงพอ": GREY_TEXT}.get(status, GREY_TEXT)
    bg = TAG_BG if status != "ข้อมูลไม่เพียงพอ" else GREY_BG
    label = STATUS_LABELS.get(status, status)
    return f'<span class="pill" style="background:{bg}; color:{color};">{label}</span>'


# ============================================================
# SIDEBAR FILTERS (ใช้แทนแถบตัวกรองแนวนอนของเทมเพลต เพื่อความเร็วในการพัฒนา)
# ============================================================
with st.sidebar:
    st.markdown("### ตัวกรอง")
    tambon_opt = sorted(plots["tambon_name"].unique().tolist())
    sel_tambon = st.multiselect("ตำบล", tambon_opt, default=tambon_opt)
    sel_status = st.multiselect("สถานะ", STATUS_ORDER, default=STATUS_ORDER,
                                 format_func=lambda s: STATUS_LABELS.get(s, s))

filtered = plots[plots["tambon_name"].isin(sel_tambon) & plots["burn_status"].isin(sel_status)]

# ============================================================
# PAGE: ภาพรวม
# ============================================================
if page == "ภาพรวม":
    st.markdown("# ภาพรวมพื้นที่นำร่อง")
    st.markdown(
        f'<p class="caption-muted">อำเภอท่าตะโก · แสดง {len(filtered):,} แปลง '
        f'จากทั้งหมด {len(plots):,} แปลง</p>', unsafe_allow_html=True,
    )

    n_total = len(filtered)
    n_burn = (filtered["burn_status"] == "Burn").sum()
    n_noburn = (filtered["burn_status"] == "No Burn").sum()
    n_unknown = (filtered["burn_status"] == "ข้อมูลไม่เพียงพอ").sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("แปลงทั้งหมด", f"{n_total:,}", "แปลง", RED)
    with c2:
        kpi_card("ตรวจพบสัญญาณเผา", f"{n_burn:,}",
                  f"{n_burn/max(n_total,1)*100:.1f}% ของแปลงที่แสดง", RED)
    with c3:
        kpi_card("ไม่เข้าเกณฑ์ตรวจพบ", f"{n_noburn:,}",
                  f"{n_noburn/max(n_total,1)*100:.1f}% ของแปลงที่แสดง", ORANGE)
    with c4:
        kpi_card("ข้อมูลไม่เพียงพอ", f"{n_unknown:,}",
                  f"{n_unknown/max(n_total,1)*100:.1f}% · แยกจาก No Burn", GREY_TEXT)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        st.markdown('<div class="bw-card">', unsafe_allow_html=True)
        st.markdown("#### สถานะรายตำบล")
        st.markdown('<p class="caption-muted">จำนวนแปลงแยกตามสถานะ</p>', unsafe_allow_html=True)
        counts = (filtered.groupby(["tambon_name", "burn_status"]).size()
                  .unstack(fill_value=0).reindex(columns=STATUS_ORDER, fill_value=0))
        fig = go.Figure()
        for s in STATUS_ORDER:
            fig.add_bar(y=counts.index, x=counts[s], name=STATUS_LABELS[s],
                        orientation="h", marker_color=STATUS_COLORS[s])
        fig.update_layout(
            barmode="stack", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_family="Noto Sans Thai", margin=dict(t=10, b=10, l=10, r=10), height=360,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            '<p class="caption-muted">ข้อมูลไม่เพียงพอ แยกจาก "ไม่เข้าเกณฑ์ตรวจพบ" เสมอ '
            'ไม่ถูกนับรวมเป็น No Burn</p>', unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="bw-card">', unsafe_allow_html=True)
        st.markdown("#### Access Gap vs สัดส่วนเผา")
        scatter_df = filtered.dropna(subset=["access_gap_index", "burn_pct"])
        fig2 = px.scatter(
            scatter_df, x="access_gap_index", y="burn_pct", color="burn_status",
            color_discrete_map=STATUS_COLORS, opacity=0.55,
            labels={"access_gap_index": "Access Gap (0–1)", "burn_pct": "สัดส่วนเผา (%)"},
        )
        fig2.add_vline(x=0.6, line_dash="dash", line_color=ORANGE)
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_family="Noto Sans Thai", margin=dict(t=10, b=10, l=10, r=10), height=360,
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="bw-card">', unsafe_allow_html=True)
    st.markdown("#### แปลงที่ควรตรวจสอบเพิ่มเติม")
    st.markdown('<p class="caption-muted">แยกเหตุผลก่อนเสนอการช่วยเหลือ</p>', unsafe_allow_html=True)
    review_df = filtered[
        filtered["needs_verification"].notna() | filtered["exclusion_reason"].notna()
    ].copy()
    if review_df.empty:
        st.info("ไม่มีแปลงที่ต้องตรวจสอบเพิ่มเติมในตัวกรองปัจจุบัน")
    else:
        show_cols = ["plot_id", "tambon_name", "burn_status", "burn_pct", "valid_observation_pct"]
        st.dataframe(review_df[show_cols].head(50), use_container_width=True, height=280)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<p class="caption-muted">No Burn = ไม่เข้าเกณฑ์ตรวจพบ ไม่ได้ยืนยันว่าไม่เผาหรือไถกลบ</p>',
        unsafe_allow_html=True,
    )

# ============================================================
# PAGE: สำรวจแปลง
# ============================================================
elif page == "สำรวจแปลง":
    st.markdown("# สำรวจแปลงและการเข้าถึง")
    st.markdown(
        '<p class="caption-muted">ค้นหาแปลง ดูหลักฐาน และแยกพื้นที่รอตรวจสอบก่อนเสนอมาตรการ</p>',
        unsafe_allow_html=True,
    )

    search = st.text_input("ค้นหารหัสแปลง / ชื่อตำบล", "")
    explore_df = filtered.copy()
    if search:
        mask = (explore_df["plot_id"].astype(str).str.contains(search, case=False, na=False) |
                explore_df["tambon_name"].astype(str).str.contains(search, case=False, na=False))
        explore_df = explore_df[mask]

    col_map, col_detail = st.columns([1.6, 1])

    with col_map:
        st.markdown('<div class="bw-card">', unsafe_allow_html=True)
        st.markdown("#### แผนที่แปลง")
        map_df = explore_df.dropna(subset=["centroid_lat", "centroid_lon"])
        MAX_PTS = 6000
        if len(map_df) > MAX_PTS:
            st.caption(f"แสดงตัวอย่างสุ่ม {MAX_PTS:,} จุด จาก {len(map_df):,} จุด")
            map_df = map_df.sample(MAX_PTS, random_state=42)
        fig_map = px.scatter_mapbox(
            map_df, lat="centroid_lat", lon="centroid_lon", color="burn_status",
            color_discrete_map=STATUS_COLORS,
            hover_data=["plot_id", "tambon_name", "burn_pct"],
            zoom=10.3, height=520, opacity=0.65,
        )
        fig_map.update_layout(
            mapbox_style="carto-positron", margin=dict(t=0, b=0, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.0),
        )
        st.plotly_chart(fig_map, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_detail:
        st.markdown('<div class="bw-card">', unsafe_allow_html=True)
        st.markdown("#### รายละเอียดแปลง")
        if len(explore_df) > 0:
            pick = st.selectbox("เลือกแปลง", explore_df["plot_id"].head(500).tolist())
            row = explore_df[explore_df["plot_id"] == pick].iloc[0]
            st.markdown(status_pill(row["burn_status"]), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.metric("สัดส่วนสัญญาณเผาในพื้นที่ที่ประเมินได้", f"{row.get('burn_pct', float('nan')):.1f}%"
                       if pd.notna(row.get("burn_pct")) else "—")
            st.metric("ภาพใช้ได้ครอบคลุม", f"{row.get('valid_observation_pct', float('nan')):.1f}%")
            if pd.notna(row.get("access_gap_index")):
                st.metric("Access Gap", f"{row['access_gap_index']:.2f} / 1.00")
            if pd.notna(row.get("distance_to_collection_km")):
                st.metric("ระยะทางตามกราฟถนน", f"{row['distance_to_collection_km']:.1f} กม.")
            if pd.notna(row.get("exclusion_reason")):
                st.markdown(
                    f'<div class="bw-banner" style="margin-top:0.6rem;">เหตุผลข้อมูลไม่พอ: {row["exclusion_reason"]}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("ไม่พบแปลงตามคำค้นหา")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="bw-card">', unsafe_allow_html=True)
    st.markdown("#### รายการแปลง")
    st.markdown('<p class="caption-muted">ข้อมูลไม่พอจะไม่ถูกจัดเป็นไม่เผา</p>', unsafe_allow_html=True)
    show_cols = ["plot_id", "tambon_name", "burn_status", "burn_pct", "valid_observation_pct"]
    st.dataframe(explore_df[show_cols], use_container_width=True, height=380)
    csv_bytes = explore_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇ ดาวน์โหลดตารางที่กรองแล้ว (CSV)", csv_bytes,
                        file_name="burnwise_filtered_plots.csv", mime="text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="bw-banner">ก่อนใช้งานจริง: ยืนยันจุดรับซื้อและตรวจแปลงที่ภาพไม่พอ/ข้อมูลขัดกัน</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# PAGE: คุณภาพข้อมูล
# ============================================================
elif page == "คุณภาพข้อมูล":
    st.markdown("# คุณภาพข้อมูล")
    st.markdown(
        '<p class="caption-muted">สัดส่วนภาพใช้ได้ และเหตุผลที่แปลงถูกจัดเป็นข้อมูลไม่เพียงพอ '
        'ก่อนเชื่อผลใดๆ ควรตรวจหน้านี้ก่อน</p>', unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="bw-card">', unsafe_allow_html=True)
        st.markdown("#### การกระจายตัวของ Coverage (valid_observation_pct)")
        fig = px.histogram(filtered, x="valid_observation_pct", nbins=40,
                            color_discrete_sequence=[RED])
        fig.add_vline(x=80, line_dash="dash", line_color=ORANGE,
                      annotation_text="เกณฑ์ขั้นต่ำ 80%")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           font_family="Noto Sans Thai", margin=dict(t=10, b=10, l=10, r=10), height=340,
                           xaxis_title="% ภาพใช้ได้", yaxis_title="จำนวนแปลง")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="bw-card">', unsafe_allow_html=True)
        st.markdown("#### เหตุผลที่ถูกจัดเป็นข้อมูลไม่เพียงพอ")
        reasons = filtered["exclusion_reason"].dropna().value_counts().reset_index()
        reasons.columns = ["เหตุผล", "จำนวนแปลง"]
        if reasons.empty:
            st.info("ไม่มีแปลงที่ถูกติดเหตุผลในตัวกรองปัจจุบัน")
        else:
            fig2 = px.bar(reasons, x="จำนวนแปลง", y="เหตุผล", orientation="h",
                          color_discrete_sequence=[GREY_BORDER])
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               font_family="Noto Sans Thai", margin=dict(t=10, b=10, l=10, r=10), height=340)
            st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="bw-card">', unsafe_allow_html=True)
    st.markdown("#### การกระจายตัวของ Tier")
    tier_counts = filtered["burn_tier"].value_counts().reindex(TIER_ORDER).fillna(0).reset_index()
    tier_counts.columns = ["tier", "count"]
    fig3 = px.bar(tier_counts, x="tier", y="count", color="tier",
                  color_discrete_map=TIER_COLORS, category_orders={"tier": TIER_ORDER})
    fig3.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        font_family="Noto Sans Thai", margin=dict(t=10, b=10, l=10, r=10), height=320,
                        xaxis_title=None, yaxis_title="จำนวนแปลง")
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: เกี่ยวกับโครงการ
# ============================================================
else:
    st.markdown("# เกี่ยวกับ BurnWise")
    st.markdown('<div class="bw-card">', unsafe_allow_html=True)
    st.markdown("""
BurnWise ตรวจสัญญาณการเผาตอซังข้าวระดับแปลง จากภาพถ่ายดาวเทียม Sentinel-2
เพื่อสนับสนุนการจัดลำดับความช่วยเหลือเกษตรกรในอำเภอท่าตะโก จังหวัดนครสวรรค์

**ขั้นตอนหลัก:** คำนวณ dNBR เทียบภาพก่อน–หลังฤดูเก็บเกี่ยว → หา threshold จากค่าเฉลี่ย dNBR
ที่จุดความร้อน VIIRS/FIRMS → ตัดขอบเขตแปลงด้วย Fields of The World (FTW) →
คำนวณ Access Gap จากระยะทางถนนและรายได้ตำบล (จปฐ.)
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="bw-card">', unsafe_allow_html=True)
    st.markdown("#### นิยามที่ต้องเข้าใจก่อนอ่านผล")
    st.markdown("""
- **No Burn** = ไม่เข้าเกณฑ์ตรวจพบในข้อมูลที่ใช้ **ไม่ได้ยืนยัน**ว่าไม่เคยเผา และไม่ได้ยืนยันว่าไถกลบ
- **ข้อมูลไม่เพียงพอ** แยกออกจาก No Burn เสมอ — คือแปลงที่ภาพใช้ได้ไม่ถึง 80% ของพื้นที่เกษตร
- **burn_pct** คือสัดส่วนของ "พื้นที่ภาพใช้ได้" ไม่ใช่สัดส่วนของพื้นที่ทั้งแปลง
- **Green** = กลุ่มสัญญาณเผาต่ำตามสูตรนี้ ไม่ใช่การรับรองพฤติกรรมดีของเจ้าของแปลง
- ผลที่แสดงยังไม่ใช่ผลยืนยันการเผาจริง อยู่ระหว่างตรวจกับชุดอ้างอิงอิสระ
    """)
    st.markdown('</div>', unsafe_allow_html=True)
