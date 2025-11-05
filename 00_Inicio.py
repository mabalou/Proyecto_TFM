# ==========================================
# 00_Inicio.py — versión final pulida (colores corregidos + sin subrayados)
# ==========================================
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="🌍 Visualizador climático global del TFM", layout="wide")

# -------------------------------
# Ocultar sidebar y header nativo
# -------------------------------
st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
header[data-testid="stHeader"], section[data-testid="stToolbar"] {display: none !important;}
div.block-container {
    padding-left: 3rem;
    padding-right: 3rem;
    max-width: 1500px;
    animation: fadeIn 0.8s ease-in-out;
}
@keyframes fadeIn {
    from {opacity: 0; transform: translateY(10px);}
    to {opacity: 1; transform: translateY(0);}
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Páginas
# -------------------------------
PAGES = {
    "Inicio": "00_Inicio",
    "Temperatura": "1_Temperatura",
    "Gases de efecto invernadero": "2_Gases_efecto_invernadero",
    "Nivel del mar": "3_Nivel_del_mar",
    "Hielo marino": "4_Hielo_marino",
    "Exploración socioeconómica": "5_Exploración_socioeconómica",
    "Población mundial": "6_Población_mundial",
    "PIB y crecimiento económico": "7_PIB_y_crecimiento_económico",
    "Consumo energético": "8_Consumo_energético_por_fuente",
    "Análisis multivariable": "9_Análisis_multivariable",
    "Mapa global": "10_Mapa_global",
}

# -------------------------------
# Estado global (página / tema / filtros)
# -------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Inicio"
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "ui_show_filters" not in st.session_state:
    st.session_state.ui_show_filters = False

qp = st.query_params
if qp.get("page") in PAGES:
    st.session_state.current_page = qp["page"]
if qp.get("theme") in ("light", "dark"):
    st.session_state.theme = qp["theme"]
if qp.get("filters") is not None:
    st.session_state.ui_show_filters = qp["filters"] in ("1", "true", "on")

current_theme = st.session_state.theme
other_theme = "light" if current_theme == "dark" else "dark"

# -------------------------------
# URLs dinámicas
# -------------------------------
theme_url = f"?page={st.session_state.current_page}&theme={other_theme}&filters={'1' if st.session_state.ui_show_filters else '0'}"
filters_url = f"?page={st.session_state.current_page}&theme={current_theme}&filters={'0' if st.session_state.ui_show_filters else '1'}"

# -------------------------------
# Construir menú
# -------------------------------
menu_html = ""
for name, module in PAGES.items():
    active = "active" if name == st.session_state.current_page else ""
    filters_flag = "1" if st.session_state.ui_show_filters else "0"
    menu_html += f'<a class="menu-link {active}" href="?page={name}&theme={current_theme}&filters={filters_flag}" target="_self">{name}</a>'

# -------------------------------
# Estilos generales (tema claro/oscuro)
# -------------------------------
light_override = (
    ":root {"
    "--bg-color: #f7f7f5;"
    "--text-color: #1b1b1b;"
    "--menu-bg: rgba(255,255,255,0.9);"
    "--menu-link: #2b3a3a;"
    "--menu-active: #007b7b;"
    "--toggle-bg: #ffffff;"
    "--toggle-text: #2b3a3a;"
    "--switch-bg: #bbb;"
    "--switch-ball: #007b7b;"
    "--input-bg: #ffffff;"
    "--button-bg: #eaeaea;"
    "--button-text: #1a1a1a;"
    "--metric-text: #1a1a1a;"
    "--primary-color: #007b7b;"
    "}"
) if current_theme == "light" else ""

# -------------------------------
# CSS visual principal
# -------------------------------
st.markdown(f"""
<style>
:root {{
    --bg-color: #0f0f0f;
    --text-color: #f0f0f0;
    --menu-bg: rgba(30,30,30,0.85);
    --menu-link: #cfdedf;
    --menu-active: #aeeae1;
    --toggle-bg: #1e1e1e;
    --toggle-text: #e0e0e0;
    --switch-bg: #3b3b3b;
    --switch-ball: #aeeae1;
    --input-bg: #1b1b1b;
    --button-bg: #1e1e1e;
    --button-text: #f0f0f0;
    --metric-text: #ffffff;
    --primary-color: #aeeae1;
}}
{light_override}

/* Fondo general */
[data-testid="stAppViewContainer"] {{
    background-color: var(--bg-color);
    color: var(--text-color);
    transition: background-color .3s ease, color .3s ease;
}}

/* Colores globales */
[data-testid="stAppViewContainer"], [data-testid="stMarkdown"], .stText, p, label, h1, h2, h3, h4, h5, h6, span {{
    color: var(--text-color) !important;
}}
[data-baseweb="input"], [data-baseweb="select"], [data-baseweb="slider"], .stMultiSelect, .stSelectbox, .stTextInput input {{
    color: var(--text-color) !important;
    background-color: var(--input-bg) !important;
}}
[data-testid="stCheckbox"], .stCheckbox, [data-testid="stSliderLabel"] {{
    color: var(--text-color) !important;
}}
[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
    color: var(--metric-text) !important;
}}
[data-testid="stButton"] button, .stButton>button {{
    background-color: var(--button-bg) !important;
    color: var(--button-text) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    border: 1px solid rgba(0,0,0,0.1);
}}
[data-testid="stButton"] button:hover {{
    background-color: var(--primary-color) !important;
    color: white !important;
}}

/* Header */
.header-bar {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    display: flex; justify-content: space-between; align-items: center;
    padding: 1rem 2rem; border-radius: 0 0 18px 18px;
    background: var(--menu-bg); backdrop-filter: blur(12px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
}}
div.block-container {{ padding-top: 7.2rem !important; }}

/* Menú */
.menu-links {{
    display: flex; flex-wrap: wrap; gap: 1.8rem;
    justify-content: center; align-items: center;
}}
.menu-link {{
    font-size: 1.05rem; font-weight: 600;
    text-decoration: none !important;
    border-bottom: 2px solid transparent;
    color: var(--menu-link);
    transition: all 0.25s ease;
}}
.menu-link:hover, .menu-link.active {{
    color: var(--menu-active);
    border-bottom: 2px solid var(--menu-active);
}}

/* Toggles */
.tools-wrap {{
    display: flex; flex-direction: column; gap: 8px; align-items: flex-end;
}}
.pill {{
    display: inline-flex; align-items: center; gap: 10px;
    background: var(--toggle-bg); color: var(--toggle-text);
    border-radius: 25px; padding: 6px 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    font-weight: 600; white-space: nowrap;
    text-decoration: none !important;
}}
.pill .switch {{
    position: relative; width: 50px; height: 26px;
    background: var(--switch-bg);
    border-radius: 34px; overflow: hidden;
}}
.pill .switch::before {{
    content: ""; position: absolute; top: 3px; left: 3px;
    width: 20px; height: 20px;
    background: var(--switch-ball);
    border-radius: 50%;
    transition: transform .25s ease;
}}
.pill.is-on .switch::before {{ transform: translateX(24px); }}
</style>

<div class="header-bar">
  <div class="menu-links">{menu_html}</div>
  <div class="tools-wrap">
    <a class="pill {'is-on' if current_theme=='light' else ''}" href="{theme_url}" target="_self">
      <span>{'☀️ Modo claro' if current_theme=='light' else '🌙 Modo oscuro'}</span>
      <span class="switch"></span>
    </a>
    {f'<a class="pill {"is-on" if st.session_state.ui_show_filters else ""}" href="{filters_url}" target="_self"><span>⚙️ Filtros</span><span class="switch"></span></a>' if st.session_state.current_page != "Inicio" else ""}
  </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# Navegación a otras páginas
# -------------------------------
selected_module = PAGES[st.session_state.current_page]
if selected_module != "00_Inicio":
    exec(Path(f"pages/{selected_module}.py").read_text(), globals())
    st.stop()

# -------------------------------
# Contenido principal de Inicio
# -------------------------------
st.markdown("""
<div style='text-align:center;margin-top:1.2rem;'>
  <h1 style='font-size:2.3rem;font-weight:800;margin-bottom:0.6rem;'>🌍 Visualizador climático global del TFM</h1>
  <p style='font-size:1.15rem;line-height:1.6em;max-width:900px;margin:auto;'>
  Este proyecto forma parte del <b>Trabajo de Fin de Máster</b> del programa
  <b>Máster en Big Data & Visual Analytics</b> (UNIR).<br><br>
  Explora cómo el <b>cambio climático global</b> se relaciona con variables
  socioeconómicas, energéticas y ambientales a lo largo del tiempo.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.subheader("Explora las secciones del análisis:")

col1, col2, col3 = st.columns(3)
with col1:
    st.image("images/energia.png", use_container_width=True)
    st.markdown("**Consumo energético por fuente**")
    st.caption("⚡ Analiza las tendencias del consumo energético global.")
with col2:
    st.image("images/analisis.png", use_container_width=True)
    st.markdown("**Análisis multivariable**")
    st.caption("📊 Explora relaciones entre energía, economía y clima.")
with col3:
    st.image("images/mapa.png", use_container_width=True)
    st.markdown("**Mapas interactivos**")
    st.caption("🗺️ Visualiza indicadores climáticos y socioeconómicos por país.")

st.markdown("---")
st.markdown("<p style='text-align:center;color:#888;'>TFM | Marcos Abal Outeda · 2025</p>", unsafe_allow_html=True)
