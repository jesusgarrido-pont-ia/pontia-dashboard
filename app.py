"""
PontIA KPI Dashboard
Lee desde Google Drive (auto-actualizable), subida manual, o ruta local.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import requests

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PontIA · KPI Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
# Colores corporativos PontIA
# Primarios: Azul #111E2D · Verde #173A32 · Amarillo #F6FAB2
# Secundarios: Azul Cielo #5683D2 · Verde Salvia #AABCA3 · Ámbar #BB812F · Naranja #EE7015
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
  * { font-family: 'Manrope', sans-serif !important; }
  .stApp { background-color: #111E2D; }
  [data-testid="stSidebar"] { background-color: #0D1820; border-right: 1px solid #173A32; }
  .stTabs [data-baseweb="tab-list"] { background:#0D1820; border-radius:10px; padding:4px; gap:3px; }
  .stTabs [data-baseweb="tab"] { color:#808080; font-weight:500; border-radius:7px; padding:8px 18px; }
  .stTabs [aria-selected="true"] { background:#173A32 !important; color:#F6FAB2 !important; }
  div[data-testid="stMetric"] {
    background:#0D1820; border:1px solid #173A32; border-radius:12px; padding:14px 18px;
  }
  div[data-testid="stMetric"] label { color:#AABCA3 !important; font-size:0.78rem !important; }
  div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#F6FAB2 !important; font-size:1.5rem !important; font-weight:700 !important; }
  h1,h2,h3,h4 { color:#F6FAB2 !important; }
  .hero { font-size:2.2rem; font-weight:800;
    background:linear-gradient(135deg,#5683D2,#F6FAB2,#AABCA3);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
  .sec { color:#F6FAB2; font-size:.85rem; font-weight:600; text-transform:uppercase;
    letter-spacing:1px; border-bottom:1px solid #173A32; padding-bottom:5px; margin-bottom:12px; }
  .badge-ok   { background:#173A32; color:#AABCA3; padding:2px 8px; border-radius:20px; font-size:.75rem; }
  .badge-warn { background:#3A2800; color:#F6FAB2; padding:2px 8px; border-radius:20px; font-size:.75rem; }
  .badge-bad  { background:#6C0000; color:#EE7015; padding:2px 8px; border-radius:20px; font-size:.75rem; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTES ──────────────────────────────────────────────────────────────
MESES = {1:"ENE",2:"FEB",3:"MAR",4:"ABR",5:"MAY",6:"JUN",
         7:"JUL",8:"AGO",9:"SEP",10:"OCT",11:"NOV",12:"DIC"}

PROG_LABELS = {
    "DATA ANALYTICS":                "Máster Data Analytics",
    "DATA SCIENCE":                  "Máster Data Science",
    "DATA ANALYTICS & SCIENCE":      "Doble Titulación",
    "IA":                            "Máster IA & Cloud",
    "IA AVANZADA":                   "Máster IA Avanzada",
}
FUENTE_LABELS = {
    "ORGANICO":             "Orgánico",
    "GOOGLE ADS":           "Google Ads",
    "EMAIL MKT":            "Email Marketing",
    "ORGANICO RRSS":        "Orgánico RRSS",
    "REFERIDOS":            "Referidos",
    "DIRECTO":              "Directo",
    "FUENTES SIN CONEXION": "Sin Conexión",
    "FACEBOOK ADS":         "Facebook/Instagram Ads",
    "IA":                   "Fuente IA",
}

# DATOS sheet — columna → (fuente, programa)
LEAD_MAP = {
    8:('ORGANICO','DATA ANALYTICS'), 9:('ORGANICO','DATA SCIENCE'),
    10:('ORGANICO','DATA ANALYTICS & SCIENCE'), 11:('ORGANICO','IA'),
    12:('GOOGLE ADS','DATA ANALYTICS'), 13:('GOOGLE ADS','DATA SCIENCE'),
    14:('GOOGLE ADS','DATA ANALYTICS & SCIENCE'), 15:('GOOGLE ADS','IA'),
    16:('EMAIL MKT','DATA ANALYTICS'), 17:('EMAIL MKT','DATA SCIENCE'),
    18:('EMAIL MKT','DATA ANALYTICS & SCIENCE'), 19:('EMAIL MKT','IA'),
    20:('ORGANICO RRSS','DATA ANALYTICS'), 21:('ORGANICO RRSS','DATA SCIENCE'),
    22:('ORGANICO RRSS','DATA ANALYTICS & SCIENCE'), 23:('ORGANICO RRSS','IA'),
    24:('REFERIDOS','DATA ANALYTICS'), 25:('REFERIDOS','DATA SCIENCE'),
    26:('REFERIDOS','DATA ANALYTICS & SCIENCE'), 27:('REFERIDOS','IA'),
    28:('DIRECTO','DATA ANALYTICS'), 29:('DIRECTO','DATA SCIENCE'),
    30:('DIRECTO','DATA ANALYTICS & SCIENCE'), 31:('DIRECTO','IA'),
    32:('FUENTES SIN CONEXION','DATA ANALYTICS'), 33:('FUENTES SIN CONEXION','DATA SCIENCE'),
    34:('FUENTES SIN CONEXION','DATA ANALYTICS & SCIENCE'), 35:('FUENTES SIN CONEXION','IA'),
    36:('FACEBOOK ADS','DATA ANALYTICS'), 37:('IA','DATA ANALYTICS'),
    38:('FACEBOOK ADS','DATA SCIENCE'), 39:('FACEBOOK ADS','DATA ANALYTICS & SCIENCE'),
    40:('FACEBOOK ADS','IA'),
}
MATS_MAP = {
    41:('ORGANICO','DATA ANALYTICS'), 42:('ORGANICO','DATA SCIENCE'),
    43:('ORGANICO','DATA ANALYTICS & SCIENCE'), 44:('ORGANICO','IA'), 45:('ORGANICO','IA AVANZADA'),
    46:('GOOGLE ADS','DATA ANALYTICS'), 47:('GOOGLE ADS','DATA SCIENCE'),
    48:('GOOGLE ADS','DATA ANALYTICS & SCIENCE'), 49:('GOOGLE ADS','IA'), 50:('GOOGLE ADS','IA AVANZADA'),
    51:('EMAIL MKT','DATA ANALYTICS'), 52:('EMAIL MKT','DATA SCIENCE'),
    53:('EMAIL MKT','DATA ANALYTICS & SCIENCE'), 54:('EMAIL MKT','IA'), 55:('EMAIL MKT','IA AVANZADA'),
    56:('ORGANICO RRSS','DATA ANALYTICS'), 57:('ORGANICO RRSS','DATA SCIENCE'),
    58:('ORGANICO RRSS','DATA ANALYTICS & SCIENCE'), 59:('ORGANICO RRSS','IA'), 60:('ORGANICO RRSS','IA AVANZADA'),
    61:('REFERIDOS','DATA ANALYTICS'), 62:('REFERIDOS','DATA SCIENCE'),
    63:('REFERIDOS','DATA ANALYTICS & SCIENCE'), 64:('REFERIDOS','IA'), 65:('REFERIDOS','IA AVANZADA'),
    66:('DIRECTO','DATA ANALYTICS'), 67:('DIRECTO','DATA SCIENCE'),
    68:('DIRECTO','DATA ANALYTICS & SCIENCE'), 69:('DIRECTO','IA'), 70:('DIRECTO','IA AVANZADA'),
    71:('FUENTES SIN CONEXION','DATA ANALYTICS'), 72:('FUENTES SIN CONEXION','DATA SCIENCE'),
    73:('FUENTES SIN CONEXION','DATA ANALYTICS & SCIENCE'), 74:('FUENTES SIN CONEXION','IA'), 75:('FUENTES SIN CONEXION','IA AVANZADA'),
    76:('FACEBOOK ADS','DATA ANALYTICS'), 77:('FACEBOOK ADS','DATA SCIENCE'),
    78:('FACEBOOK ADS','DATA ANALYTICS & SCIENCE'), 79:('FACEBOOK ADS','IA'), 80:('FACEBOOK ADS','IA AVANZADA'),
}
FACT_MAP = {k+40: v for k, v in MATS_MAP.items()}  # cols 81-120

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def eur(v):
    try:
        v = float(v)
        if v >= 1_000_000: return f"€{v/1_000_000:.2f}M"
        if v >= 1_000: return f"€{v/1_000:.1f}K"
        return f"€{v:,.0f}"
    except: return "—"

def num(v):
    try:
        v = float(v)
        if v >= 1000: return f"{v/1000:.1f}K"
        return f"{v:,.1f}" if v != int(v) else f"{int(v):,}"
    except: return "—"

def pct(v):
    try: return f"{float(v)*100:.2f}%"
    except: return "—"

def delta_color(v, inv=False):
    try:
        f = float(v)
        ok = f >= 1.0 if not inv else f <= 1.0
        return "normal" if ok else "inverse"
    except: return "off"

# ─── PALETA CORPORATIVA PONTIA ───────────────────────────────────────────────
C = {
    "purple": "#5683D2",   # Azul Cielo PontIA
    "indigo": "#744A6E",   # Morado Oscuro PontIA
    "teal":   "#AABCA3",   # Verde Salvia PontIA
    "green":  "#AABCA3",   # Verde Salvia PontIA
    "amber":  "#BB812F",   # Ámbar Oscuro PontIA
    "red":    "#EE7015",   # Naranja Intenso PontIA
    "pink":   "#F6FAB2",   # Amarillo Botón PontIA (acento principal)
    "sky":    "#5683D2",   # Azul Cielo PontIA
    "orange": "#EE7015",   # Naranja Intenso PontIA
}
PAL = ["#5683D2","#F6FAB2","#AABCA3","#BB812F","#EE7015","#744A6E","#173A32","#808080"]
CHART = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#EFEEEA", family="Manrope,sans-serif"),
    title_font=dict(size=13, color="#F6FAB2"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#AABCA3", size=10)),
    xaxis=dict(gridcolor="#1a2d3a", zerolinecolor="#1a2d3a", tickfont=dict(color="#808080",size=10)),
    yaxis=dict(gridcolor="#1a2d3a", zerolinecolor="#1a2d3a", tickfont=dict(color="#808080",size=10)),
    margin=dict(l=5, r=15, t=40, b=5),
)

def T(fig, **kw):
    d = {**CHART, **kw}
    fig.update_layout(**d)
    return fig

# ─── PARSEO DE DATOS ─────────────────────────────────────────────────────────
@st.cache_data
def parse_datos(raw_bytes):
    """Parse DATOS sheet → df_daily with leads, mats, fact, coste per day."""
    buf = io.BytesIO(raw_bytes)
    df_raw = pd.read_excel(buf, sheet_name='DATOS', header=None)
    data = df_raw.iloc[12:377].copy()  # 365 days
    data.columns = range(len(data.columns))

    rows = []
    for _, row in data.iterrows():
        fecha = row[7]
        if not isinstance(fecha, (datetime, pd.Timestamp)):
            try: fecha = pd.to_datetime(fecha)
            except: continue
        fecha = pd.to_datetime(fecha)
        if pd.isna(fecha): continue

        def n(c): return pd.to_numeric(row.get(c, 0), errors='coerce') or 0

        rec = {
            'fecha':     fecha,
            'mes':       int(n(3)) if n(3) else fecha.month,
            'semana':    int(n(4)) if n(4) else None,
            'dia_com':   int(n(5)),
            'festivo':   1 if str(row.get(6,'')).strip() == 'x' else 0,
            'leads':     n(2),
            'mats':      n(1),
            'gasto_google':   n(125),
            'gasto_facebook': n(149),
        }
        # leads desglosados
        for col, (fuente, prog) in LEAD_MAP.items():
            rec[f'lead_{fuente}__{prog}'] = n(col)
        # mats desglosados
        for col, (fuente, prog) in MATS_MAP.items():
            rec[f'mat_{fuente}__{prog}'] = n(col)
        # facturación desglosada
        for col, (fuente, prog) in FACT_MAP.items():
            rec[f'fact_{fuente}__{prog}'] = n(col)
        rows.append(rec)

    df = pd.DataFrame(rows)
    df['gasto'] = df['gasto_google'] + df['gasto_facebook']
    # facturación total por fila
    fact_cols = [c for c in df.columns if c.startswith('fact_')]
    df['fact'] = df[fact_cols].sum(axis=1)
    return df

@st.cache_data
def parse_mes(raw_bytes):
    """Parse MES sheet → df_mes con KPIs mensuales."""
    buf = io.BytesIO(raw_bytes)
    df_raw = pd.read_excel(buf, sheet_name='MES', header=None)
    rows = []
    for i in range(5, 17):  # filas ENE-DIC
        row = df_raw.iloc[i]
        def g(c):
            v = row.iloc[c]
            try: return float(v)
            except: return None
        mes_num = g(5)
        if mes_num is None: continue
        rows.append({
            'mes':        int(mes_num),
            'mes_name':   MESES.get(int(mes_num), ""),
            'leads':      g(7),
            'mats':       g(8),
            'mats_red':   g(10),
            'fact':       g(11),
            'inversion':  g(14),
            'conversion': g(15),
            'mats_proj':  g(16),
            'fact_proj':  g(17),
            'precio_medio': g(19),
            'cpl':        g(20),
            'dias_lleva': g(21),
            'dias_total': g(22),
        })
    return pd.DataFrame(rows)

@st.cache_data
def parse_diario(raw_bytes):
    """Parse DIARIO sheet → daily detail for current month + FCST."""
    buf = io.BytesIO(raw_bytes)
    df_raw = pd.read_excel(buf, sheet_name='DIARIO', header=None)

    def get_row(idx):
        row = df_raw.iloc[idx]
        def g(c):
            try: return float(row.iloc[c])
            except: return None
        return g

    # Current month info
    ultimo_dia = df_raw.iloc[0, 1]
    mes_actual = int(df_raw.iloc[2, 3]) if pd.notna(df_raw.iloc[2, 3]) else None

    # Daily rows: from row 6 onwards, each day has fecha at col 4
    dias = []
    for i in range(6, 37):
        row = df_raw.iloc[i]
        fecha = row.iloc[4]
        if not isinstance(fecha, (datetime, pd.Timestamp)):
            try: fecha = pd.to_datetime(fecha)
            except: continue
        fecha = pd.to_datetime(fecha)
        if pd.isna(fecha): continue
        def n(c):
            try: return float(row.iloc[c])
            except: return None
        dias.append({
            'fecha':         fecha,
            'leads_organico':   n(5),
            'leads_google':     n(6),
            'leads_email':      n(7),
            'leads_facebook':   n(8),
            'leads_rrss':       n(9),
            'leads_referidos':  n(10),
            'leads_directo':    n(11),
            'leads_sin_con':    n(12),
            'leads_ia':         n(13),
            'leads_total':      n(14),
            'mats_red':         n(16),
            'mats_total':       n(18),
            'fact_red':         n(20),
            'fact_total':       n(22),
            'conversion':       n(24),
            'gasto_facebook':   n(26),
            'gasto_google':     n(27),
            'gasto_total':      n(28),
            'f_vs_g_mkt':       n(30),
            'cpl_facebook':     n(32),
            'cpl_google':       n(33),
            'cpl_media':        n(34),
        })
    df_dias = pd.DataFrame(dias)

    # TOTAL row (idx 37), TEND (38), FCST (40), vs_fcst (41)
    g_total  = get_row(37)
    g_tend   = get_row(38)
    g_fcst   = get_row(40)
    g_vs     = get_row(41)

    totales = {
        'leads': g_total(14), 'mats': g_total(18), 'fact': g_total(22),
        'gasto_facebook': g_total(26), 'gasto_google': g_total(27), 'gasto_total': g_total(28),
        'f_vs_g_pct': g_total(30), 'cpl_media': g_total(34),
        'conversion': g_total(24),
    }
    tendencia = {
        'leads': g_tend(14), 'mats': g_tend(18), 'fact': g_tend(22),
        'gasto_total': g_tend(28), 'cpl_media': g_tend(34),
    }
    fcst = {
        'leads': g_fcst(14), 'mats': g_fcst(18), 'fact': g_fcst(22),
        'gasto_total': g_fcst(28),
    }
    vs_fcst = {
        'leads': g_vs(14), 'mats': g_vs(18), 'fact': g_vs(22),
        'gasto_total': g_vs(28),
    }
    return df_dias, totales, tendencia, fcst, vs_fcst, mes_actual, ultimo_dia

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
# ── Pon aquí el ID de tu archivo de Google Drive ──────────────────────────────
# (instrucciones en GUIA_DESPLIEGUE.md)
DEFAULT_PATH = "/Users/jesusgarrido/Applications/Claude/Cuadro de Gestion  Pontia 2026.xlsx"

# ID guardado en Streamlit Secrets (no en código público)
GDRIVE_FILE_ID = st.secrets.get("GDRIVE_FILE_ID", "")

@st.cache_data(ttl=300)   # refresca cada 5 minutos desde Google Drive
def load_from_gdrive(file_id: str) -> bytes:
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content

@st.cache_data
def load_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

with st.sidebar:
    st.markdown("## 🧠 PontIA KPIs")
    st.markdown('<div style="color:#808080;font-size:.8rem;margin-bottom:12px">Dashboard de Gestión</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📂 Archivo Excel")
    uploaded = st.file_uploader(
        "Subir Excel manualmente",
        type=["xlsx"],
        help="Cuadro de Gestion Pontia 2026.xlsx",
    )

# ── Prioridad de fuente de datos ──────────────────────────────────────────────
# 1. Archivo subido manualmente  (máxima prioridad)
# 2. Google Drive               (si GDRIVE_FILE_ID está configurado)
# 3. Ruta local                 (para desarrollo en tu propio ordenador)
if uploaded:
    raw = uploaded.read()
    source_label = f"📎 {uploaded.name}"
elif GDRIVE_FILE_ID:
    try:
        raw = load_from_gdrive(GDRIVE_FILE_ID)
        source_label = "☁️ Google Drive (auto-actualizable)"
    except Exception as e:
        st.sidebar.error(f"Error al cargar desde Google Drive: {e}")
        st.stop()
else:
    try:
        raw = load_file_bytes(DEFAULT_PATH)
        source_label = "📁 Ruta local"
    except FileNotFoundError:
        st.sidebar.warning("⬆️ Sube el archivo Excel para comenzar.")
        st.stop()

# Parse
try:
    df_daily = parse_datos(raw)
    df_mes   = parse_mes(raw)
    df_dias_actual, totales_mes, tendencia_mes, fcst_mes, vs_fcst_mes, mes_actual_num, ultimo_dia = parse_diario(raw)
except Exception as e:
    st.error(f"Error al parsear el archivo: {e}")
    st.stop()

with st.sidebar:
    st.success(source_label)
    st.markdown("---")

    # Filtro de mes
    meses_con_datos = sorted(df_daily[df_daily['leads'] > 0]['mes'].unique().tolist())
    mes_names = [MESES[m] for m in meses_con_datos]
    st.markdown("### 📅 Filtros")
    sel_mes = st.multiselect("Meses", mes_names, default=mes_names)
    sel_meses_num = [k for k, v in MESES.items() if v in sel_mes]
    if not sel_meses_num:
        sel_meses_num = meses_con_datos

    # Filtro fuente
    all_fuentes = sorted(set(f for f, _ in LEAD_MAP.values()))
    fuente_labels = [FUENTE_LABELS.get(f, f) for f in all_fuentes]
    sel_fuentes_labels = st.multiselect("Fuentes", fuente_labels, default=fuente_labels)
    sel_fuentes = [f for f in all_fuentes if FUENTE_LABELS.get(f, f) in sel_fuentes_labels]
    if not sel_fuentes: sel_fuentes = all_fuentes

    # Filtro programa
    all_progs = sorted(set(p for _, p in MATS_MAP.values()))
    prog_labels_list = [PROG_LABELS.get(p, p) for p in all_progs]
    sel_progs_labels = st.multiselect("Programas", prog_labels_list, default=prog_labels_list)
    sel_progs = [p for p in all_progs if PROG_LABELS.get(p, p) in sel_progs_labels]
    if not sel_progs: sel_progs = all_progs

    st.markdown("---")
    st.markdown(f'<div style="color:#4C4C4C;font-size:.72rem;text-align:center">Datos hasta: {ultimo_dia.strftime("%d/%m/%Y") if isinstance(ultimo_dia, (datetime, pd.Timestamp)) else ultimo_dia}</div>', unsafe_allow_html=True)

# ─── FILTRAR DATOS ────────────────────────────────────────────────────────────
df_f = df_daily[df_daily['mes'].isin(sel_meses_num)].copy()

# Para leads por fuente filtrado
lead_cols_sel = [f'lead_{f}__{p}' for f, p in LEAD_MAP.values() if f in sel_fuentes and p in sel_progs]
mat_cols_sel  = [f'mat_{f}__{p}'  for f, p in MATS_MAP.values() if f in sel_fuentes and p in sel_progs]
fact_cols_sel = [f'fact_{f}__{p}' for f, p in FACT_MAP.values() if f in sel_fuentes and p in sel_progs]

total_leads = df_f[[c for c in lead_cols_sel if c in df_f.columns]].sum().sum()
total_mats  = df_f[[c for c in mat_cols_sel  if c in df_f.columns]].sum().sum()
total_fact  = df_f[[c for c in fact_cols_sel if c in df_f.columns]].sum().sum()
total_gasto = df_f[['gasto_google','gasto_facebook']].sum().sum()
conversion  = total_mats / total_leads if total_leads > 0 else 0
precio_medio= total_fact  / total_mats  if total_mats  > 0 else 0
cpl         = total_gasto / total_leads if total_leads > 0 else 0
roas        = total_fact  / total_gasto if total_gasto > 0 else 0

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero">🧠 PontIA · Dashboard KPIs 2026</div>', unsafe_allow_html=True)
mes_actual_name = MESES.get(mes_actual_num, "") if mes_actual_num else ""
if isinstance(ultimo_dia, (datetime, pd.Timestamp)):
    st.markdown(f'<div style="color:#808080;font-size:.85rem;margin-bottom:20px">Último dato: <b style="color:#F6FAB2">{ultimo_dia.strftime("%d/%m/%Y")}</b> · Mes en curso: <b style="color:#F6FAB2">{mes_actual_name}</b></div>', unsafe_allow_html=True)

# ─── KPIs GLOBALES ────────────────────────────────────────────────────────────
# Variación vs mes anterior
_meses_ord = sorted(df_mes[df_mes['leads'].notna() & (df_mes['leads'] > 0)]['mes'].tolist())
_delta_leads = _delta_mats = _delta_fact = None
if len(_meses_ord) >= 2:
    _m_ult  = _meses_ord[-1]
    _m_prev = _meses_ord[-2]
    _r_ult  = df_mes[df_mes['mes'] == _m_ult].iloc[0]
    _r_prev = df_mes[df_mes['mes'] == _m_prev].iloc[0]
    if _r_prev['leads'] and _r_prev['leads'] > 0:
        _delta_leads = f"{((_r_ult['leads'] or 0) - _r_prev['leads']) / _r_prev['leads'] * 100:+.1f}% vs {MESES[_m_prev]}"
    if _r_prev['mats'] and _r_prev['mats'] > 0:
        _delta_mats  = f"{((_r_ult['mats']  or 0) - _r_prev['mats'])  / _r_prev['mats']  * 100:+.1f}% vs {MESES[_m_prev]}"
    if _r_prev['fact'] and _r_prev['fact'] > 0:
        _delta_fact  = f"{((_r_ult['fact']  or 0) - _r_prev['fact'])  / _r_prev['fact']  * 100:+.1f}% vs {MESES[_m_prev]}"

st.markdown('<div class="sec">Resumen Acumulado (YTD)</div>', unsafe_allow_html=True)
c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
c1.metric("🎯 Leads",          num(total_leads),   delta=_delta_leads)
c2.metric("🎓 Matrículas",     num(total_mats),    delta=_delta_mats)
c3.metric("💰 Facturación",    eur(total_fact),    delta=_delta_fact)
c4.metric("📈 Conversión",     f"{conversion*100:.2f}%")
c5.metric("🏷️ Precio Medio",  eur(precio_medio))
c6.metric("💸 Gasto MKT",      eur(total_gasto))
c7.metric("📣 ROAS",           f"{roas:.1f}x")
st.markdown("<br>", unsafe_allow_html=True)

# ─── SEMÁFORO KPIs MES ACTUAL ─────────────────────────────────────────────────
def _sema(ratio):
    if ratio is None: return "#1a2d3a", "⬜", "Sin datos"
    try:
        r = float(ratio)
        if r >= 0.9: return "#0f2918", "🟢", f"{r*100:.0f}% obj."
        if r >= 0.7: return "#2a1e00", "🟡", f"{r*100:.0f}% obj."
        return "#3d0f00", "🔴", f"{r*100:.0f}% obj."
    except: return "#1a2d3a", "⬜", "Sin datos"

_vs_l = vs_fcst_mes.get('leads'); _vs_m = vs_fcst_mes.get('mats'); _vs_f = vs_fcst_mes.get('fact')
_bg_l, _ic_l, _tx_l = _sema(_vs_l)
_bg_m, _ic_m, _tx_m = _sema(_vs_m)
_bg_f, _ic_f, _tx_f = _sema(_vs_f)
_fcst_l = num(fcst_mes.get('leads') or 0)
_fcst_m = num(fcst_mes.get('mats') or 0)
_fcst_f = eur(fcst_mes.get('fact') or 0)
st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px">
  <div style="background:{_bg_l};border:1px solid #1a2d3a;border-radius:10px;padding:12px 16px;display:flex;align-items:center;gap:12px">
    <span style="font-size:1.5rem">{_ic_l}</span>
    <div>
      <div style="color:#808080;font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.6px">Leads · Mes actual vs FCST</div>
      <div style="color:#EFEEEA;font-weight:700;font-size:.92rem">{_tx_l} &nbsp;·&nbsp; Obj: {_fcst_l}</div>
    </div>
  </div>
  <div style="background:{_bg_m};border:1px solid #1a2d3a;border-radius:10px;padding:12px 16px;display:flex;align-items:center;gap:12px">
    <span style="font-size:1.5rem">{_ic_m}</span>
    <div>
      <div style="color:#808080;font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.6px">Matrículas · Mes actual vs FCST</div>
      <div style="color:#EFEEEA;font-weight:700;font-size:.92rem">{_tx_m} &nbsp;·&nbsp; Obj: {_fcst_m}</div>
    </div>
  </div>
  <div style="background:{_bg_f};border:1px solid #1a2d3a;border-radius:10px;padding:12px 16px;display:flex;align-items:center;gap:12px">
    <span style="font-size:1.5rem">{_ic_f}</span>
    <div>
      <div style="color:#808080;font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:.6px">Facturación · Mes actual vs FCST</div>
      <div style="color:#EFEEEA;font-weight:700;font-size:.92rem">{_tx_f} &nbsp;·&nbsp; Obj: {_fcst_f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📅 Mes a Mes",
    "🎯 Leads",
    "🎓 Matrículas",
    "💰 Facturación",
    "📣 Marketing",
    "📆 Mes Actual",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 · MES A MES
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="sec">Evolución Mensual de KPIs</div>', unsafe_allow_html=True)

    # Usar df_mes para los datos mensuales (incluye datos projectados del MES sheet)
    df_m = df_mes[df_mes['mes'].isin(meses_con_datos)].copy()
    df_m['mes_name'] = df_m['mes'].map(MESES)

    if not df_m.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_m['mes_name'], y=df_m['leads'],
                name='Leads', marker_color=C['purple'], opacity=.85,
            ))
            fig.add_trace(go.Scatter(
                x=df_m['mes_name'], y=df_m['leads'].rolling(2, min_periods=1).mean(),
                name='Media móvil', line=dict(color=C['teal'], width=2, dash='dot'),
            ))
            T(fig).update_layout(title="📊 Leads por Mes")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_m['mes_name'], y=df_m['mats'],
                name='Matrículas reales', marker_color=C['indigo'], opacity=.85,
            ))
            # proyección
            mask_proj = df_m['mats_proj'].notna() & (df_m['mats_proj'] != df_m['mats'])
            if mask_proj.any():
                fig.add_trace(go.Bar(
                    x=df_m.loc[mask_proj, 'mes_name'],
                    y=df_m.loc[mask_proj, 'mats_proj'],
                    name='Proyección fin mes', marker_color=C['teal'],
                    opacity=.5, marker_pattern_shape='/',
                ))
            T(fig).update_layout(title="🎓 Matrículas por Mes (real vs proyección)")
            st.plotly_chart(fig, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_m['mes_name'], y=df_m['fact'],
                name='Facturación', marker_color=C['green'], opacity=.85,
            ))
            if df_m['fact_proj'].notna().any():
                fig.add_trace(go.Bar(
                    x=df_m['mes_name'], y=df_m['fact_proj'],
                    name='Proyección', marker_color=C['amber'], opacity=.5,
                    marker_pattern_shape='/',
                ))
            T(fig).update_layout(title="💰 Facturación por Mes")
            st.plotly_chart(fig, use_container_width=True)

        with col4:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_m['mes_name'], y=df_m['inversion'],
                name='Inversión MKT', marker_color=C['red'], opacity=.75,
                yaxis='y',
            ))
            fig.add_trace(go.Scatter(
                x=df_m['mes_name'], y=df_m['cpl'],
                name='CPL (€)', line=dict(color=C['amber'], width=2),
                yaxis='y2',
            ))
            T(fig).update_layout(
                title="📣 Inversión MKT y CPL por Mes",
                yaxis2=dict(overlaying='y', side='right',
                            gridcolor='#1a2d3a', tickfont=dict(color='#808080', size=10)),
            )
            st.plotly_chart(fig, use_container_width=True)

        col5, col6 = st.columns(2)

        with col5:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_m['mes_name'], y=df_m['conversion'].apply(lambda x: x*100 if x else None),
                name='Conversión %', line=dict(color=C['pink'], width=2),
                fill='tozeroy', fillcolor='rgba(246,250,178,0.08)',
                mode='lines+markers',
            ))
            T(fig).update_layout(title="📈 Tasa de Conversión por Mes")
            fig.update_yaxes(ticksuffix='%')
            st.plotly_chart(fig, use_container_width=True)

        with col6:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_m['mes_name'], y=df_m['precio_medio'],
                name='Precio Medio', line=dict(color=C['sky'], width=2),
                fill='tozeroy', fillcolor='rgba(86,131,210,0.1)',
                mode='lines+markers',
            ))
            T(fig).update_layout(title="🏷️ Precio Medio por Mes (€)")
            fig.update_yaxes(tickprefix='€')
            st.plotly_chart(fig, use_container_width=True)

    # Tabla resumen mensual
    st.markdown('<div class="sec">Tabla Resumen Mensual</div>', unsafe_allow_html=True)
    tbl = df_mes[df_mes['mes'].isin(meses_con_datos)].copy()
    tbl['mes_name'] = tbl['mes'].map(MESES)
    display = pd.DataFrame({
        'Mes':          tbl['mes_name'],
        'Leads':        tbl['leads'].apply(lambda x: num(x) if x else '—'),
        'Matrículas':   tbl['mats'].apply(lambda x: f"{x:.1f}" if x else '—'),
        'Facturación':  tbl['fact'].apply(lambda x: eur(x) if x else '—'),
        'Inversión':    tbl['inversion'].apply(lambda x: eur(x) if x else '—'),
        'Conversión':   tbl['conversion'].apply(lambda x: f"{x*100:.2f}%" if x else '—'),
        'Precio Medio': tbl['precio_medio'].apply(lambda x: eur(x) if x else '—'),
        'CPL':          tbl['cpl'].apply(lambda x: eur(x) if x else '—'),
        'Días Com.':    tbl.apply(lambda r: f"{int(r['dias_lleva'])}/{int(r['dias_total'])}" if pd.notna(r['dias_lleva']) and pd.notna(r['dias_total']) else '—', axis=1),
    })
    st.dataframe(display, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 · LEADS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="sec">Análisis de Leads</div>', unsafe_allow_html=True)

    # KPIs leads
    c1,c2,c3,c4 = st.columns(4)
    leads_google   = df_f[[c for c in df_f.columns if 'lead_GOOGLE ADS__' in c]].sum().sum()
    leads_facebook = df_f[[c for c in df_f.columns if 'lead_FACEBOOK ADS__' in c]].sum().sum()
    leads_organico = df_f[[c for c in df_f.columns if 'lead_ORGANICO__' in c or 'lead_ORGANICO RRSS__' in c]].sum().sum()
    leads_directo  = df_f[[c for c in df_f.columns if 'lead_DIRECTO__' in c]].sum().sum()
    c1.metric("Google Ads",          num(leads_google))
    c2.metric("Facebook/Instagram",  num(leads_facebook))
    c3.metric("Orgánico + RRSS",     num(leads_organico))
    c4.metric("Directo",             num(leads_directo))
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Leads por fuente (total YTD)
    with col1:
        fuente_leads = {}
        for col_idx, (fuente, prog) in LEAD_MAP.items():
            col_name = f'lead_{fuente}__{prog}'
            if col_name in df_f.columns:
                fuente_leads[FUENTE_LABELS.get(fuente, fuente)] = \
                    fuente_leads.get(FUENTE_LABELS.get(fuente, fuente), 0) + df_f[col_name].sum()
        df_fl = pd.DataFrame(list(fuente_leads.items()), columns=['fuente','leads']).sort_values('leads', ascending=False)
        fig = px.bar(df_fl, x='fuente', y='leads', title='🔍 Leads por Fuente (YTD)',
                     color='leads', color_continuous_scale=['#111E2D','#5683D2'],
                     text=df_fl['leads'].apply(lambda x: num(x)))
        T(fig).update_traces(textposition='outside').update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Leads por programa
    with col2:
        prog_leads = {}
        for col_idx, (fuente, prog) in LEAD_MAP.items():
            col_name = f'lead_{fuente}__{prog}'
            if col_name in df_f.columns:
                prog_leads[PROG_LABELS.get(prog, prog)] = \
                    prog_leads.get(PROG_LABELS.get(prog, prog), 0) + df_f[col_name].sum()
        df_pl = pd.DataFrame(list(prog_leads.items()), columns=['programa','leads'])
        df_pl = df_pl[df_pl['leads'] > 0].sort_values('leads', ascending=False)
        fig = px.pie(df_pl, values='leads', names='programa',
                     title='🎓 Leads por Programa', color_discrete_sequence=PAL, hole=0.45)
        T(fig)
        st.plotly_chart(fig, use_container_width=True)

    # Evolución mensual de leads por fuente
    col3, col4 = st.columns(2)

    with col3:
        # Leads diarios → agregar por mes × fuente
        records = []
        for col_idx, (fuente, prog) in LEAD_MAP.items():
            col_name = f'lead_{fuente}__{prog}'
            if col_name not in df_f.columns: continue
            tmp = df_f.groupby('mes')[col_name].sum().reset_index()
            tmp['fuente'] = FUENTE_LABELS.get(fuente, fuente)
            tmp.rename(columns={col_name: 'leads'}, inplace=True)
            records.append(tmp)
        if records:
            df_ev = pd.concat(records).groupby(['mes','fuente'])['leads'].sum().reset_index()
            df_ev['mes_name'] = df_ev['mes'].map(MESES)
            # Top 5 fuentes
            top5 = df_ev.groupby('fuente')['leads'].sum().nlargest(5).index.tolist()
            df_ev5 = df_ev[df_ev['fuente'].isin(top5)]
            fig = px.line(df_ev5, x='mes_name', y='leads', color='fuente',
                          title='📅 Evolución Leads por Fuente (Top 5)',
                          color_discrete_sequence=PAL, markers=True)
            T(fig)
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        # Heatmap fuente × mes
        if records:
            hm = df_ev.pivot_table(index='fuente', columns='mes_name', values='leads', fill_value=0)
            # Ordenar meses correctamente
            mes_ord = [MESES[m] for m in sorted(MESES.keys()) if MESES[m] in hm.columns]
            hm = hm[mes_ord]
            fig = px.imshow(hm, title='🗺️ Heatmap Leads: Fuente × Mes',
                            color_continuous_scale=['#0D1820','#173A32','#5683D2'],
                            aspect='auto', text_auto=True)
            T(fig).update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    # CPL por fuente (basado en gasto total / leads por fuente pagada)
    st.markdown('<div class="sec">CPL detallado por fuente de pago</div>', unsafe_allow_html=True)
    col5, col6 = st.columns(2)

    with col5:
        # Leads pagados: Google ADS y Facebook ADS
        cpl_data = {
            'Google Ads': {
                'gasto': df_f['gasto_google'].sum(),
                'leads': df_f[[c for c in df_f.columns if 'lead_GOOGLE ADS__' in c]].sum().sum(),
            },
            'Facebook/Instagram Ads': {
                'gasto': df_f['gasto_facebook'].sum(),
                'leads': df_f[[c for c in df_f.columns if 'lead_FACEBOOK ADS__' in c]].sum().sum(),
            },
        }
        cpl_rows = []
        for fuente, vals in cpl_data.items():
            cpl_v = vals['gasto'] / vals['leads'] if vals['leads'] > 0 else 0
            cpl_rows.append({'Fuente': fuente, 'Gasto (€)': vals['gasto'], 'Leads': vals['leads'], 'CPL (€)': cpl_v})
        df_cpl = pd.DataFrame(cpl_rows)
        fig = go.Figure(go.Bar(
            x=df_cpl['Fuente'], y=df_cpl['CPL (€)'],
            marker_color=[C['sky'], C['pink']],
            text=[f"€{v:.2f}" for v in df_cpl['CPL (€)']],
            textposition='outside',
        ))
        T(fig).update_layout(title='💸 CPL por Canal de Pago')
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        # Evolución CPL mensual (del sheet MES)
        df_m_cpl = df_mes[df_mes['mes'].isin(meses_con_datos) & df_mes['cpl'].notna()].copy()
        df_m_cpl['mes_name'] = df_m_cpl['mes'].map(MESES)
        if not df_m_cpl.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_m_cpl['mes_name'], y=df_m_cpl['cpl'],
                mode='lines+markers', name='CPL Medio',
                line=dict(color=C['amber'], width=2),
                fill='tozeroy', fillcolor='rgba(187,129,47,0.1)',
            ))
            T(fig).update_layout(title='📉 Evolución CPL Mensual (€)')
            fig.update_yaxes(tickprefix='€')
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 · MATRÍCULAS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="sec">Análisis de Matrículas</div>', unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Matrículas", num(total_mats))
    c2.metric("Conversión", f"{conversion*100:.2f}%")
    c3.metric("Precio Medio", eur(precio_medio))
    prog_top = max(
        {PROG_LABELS.get(p,p): df_f[[c for c in df_f.columns if f'mat__{p}' in c]].sum().sum()
         for p in sel_progs}.items(), key=lambda x: x[1], default=('—', 0)
    )[0] if sel_progs else '—'
    c4.metric("Programa Líder", prog_top)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Mats por fuente
    with col1:
        fuente_mats = {}
        for col_idx, (fuente, prog) in MATS_MAP.items():
            col_name = f'mat_{fuente}__{prog}'
            if col_name in df_f.columns and fuente in sel_fuentes and prog in sel_progs:
                lbl = FUENTE_LABELS.get(fuente, fuente)
                fuente_mats[lbl] = fuente_mats.get(lbl, 0) + df_f[col_name].sum()
        df_fm = pd.DataFrame(list(fuente_mats.items()), columns=['fuente','mats'])
        df_fm = df_fm[df_fm['mats'] > 0].sort_values('mats', ascending=False)
        fig = px.bar(df_fm, x='mats', y='fuente', orientation='h',
                     title='📊 Matrículas por Fuente',
                     color='mats', color_continuous_scale=['#111E2D','#744A6E'],
                     text=df_fm['mats'].apply(lambda x: f"{x:.0f}"))
        T(fig).update_traces(textposition='outside').update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Mats por programa
    with col2:
        prog_mats = {}
        for col_idx, (fuente, prog) in MATS_MAP.items():
            col_name = f'mat_{fuente}__{prog}'
            if col_name in df_f.columns and prog in sel_progs:
                lbl = PROG_LABELS.get(prog, prog)
                prog_mats[lbl] = prog_mats.get(lbl, 0) + df_f[col_name].sum()
        df_pm = pd.DataFrame(list(prog_mats.items()), columns=['programa','mats'])
        df_pm = df_pm[df_pm['mats'] > 0]
        fig = px.pie(df_pm, values='mats', names='programa',
                     title='🎓 Matrículas por Programa',
                     color_discrete_sequence=PAL, hole=0.45)
        T(fig)
        st.plotly_chart(fig, use_container_width=True)

    # Evolución mensual mats
    col3, col4 = st.columns(2)

    with col3:
        # Mats por mes × programa
        mat_recs = []
        for col_idx, (fuente, prog) in MATS_MAP.items():
            col_name = f'mat_{fuente}__{prog}'
            if col_name not in df_f.columns or prog not in sel_progs: continue
            tmp = df_f.groupby('mes')[col_name].sum().reset_index()
            tmp['programa'] = PROG_LABELS.get(prog, prog)
            tmp.rename(columns={col_name: 'mats'}, inplace=True)
            mat_recs.append(tmp)
        if mat_recs:
            df_ev_m = pd.concat(mat_recs).groupby(['mes','programa'])['mats'].sum().reset_index()
            df_ev_m['mes_name'] = df_ev_m['mes'].map(MESES)
            df_ev_m = df_ev_m[df_ev_m['mats'] > 0]
            fig = px.bar(df_ev_m, x='mes_name', y='mats', color='programa',
                         title='📅 Matrículas por Mes y Programa',
                         color_discrete_sequence=PAL, barmode='stack')
            T(fig)
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        # Heatmap fuente × programa (mats)
        hm_data = []
        for col_idx, (fuente, prog) in MATS_MAP.items():
            col_name = f'mat_{fuente}__{prog}'
            if col_name in df_f.columns:
                hm_data.append({
                    'fuente':   FUENTE_LABELS.get(fuente, fuente),
                    'programa': PROG_LABELS.get(prog, prog),
                    'mats':     df_f[col_name].sum(),
                })
        df_hm = pd.DataFrame(hm_data)
        if not df_hm.empty:
            pivot = df_hm.pivot_table(index='fuente', columns='programa', values='mats', fill_value=0)
            fig = px.imshow(pivot, title='🗺️ Heatmap Mats: Fuente × Programa',
                            color_continuous_scale=['#0D1820','#111E2D','#744A6E'],
                            aspect='auto', text_auto='.0f')
            T(fig).update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    # ── CONVERSIÓN POR FUENTE + EMBUDO ────────────────────────────────────────
    st.markdown('<div class="sec">Conversión por Fuente y Embudo</div>', unsafe_allow_html=True)
    col5, col6 = st.columns(2)

    with col5:
        conv_data = []
        for fuente in all_fuentes:
            lbl = FUENTE_LABELS.get(fuente, fuente)
            lead_cols_f = [f'lead_{fuente}__{p}' for p in set(p for _, p in LEAD_MAP.values()) if f'lead_{fuente}__{p}' in df_f.columns]
            mat_cols_f  = [f'mat_{fuente}__{p}'  for p in set(p for _, p in MATS_MAP.values()) if f'mat_{fuente}__{p}'  in df_f.columns]
            tot_leads_f = df_f[lead_cols_f].sum().sum() if lead_cols_f else 0
            tot_mats_f  = df_f[mat_cols_f].sum().sum()  if mat_cols_f  else 0
            if tot_leads_f > 0:
                conv_data.append({
                    'Fuente': lbl,
                    'Leads': tot_leads_f,
                    'Matrículas': tot_mats_f,
                    'Conv %': tot_mats_f / tot_leads_f * 100,
                })
        if conv_data:
            df_conv = pd.DataFrame(conv_data).sort_values('Conv %', ascending=True)
            norm = df_conv['Conv %'].max() or 1
            colors = [
                f"rgba({int(86 + (246-86)*v/norm)},{int(131 + (250-131)*v/norm)},{int(210 + (178-210)*v/norm)},0.85)"
                for v in df_conv['Conv %']
            ]
            fig = go.Figure(go.Bar(
                x=df_conv['Conv %'], y=df_conv['Fuente'], orientation='h',
                marker_color=colors,
                text=[f"{v:.1f}%" for v in df_conv['Conv %']],
                textposition='outside',
                customdata=np.stack([df_conv['Leads'], df_conv['Matrículas']], axis=1),
                hovertemplate='<b>%{y}</b><br>Conv: %{x:.1f}%<br>Leads: %{customdata[0]:.0f}<br>Mats: %{customdata[1]:.0f}<extra></extra>',
            ))
            T(fig).update_layout(title='📊 Tasa de Conversión por Fuente (Leads → Mats)')
            fig.update_xaxes(ticksuffix='%')
            st.plotly_chart(fig, use_container_width=True)

    with col6:
        # Funnel: Leads → Matrículas global
        if total_leads > 0:
            fig = go.Figure(go.Funnel(
                y=['🎯 Leads captados', '🎓 Matrículas cerradas'],
                x=[total_leads, total_mats],
                textposition='inside',
                textinfo='value+percent initial',
                marker=dict(color=[C['sky'], C['indigo']]),
                connector=dict(line=dict(color='#1a2d3a', width=1)),
            ))
            T(fig).update_layout(title='🔽 Embudo Global: Leads → Matrículas')
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 · FACTURACIÓN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="sec">Análisis de Facturación</div>', unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    c1.metric("Facturación Total",  eur(total_fact))
    c2.metric("Precio Medio",       eur(precio_medio))
    c3.metric("ROAS",               f"{roas:.1f}x")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Fact por fuente
        fuente_fact = {}
        for col_idx, (fuente, prog) in FACT_MAP.items():
            col_name = f'fact_{fuente}__{prog}'
            if col_name in df_f.columns and fuente in sel_fuentes and prog in sel_progs:
                lbl = FUENTE_LABELS.get(fuente, fuente)
                fuente_fact[lbl] = fuente_fact.get(lbl, 0) + df_f[col_name].sum()
        df_ff = pd.DataFrame(list(fuente_fact.items()), columns=['fuente','fact'])
        df_ff = df_ff[df_ff['fact'] > 0].sort_values('fact', ascending=False)
        fig = px.bar(df_ff, x='fact', y='fuente', orientation='h',
                     title='💰 Facturación por Fuente',
                     color='fact', color_continuous_scale=['#173A32','#AABCA3'],
                     text=df_ff['fact'].apply(eur))
        T(fig).update_traces(textposition='outside').update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Fact por programa
        prog_fact = {}
        for col_idx, (fuente, prog) in FACT_MAP.items():
            col_name = f'fact_{fuente}__{prog}'
            if col_name in df_f.columns and prog in sel_progs:
                lbl = PROG_LABELS.get(prog, prog)
                prog_fact[lbl] = prog_fact.get(lbl, 0) + df_f[col_name].sum()
        df_pf = pd.DataFrame(list(prog_fact.items()), columns=['programa','fact'])
        df_pf = df_pf[df_pf['fact'] > 0]
        fig = px.pie(df_pf, values='fact', names='programa',
                     title='🎓 Facturación por Programa',
                     color_discrete_sequence=PAL, hole=0.45)
        T(fig)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Evolución mensual facturación (del MES sheet)
        df_m_f = df_mes[df_mes['mes'].isin(meses_con_datos)].copy()
        df_m_f['mes_name'] = df_m_f['mes'].map(MESES)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_m_f['mes_name'], y=df_m_f['fact'],
            name='Real', marker_color=C['green'], opacity=.85,
        ))
        if df_m_f['fact_proj'].notna().any():
            fig.add_trace(go.Bar(
                x=df_m_f['mes_name'], y=df_m_f['fact_proj'],
                name='Proyectado', marker_color=C['amber'],
                opacity=.5, marker_pattern_shape='/',
            ))
        T(fig).update_layout(title='📈 Evolución Facturación Mensual')
        fig.update_yaxes(tickprefix='€')
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        # Precio medio por mes
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_m_f['mes_name'],
            y=df_m_f['precio_medio'],
            mode='lines+markers',
            name='Precio Medio',
            line=dict(color=C['sky'], width=2),
            fill='tozeroy', fillcolor='rgba(86,131,210,0.1)',
        ))
        T(fig).update_layout(title='🏷️ Precio Medio Mensual (€)')
        fig.update_yaxes(tickprefix='€')
        st.plotly_chart(fig, use_container_width=True)

    # Tabla fact por fuente × programa
    st.markdown('<div class="sec">Detalle Facturación por Fuente y Programa</div>', unsafe_allow_html=True)
    hm_fact = []
    for col_idx, (fuente, prog) in FACT_MAP.items():
        col_name = f'fact_{fuente}__{prog}'
        if col_name in df_f.columns:
            v = df_f[col_name].sum()
            if v > 0:
                hm_fact.append({
                    'Fuente':    FUENTE_LABELS.get(fuente, fuente),
                    'Programa':  PROG_LABELS.get(prog, prog),
                    'Fact (€)':  eur(v),
                    '_sort':     v,
                })
    if hm_fact:
        df_tbl = pd.DataFrame(hm_fact).sort_values('_sort', ascending=False).drop('_sort', axis=1)
        st.dataframe(df_tbl, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 · MARKETING
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="sec">Análisis de Marketing Digital</div>', unsafe_allow_html=True)

    gasto_google   = df_f['gasto_google'].sum()
    gasto_facebook = df_f['gasto_facebook'].sum()
    leads_google_t = df_f[[c for c in df_f.columns if 'lead_GOOGLE ADS__' in c]].sum().sum()
    leads_fb_t     = df_f[[c for c in df_f.columns if 'lead_FACEBOOK ADS__' in c]].sum().sum()
    fact_google    = df_f[[c for c in df_f.columns if 'fact_GOOGLE ADS__' in c]].sum().sum()
    fact_fb        = df_f[[c for c in df_f.columns if 'fact_FACEBOOK ADS__' in c]].sum().sum()
    cpl_google     = gasto_google  / leads_google_t if leads_google_t > 0 else 0
    cpl_facebook   = gasto_facebook / leads_fb_t    if leads_fb_t    > 0 else 0
    roas_google    = fact_google   / gasto_google   if gasto_google   > 0 else 0
    roas_facebook  = fact_fb       / gasto_facebook if gasto_facebook > 0 else 0
    f_vs_g         = total_fact    / total_gasto    if total_gasto    > 0 else 0

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Gasto Google Ads",   eur(gasto_google))
    c2.metric("Gasto Facebook Ads", eur(gasto_facebook))
    c3.metric("CPL Google",         eur(cpl_google))
    c4.metric("CPL Facebook",       eur(cpl_facebook))
    c5.metric("ROAS Google",        f"{roas_google:.1f}x")
    c6.metric("ROAS Facebook",      f"{roas_facebook:.1f}x")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Gasto vs Facturación por canal
        fig = go.Figure()
        canales = ['Google Ads', 'Facebook/Instagram']
        gastos  = [gasto_google, gasto_facebook]
        facts   = [fact_google,  fact_fb]
        fig.add_trace(go.Bar(name='Gasto', x=canales, y=gastos,
                             marker_color=C['red'], opacity=.8))
        fig.add_trace(go.Bar(name='Facturación', x=canales, y=facts,
                             marker_color=C['green'], opacity=.8))
        T(fig).update_layout(title='💸 Gasto vs Facturación por Canal', barmode='group')
        fig.update_yaxes(tickprefix='€')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # ROAS por canal con línea objetivo
        fig = go.Figure()
        roas_vals = [roas_google, roas_facebook]
        colors = [C['green'] if r >= 3 else C['amber'] if r >= 2 else C['red'] for r in roas_vals]
        fig.add_trace(go.Bar(x=canales, y=roas_vals,
                             marker_color=colors,
                             text=[f"{v:.1f}x" for v in roas_vals],
                             textposition='outside'))
        fig.add_hline(y=3, line_dash='dash', line_color=C['green'],
                      annotation_text='Objetivo ROAS 3x',
                      annotation_font_color='#AABCA3')
        T(fig).update_layout(title='📣 ROAS por Canal')
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Evolución mensual gasto Google + Facebook
        df_m_gasto = df_f.groupby('mes').agg(
            gasto_google=('gasto_google','sum'),
            gasto_facebook=('gasto_facebook','sum'),
        ).reset_index()
        df_m_gasto['mes_name'] = df_m_gasto['mes'].map(MESES)
        df_m_gasto['gasto_total'] = df_m_gasto['gasto_google'] + df_m_gasto['gasto_facebook']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_m_gasto['mes_name'], y=df_m_gasto['gasto_google'],
                             name='Google Ads', marker_color=C['sky'], opacity=.85))
        fig.add_trace(go.Bar(x=df_m_gasto['mes_name'], y=df_m_gasto['gasto_facebook'],
                             name='Facebook Ads', marker_color=C['indigo'], opacity=.85))
        T(fig).update_layout(title='📅 Gasto MKT Mensual por Canal', barmode='stack')
        fig.update_yaxes(tickprefix='€')
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        # Facturación/Gasto ratio mensual (F vs G MKT)
        df_m_fg = df_f.groupby('mes').agg(
            fact=('fact','sum'),
            gasto=('gasto','sum'),
        ).reset_index()
        df_m_fg['mes_name'] = df_m_fg['mes'].map(MESES)
        df_m_fg['roas'] = df_m_fg['fact'] / df_m_fg['gasto'].replace(0, np.nan)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_m_fg['mes_name'], y=df_m_fg['roas'],
            mode='lines+markers', name='ROAS',
            line=dict(color=C['teal'], width=2),
            fill='tozeroy', fillcolor='rgba(170,188,163,0.1)',
        ))
        fig.add_hline(y=3, line_dash='dash', line_color=C['green'],
                      annotation_text='Objetivo 3x')
        T(fig).update_layout(title='📈 Evolución ROAS Mensual')
        st.plotly_chart(fig, use_container_width=True)

    # Tabla resumen marketing por mes
    st.markdown('<div class="sec">Tabla Marketing por Mes</div>', unsafe_allow_html=True)
    df_mkt_tbl = df_f.groupby('mes').agg(
        gasto_google=('gasto_google','sum'),
        gasto_facebook=('gasto_facebook','sum'),
    ).reset_index()
    df_mkt_tbl['mes_name']    = df_mkt_tbl['mes'].map(MESES)
    df_mkt_tbl['gasto_total'] = df_mkt_tbl['gasto_google'] + df_mkt_tbl['gasto_facebook']
    # Add leads from df_f
    leads_g_m  = df_f.groupby('mes')[[c for c in df_f.columns if 'lead_GOOGLE ADS__' in c]].sum().sum(axis=1)
    leads_fb_m = df_f.groupby('mes')[[c for c in df_f.columns if 'lead_FACEBOOK ADS__' in c]].sum().sum(axis=1)
    df_mkt_tbl = df_mkt_tbl.join(leads_g_m.rename('leads_google'), on='mes')
    df_mkt_tbl = df_mkt_tbl.join(leads_fb_m.rename('leads_facebook'), on='mes')
    df_mkt_tbl['cpl_google']   = df_mkt_tbl['gasto_google']   / df_mkt_tbl['leads_google'].replace(0, np.nan)
    df_mkt_tbl['cpl_facebook'] = df_mkt_tbl['gasto_facebook'] / df_mkt_tbl['leads_facebook'].replace(0, np.nan)
    show = pd.DataFrame({
        'Mes':              df_mkt_tbl['mes_name'],
        'Gasto Google':     df_mkt_tbl['gasto_google'].apply(eur),
        'Gasto Facebook':   df_mkt_tbl['gasto_facebook'].apply(eur),
        'Gasto Total':      df_mkt_tbl['gasto_total'].apply(eur),
        'Leads Google':     df_mkt_tbl['leads_google'].apply(lambda x: f"{x:.0f}"),
        'Leads Facebook':   df_mkt_tbl['leads_facebook'].apply(lambda x: f"{x:.0f}"),
        'CPL Google':       df_mkt_tbl['cpl_google'].apply(lambda x: eur(x) if pd.notna(x) else '—'),
        'CPL Facebook':     df_mkt_tbl['cpl_facebook'].apply(lambda x: eur(x) if pd.notna(x) else '—'),
    })
    st.dataframe(show, use_container_width=True, hide_index=True)

    # ── COSTE POR MATRÍCULA ────────────────────────────────────────────────────
    st.markdown('<div class="sec">Coste por Matrícula por Canal</div>', unsafe_allow_html=True)
    col5, col6 = st.columns(2)

    _cpm_data = []
    for _fuente_mkt, _gasto_mkt, _lbl_mkt in [
        ('GOOGLE ADS',   gasto_google,   'Google Ads'),
        ('FACEBOOK ADS', gasto_facebook, 'Facebook/Instagram'),
    ]:
        _mat_cols_mkt = [c for c in df_f.columns if f'mat_{_fuente_mkt}__' in c]
        _tot_mats_mkt = df_f[_mat_cols_mkt].sum().sum() if _mat_cols_mkt else 0
        _cpm_v = _gasto_mkt / _tot_mats_mkt if _tot_mats_mkt > 0 else 0
        _cpm_data.append({'Canal': _lbl_mkt, 'Gasto': _gasto_mkt, 'Mats': _tot_mats_mkt, 'Coste/Mat': _cpm_v})
    df_cpm = pd.DataFrame(_cpm_data)

    with col5:
        fig = go.Figure(go.Bar(
            x=df_cpm['Canal'],
            y=df_cpm['Coste/Mat'],
            marker_color=[C['sky'], C['indigo']],
            text=[eur(v) if v > 0 else '—' for v in df_cpm['Coste/Mat']],
            textposition='outside',
            customdata=np.stack([df_cpm['Gasto'], df_cpm['Mats']], axis=1),
            hovertemplate='<b>%{x}</b><br>Coste/Mat: %{y:.0f}€<br>Gasto: %{customdata[0]:.0f}€<br>Mats: %{customdata[1]:.0f}<extra></extra>',
        ))
        T(fig).update_layout(title='💸 Coste por Matrícula por Canal Pagado')
        fig.update_yaxes(tickprefix='€')
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        _total_cpm = total_gasto / total_mats if total_mats > 0 else 0
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("📊 Coste Medio por Matrícula (todos los canales)", eur(_total_cpm))
        st.markdown("<br>", unsafe_allow_html=True)
        _tbl_cpm = pd.DataFrame({
            'Canal':        df_cpm['Canal'],
            'Gasto':        df_cpm['Gasto'].apply(eur),
            'Matrículas':   df_cpm['Mats'].apply(lambda x: f"{x:.0f}"),
            'Coste/Mat':    df_cpm['Coste/Mat'].apply(lambda x: eur(x) if x > 0 else '—'),
        })
        st.dataframe(_tbl_cpm, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 · MES ACTUAL (detalle diario + FCST)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown(f'<div class="sec">Detalle Mes Actual: {mes_actual_name}</div>', unsafe_allow_html=True)

    # KPIs vs FCST
    st.markdown("#### Real vs Objetivo (FCST)")
    c1,c2,c3,c4 = st.columns(4)

    def vs_badge(ratio):
        if ratio is None: return ""
        try:
            r = float(ratio)
            if r >= 0.9: return f'<span class="badge-ok">✓ {r*100:.0f}%</span>'
            if r >= 0.7: return f'<span class="badge-warn">⚡ {r*100:.0f}%</span>'
            return f'<span class="badge-bad">⚠ {r*100:.0f}%</span>'
        except: return ""

    def fcst_metric(col, label, real, fcst_val, ratio):
        fcst_str = num(fcst_val) if fcst_val else '—'
        badge = vs_badge(ratio)
        col.metric(
            label,
            num(real) if real else '—',
            delta=f"Obj: {fcst_str}",
        )
        col.markdown(badge, unsafe_allow_html=True)

    fcst_metric(c1, "🎯 Leads",     totales_mes.get('leads'), fcst_mes.get('leads'),   vs_fcst_mes.get('leads'))
    fcst_metric(c2, "🎓 Matrículas",totales_mes.get('mats'),  fcst_mes.get('mats'),    vs_fcst_mes.get('mats'))
    fcst_metric(c3, "💰 Fact (€)",  totales_mes.get('fact'),  fcst_mes.get('fact'),    vs_fcst_mes.get('fact'))
    fcst_metric(c4, "💸 Gasto MKT", totales_mes.get('gasto_total'), fcst_mes.get('gasto_total'), vs_fcst_mes.get('gasto_total'))

    st.markdown("<br>", unsafe_allow_html=True)

    # Métricas adicionales del mes
    c5,c6,c7 = st.columns(3)
    c5.metric("📈 Conversión",     pct(totales_mes.get('conversion', 0)))
    c6.metric("💡 CPL Medio",      eur(totales_mes.get('cpl_media', 0)))
    c7.metric("💰 F vs G MKT",     f"{(totales_mes.get('f_vs_g_pct') or 0)*100:.1f}%" if totales_mes.get('f_vs_g_pct') else '—')

    st.markdown("<br>", unsafe_allow_html=True)

    if not df_dias_actual.empty:
        col1, col2 = st.columns(2)

        # Leads diarios por fuente
        with col1:
            df_d = df_dias_actual[df_dias_actual['leads_total'].notna() & (df_dias_actual['leads_total'] > 0)].copy()
            if not df_d.empty:
                fig = go.Figure()
                fuente_day_cols = {
                    'Orgánico':   'leads_organico',
                    'Google Ads': 'leads_google',
                    'Facebook':   'leads_facebook',
                    'Email MKT':  'leads_email',
                    'Directo':    'leads_directo',
                    'RRSS':       'leads_rrss',
                }
                for i, (lbl, col_n) in enumerate(fuente_day_cols.items()):
                    if col_n in df_d.columns:
                        fig.add_trace(go.Bar(
                            x=df_d['fecha'].dt.strftime('%d'),
                            y=df_d[col_n],
                            name=lbl,
                            marker_color=PAL[i % len(PAL)],
                        ))
                T(fig).update_layout(title=f'📅 Leads Diarios {mes_actual_name} por Fuente', barmode='stack')
                st.plotly_chart(fig, use_container_width=True)

        # Matrículas y facturación diaria
        with col2:
            df_d2 = df_dias_actual[df_dias_actual['mats_total'].notna() & (df_dias_actual['fact_total'].notna())].copy()
            if not df_d2.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_d2['fecha'].dt.strftime('%d'),
                    y=df_d2['fact_total'],
                    name='Facturación', marker_color=C['green'], opacity=.8,
                ))
                fig.add_trace(go.Scatter(
                    x=df_d2['fecha'].dt.strftime('%d'),
                    y=df_d2['mats_total'],
                    name='Matrículas', yaxis='y2',
                    line=dict(color=C['purple'], width=2),
                    mode='lines+markers',
                ))
                T(fig).update_layout(
                    title=f'🎓 Matrículas y Facturación Diaria {mes_actual_name}',
                    yaxis2=dict(overlaying='y', side='right',
                                gridcolor='#1a2d3a', tickfont=dict(color='#808080',size=10)),
                )
                st.plotly_chart(fig, use_container_width=True)

        col3, col4 = st.columns(2)

        # Gasto diario Google + Facebook
        with col3:
            df_d3 = df_dias_actual[df_dias_actual['gasto_total'].notna() & (df_dias_actual['gasto_total'] > 0)].copy()
            if not df_d3.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_d3['fecha'].dt.strftime('%d'),
                    y=df_d3['gasto_google'],
                    name='Google Ads', marker_color=C['sky'], opacity=.85,
                ))
                fig.add_trace(go.Bar(
                    x=df_d3['fecha'].dt.strftime('%d'),
                    y=df_d3['gasto_facebook'],
                    name='Facebook Ads', marker_color=C['indigo'], opacity=.85,
                ))
                T(fig).update_layout(title=f'💸 Gasto MKT Diario {mes_actual_name}', barmode='stack')
                fig.update_yaxes(tickprefix='€')
                st.plotly_chart(fig, use_container_width=True)

        # CPL diario
        with col4:
            df_d4 = df_dias_actual[df_dias_actual['cpl_media'].notna() & (df_dias_actual['cpl_media'] > 0)].copy()
            if not df_d4.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_d4['fecha'].dt.strftime('%d'),
                    y=df_d4['cpl_google'],
                    name='CPL Google', line=dict(color=C['sky'], width=1.5), mode='lines+markers',
                ))
                fig.add_trace(go.Scatter(
                    x=df_d4['fecha'].dt.strftime('%d'),
                    y=df_d4['cpl_facebook'],
                    name='CPL Facebook', line=dict(color=C['pink'], width=1.5), mode='lines+markers',
                ))
                fig.add_trace(go.Scatter(
                    x=df_d4['fecha'].dt.strftime('%d'),
                    y=df_d4['cpl_media'],
                    name='CPL Medio', line=dict(color=C['amber'], width=2, dash='dot'), mode='lines',
                ))
                T(fig).update_layout(title=f'💡 CPL Diario {mes_actual_name}')
                fig.update_yaxes(tickprefix='€')
                st.plotly_chart(fig, use_container_width=True)

    # Tendencia vs FCST - gauge style
    st.markdown('<div class="sec">Proyección a Fin de Mes vs FCST</div>', unsafe_allow_html=True)
    col5, col6, col7, col8 = st.columns(4)
    metrics_tend = [
        (col5, "🎯 Leads",      tendencia_mes.get('leads'),   fcst_mes.get('leads'),   'leads'),
        (col6, "🎓 Matrículas", tendencia_mes.get('mats'),    fcst_mes.get('mats'),    'mats'),
        (col7, "💰 Facturación",tendencia_mes.get('fact'),    fcst_mes.get('fact'),    'fact'),
        (col8, "💸 Gasto MKT",  tendencia_mes.get('gasto_total'), fcst_mes.get('gasto_total'), 'gasto'),
    ]
    for col, label, tend, fcst_v, key in metrics_tend:
        tend_v = tend or 0
        fcst_v2 = fcst_v or 1
        pct_v = tend_v / fcst_v2 * 100
        col.metric(
            label,
            num(tend_v) if tend_v else '—',
            delta=f"Obj: {num(fcst_v2)} ({pct_v:.0f}%)",
            delta_color="normal" if pct_v >= 90 else "inverse",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── VELOCIDAD NECESARIA ────────────────────────────────────────────────────
    st.markdown('<div class="sec">Velocidad Necesaria para Alcanzar el Objetivo</div>', unsafe_allow_html=True)
    _row_mes_act = df_mes[df_mes['mes'] == mes_actual_num] if mes_actual_num else pd.DataFrame()
    if not _row_mes_act.empty:
        _rm = _row_mes_act.iloc[0]
        _dias_lleva = float(_rm.get('dias_lleva') or 0)
        _dias_total = float(_rm.get('dias_total') or 1)
        _dias_rest  = max(_dias_total - _dias_lleva, 1)

        _leads_real  = float(totales_mes.get('leads') or 0)
        _leads_fcst  = float(fcst_mes.get('leads') or 0)
        _leads_rest  = max(_leads_fcst - _leads_real, 0)
        _vel_nec_l   = _leads_rest / _dias_rest if _dias_rest > 0 else 0
        _vel_act_l   = _leads_real / _dias_lleva if _dias_lleva > 0 else 0

        _mats_real   = float(totales_mes.get('mats') or 0)
        _mats_proj   = float(_rm.get('mats_proj') or 0)
        _mats_rest   = max(_mats_proj - _mats_real, 0)
        _vel_nec_m   = _mats_rest / _dias_rest if _dias_rest > 0 else 0
        _vel_act_m   = _mats_real / _dias_lleva if _dias_lleva > 0 else 0

        _cv1, _cv2, _cv3, _cv4, _cv5 = st.columns(5)
        _cv1.metric("📅 Días restantes",
                    f"{int(_dias_rest)}",
                    delta=f"de {int(_dias_total)} totales",
                    delta_color="off")
        _cv2.metric("⚡ Leads/día (real)",    f"{_vel_act_l:.1f}")
        _cv3.metric("🎯 Leads/día (necesario)", f"{_vel_nec_l:.1f}",
                    delta=f"{_vel_nec_l - _vel_act_l:+.1f} vs actual",
                    delta_color="inverse" if _vel_nec_l > _vel_act_l else "normal")
        _cv4.metric("⚡ Mats/día (real)",    f"{_vel_act_m:.2f}")
        _cv5.metric("🎓 Mats/día (necesario)", f"{_vel_nec_m:.2f}",
                    delta=f"{_vel_nec_m - _vel_act_m:+.2f} vs actual",
                    delta_color="inverse" if _vel_nec_m > _vel_act_m else "normal")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PROGRESO VS OBJETIVO MENSUAL ───────────────────────────────────────────
    st.markdown('<div class="sec">Progreso vs Objetivo Mensual (Proyección)</div>', unsafe_allow_html=True)
    if not _row_mes_act.empty:
        _rm2 = _row_mes_act.iloc[0]
        _mats_proj2 = float(_rm2.get('mats_proj') or 0)
        _fact_proj2 = float(_rm2.get('fact_proj') or 0)
        _leads_fcst2 = float(fcst_mes.get('leads') or 0)
        _mats_real2  = float(totales_mes.get('mats') or 0)
        _fact_real2  = float(totales_mes.get('fact') or 0)
        _leads_real2 = float(totales_mes.get('leads') or 0)

        def _bar_col(pct):
            if pct >= 90: return "#AABCA3"
            if pct >= 70: return "#BB812F"
            return "#EE7015"

        _pct_l = min(_leads_real2 / _leads_fcst2 * 100, 100) if _leads_fcst2 > 0 else 0
        _pct_m = min(_mats_real2  / _mats_proj2  * 100, 100) if _mats_proj2  > 0 else 0
        _pct_f = min(_fact_real2  / _fact_proj2  * 100, 100) if _fact_proj2  > 0 else 0

        st.markdown(f"""
<div style="max-width:720px">
  <div style="margin-bottom:14px">
    <div style="display:flex;justify-content:space-between;margin-bottom:5px">
      <span style="color:#AABCA3;font-size:.82rem;font-weight:600">🎯 Leads</span>
      <span style="color:#F6FAB2;font-size:.82rem;font-weight:700">{_leads_real2:.0f} / {_leads_fcst2:.0f} &nbsp;({_pct_l:.0f}%)</span>
    </div>
    <div style="background:#0D1820;border-radius:8px;height:16px;overflow:hidden">
      <div style="background:{_bar_col(_pct_l)};width:{_pct_l:.1f}%;height:100%;border-radius:8px"></div>
    </div>
  </div>
  <div style="margin-bottom:14px">
    <div style="display:flex;justify-content:space-between;margin-bottom:5px">
      <span style="color:#AABCA3;font-size:.82rem;font-weight:600">🎓 Matrículas</span>
      <span style="color:#F6FAB2;font-size:.82rem;font-weight:700">{_mats_real2:.0f} / {_mats_proj2:.0f} &nbsp;({_pct_m:.0f}%)</span>
    </div>
    <div style="background:#0D1820;border-radius:8px;height:16px;overflow:hidden">
      <div style="background:{_bar_col(_pct_m)};width:{_pct_m:.1f}%;height:100%;border-radius:8px"></div>
    </div>
  </div>
  <div style="margin-bottom:14px">
    <div style="display:flex;justify-content:space-between;margin-bottom:5px">
      <span style="color:#AABCA3;font-size:.82rem;font-weight:600">💰 Facturación</span>
      <span style="color:#F6FAB2;font-size:.82rem;font-weight:700">{eur(_fact_real2)} / {eur(_fact_proj2)} &nbsp;({_pct_f:.0f}%)</span>
    </div>
    <div style="background:#0D1820;border-radius:8px;height:16px;overflow:hidden">
      <div style="background:{_bar_col(_pct_f)};width:{_pct_f:.1f}%;height:100%;border-radius:8px"></div>
    </div>
  </div>
  <div style="color:#4C4C4C;font-size:.72rem;margin-top:8px">
    🟢 ≥90% &nbsp;|&nbsp; 🟡 70–89% &nbsp;|&nbsp; 🔴 &lt;70% del objetivo mensual
  </div>
</div>
""", unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#EFEEEA;font-size:.75rem">'
    '🧠 PontIA KPI Dashboard · Streamlit + Plotly · '
    'Fuente: Cuadro de Gestion Pontia 2026.xlsx'
    '</div>',
    unsafe_allow_html=True,
)
