"""BurnWise dashboard: CSV display only; no Earth Engine credentials required.

Soft UI theme: palette #FCF7F8 / #CED3DC / #A31621 (brand) / #4E8098 / #90C2E7.
Brand red is decoration (logo, menu, buttons, key numbers). Data status colours
(red / green / amber) are separate and always come with an icon + text label.
"""
from pathlib import Path
from html import escape
import io
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="BurnWise · ท่าตะโก", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")
BASE = Path(__file__).resolve().parent

# ── Brand palette (decoration) ───────────────────────────────────────────────
BG, LINE, BRAND, SEC, SKY = "#FCF7F8", "#CED3DC", "#A31621", "#4E8098", "#90C2E7"
INK, MUTED = "#26303B", "#5B6675"
# ── Data-status colours: burn signal uses the brand red; meaning is always carried by icon + text ──
S_RED, S_GREEN, S_AMBER, S_GREY = BRAND, "#4B8F6D", "#D8A94A", "#9AA5B4"
FONT_PLOT = "Noto Sans Thai, Sarabun, sans-serif"

STATUS = {"Burn": "ตรวจพบสัญญาณเผา", "No Burn": "ไม่เข้าเกณฑ์ตรวจพบ", "Unknown": "ข้อมูลไม่เพียงพอ"}
STATUS_ICON = {"ตรวจพบสัญญาณเผา": "▲", "ไม่เข้าเกณฑ์ตรวจพบ": "✓", "ข้อมูลไม่เพียงพอ": "?",
               "Tier เขียว (เดิม)": "✓", "Tier เหลือง (เดิม)": "!", "Tier แดง (เดิม)": "▲"}
PAGES = ["ภาพรวม", "สำรวจแปลง", "คุณภาพข้อมูล", "เกี่ยวกับโครงการ"]
PAGE_ICON = {"ภาพรวม": "space_dashboard", "สำรวจแปลง": "map", "คุณภาพข้อมูล": "fact_check", "เกี่ยวกับโครงการ": "info"}

CSS = '''<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&family=Sarabun:wght@400;500;600;700&display=swap');
:root{color-scheme:light;--bg:#FCF7F8;--line:#CED3DC;--brand:#A31621;--brand-d:#85101A;--sec:#4E8098;--sky:#90C2E7;--ink:#26303B;--muted:#5B6675;
--raise:4px 5px 12px rgba(120,132,150,.20),-4px -4px 10px rgba(255,255,255,.92);
--raise-s:3px 3px 8px rgba(120,132,150,.17),-3px -3px 7px rgba(255,255,255,.92);
--inset:inset 2px 2px 5px rgba(120,132,150,.18),inset -2px -2px 5px rgba(255,255,255,.92);}
/* fonts: text elements only, so Material icon fonts keep working */
.stApp,.stApp p,.stApp label,.stApp li,.stApp td,.stApp th,.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp button,.stApp input,.stApp textarea,.stApp [data-baseweb]{font-family:'Noto Sans Thai','Sarabun',sans-serif;}
.stApp{background:linear-gradient(160deg,#DDE1E8 0%,#CED3DC 55%,#C5CBD6 100%);color:var(--ink);line-height:1.55;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{overflow-x:hidden;}
[data-testid="stElementContainer"]:has(style),.element-container:has(style){display:none;}
[data-testid="stHeader"]{background:transparent;}
/* ── floating main panel ── */
.block-container,[data-testid="stMainBlockContainer"]{max-width:1380px!important;width:calc(100% - 32px);margin:56px auto 32px!important;padding:24px 26px 26px!important;
background:linear-gradient(145deg,#F7F2F4,#EFE9EC);border:2px solid rgba(255,255,255,.95);border-radius:32px;
box-shadow:0 14px 30px -18px rgba(78,128,152,.38),0 3px 8px rgba(90,100,120,.08);}
/* ── floating sidebar ── */
[data-testid="stSidebar"]{background:transparent!important;border:0!important;padding:56px 0 16px 16px;box-sizing:border-box;}
[data-testid="stSidebarContent"]{background:linear-gradient(145deg,#FCF7F8,#F5EFF2);border:2px solid rgba(255,255,255,.95);border-radius:28px;box-shadow:3px 5px 14px rgba(120,132,150,.16);height:100%;}
[data-testid="stSidebarHeader"]{height:auto!important;min-height:0!important;padding:10px 14px 0!important;margin:0!important;}
[data-testid="stSidebarUserContent"]{padding:2px 18px 22px!important;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.65rem;}
.side-title{font-size:15px;font-weight:700;color:var(--ink);margin:0 0 2px;display:flex;align-items:center;gap:8px;line-height:1.4;}
.side-title::before{content:"";width:4px;height:16px;border-radius:4px;background:var(--brand);flex:none;}
.side-sep{height:1px;background:var(--line);margin:6px 0 4px;}
[data-testid="stSidebar"] label p{font-size:13px;color:var(--muted);font-weight:600;line-height:1.45;overflow-wrap:anywhere;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{line-height:1.5;}
/* ── cards (plain keyed containers; no thin default border) ── */
[class*="st-key-card-"]{background:var(--bg);border:1px solid rgba(206,211,220,.55);border-radius:26px;padding:22px 24px;box-shadow:var(--raise);box-sizing:border-box;min-width:0;}
[data-testid="stHorizontalBlock"]{align-items:stretch!important;gap:18px!important;}
[data-testid="stColumn"]{min-width:0;}
[data-testid="stColumn"]>[data-testid="stVerticalBlock"]{flex:1 1 auto;}
[data-testid="stColumn"]>[data-testid="stVerticalBlock"]>*:only-child{flex:1 1 auto;display:flex;flex-direction:column;}
[data-testid="stColumn"]>[data-testid="stVerticalBlock"]>*:only-child>[class*="st-key-card-"],
[data-testid="stColumn"]>[data-testid="stVerticalBlock"]>[class*="st-key-card-"]:only-child{flex:1 1 auto;}
/* ── top bar: one row on desktop, deliberate 2-row / stacked layouts when narrow (container queries) ── */
.st-key-topbar{container-type:inline-size;background:var(--bg);border:1px solid rgba(206,211,220,.6);border-radius:26px;padding:8px 14px;box-shadow:var(--raise);}
.st-key-topbar [data-testid="stHorizontalBlock"]{flex-wrap:wrap;align-items:center!important;gap:8px 14px!important;}
.st-key-topbar [data-testid="stColumn"]{flex:0 0 auto!important;width:auto!important;min-width:0!important;}
.st-key-topbar [data-testid="stColumn"]:nth-child(1){flex:1 1 0!important;min-width:max-content!important;order:1;}
.st-key-topbar [data-testid="stColumn"]:nth-child(2){flex:0 1 auto!important;max-width:100%;order:2;}
.st-key-topbar [data-testid="stColumn"]:nth-child(3){flex:1 1 0!important;min-width:max-content!important;order:3;}
.st-key-topbar [data-testid="stColumn"]:nth-child(3)>[data-testid="stVerticalBlock"]{align-items:flex-end;}
.st-key-topbar [data-testid="stDownloadButton"]{width:auto;}
.brand{display:flex;align-items:center;gap:10px;white-space:nowrap;}
.brand .logo{width:40px;height:40px;border-radius:14px;flex:none;background:var(--brand) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z'/%3E%3C/svg%3E") center/22px no-repeat;box-shadow:0 3px 8px rgba(163,22,33,.25),inset 0 1px 0 rgba(255,255,255,.25);}
.brand .b-name{font-size:20px;font-weight:700;color:var(--brand);line-height:1.15;display:flex;align-items:center;gap:8px;}
.brand .b-sub{font-size:12px;color:var(--muted);margin-top:1px;}
.demo-badge{font-size:11.5px;font-weight:700;color:#2B2100;background:#D8A94A;border-radius:999px;padding:1px 9px;line-height:1.5;}
/* capsule menu: each item is its own capsule, radio circle removed */
.st-key-topbar [data-testid="stRadio"] [role="radiogroup"]{background:none;box-shadow:none;padding:5px 3px;gap:6px;flex-wrap:nowrap;width:fit-content;max-width:100%;overflow-x:auto;scrollbar-width:none;}
.st-key-topbar [data-testid="stRadio"] [role="radiogroup"]::-webkit-scrollbar{display:none;}
.st-key-topbar [data-testid="stRadio"] label>*:not(input):not(:has([data-testid="stMarkdownContainer"])):not([data-testid="stMarkdownContainer"]){display:none!important;}
.st-key-topbar [data-testid="stRadio"] label{margin:0!important;padding:7px 14px;border-radius:999px;background:var(--bg);border:1px solid rgba(206,211,220,.85);box-shadow:var(--raise-s);cursor:pointer;white-space:nowrap;display:flex;align-items:center;gap:6px;flex:none;transition:background .15s;}
.st-key-topbar [data-testid="stRadio"] label p{font-size:14px;font-weight:600;color:var(--ink);margin:0;white-space:nowrap;line-height:1.4;}
.st-key-topbar [data-testid="stRadio"] label:hover{background:#F2ECEF;}
.st-key-topbar [data-testid="stRadio"] label:has(input:checked){background:var(--brand);border-color:var(--brand);box-shadow:0 3px 8px rgba(163,22,33,.24);}
.st-key-topbar [data-testid="stRadio"] label:has(input:checked) *{color:#fff!important;}
.st-key-topbar [data-testid="stRadio"] label:has(input:focus-visible){outline:3px solid rgba(144,194,231,.95);outline-offset:2px;}
@container (max-width:900px){.brand .b-sub{display:none;}}
@container (max-width:800px){
.st-key-topbar [data-testid="stColumn"]:nth-child(2){flex:1 0 100%!important;order:4;}
.st-key-topbar [data-testid="stColumn"]:nth-child(2) [role="radiogroup"]{width:100%;}}
@container (max-width:520px){
.st-key-topbar [data-testid="stColumn"]:nth-child(1),.st-key-topbar [data-testid="stColumn"]:nth-child(3){flex:1 0 100%!important;}
.st-key-topbar [data-testid="stColumn"]:nth-child(2){order:2;}
.st-key-topbar [data-testid="stColumn"]:nth-child(3){order:3;}
.st-key-topbar [data-testid="stColumn"]:nth-child(3)>[data-testid="stVerticalBlock"]{align-items:flex-start;}}
/* ── typography ── */
.h-page{font-size:1.5rem;font-weight:700;color:var(--ink);line-height:1.3;display:flex;align-items:center;gap:12px;margin:6px 2px 0;}
.h-page::before{content:"";width:6px;height:26px;border-radius:6px;background:var(--brand);flex:none;}
.h-page+.desc{margin:2px 2px 0 18px;}
.h-card{font-size:1.08rem;font-weight:650;color:var(--ink);line-height:1.35;}
.h-card.first{margin-top:0;}
.desc{font-size:14px;color:var(--muted);margin-top:4px;}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--muted)!important;font-size:13px;}
a{color:var(--brand);}
/* ── metric cards: left-aligned, equal height ── */
.metric{background:var(--bg);border:1px solid rgba(206,211,220,.55);border-radius:24px;padding:18px 20px;min-height:128px;box-shadow:var(--raise);display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-start;gap:6px;box-sizing:border-box;text-align:left;}
.metric .m-top{min-height:28px;display:flex;align-items:center;}
.metric .m-label{font-size:13.5px;color:var(--muted);font-weight:600;line-height:1.3;}
.metric .m-value{font-size:34px;font-weight:700;line-height:1.1;color:var(--ink);}
.metric.key .m-value{color:var(--brand);}
.metric .m-note{font-size:12.5px;color:var(--muted);line-height:1.4;}
.pill{display:inline-flex;align-items:center;gap:7px;padding:3px 12px 3px 4px;border-radius:999px;background:#EFEAEC;background:color-mix(in srgb,var(--c) 14%,#FCF7F8);border:1px solid color-mix(in srgb,var(--c) 32%,#FCF7F8);color:var(--ink);font-size:12.5px;font-weight:600;line-height:1.3;}
.pill i{width:19px;height:19px;border-radius:50%;background:var(--c);color:var(--fg,#fff);font-style:normal;font-size:11px;font-weight:700;display:inline-grid;place-items:center;flex:none;}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0;align-items:center;}
.chip{background:rgba(144,194,231,.38);color:#1F3A4D;border-radius:999px;padding:4px 14px;font-size:13px;font-weight:500;}
.strip{display:flex;gap:10px;align-items:flex-start;background:rgba(144,194,231,.26);border:1px solid rgba(144,194,231,.75);border-radius:20px;padding:11px 18px;color:var(--ink);font-size:14px;}
.strip .ico{width:20px;height:20px;border-radius:50%;background:var(--sec);color:#fff;font-size:12px;font-weight:700;display:inline-grid;place-items:center;flex:none;margin-top:2px;}
.legend-note{font-size:12.5px;color:var(--muted);line-height:1.5;}
.legend-stack{display:flex;flex-direction:column;gap:7px;align-items:flex-start;}
.steps{margin:0;padding-left:1.2rem;color:var(--ink);line-height:1.8;}
.footer{text-align:center;color:var(--muted);font-size:12.5px;padding:4px 0 0;}
/* ── widgets ── */
.stButton button,.stDownloadButton button,[data-testid="stBaseButton-secondary"],[data-testid="stBaseButton-primary"]{border-radius:999px!important;padding:.4rem 1.1rem;font-weight:600;transition:background .15s;max-width:100%;}
.stButton button[kind="secondary"],.stDownloadButton button[kind="secondary"],[data-testid="stBaseButton-secondary"]{background:var(--bg);border:1px solid var(--line);color:var(--ink);box-shadow:var(--raise-s);}
.stButton button[kind="primary"],.stDownloadButton button[kind="primary"],[data-testid="stBaseButton-primary"]{background:var(--brand)!important;border:1px solid var(--brand)!important;color:#fff!important;box-shadow:0 3px 8px rgba(163,22,33,.22);}
.stButton button[kind="primary"] *,.stDownloadButton button[kind="primary"] *,[data-testid="stBaseButton-primary"] *{color:#fff!important;}
.stButton button[kind="primary"]:hover,.stDownloadButton button[kind="primary"]:hover,[data-testid="stBaseButton-primary"]:hover{background:var(--brand-d)!important;border-color:var(--brand-d)!important;}
button:focus-visible{outline:3px solid rgba(144,194,231,.95)!important;outline-offset:2px;}
[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{background:var(--bg)!important;border-radius:16px!important;border-color:var(--line)!important;}
[data-baseweb="input"],[data-baseweb="select"]>div{box-shadow:var(--inset);}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]>div:focus-within{border-color:var(--brand)!important;box-shadow:0 0 0 3px rgba(163,22,33,.12)!important;}
[data-testid="stMultiSelect"] [data-baseweb="select"]>div{max-height:none!important;overflow:visible!important;}
[data-testid="stMultiSelect"] [data-baseweb="select"]>div>div{max-height:none!important;overflow:visible!important;flex-wrap:wrap;gap:4px;}
[data-baseweb="tag"]{background:rgba(144,194,231,.45)!important;color:#1F3A4D!important;border-radius:999px!important;max-width:100%!important;height:auto!important;margin:0!important;padding:1px 4px 1px 10px!important;}
[data-baseweb="tag"] span{max-width:none!important;overflow:visible!important;text-overflow:clip!important;white-space:normal!important;color:#1F3A4D!important;font-size:12.5px!important;font-weight:500;}
[data-baseweb="tag"] svg{fill:#1F3A4D!important;}
[data-testid="stFileUploader"] section,[data-testid="stFileUploaderDropzone"]{background:var(--bg);border:1.5px dashed var(--line);border-radius:18px;max-width:100%;box-sizing:border-box;}
[data-testid="stFileUploaderDropzone"] button{max-width:100%;}
[data-testid="stFileUploaderDropzoneInstructions"],[data-testid="stFileUploaderDropzoneInstructions"] *{font-size:12px;overflow-wrap:anywhere;}
[data-testid="stSidebar"] [data-testid="stToggle"] label,[data-testid="stSidebar"] [data-testid="stCheckbox"] label{max-width:100%;}
[data-testid="stAlert"]{border-radius:20px!important;border:1px solid var(--line)!important;}
[data-testid="stDataFrame"]{border-radius:18px;overflow:hidden;border:1px solid var(--line);}
[data-testid="stPlotlyChart"]{border-radius:18px;overflow:hidden;background:transparent;}
[data-testid="stPlotlyChart"] .main-svg,[data-testid="stPlotlyChart"] .js-plotly-plot,[data-testid="stPlotlyChart"] .plot-container{background:transparent!important;}
/* ── responsive ── */
@media(max-width:1100px){.block-container,[data-testid="stMainBlockContainer"]{padding:20px 18px 22px!important;border-radius:28px;}
[class*="st-key-card-"]{padding:20px;}
.metric .m-value{font-size:30px;}}
@media(max-width:800px){.block-container,[data-testid="stMainBlockContainer"]{width:calc(100% - 16px);margin:52px auto 20px!important;padding:14px 12px 18px!important;border-radius:24px;}
[data-testid="stSidebar"]{padding:12px;}
.st-key-topbar{padding:8px 10px;border-radius:22px;}
[data-testid="stHorizontalBlock"]{gap:14px!important;}
[class*="st-key-card-"]{padding:16px;border-radius:22px;}
.h-page{font-size:1.3rem;}.metric{min-height:112px;padding:15px;}.metric .m-value{font-size:28px;}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;}}
</style>'''
st.markdown(CSS, unsafe_allow_html=True)


# ── small UI helpers ─────────────────────────────────────────────────────────
def card(name):
    """Rounded soft-UI card (keyed container): heading, text and charts live inside it."""
    return st.container(key=f"card-{name}")


def head(title, desc=None, page=False):
    html = f'<div class="{"h-page" if page else "h-card"}">{escape(title)}</div>'
    if desc:
        html += f'<div class="desc">{escape(desc)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def fg_for(color):
    return "#2B2100" if color == S_AMBER else "#fff"


def pill_html(label, icon, color):
    return f'<span class="pill" style="--c:{color};--fg:{fg_for(color)}"><i>{escape(icon)}</i>{escape(label)}</span>'


def status_pill(label):
    return pill_html(label, STATUS_ICON.get(label, "•"), colors.get(label, S_GREY))


def metric(label, value, note, tag=None):
    """tag=(icon, colour) renders a status pill; otherwise a brand-coloured key number."""
    if tag:
        top, cls = pill_html(label, tag[0], tag[1]), "metric"
    else:
        top, cls = f'<span class="m-label">{escape(label)}</span>', "metric key"
    st.markdown(f'<div class="{cls}"><div class="m-top">{top}</div><div class="m-value">{escape(str(value))}</div><div class="m-note">{escape(note)}</div></div>', unsafe_allow_html=True)


def strip(text):
    st.markdown(f'<div class="strip"><span class="ico">i</span><span>{escape(text)}</span></div>', unsafe_allow_html=True)


# ── data helpers (unchanged logic) ───────────────────────────────────────────
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
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=FONT_PLOT, color=INK, size=13), height=height, margin=dict(l=8, r=8, t=18, b=8),
                      legend=dict(title=None, orientation="h", y=-.22, font=dict(size=12)),
                      hoverlabel=dict(bgcolor=BG, bordercolor=LINE, font=dict(family=FONT_PLOT, color=INK)))
    fig.update_xaxes(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE, tickfont=dict(color=MUTED))
    return fig


def csv_bytes(frame):
    return frame.to_csv(index=False).encode("utf-8-sig")


def status_chart(frame):
    counts = pd.crosstab(frame["tambon_name"], frame["display_status"]).reindex(columns=order, fill_value=0)
    counts.index.name = "tambon_name"
    pct = counts.div(counts.sum(axis=1), axis=0).mul(100)
    table = pct.reset_index().melt(id_vars="tambon_name", var_name="สถานะ", value_name="สัดส่วน (%)")
    actual = counts.reset_index().melt(id_vars="tambon_name", var_name="สถานะ", value_name="จำนวนแปลง")
    table = table.merge(actual, on=["tambon_name", "สถานะ"], validate="one_to_one")
    fig = px.bar(table, x="สัดส่วน (%)", y="tambon_name", color="สถานะ", orientation="h", color_discrete_map=colors, category_orders={"สถานะ": order}, hover_data={"จำนวนแปลง": True, "สัดส่วน (%)": ":.1f"}, labels={"tambon_name": ""}, barmode="stack")
    fig.update_traces(marker_line_color=BG, marker_line_width=1)
    return chart_style(fig, max(340, len(counts) * 35 + 110)), counts


def show_map(frame, limit=12000):
    located = frame.dropna(subset=["centroid_lat", "centroid_lon"])
    if located.empty:
        strip("ยังไม่มี centroid_lat / centroid_lon สำหรับแสดงแผนที่")
        return
    sampled = located if len(located) <= limit else located.sample(limit, random_state=42)
    fig = px.scatter_map(sampled, lat="centroid_lat", lon="centroid_lon", color="display_status", color_discrete_map=colors, category_orders={"display_status": order}, hover_name="plot_id", hover_data={"tambon_name": True, "burn_pct": ":.1f", "distance_to_collection_km": ":.2f", "centroid_lat": False, "centroid_lon": False}, zoom=10, center={"lat": located["centroid_lat"].median(), "lon": located["centroid_lon"].median()}, map_style="open-street-map", labels={"display_status": "สถานะ", "burn_pct": "สัญญาณเผา (%)", "distance_to_collection_km": "ระยะทาง (กม.)", "tambon_name": "ตำบล"})
    fig.update_traces(marker=dict(size=7, opacity=.75))
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=0, b=0), font=dict(family=FONT_PLOT, color=INK),
                      legend=dict(title=None, orientation="h", bgcolor="rgba(252,247,248,.88)", bordercolor=LINE, borderwidth=1),
                      hoverlabel=dict(bgcolor=BG, bordercolor=LINE, font=dict(family=FONT_PLOT, color=INK)))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"จุดกึ่งกลางแปลง {len(sampled):,} / {len(located):,} จุดที่มีพิกัด · ขาดพิกัด {len(frame)-len(located):,} แปลง · ไม่ใช่ขอบเขตแปลง" + (" · สุ่มเพื่อให้แผนที่โหลดเร็ว; ตัวเลขสรุปใช้ข้อมูลครบ" if len(sampled) < len(located) else ""))


def show_scatter(frame):
    eligible = frame[~frame["display_status"].eq("ข้อมูลไม่เพียงพอ")].dropna(subset=["burn_pct", "access_gap_index"])
    if eligible.empty:
        strip("ยังไม่มีแปลงที่มีสถานะและค่า burn_pct / access_gap_index ครบ")
        return
    sampled = eligible if len(eligible) <= 6000 else eligible.sample(6000, random_state=42)
    fig = px.scatter(sampled, x="access_gap_index", y="burn_pct", color="display_status", color_discrete_map=colors, hover_name="plot_id", hover_data=["tambon_name"], opacity=.6, labels={"access_gap_index": "Access Gap (0–1)", "burn_pct": "สัดส่วนสัญญาณเผา (%)", "display_status": "สถานะ"})
    fig.update_traces(marker=dict(size=6))
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


st.session_state.setdefault("demo_mode", False)


def start_demo():
    st.session_state["demo_mode"] = True


# ── sidebar skeleton (order: filters → status key → data source) ─────────────
with st.sidebar:
    filter_box = st.container()
    legend_box = st.container()
    st.markdown('<div class="side-sep"></div>', unsafe_allow_html=True)
    data_box = st.container()

with data_box:
    st.markdown('<div class="side-title">ข้อมูลของโครงการ</div>', unsafe_allow_html=True)
    st.caption("ใส่ CSV ใน data/ บน GitHub หรืออัปโหลดเพื่อดูในเซสชันนี้")
    uploaded = st.file_uploader("ตารางแปลง burnwise_master_plots.csv", type=["csv"], key="plots_upload")
    optional_overview = st.file_uploader("ภาพรวมตำบล (ไม่จำเป็น)", type=["csv"], key="overview_upload")
    demo = st.toggle("ทดลองหน้าตาด้วยข้อมูลจำลอง", key="demo_mode")
    period = st.text_input("ช่วงศึกษาที่ระบุใน notebook", placeholder="เช่น พ.ย. 2568 – ม.ค. 2569")
    st.caption("ชื่อช่วงศึกษาใช้แสดงประกอบเท่านั้น ไม่ได้กรองวันที่ใน CSV")

# ── top bar: logo + capsule menu + download slot ─────────────────────────────
with st.container(key="topbar"):
    c_brand, c_nav, c_dl = st.columns([1.15, 2.7, 1.2], vertical_alignment="center")
    badge = '<span class="demo-badge">ข้อมูลจำลอง</span>' if demo else ""
    c_brand.markdown(f'<div class="brand"><span class="logo"></span><div><div class="b-name">BurnWise{badge}</div><div class="b-sub">อำเภอท่าตะโก · Field Insights</div></div></div>', unsafe_allow_html=True)
    with c_nav:
        page = st.radio("หน้าเว็บ", PAGES, horizontal=True, label_visibility="collapsed", format_func=lambda p: f":material/{PAGE_ICON[p]}: {p}")
    dl_slot = c_dl.empty()

path = BASE / "data" / "burnwise_master_plots.csv"
try:
    if demo:
        raw = demo_data(); source_name = "ข้อมูลจำลอง"
    elif uploaded is not None:
        raw = read_csv(io.BytesIO(uploaded.getvalue())); source_name = uploaded.name
    elif path.is_file():
        raw = read_csv(path); source_name = "data/burnwise_master_plots.csv"
    else:
        with card("start"):
            head("เริ่มต้นใช้งาน BurnWise", "ยังไม่มีข้อมูลแปลงให้แสดง", page=True)
            st.markdown('<ol class="steps"><li>อัปโหลด <b>burnwise_master_plots.csv</b> ทางแถบด้านซ้าย</li><li>หรือเพิ่มไฟล์นี้ในโฟลเดอร์ <b>data</b> ของ GitHub</li><li>หรือดูหน้าตาเว็บก่อนด้วยข้อมูลจำลอง (ไม่ใช่ผลของโครงการ)</li></ol>', unsafe_allow_html=True)
            st.button(":material/science: ทดลองด้วยข้อมูลจำลอง", type="primary", on_click=start_demo)
        st.stop()
    plots, mode = prepare(raw)
except (ValueError, OSError) as exc:
    st.error(str(exc)); st.stop()

if mode == "modern":
    order = list(STATUS.values()); colors = dict(zip(order, [S_RED, S_GREEN, S_AMBER]))
else:
    order = ["Tier เขียว (เดิม)", "Tier เหลือง (เดิม)", "Tier แดง (เดิม)", "ข้อมูลไม่เพียงพอ"]
    colors = dict(zip(order, [S_GREEN, S_AMBER, S_RED, S_GREY]))

# ── sidebar: filters + status key ────────────────────────────────────────────
with filter_box:
    st.markdown('<div class="side-title">ตัวกรอง</div>', unsafe_allow_html=True)
    names = sorted(plots["tambon_name"].unique())
    selected_names = st.multiselect("ตำบล", names, default=names)
    st.caption(f"เลือก {len(selected_names)} จาก {len(names)} ตำบล")
    selected_status = st.multiselect("สถานะ", order, default=order)
with legend_box:
    st.markdown('<div class="side-title">สัญลักษณ์สถานะข้อมูล</div>', unsafe_allow_html=True)
    st.markdown('<div class="legend-stack">' + "".join(status_pill(s) for s in order) + '</div>', unsafe_allow_html=True)
    st.markdown('<div class="legend-note">สีแดงเข้มของโลโก้ เมนู และปุ่มเป็นสีแบรนด์ ไม่ใช่การแจ้งเตือนการเผา สถานะข้อมูลแสดงด้วยป้ายพร้อมไอคอนข้างต้นเสมอ</div>', unsafe_allow_html=True)

# ── notices ──────────────────────────────────────────────────────────────────
if demo:
    st.warning("ข้อมูลจำลองทั้งหมด: ใช้ตรวจหน้าตาเว็บเท่านั้น ตัวเลขและพิกัดไม่ใช่ผลของโครงการ")
elif mode == "legacy":
    st.warning("ไฟล์นี้ใช้ Tier เดิมจากสัดส่วนไถกลบ: แสดงกลุ่มตามต้นทาง ไม่แปลงเป็น Burn / No Burn · valid_observation_pct เดิมอาจเป็นผลรวมเผา+ไถกลบ จึงยังใช้ยืนยัน coverage ไม่ได้")
else:
    strip("ผลจากดาวเทียมเบื้องต้น · No Burn = ไม่เข้าเกณฑ์ตรวจพบ ไม่ใช่หลักฐานยืนยันว่าไม่เผาหรือไถกลบ")
st.markdown(f'<div class="chips"><span class="chip">แหล่งข้อมูล: {escape(source_name)}</span><span class="chip">{("ช่วงศึกษา: " + escape(period)) if period else "ยังไม่ได้ระบุช่วงศึกษา"}</span></div>', unsafe_allow_html=True)

f = plots[plots["tambon_name"].isin(selected_names) & plots["display_status"].isin(selected_status)].copy()
if f.empty:
    strip("ไม่มีแปลงตรงกับตัวกรอง กรุณาเลือกตำบลหรือสถานะเพิ่ม"); st.stop()

export_cols = [c for c in f.columns if c not in ["display_status", "review_flag"]]
dl_slot.download_button(":material/download: ดาวน์โหลด", csv_bytes(f[export_cols]), "burnwise_filtered_plots.csv", "text/csv", type="primary", help="ดาวน์โหลดแปลงที่เลือกเป็น CSV")

# ── pages ────────────────────────────────────────────────────────────────────
if page == "ภาพรวม":
    head("ภาพรวมพื้นที่นำร่อง", f"อำเภอท่าตะโก · {len(f):,} จาก {len(plots):,} แปลง · {f['tambon_name'].nunique()} ตำบล · พื้นที่รวม {f['plot_area_rai'].sum():,.1f} ไร่", page=True)
    if mode == "modern":
        cards = [("แปลงทั้งหมด", len(f), "แปลงในตัวกรอง", None)] + [(label, int(f["display_status"].eq(label).sum()), f"{f['display_status'].eq(label).mean()*100:.1f}% ของแปลงที่เลือก", (STATUS_ICON[label], colors[label])) for label in order]
    else:
        cards = [("แปลงทั้งหมด", len(f), "แปลงในตัวกรอง", None),
                 ("พื้นที่รวม (ไร่)", f"{f['plot_area_rai'].sum():,.0f}", "ผลรวมพื้นที่แปลงตาม CSV", None),
                 ("Tier แดง (เดิม)", int(f["display_status"].eq("Tier แดง (เดิม)").sum()), "กลุ่มจากตรรกะเดิม ไม่ยืนยันว่าเผา", (STATUS_ICON["Tier แดง (เดิม)"], colors["Tier แดง (เดิม)"])),
                 ("ข้อมูลไม่เพียงพอ", int(f["display_status"].eq("ข้อมูลไม่เพียงพอ").sum()), "แยกจากกลุ่มที่จัดสถานะได้", (STATUS_ICON["ข้อมูลไม่เพียงพอ"], colors["ข้อมูลไม่เพียงพอ"]))]
    for col, (label, value, note, tag) in zip(st.columns(4), cards):
        with col:
            metric(label, f"{value:,}" if isinstance(value, int) else value, note, tag)
    left, right = st.columns([1.1, 1])
    with left, card("tambon-status"):
        head("สถานะรายตำบล", "สัดส่วนจำนวนแปลงในตัวกรอง รวมกลุ่มข้อมูลไม่พอ")
        fig, counts = status_chart(f); st.plotly_chart(fig, width="stretch")
        st.download_button("ดาวน์โหลดจำนวนแปลงรายตำบล", csv_bytes(counts.reset_index()), "burnwise_tambon_counts.csv", "text/csv")
    with right, card("tambon-burn"):
        head("สัดส่วนสัญญาณเผารายตำบล")
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
            fig = px.bar(overview.sort_values("burn_pct (%)"), x="burn_pct (%)", y="tambon_name", orientation="h", color_discrete_sequence=[S_RED], labels={"tambon_name": "", "burn_pct (%)": "สัดส่วนพื้นที่ (%)"})
            st.plotly_chart(chart_style(fig), width="stretch")
            st.caption("▲ สัญญาณเผา · ใช้ตารางภาพรวมจาก notebook ตามตำบลที่เลือก · ไม่เปลี่ยนตามตัวกรองสถานะแปลง · ฐานพื้นที่ต่างจากกราฟจำนวนแปลง")
            st.dataframe(overview, hide_index=True, width="stretch")
        else:
            mean_burn = f[~f["display_status"].eq("ข้อมูลไม่เพียงพอ")].groupby("tambon_name", as_index=False)["burn_pct"].mean().dropna()
            if mean_burn.empty:
                strip("ยังไม่มีค่าสัญญาณเผาในแปลงที่จัดสถานะได้")
            else:
                fig = px.bar(mean_burn.sort_values("burn_pct"), x="burn_pct", y="tambon_name", orientation="h", color_discrete_sequence=[S_RED], labels={"tambon_name": "", "burn_pct": "ค่าเฉลี่ยต่อแปลง (%)"})
                st.plotly_chart(chart_style(fig), width="stretch")
            st.caption("▲ สัญญาณเผา · ค่าเฉลี่ย burn_pct ต่อแปลงที่ไม่อยู่กลุ่มข้อมูลไม่พอ · ไม่ใช่สัดส่วนพื้นที่เผาทั้งตำบล · เพิ่ม CSV ภาพรวมเพื่อแสดงผลระดับพื้นที่")
    left, right = st.columns([1.2, 1])
    with left, card("map"):
        head("แผนที่พื้นที่ศึกษา"); show_map(f)
    with right, card("scatter"):
        head("สัญญาณเผา × Access Gap"); show_scatter(f)
    with card("review"):
        head("แปลงที่ควรตรวจสอบเพิ่มเติม")
        review = f[f["review_flag"]]
        st.caption(f"{len(review):,} แปลง · รวมสถานะข้อมูลไม่พอ เหตุผลคัดออก หรือธงตรวจสอบจากต้นทาง · ตัวอย่าง 100 แถวแรก")
        st.dataframe(review[["plot_id", "tambon_name", "display_status", "burn_pct", "valid_observation_pct", "exclusion_reason", "needs_verification"]].head(100), hide_index=True, width="stretch")

elif page == "สำรวจแปลง":
    with card("hero"):
        head("สำรวจแปลงรายพื้นที่", "ค้นหารหัสแปลง ดูตำแหน่ง และตรวจรายละเอียดรายแปลง", page=True)
        q_col, r_col = st.columns([2, 1], vertical_alignment="bottom")
        query = q_col.text_input("ค้นหารหัสแปลง", placeholder="พิมพ์ส่วนหนึ่งของ plot_id")
        review_only = r_col.checkbox("แสดงเฉพาะแปลงที่ควรตรวจสอบเพิ่มเติม")
    explored = f[f["plot_id"].astype(str).str.contains(query, regex=False, case=False)]
    if review_only: explored = explored[explored["review_flag"]]
    with card("explore-map"):
        head("ตำแหน่งแปลง", f"พบ {len(explored):,} แปลง · ตารางแสดงไม่เกิน 1,000 แถวแรก")
        show_map(explored)
    with card("explore-table"):
        head("ตารางแปลง")
        cols = ["plot_id", "tambon_name", "display_status", "plot_area_rai", "burn_pct", "valid_observation_pct", "distance_to_collection_km", "access_gap_index", "exclusion_reason"]
        st.dataframe(explored[cols].head(1000), hide_index=True, width="stretch")
        st.download_button("ดาวน์โหลดผลค้นหาทั้งหมด", csv_bytes(explored[export_cols]), "burnwise_search.csv", "text/csv")
    if not explored.empty:
        with card("explore-detail"):
            ids = explored["plot_id"].tolist()[:1000]
            choice = st.selectbox("ดูรายละเอียดแปลง (จาก 1,000 แถวแรก)", ids)
            row = explored[explored["plot_id"].eq(choice)].iloc[0]
            head(str(choice))
            st.markdown(f'<div class="chips"><span class="chip">ตำบล: {escape(str(row["tambon_name"]))}</span>{status_pill(row["display_status"])}</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame({"รายการ": export_cols, "ค่า": ["—" if pd.isna(row[c]) else str(row[c]) for c in export_cols]}), hide_index=True, width="stretch")

elif page == "คุณภาพข้อมูล":
    unknown = f[f["display_status"].eq("ข้อมูลไม่เพียงพอ")]
    head("คุณภาพข้อมูลและจุดที่ต้องตรวจสอบ", "สัดส่วนภาพใช้ได้และเหตุผลที่แปลงถูกจัดเป็นข้อมูลไม่เพียงพอ ก่อนเชื่อผลใด ๆ ควรตรวจหน้านี้ก่อน", page=True)
    a, b, c = st.columns(3)
    with a: metric("ข้อมูลไม่เพียงพอ", f"{len(unknown):,}", "แปลงที่ยังไม่ควรสรุปสถานะ", (STATUS_ICON["ข้อมูลไม่เพียงพอ"], colors["ข้อมูลไม่เพียงพอ"]))
    with b: metric("ไม่มีระยะทางถนน", f"{f['distance_to_collection_km'].isna().sum():,}", "ไม่แทนระยะทางที่หายด้วยศูนย์", ("!", S_AMBER))
    with c: metric("ไม่มี Access Gap", f"{f['access_gap_index'].isna().sum():,}", "ตรวจข้อมูลประกอบก่อนจัดลำดับ", ("!", S_AMBER))
    left, right = st.columns(2)
    with left, card("coverage"):
        head("Coverage" if mode == "modern" else "สัดส่วน valid_observation_pct เดิม", "การกระจายตัวของ valid_observation_pct")
        valid = f.dropna(subset=["valid_observation_pct"])
        if valid.empty: strip("ไม่มีข้อมูล valid_observation_pct")
        else:
            fig = px.histogram(valid, x="valid_observation_pct", nbins=20, color_discrete_sequence=[SEC], labels={"valid_observation_pct": "สัดส่วน (%)"})
            fig.update_traces(marker_line_color=BG, marker_line_width=1)
            if mode == "modern": fig.add_vline(x=80, line_dash="dash", line_color=BRAND, line_width=2, annotation_text="เกณฑ์โค้ดหลัก 80%", annotation_font=dict(color=BRAND, size=12))
            st.plotly_chart(chart_style(fig), width="stretch")
        st.caption(f"ไม่มีค่า {f['valid_observation_pct'].isna().sum():,} แปลง" + (" · ในไฟล์เดิมค่านี้อาจเป็นเผา+ไถกลบ ไม่ใช่พื้นที่ที่มีภาพใช้ได้" if mode == "legacy" else " · กราฟไม่เปลี่ยนสถานะที่บันทึกใน CSV"))
    with right, card("reasons"):
        head("เหตุผลที่ต้องตรวจสอบ", "จำนวนแปลงแยกตามเหตุผลคัดออกหรือธงตรวจสอบ")
        reasons = f.loc[f["review_flag"], "exclusion_reason"].fillna("").astype(str).str.strip().replace("", "ธงตรวจสอบ/สถานะข้อมูลไม่พอ แต่ไม่มีเหตุผลคัดออก")
        counts = reasons.value_counts().rename_axis("เหตุผล").reset_index(name="จำนวนแปลง")
        st.dataframe(counts, hide_index=True, width="stretch")
    with card("notes"):
        head("ข้อควรทราบ")
        strip("GISTDA เป็นส่วนเปรียบเทียบเพิ่มเติม: เว็บนี้ไม่ต้องรอไฟล์รอยเผา หากช่วงอ้างอิงไม่ครบ ให้เว้นผลประเมินส่วนนั้นไว้")
        st.markdown("ผล FIRMS ที่เคยทดสอบ 2/2 จุดที่อ่านภาพได้ มีตัวอย่างน้อย และไม่มีตัวอย่างยืนยันไม่เผา จึงยังไม่ใช้สรุปความแม่นยำทั้งโครงการ")

else:
    with card("about"):
        head("เกี่ยวกับ BurnWise", "ข้อมูลสำหรับสำรวจและช่วยเหลือพื้นที่", page=True)
        st.write("BurnWise รวบรวมสัญญาณจากดาวเทียม ขอบเขตแปลง และการเข้าถึงจุดรวบรวม เพื่อช่วยสำรวจพื้นที่นำร่องอำเภอท่าตะโก")
        st.write("เว็บนี้อ่านผล CSV ที่คำนวณแล้วจาก notebook ไม่ได้คำนวณ Earth Engine ใหม่ ไม่ได้เปลี่ยน threshold หรือจัดสถานะแปลงใหม่")
        st.caption("ภาพรวมจำนวนแปลงคำนวณใหม่จากตารางหลัก เพื่อหลีกเลี่ยง Score Panel จากคนละรอบประมวลผล")
    with card("about-sources"):
        head("แหล่งข้อมูลและข้อจำกัด")
        st.markdown("**แหล่งข้อมูลในกระบวนการ:** Sentinel-2, FIRMS, Fields of The World, ขอบเขต DOPA, โครงข่ายถนน OpenStreetMap และข้อมูลรายได้ระดับตำบลที่ทีมเลือกใช้")
        st.markdown("**ข้อจำกัด:** สัญญาณเผาไม่ใช่หลักฐานยืนยันรายบุคคล · No Burn ไม่ยืนยันว่าไถกลบ · รายได้ตำบลไม่ใช่รายได้เจ้าของแปลง · Access Gap เป็นดัชนีประกอบการสำรวจ")

st.markdown('<div class="footer">BurnWise · ท่าตะโก · ตรวจสอบข้อมูลและหลักฐานภาคสนามก่อนใช้กำหนดมาตรการ</div>', unsafe_allow_html=True)
