# ==========================================
# 00_Inicio.py — Versión pastel ultra suave (más apagada y relajada)
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

# Estado inicial
if "current_page" not in st.session_state:
    st.session_state.current_page = "Inicio"

# Capturar parámetro de URL
page_param = st.query_params.get("page")
if page_param and page_param in PAGES:
    st.session_state.current_page = page_param

# ----------------------------------------------------
# CABECERA — RECTÁNGULO OSCURO + MENÚ HORIZONTAL pastel suave
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

    /* Texto base muy suave */
    .menu-link {
        color: #cfdedf; /* gris verdoso pálido */
        font-size: 1.05rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: color 0.25s ease, border-bottom 0.25s ease;
        padding-bottom: 3px;
        border-bottom: 2px solid transparent;
    }

    /* Hover: tono menta pastel */
    .menu-link:hover {
        color: #aeeae1;
        border-bottom: 2px solid #aeeae1;
    }

    /* Activo: mismo tono, más visible */
    .menu-link.active {
        color: #aeeae1;
        font-weight: 700;
        border-bottom: 2px solid #aeeae1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Renderizado del menú ---
menu_html = '<div class="menu-container">'
for name, module in PAGES.items():
    active_class = "active" if name == st.session_state.current_page else ""
    menu_html += f'<a class="menu-link {active_class}" href="?page={name}" target="_self">{name}</a>'
menu_html += "</div>"
st.markdown(menu_html, unsafe_allow_html=True)

# ==========================================
# Toggle Modo Claro / Oscuro — Versión funcional para Streamlit (corregido)
# ==========================================
st.markdown(
    """
    <style>
    /* Posición y estilo del switch */
    .theme-toggle-container {
        position: fixed;
        top: 0.2rem;  /* más arriba */
        right: 1.2rem;
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 10px;
        background: var(--toggle-bg);
        border-radius: 25px;
        padding: 6px 14px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.35);
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--toggle-text);
        transition: all 0.3s ease;
    }

    .toggle-switch {
        position: relative;
        width: 52px;
        height: 26px;
        background: var(--switch-bg);
        border-radius: 34px;
        cursor: pointer;
        transition: background 0.25s ease;
    }

    .toggle-switch::before {
        content: "";
        position: absolute;
        top: 3px;
        left: 3px;
        width: 20px;
        height: 20px;
        background: var(--switch-ball);
        border-radius: 50%;
        transition: transform 0.25s ease, background 0.25s ease;
    }

    /* Variables por defecto (modo oscuro) */
    :root {
        --bg-color: #0f0f0f;
        --text-color: #f0f0f0;
        --menu-bg: #1e1e1e;
        --menu-link: #c5c5c5;
        --menu-active: #aeeae1;
        --toggle-bg: #1e1e1e;
        --toggle-text: #e0e0e0;
        --switch-bg: #3b3b3b;
        --switch-ball: #aeeae1;
    }

    /* Variables para modo claro */
    [data-theme="light"] {
        --bg-color: #f9f9f7;
        --text-color: #1a1a1a;
        --menu-bg: #f4f4f4;
        --menu-link: #2f3b40;
        --menu-active: #52c7b8;
        --toggle-bg: #f4f4f4;
        --toggle-text: #2f3b40;
        --switch-bg: #ccc;
        --switch-ball: #2f3b40;
    }

    [data-theme="light"] .toggle-switch::before {
        transform: translateX(26px);
    }

    /* Aplicar los colores a la app */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-color);
        color: var(--text-color);
        transition: background-color 0.3s ease, color 0.3s ease;
    }

    .menu-container {
        background-color: var(--menu-bg) !important;
        margin-top: 0.3rem !important;
    }

    .menu-link {
        color: var(--menu-link) !important;
    }

    .menu-link.active, .menu-link:hover {
        color: var(--menu-active) !important;
        border-bottom: 2px solid var(--menu-active) !important;
    }
    </style>

    <div class="theme-toggle-container" id="themeBox">
        <span id="themeLabel">🌙 Modo oscuro</span>
        <div class="toggle-switch" id="themeToggle"></div>
    </div>

    <script>
    (function(){
        const root = document.querySelector('[data-testid="stAppViewContainer"]');
        const label = document.getElementById('themeLabel');
        const toggle = document.getElementById('themeToggle');

        function initTheme(){
            if (!root || !label || !toggle) {
                setTimeout(initTheme, 100);
                return;
            }

            function setTheme(mode){
                root.setAttribute('data-theme', mode);
                label.textContent = (mode === 'light') ? '☀️ Modo claro' : '🌙 Modo oscuro';
                localStorage.setItem('tfm_theme', mode);
            }

            let mode = localStorage.getItem('tfm_theme');
            if (!mode){
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                mode = prefersDark ? 'dark' : 'light';
            }
            setTheme(mode);

            toggle.addEventListener('click', ()=>{
                mode = (root.getAttribute('data-theme') === 'light') ? 'dark' : 'light';
                setTheme(mode);
            });
        }

        initTheme();
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------
# NAVEGACIÓN
# ----------------------------------------------------
selected_module = PAGES[st.session_state.current_page]
if selected_module != "00_Inicio":
    try:
        exec(Path(f"pages/{selected_module}.py").read_text(), globals())
    except Exception as e:
        st.error(f"⚠️ No se pudo cargar la página: {e}")
    st.stop()

# ----------------------------------------------------
# CONTENIDO INICIO
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
