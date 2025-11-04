# ==========================================
# 00_Inicio.py — versión glass definitiva (expanders corregidos)
# ==========================================
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="🌍 Visualizador climático global del TFM", layout="wide")

# ----------------------------------------------------
# Ocultar barra lateral y header
# ----------------------------------------------------
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

# ----------------------------------------------------
# Definición de páginas
# ----------------------------------------------------
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

# ----------------------------------------------------
# Estado de página y tema
# ----------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Inicio"

page_param = st.query_params.get("page")
if page_param and page_param in PAGES:
    st.session_state.current_page = page_param

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

url_theme = st.query_params.get("theme")
if url_theme in ("light", "dark"):
    st.session_state.theme = url_theme
if st.query_params.get("theme") != st.session_state.theme:
    st.query_params.update({"theme": st.session_state.theme})
current_theme = st.session_state.theme

# ----------------------------------------------------
# Cabecera glass + menú + switch
# ----------------------------------------------------
other_theme = "light" if current_theme == "dark" else "dark"
label_text = "☀️ Modo claro" if current_theme == "light" else "🌙 Modo oscuro"
toggle_url = f"?page={st.session_state.current_page}&theme={other_theme}"

menu_items = ""
for name, module in PAGES.items():
    active = "active" if name == st.session_state.current_page else ""
    menu_items += f'<a class="menu-link {active}" href="?page={name}&theme={current_theme}" target="_self">{name}</a>'

# ----------------------------------------------------
# Estilos principales (corregidos)
# ----------------------------------------------------
st.markdown(f"""
<style>
.header-bar {{
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
    display: flex; justify-content: space-between; align-items: center;
    padding: 1rem 2rem;
    border-radius: 0 0 18px 18px;
    background: rgba(30,30,30,0.85);
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    backdrop-filter: blur(12px);
    transition: background 0.4s ease, color 0.4s ease;
}}
div.block-container {{ padding-top: 7.2rem !important; }}

.menu-links {{
    display: flex; flex-wrap: wrap; gap: 1.8rem; justify-content: center; align-items: center;
}}
.menu-link {{
    font-size: 1.05rem; font-weight: 600;
    text-decoration: none !important; border-bottom: 2px solid transparent;
    transition: all 0.25s ease; color: var(--menu-link);
}}
.menu-link:hover, .menu-link.active {{
    color: var(--menu-active);
    border-bottom: 2px solid var(--menu-active);
}}

.theme-toggle {{
    display: flex; align-items: center; gap: 10px;
    background: var(--toggle-bg);
    border-radius: 25px; padding: 6px 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    font-size: 0.9rem; font-weight: 600;
    color: var(--toggle-text); white-space: nowrap;
}}
.toggle-switch {{
    position: relative; width: 50px; height: 26px;
    background: var(--switch-bg);
    border-radius: 34px; cursor: pointer;
    display: inline-block; overflow: hidden;
}}
.toggle-switch::before {{
    content: ""; position: absolute; top: 3px; left: 3px;
    width: 20px; height: 20px;
    background: var(--switch-ball); border-radius: 50%;
    transition: transform 0.25s ease, background 0.25s ease;
}}

/* ===========================
   MODO OSCURO
   =========================== */
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

/* ===========================
   MODO CLARO MEJORADO
   =========================== */
{"".join([
    ":root {",
    "--bg-color: #f7f7f5;",
    "--text-color: #1b1b1b;",
    "--menu-bg: rgba(255,255,255,0.9);",
    "--menu-link: #2b3a3a;",
    "--menu-active: #007b7b;",
    "--toggle-bg: #ffffff;",
    "--toggle-text: #2b3a3a;",
    "--switch-bg: #bbb;",
    "--switch-ball: #007b7b;",
    "--input-bg: #ffffff;",
    "--button-bg: #f0f0f0;",
    "--button-text: #1a1a1a;",
    "--metric-text: #111;",
    "--primary-color: #007b7b;",
    "}"
]) if current_theme == "light" else ""}

.theme-toggle.is-light .toggle-switch::before {{ transform: translateX(24px); }}

[data-testid="stAppViewContainer"] {{
    background-color: var(--bg-color);
    color: var(--text-color);
    transition: background-color 0.3s ease, color 0.3s ease;
}}

/* ===========================
   EXPANDERS 100% CORREGIDOS
   =========================== */
[data-testid="stExpander"], 
[data-testid="stExpanderContent"],
[data-testid="stExpander"] div[role="region"],
[data-testid="stExpander"] div[data-testid="stVerticalBlock"],
[data-testid="stExpander"] div[role="button"],
[data-testid="stExpander"] * {{
    background-color: var(--input-bg) !important;
    color: var(--text-color) !important;
    border: none !important;
    border-radius: 10px !important;
}}
[data-testid="stExpander"] p, [data-testid="stExpander"] span, [data-testid="stExpander"] li {{
    color: var(--text-color) !important;
}}

/* ===========================
   MÉTRICAS / BOTONES
   =========================== */
[data-testid="stMetric"], [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
button, .stButton>button {{
    color: var(--metric-text) !important;
    background-color: var(--button-bg) !important;
}}
</style>

<div class="header-bar" style="background: var(--menu-bg);">
    <div class="menu-links">{menu_items}</div>
    <div class="theme-toggle {'is-light' if current_theme == 'light' else ''}">
        <span>{label_text}</span>
        <a class="toggle-switch" href="{toggle_url}" target="_self"></a>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Navegación
# ----------------------------------------------------
selected_module = PAGES[st.session_state.current_page]
if selected_module != "00_Inicio":
    exec(Path(f"pages/{selected_module}.py").read_text(), globals())
    st.stop()

# ----------------------------------------------------
# Contenido principal
# ----------------------------------------------------
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
