# ==========================================
# 00_Inicio.py — Versión final (visual y funcional)
# ==========================================
import streamlit as st
from pathlib import Path
import importlib

st.set_page_config(page_title="🌍 Visualizador climático global del TFM", layout="wide")

# ----------------------------------------------------
# Ocultar sidebar y animar contenedor
# ----------------------------------------------------
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {display: none;}
    .block-container {
        padding-top: 2rem;
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
    """,
    unsafe_allow_html=True,
)

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

if "current_page" not in st.session_state:
    st.session_state.current_page = "Inicio"

# ----------------------------------------------------
# MENÚ SUPERIOR — FUNCIONAL Y VISUAL
# ----------------------------------------------------
st.markdown(
    """
    <style>
    .nav-container {
        position: sticky;
        top: 0;
        z-index: 100;
        background-color: #1e1e1e;
        border-radius: 12px;
        padding: 1.2rem 2.5rem;
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 2.2rem;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.4);
        margin-bottom: 2.8rem;
    }
    div.stButton > button {
        background: transparent !important;
        border: none !important;
        color: #b9b9b9 !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        cursor: pointer;
        transition: all 0.25s ease;
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
    }
    div.stButton > button:hover {
        color: #2e9aff !important;
    }
    div.stButton > button.active {
        color: #2e9aff !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #2e9aff !important;
        padding-bottom: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="nav-container">', unsafe_allow_html=True)

# Menú con botones Streamlit (funcionales)
cols = st.columns(len(PAGES))
for i, (name, module) in enumerate(PAGES.items()):
    is_active = name == st.session_state.current_page
    with cols[i]:
        btn = st.button(name, key=name)
        if btn:
            st.session_state.current_page = name
            st.rerun()
        if is_active:
            st.markdown(
                f"<style>div[data-testid='stButton'] button#{name.replace(' ','_')}{{color:#2e9aff !important;font-weight:700 !important;border-bottom:2px solid #2e9aff !important;}}</style>",
                unsafe_allow_html=True,
            )

st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# NAVEGACIÓN INTERNA
# ----------------------------------------------------
selected_module = PAGES[st.session_state.current_page]

if selected_module != "00_Inicio":
    try:
        exec(Path(f"pages/{selected_module}.py").read_text(), globals())
    except Exception as e:
        st.error(f"⚠️ No se pudo cargar la página: {e}")
    st.stop()

# ----------------------------------------------------
# CONTENIDO DE INICIO
# ----------------------------------------------------
st.title("🌍 Visualizador climático global del TFM")

st.markdown(
    """
    <p style='font-size:1.15rem; line-height:1.6em;'>
    Este proyecto forma parte del <b>Trabajo de Fin de Máster</b> del programa
    <b>Máster en Big Data & Visual Analytics</b> (UNIR).<br><br>
    Explora cómo el <b>cambio climático global</b> se relaciona con variables
    socioeconómicas, energéticas y ambientales a lo largo del tiempo.
    </p>
    """,
    unsafe_allow_html=True,
)

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
st.markdown(
    "<p style='text-align:center; color:#888;'>TFM | Marcos Abal Outeda · 2025</p>",
    unsafe_allow_html=True,
)
