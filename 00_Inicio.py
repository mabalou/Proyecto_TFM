# ==========================================
# 00_Inicio.py — Versión final: navegación activa funcional + diseño perfecto
# ==========================================
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="🌍 Visualizador climático global del TFM", layout="wide")

# ----------------------------------------------------
# Eliminar espacio superior, header y sidebar
# ----------------------------------------------------
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}

        header[data-testid="stHeader"] {
            display: none;
        }
        section[data-testid="stToolbar"] {
            display: none !important;
        }

        div.block-container {
            padding-top: 0rem !important;
            margin-top: 0.5rem !important;
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 1500px;
            animation: fadeIn 0.8s ease-in-out;
        }

        body {
            margin-top: 0 !important;
            padding-top: 0 !important;
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

# Inicializar estado si no existe
if "current_page" not in st.session_state:
    st.session_state.current_page = "Inicio"

# ----------------------------------------------------
# Capturar parámetro de URL (nuevo método correcto)
# ----------------------------------------------------
page_param = st.query_params.get("page")

# Si el parámetro existe y es válido, actualizar el estado
if page_param and page_param in PAGES:
    st.session_state.current_page = page_param

# ----------------------------------------------------
# CABECERA — RECTÁNGULO OSCURO + MENÚ HORIZONTAL
# ----------------------------------------------------
st.markdown(
    """
    <style>
    .menu-container {
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: #1e1e1e;
        border-radius: 15px;
        padding: 1.2rem 2.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2.5rem;
        flex-wrap: wrap;
        margin-bottom: 3rem;
    }

    .menu-link {
        color: #b9b9b9;
        font-size: 1.05rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: color 0.25s ease, border-bottom 0.25s ease;
        padding-bottom: 3px;
        border-bottom: 2px solid transparent;
    }

    .menu-link.active {
    color: #4da8ff;  /* Azul más suave */
    border-bottom: 2px solid #4da8ff;
    }
    .menu-link:hover {
        color: #ffffff;
        border-bottom: 2px solid #4da8ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Renderizado del menú horizontal ---
menu_html = '<div class="menu-container">'
for name, module in PAGES.items():
    active_class = "active" if name == st.session_state.current_page else ""
    menu_html += f'<a class="menu-link {active_class}" href="?page={name}" target="_self">{name}</a>'
menu_html += "</div>"

st.markdown(menu_html, unsafe_allow_html=True)

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
# CONTENIDO DE INICIO — CENTRADO
# ----------------------------------------------------
st.markdown(
    """
    <div style='text-align: center;'>
        <h1 style='font-size:2.3rem; font-weight:800; margin-bottom:0.6rem;'>🌍 Visualizador climático global del TFM</h1>
        <p style='font-size:1.15rem; line-height:1.6em; max-width:900px; margin:auto;'>
        Este proyecto forma parte del <b>Trabajo de Fin de Máster</b> del programa
        <b>Máster en Big Data & Visual Analytics</b> (UNIR).<br><br>
        Explora cómo el <b>cambio climático global</b> se relaciona con variables
        socioeconómicas, energéticas y ambientales a lo largo del tiempo.
        </p>
    </div>
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
