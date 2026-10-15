"""BurnWise plot workbook. Run with: streamlit run app.py
Uses supplied January 2026 results; never computes or invents Earth Engine results.
"""
from pathlib import Path
from html import escape
from urllib.parse import urlencode
import gzip, io, json, math, base64
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title='BurnWise · Plot workbook',page_icon='🔥',layout='wide')
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
TAMBONS={'ต.หนองหลวง':'Nong Luang','ต.สายลำโพง':'Sai Lamphong','ต.วังใหญ่':'Wang Yai','ต.พนมเศษ':'Phanom Set','ต.ดอนคา':'Don Kha','ต.พนมรอก':'Phanom Rok','ต.วังมหากร':'Wang Mahakon','ต.ท่าตะโก':'Tha Tako','ต.หัวถนน':'Hua Thanon','ต.ทำนบ':'Thamnop'}

def truth(s):
    return s.astype('string').str.strip().str.lower().isin(['true','1','yes'])

@st.cache_data(show_spinner=False)
def load_bundle():
    path=DATA/'burnwise_master_plots_with_measures_last1.csv.gz'
    if not path.exists():path=DATA/'burnwise_master_plots.csv'
    b=path.read_bytes()
    if b.startswith(b'version https://git-lfs'):raise ValueError('Git LFS pointer: actual data file is missing.')
    if b[:2]==b'\x1f\x8b':
        try:
            b=gzip.decompress(b)
        except (EOFError, OSError) as exc:
            raise ValueError(
                'Data archive is damaged or incomplete. Replace data/' + path.name +
                ' with the verified file from the corrected app bundle, then restart the app. '
                'ไฟล์ข้อมูลบีบอัดเสียหรือไม่ครบ กรุณาแทนที่ด้วยไฟล์จากชุดแก้ไขแล้วเริ่มแอปใหม่'
            ) from exc
    d=pd.read_csv(io.BytesIO(b),dtype={'plot_id':'string','tambon_id':'string'})
    required={'plot_id','burn_status','tambon_name','burn_pct','plot_area_rai','analysis_eligible'}
    if required-set(d):raise ValueError('Missing columns: '+', '.join(sorted(required-set(d))))
    if d.plot_id.isna().any() or d.plot_id.duplicated().any():raise ValueError('Missing or duplicate plot ID.')
    for col in ['analysis_eligible','access_analysis_eligible','is_boundary_fragment']: 
        if col in d:d[col]=truth(d[col])
    for col in ['burn_pct','valid_observation_pct','access_gap_index','distance_to_collection_km','plot_area_rai','centroid_lat','centroid_lon']:
        if col in d:d[col]=pd.to_numeric(d[col],errors='coerce')
    d['status_code']=d.burn_status.map({'Burn':'burn','No Burn':'no_burn','Unknown':'unknown','ข้อมูลไม่เพียงพอ':'unknown'}).fillna('unknown')
    # Fail closed if a supplied eligibility flag conflicts with its actual image fields.
    eligible=d.analysis_eligible & d.status_code.ne('unknown') & d.burn_pct.between(0,100)
    if 'valid_observation_pct' in d:eligible &= d.valid_observation_pct.ge(80)
    d['analysis_eligible']=eligible
    manifest=json.loads((DATA/'burnwise_run_manifest.json').read_text()) if (DATA/'burnwise_run_manifest.json').exists() else {}
    vpath=DATA/'burnwise_gistda_validation_plots.csv'
    v=pd.read_csv(vpath,dtype={'plot_id':'string'}) if vpath.exists() else pd.DataFrame()
    if len(v):
        if v.plot_id.duplicated().any():raise ValueError('Duplicate comparison plot ID.')
        cols=['plot_id','BurnWise_Burn','GISTDA_Burn','burnwise_eval_pct','gistda_overlap_pct']
        d=d.merge(v[[c for c in cols if c in v]],on='plot_id',how='left',validate='one_to_one')
    disc=DATA/'burnwise_table_grid_discrepancies.csv'
    discrep=pd.read_csv(disc,dtype={'plot_id':'string'}) if disc.exists() else pd.DataFrame()
    d['grid_discrepancy']=d.plot_id.isin(discrep.plot_id) if 'plot_id' in discrep else False
    return d,manifest,v,discrep

def select_rows(d,scope,tambon,status,query,sort,descending):
    f=d.copy()
    if scope=='ready':f=f[f.analysis_eligible]
    elif scope=='pending':f=f[~f.analysis_eligible]
    if tambon!='all':f=f[f.tambon_name.eq(tambon)]
    if status!='all':f=f[f.status_code.eq(status)]
    if query:f=f[f.plot_id.str.contains(query,case=False,regex=False,na=False)]
    return f.sort_values([sort,'plot_id'] if sort!='plot_id' else ['plot_id'],ascending=not descending,na_position='last',kind='stable')

@st.cache_data(show_spinner=False)
def excel_bytes(frame):
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine='xlsxwriter',engine_kwargs={'options':{'strings_to_formulas':False,'strings_to_urls':False}}) as w:
        frame.to_excel(w,sheet_name='Plots',index=False)
        sheet=w.sheets['Plots'];sheet.freeze_panes(1,1);sheet.autofilter(0,0,len(frame),len(frame.columns)-1);sheet.set_column(0,len(frame.columns)-1,20)
    return buf.getvalue()

# State is per session, and links carry the current filters/language/theme.
q=st.query_params
if 'language' not in st.session_state:st.session_state.language=q.get('lang','en') if q.get('lang','en') in ['en','th'] else 'en'
if 'appearance' not in st.session_state:st.session_state.appearance=q.get('theme','light') if q.get('theme','light') in ['light','dark','mono'] else 'light'
with st.sidebar:
    st.markdown('### BurnWise')
    st.selectbox('Language / ภาษา',['en','th'],format_func=lambda x:'English' if x=='en' else 'ไทย',key='language')
lang=st.session_state.language
def tr(en,th):return th if lang=='th' else en
with st.sidebar:
    st.selectbox(tr('Appearance','รูปแบบหน้าจอ'),['light','dark','mono'],format_func=lambda x:{'light':tr('Light','สว่าง'),'dark':tr('Dark','มืด'),'mono':tr('Black & white','ขาวดำ')}[x],key='appearance')
theme=st.session_state.appearance
dark=theme=='dark';bg='#121315' if dark else '#FCF7F8';surface='#1D1F23' if dark else '#FFFFFF';ink='#F4F4F5' if dark else '#24262B';muted='#B9BDC5' if dark else '#616570';line='#3C4047' if dark else '#DDE0E4';accent='#E97780' if dark else '#A31621'
if theme=='mono':bg='#FFFFFF';surface='#FFFFFF';ink='#111111';muted='#454545';accent='#111111';line='#B8B8B8'
font_data=base64.b64encode((ROOT/'assets/NotoSansThai.ttf').read_bytes()).decode()
st.markdown(f'''<style>
@font-face{{font-family:BurnWiseThai;src:url(data:font/ttf;base64,{font_data}) format("truetype");font-weight:100 900}}
html,body,.stApp,p,h1,h2,h3,h4,label,input,button,table,summary,[data-testid="stMetricValue"],[data-baseweb="select"]{{font-family:BurnWiseThai,Arial,sans-serif!important}}
.stApp, [data-testid="stAppViewContainer"]{{background:{bg};color:{ink}}}
[data-testid="stHeader"]{{background:{bg}}}
[data-testid="stSidebar"]{{background:{surface};border-right:1px solid {line}}}
.stApp p,.stApp h1,.stApp h2,.stApp h3,.stApp label,[data-testid="stMetricValue"],[data-testid="stMetricLabel"]{{color:{ink}}}
.stApp [data-testid="stCaptionContainer"] p{{color:{muted}}}
[data-testid="stSelectbox"] div[data-baseweb="select"]>div,div[data-baseweb="input"],.stTextInput input,.stNumberInput input{{background:{surface}!important;color:{ink}!important;border-color:{line}!important}}
[data-baseweb="popover"],[data-baseweb="menu"],li[role="option"]{{background:{surface}!important;color:{ink}!important}}
.stButton button,.stDownloadButton button{{background:{surface};color:{ink};border:1px solid {line};border-radius:8px}}
button[kind="primary"]{{background:{accent};color:white}}
[data-testid="stExpander"]{{background:{surface};border-color:{line}}}
[data-testid="stSelectbox"] [role="combobox"], [data-testid="stSelectbox"] [data-baseweb="select"] *,[data-testid="stNumberInput"] button{{color:{ink}!important;background-color:{surface}!important}}
.block-container{{padding-top:2rem;max-width:1600px}}
a{{color:{accent}}}.intro{{color:{muted};font-size:1.03rem;margin:0 0 20px}}
.ledger-wrap{{overflow:auto;border:1px solid {line};border-radius:10px;max-height:580px;background:{surface}}}
.ledger{{border-collapse:separate;border-spacing:0;width:100%;font-size:14px;white-space:nowrap;color:{ink}}}
.ledger th{{position:sticky;top:0;background:{surface};z-index:1;text-align:left;border-bottom:2px solid {line};padding:13px 15px}}
.ledger td{{padding:12px 15px;border-bottom:1px solid {line}}}.ledger tr:hover td{{background:{'#2B2E34' if dark else '#F1F2F4'}}}
.ledger a{{font-weight:650;text-decoration:underline;text-underline-offset:3px}}
.status-burn{{color:{accent};font-weight:700}}.status-no_burn{{color:{ink}}}.status-unknown{{color:{muted}}}
.facts{{display:grid;grid-template-columns:1fr 1fr;gap:0 28px}}.facts div{{border-bottom:1px solid {line};padding:12px 0}}
.facts small{{display:block;color:{muted};margin-bottom:5px}}.facts strong{{font-size:18px}}
@media(max-width:700px){{.facts{{grid-template-columns:1fr}}.block-container{{padding-left:1rem;padding-right:1rem}}}}
</style>''',unsafe_allow_html=True)
if theme=='mono':st.markdown('<style>.stApp{filter:grayscale(1)}</style>',unsafe_allow_html=True)
try:plots,manifest,comparison,discrepancies=load_bundle()
except Exception as e:
    st.error(tr('Unable to load project data.','โหลดข้อมูลโครงการไม่ได้'));st.code(str(e));st.stop()

status_labels={'burn':tr('Burn signal','พบสัญญาณเผา'),'no_burn':tr('No burn signal detected','ไม่เข้าเกณฑ์ตรวจพบ'),'unknown':tr('Insufficient imagery','ข้อมูลภาพไม่เพียงพอ')}
def tambon_name(x):return TAMBONS.get(x,x) if lang=='en' else x
def fmt(x,dec=1,suffix=''):
    return tr('Not available','ยังไม่มีข้อมูล') if pd.isna(x) else f'{float(x):,.{dec}f}{suffix}'
def link(**changes):
    params=dict(lang=lang,theme=theme,scope=scope,tambon=tambon,status=status,search=search,sort=sort,desc=str(int(desc)),page=str(page))
    params.update(changes)
    return '?'+urlencode(params)
def initial(options,name,default):
    val=q.get(name,default);return options.index(val) if val in options else options.index(default)

with st.sidebar:
    st.divider();st.subheader(tr('Find a plot','ค้นหาแปลง'))
    scopes=['ready','all','pending']
    scope=st.selectbox(tr('Data scope','ชุดข้อมูล'),scopes,index=initial(scopes,'scope','ready'),format_func=lambda x:{'ready':tr('Sufficient imagery','ข้อมูลภาพเพียงพอ'),'all':tr('All plots','ทุกแปลง'),'pending':tr('Awaiting imagery','รอข้อมูลภาพ')}[x],key='scope')
    ts=['all']+sorted(plots.tambon_name.unique())
    tambon=st.selectbox(tr('Subdistrict','ตำบล'),ts,index=initial(ts,'tambon','all'),format_func=lambda x:tr('All subdistricts','ทุกตำบล') if x=='all' else tambon_name(x),key='tambon')
    ss=['all','burn','no_burn','unknown']
    status=st.selectbox(tr('Signal status','สถานะสัญญาณ'),ss,index=initial(ss,'status','all'),format_func=lambda x:tr('All statuses','ทุกสถานะ') if x=='all' else status_labels[x],key='status')
    search=st.text_input(tr('Plot ID contains','ค้นหารหัสแปลง'),value=q.get('search',''),key='search')
    sorts=['plot_id','burn_pct','valid_observation_pct','plot_area_rai']
    sort=st.selectbox(tr('Sort by','เรียงตาม'),sorts,index=initial(sorts,'sort','plot_id'),format_func=lambda x:{'plot_id':tr('Plot ID','รหัสแปลง'),'burn_pct':tr('Burn signal %','สัญญาณเผา %'),'valid_observation_pct':tr('Valid imagery %','ภาพใช้ได้ %'),'plot_area_rai':tr('Area (rai)','พื้นที่ (ไร่)')}[x],key='sort')
    desc=st.checkbox(tr('Descending','มากไปน้อย'),value=q.get('desc','0')=='1',key='descending')
    st.caption(tr('January 2026 study. Provisional satellite screening.','รอบศึกษามกราคม 2569 ผลคัดกรองดาวเทียมเบื้องต้น'))

st.title(tr('Plot workbook','สมุดข้อมูลแปลง'))
st.markdown('<p class="intro">'+tr('Find a plot. Open its evidence. Decide what to verify next.','ค้นหาแปลง เปิดดูข้อมูล และเลือกสิ่งที่ต้องตรวจสอบต่อ')+'</p>',unsafe_allow_html=True)
counts=st.columns(4)
for c,label,value in zip(counts,[tr('All study plots','แปลงทั้งหมด'),tr('Sufficient imagery','ภาพเพียงพอ'),tr('Awaiting imagery','รอข้อมูลภาพ'),tr('Image eligibility','สัดส่วนแปลงผ่านเกณฑ์')],[f'{len(plots):,}',f'{plots.analysis_eligible.sum():,}',f'{(~plots.analysis_eligible).sum():,}',f'{plots.analysis_eligible.mean()*100:.1f}%']):c.metric(label,value)
st.warning(tr('Only 2.6% of study plots pass image requirements in this run. Results cannot represent the entire district. No Burn means no signal above the rule, not confirmed absence of burning.','รอบนี้มีแปลงผ่านเกณฑ์ภาพเพียง 2.6% จึงยังสรุปแทนทั้งอำเภอไม่ได้ No Burn หมายถึงไม่เข้าเกณฑ์ตรวจพบ ไม่ใช่ยืนยันว่าไม่เผา') if len(plots)==47316 and int(plots.analysis_eligible.sum())==1229 else tr('Read results together with coverage. No Burn does not confirm absence of burning.','อ่านผลคู่กับ coverage เสมอ No Burn ไม่ใช่ยืนยันว่าไม่เผา'))
filtered=select_rows(plots,scope,tambon,status,search,sort,desc)
page_size=50
pages=max(1,math.ceil(len(filtered)/page_size))
try:initial_page=max(0,min(int(q.get('page',0)),pages-1))
except ValueError:initial_page=0
signature=(scope,tambon,status,search,sort,desc)
if st.session_state.get('filter_signature')!=signature:
    st.session_state['page_number']=initial_page+1 if 'filter_signature' not in st.session_state else 1
    st.session_state['filter_signature']=signature
st.session_state['page_number']=min(st.session_state.get('page_number',1),pages)
bar=st.columns([3,1,1])
bar[0].caption(tr(f'{len(filtered):,} matching plots · click a plot ID to open details',f'พบ {len(filtered):,} แปลง · กดรหัสแปลงเพื่อดูรายละเอียด'))
page=int(bar[1].number_input(tr('Page','หน้า'),min_value=1,max_value=pages,step=1,key='page_number'))-1
export=filtered.drop(columns=['status_code'],errors='ignore')
bar[2].download_button(tr('Download CSV','ดาวน์โหลด CSV'),export.to_csv(index=False).encode('utf-8-sig'),'burnwise_filtered_plots.csv','text/csv')
with st.expander(tr('Excel download','ดาวน์โหลด Excel')):
    if st.button(tr('Prepare Excel file','เตรียมไฟล์ Excel')):
        st.download_button(tr('Download .xlsx','ดาวน์โหลด .xlsx'),excel_bytes(export),'burnwise_filtered_plots.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
shown=filtered.iloc[page*page_size:(page+1)*page_size]
headers=[tr('Plot ID ↗','รหัสแปลง ↗'),tr('Subdistrict','ตำบล'),tr('Signal','สัญญาณ'),tr('Area (rai)','พื้นที่ (ไร่)'),tr('Burn %','เผา %'),tr('Valid imagery %','ภาพใช้ได้ %'),tr('Access','การเข้าถึง'),tr('Review','ตรวจสอบ')]
rows=[]
for _,r in shown.iterrows():
    access=tr('Ready','พร้อม') if r.get('access_analysis_eligible',False) else tr('Pending verification','รอยืนยัน')
    review=tr('Required','ต้องตรวจสอบ') if pd.notna(r.get('needs_verification')) else tr('No extra flag','ไม่มีธงเพิ่ม')
    cells=[f'<a target="_self" href="{escape(link(plot=r.plot_id))}">{escape(r.plot_id)}</a>',escape(tambon_name(r.tambon_name)),f'<span class="status-{r.status_code}">{escape(status_labels[r.status_code])}</span>',fmt(r.plot_area_rai),fmt(r.burn_pct),fmt(r.valid_observation_pct),access,review]
    rows.append('<tr>'+''.join('<td>'+v+'</td>' for v in cells)+'</tr>')
if len(shown):st.html('<div class="ledger-wrap"><table class="ledger"><thead><tr>'+''.join('<th>'+escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>')
else:st.info(tr('No plots match these filters. Change the scope or search.','ไม่มีแปลงตรงตัวกรอง ลองเปลี่ยนชุดข้อมูลหรือคำค้น'))

selected=q.get('plot','')
if selected:
    hit=plots[plots.plot_id.eq(selected)]
    if hit.empty:st.error(tr('Plot ID not found in this dataset.','ไม่พบรหัสแปลงนี้ในชุดข้อมูล'))
    else:
        r=hit.iloc[0]
        st.divider();st.subheader(tr('Plot details','รายละเอียดแปลง')+' · '+r.plot_id)
        st.caption(tambon_name(r.tambon_name)+' · '+status_labels[r.status_code])
        if selected not in set(filtered.plot_id):st.info(tr('This selected plot is outside the current filters.','แปลงที่เปิดอยู่นอกตัวกรองปัจจุบัน'))
        facts=[(tr('Area','พื้นที่'),fmt(r.plot_area_rai,1,tr(' rai',' ไร่'))),(tr('Burn signal within valid crop pixels','สัญญาณเผาภายในพิกเซลเกษตรที่ภาพใช้ได้'),fmt(r.burn_pct,1,'%')),(tr('Valid imagery coverage','สัดส่วนพื้นที่ภาพใช้ได้'),fmt(r.valid_observation_pct,1,'%')),(tr('Access Gap','ดัชนีการเข้าถึง'),fmt(r.access_gap_index,2) if r.get('access_analysis_eligible',False) else tr('Awaiting verified facilities','รอยืนยันจุดรับซื้อ'))]
        st.html('<div class="facts">'+''.join('<div><small>'+escape(k)+'</small><strong>'+escape(v)+'</strong></div>' for k,v in facts)+'</div>')
        st.markdown('#### '+tr('What needs verification?','ต้องตรวจสอบอะไร?'))
        reasons=[]
        if not r.analysis_eligible:reasons.append(tr('Image evidence is insufficient for classification.','ข้อมูลภาพยังไม่เพียงพอสำหรับจัดสถานะ'))
        if r.get('is_boundary_fragment',False):reasons.append(tr('The study boundary clips this plot.','ขอบเขตพื้นที่ศึกษาตัดผ่านแปลง'))
        if pd.notna(r.burn_pct) and abs(r.burn_pct-10)<=3:reasons.append(tr('The signal is close to the 10% plot threshold.','สัญญาณใกล้เกณฑ์ระดับแปลง 10%'))
        if not r.get('access_analysis_eligible',False):reasons.append(tr('Collection facilities or routes still need verification.','จุดรับซื้อหรือเส้นทางยังต้องยืนยัน'))
        if r.grid_discrepancy:reasons.append(tr('The table and evaluation raster differ by more than 2 percentage points.','ค่าตารางกับ raster ประเมินต่างกันเกิน 2 จุดเปอร์เซ็นต์'))
        for reason in reasons:st.write('• '+reason)
        if not reasons:st.write(tr('No additional automatic flags. Field evidence is still required.','ไม่มีธงอัตโนมัติเพิ่มเติม ยังต้องตรวจหลักฐานจริง'))
        if pd.notna(r.get('GISTDA_Burn')):
            st.markdown('#### '+tr('GISTDA comparison','เทียบกับ GISTDA'))
            st.write(tr('BurnWise grid signal: ','สัญญาณในกริด BurnWise: ')+fmt(r.get('burnwise_eval_pct'),1,'%')+' · '+tr('GISTDA overlap: ','พื้นที่ทับซ้อน GISTDA: ')+fmt(r.get('gistda_overlap_pct'),1,'%'))
            st.caption(tr('External product agreement. This does not establish field truth.','ความสอดคล้องกับผลิตภัณฑ์ภายนอก ยังไม่ใช่ข้อเท็จจริงภาคสนาม'))
        else:st.caption(tr('This plot is outside the exported GISTDA comparison set.','แปลงนี้ไม่อยู่ในชุดที่ส่งออกสำหรับเทียบ GISTDA'))
        if pd.notna(r.get('centroid_lat')) and pd.notna(r.get('centroid_lon')):
            st.write(tr('Plot centroid','จุดกลางแปลง')+f': {r.centroid_lat:.6f}, {r.centroid_lon:.6f}')
            st.link_button(tr('Open location in Google Maps','เปิดตำแหน่งใน Google Maps'),f'https://www.google.com/maps/search/?api=1&query={r.centroid_lat:.6f},{r.centroid_lon:.6f}')
            st.caption(tr('Centroid only. This is not a surveyed entrance or a plot boundary.','พิกัดจุดกลางเท่านั้น ไม่ใช่ทางเข้าแปลงที่สำรวจหรือขอบเขตแปลง'))
        with st.expander(tr('Original record and exclusion codes','ข้อมูลต้นฉบับและรหัสเหตุผล')):
            st.json({k:(None if pd.isna(v) else v.item() if isinstance(v,np.generic) else v) for k,v in r.items()})
        st.download_button(tr('Download this plot','ดาวน์โหลดแปลงนี้'),hit.to_csv(index=False).encode('utf-8-sig'),'burnwise_plot.csv','text/csv')

with st.expander(tr('Study scope and comparison results','ขอบเขตการศึกษาและผลเปรียบเทียบ')):
    st.write(tr('Pre-image window: ','ช่วงภาพก่อน: ')+str(manifest.get('pre_start','?'))+' ≤ date < '+str(manifest.get('pre_end_exclusive','?')))
    st.write(tr('Post-image window: ','ช่วงภาพหลัง: ')+str(manifest.get('post_start','?'))+' ≤ date < '+str(manifest.get('post_end_exclusive','?')))
    st.write(tr('dNBR threshold: ','เกณฑ์ dNBR: ')+str(round(manifest.get('threshold',float('nan')),4)))
    if len(comparison):
        tp=int(((comparison.BurnWise_Burn==1)&(comparison.GISTDA_Burn==1)).sum());fp=int(((comparison.BurnWise_Burn==1)&(comparison.GISTDA_Burn==0)).sum());fn=int(((comparison.BurnWise_Burn==0)&(comparison.GISTDA_Burn==1)).sum());tn=len(comparison)-tp-fp-fn
        div=lambda a,b:a/b if b else np.nan
        st.write(tr(f'Provisional product comparison: {len(comparison):,} plots. Precision {div(tp,tp+fp):.1%}, recall {div(tp,tp+fn):.1%}, F1 {div(2*tp,2*tp+fp+fn):.1%}.',f'ผลเทียบผลิตภัณฑ์เบื้องต้น {len(comparison):,} แปลง Precision {div(tp,tp+fp):.1%}, Recall {div(tp,tp+fn):.1%}, F1 {div(2*tp,2*tp+fp+fn):.1%}'))
        st.write(f'TP {tp:,} · FP {fp:,} · FN {fn:,} · TN {tn:,}')
        st.warning(tr(f'{len(discrepancies)} plots have table/grid discrepancies. Independent ground truth is not available in this bundle.',f'{len(discrepancies)} แปลงมีค่าตาราง/กริดต่างกัน ชุดนี้ยังไม่มี Ground Truth อิสระ'))
    st.caption(tr('BurnWise supports review and planning. These outputs do not identify an offender or prove deliberate burning.','BurnWise สนับสนุนการตรวจสอบและวางแผน ผลนี้ไม่ระบุตัวผู้กระทำหรือพิสูจน์เจตนาเผา'))
