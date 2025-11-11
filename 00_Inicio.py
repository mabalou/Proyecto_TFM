# ==========================================
# 00_Inicio.py — inicio con tarjetas-resumen (mini-gráficas)
# Mantiene: cabecera fija, modo claro/oscuro, botón de filtros, navegación
# ==========================================
import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="🌍 Visualizador climático global del TFM", layout="wide")

# ----------------------------------------
# Animación anti-flash (suaviza carga entre páginas)
# ----------------------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { opacity: 0; animation: fadeInSlow 0.3s ease-in forwards; }
@keyframes fadeInSlow { from { opacity: 0; } to { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------
# Ocultar barra lateral y cabecera nativa
# ----------------------------------------
st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
header[data-testid="stHeader"], section[data-testid="stToolbar"] {display: none !important;}
div.block-container { padding-left: 3rem; padding-right: 3rem; max-width: 1500px; animation: fadeIn 0.8s ease-in-out; }
@keyframes fadeIn { from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: translateY(0);} }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------
# Diccionario de páginas
# ----------------------------------------
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

# ----------------------------------------
# Estado global
# ----------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Inicio"
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "ui_show_filters" not in st.session_state:
    st.session_state.ui_show_filters = True

qp = st.query_params
if qp.get("page") in PAGES:
    st.session_state.current_page = qp["page"]
if qp.get("theme") in ("light", "dark"):
    st.session_state.theme = qp["theme"]
if qp.get("filters") is not None:
    st.session_state.ui_show_filters = qp["filters"] in ("1", "true", "on")

current_theme = st.session_state.theme
other_theme = "light" if current_theme == "dark" else "dark"
primary = st.get_option("theme.primaryColor") or ("#aeeae1" if current_theme == "dark" else "#007b7b")
tpl = "plotly_dark" if current_theme == "dark" else "plotly_white"

# URLs dinámicas
def page_url(name: str, theme=current_theme, filters_flag=None):
    if filters_flag is None:
        filters_flag = "1" if st.session_state.ui_show_filters else "0"
    return f"?page={name}&theme={theme}&filters={filters_flag}"

theme_url = page_url(st.session_state.current_page, theme=other_theme)
filters_url = page_url(st.session_state.current_page, theme=current_theme,
                       filters_flag=("0" if st.session_state.ui_show_filters else "1"))

# ----------------------------------------
# Construcción del menú
# ----------------------------------------
menu_html = ""
for name, module in PAGES.items():
    active = "active" if name == st.session_state.current_page else ""
    filters_flag = "1" if st.session_state.ui_show_filters else "0"
    menu_html += f'<a class="menu-link {active}" href="?page={name}&theme={current_theme}&filters={filters_flag}" target="_self">{name}</a>'

# ----------------------------------------
# Estilos del tema + corrección tarjetas vacías + botón moderno
# ----------------------------------------
# Añadimos variables específicas para el botón "Ver más"
light_override = (
    ":root {"
    "--bg-color: #f7f7f5; --text-color: #1b1b1b; --menu-bg: rgba(255,255,255,0.9);"
    "--menu-link: #2b3a3a; --menu-active: #007b7b; --toggle-bg: #ffffff; --toggle-text: #2b3a3a;"
    "--switch-bg: #bbb; --switch-ball: #007b7b; --input-bg: #ffffff; --button-bg: #eaeaea;"
    "--button-text: #1a1a1a; --metric-text: #1a1a1a; --primary-color: #007b7b;"
    "--cta-text: #111111; --cta-bg: rgba(0,123,123,0.08); --cta-border: rgba(0,123,123,0.25);"
    "}"
) if current_theme == "light" else ""

st.markdown(f"""
<style>
:root {{
    --bg-color: #0f0f0f;
    --text-color: #f0f0f0;
    --menu-bg: rgba(30,30,30,0.85);
    --menu-link: #ffffff;
    --menu-active: #aee0ff;
    --toggle-bg: #1e1e1e;
    --toggle-text: #e0e0e0;
    --switch-bg: #3b3b3b;
    --switch-ball: #aeeae1;
    --input-bg: #1b1b1b;
    --metric-text: #ffffff;
    --primary-color: {primary};
    --cta-text: #f7f7f7;
    --cta-bg: rgba(255,255,255,0.07);
    --cta-border: rgba(255,255,255,0.15);

}}
{light_override}

/* Fondo general */
[data-testid="stAppViewContainer"] {{
    background-color: var(--bg-color);
    color: var(--text-color);
    transition: background-color .3s ease, color .3s ease;
}}
[data-testid="stAppViewContainer"], p, label, h1, h2, h3, h4, h5, h6, span {{
    color: var(--text-color) !important;
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
.menu-links {{ display: flex; flex-wrap: wrap; gap: 1.8rem; justify-content: center; align-items: center; }}
.menu-link {{
    font-size: 1.05rem; font-weight: 600; text-decoration: none !important;
    border-bottom: 2px solid transparent; color: var(--menu-link) !important;
    transition: all 0.25s ease;
}}
.menu-link:hover, .menu-link.active {{
    color: var(--menu-active) !important;
    border-bottom: 2px solid var(--menu-active);
}}

/* Toggles */
.tools-wrap {{ display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }}
.pill {{
    display: inline-flex; align-items: center; gap: 10px; background: var(--toggle-bg);
    color: var(--toggle-text); border-radius: 25px; padding: 6px 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.35); font-weight: 600;
    white-space: nowrap; text-decoration: none !important;
}}
.pill .switch {{ position: relative; width: 50px; height: 26px; background: var(--switch-bg);
    border-radius: 34px; overflow: hidden; }}
.pill .switch::before {{
    content: ""; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px;
    background: var(--switch-ball); border-radius: 50%;
    transition: transform .25s ease;
}}
.pill.is-on .switch::before {{ transform: translateX(24px); }}

/* Responsive */
#menuChk, .menu-toggle {{ display: none; }}
@media (max-width: 768px) {{
  .header-bar {{ flex-direction: column; align-items: flex-start; padding: 0.8rem 1rem; }}
  .menu-toggle {{
    display:block; cursor:pointer; font-size:1.4rem; font-weight:700;
    color:var(--menu-active); margin-right:0.8rem; user-select:none;
  }}
  .menu-links {{ display:none; flex-direction:column; align-items:flex-start;
    gap:0.6rem; width:100%; margin-top:0.6rem; }}
  #menuChk:checked + label.menu-toggle + .menu-links {{ display:flex; }}
  div.block-container {{ padding-top: 9rem !important; }}
}}

/* -------- Tarjetas -------- */
.card {{
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 18px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}}
.card:hover {{
  transform: translateY(-4px);
  box-shadow: 0 6px 18px rgba(0,0,0,0.35);
}}
/* ✨ Estilo mejorado para títulos de tarjeta */
/* ✨ Estilo visual para los títulos de sección (afuera de las tarjetas) */
div[data-testid="stVerticalBlock"] > div > h4 {{
  display: inline-block;
  margin: 0 0 8px 0;
  font-weight: 800;
  font-size: 1.1rem;
  padding: 6px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.25);
}}

/* Modo claro */
:root.light div[data-testid="stVerticalBlock"] > div > h4 {{
  background: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.08);
  box-shadow: none;
}}

/* ✨ Botón "Ver más →" con estilo más sutil y proporcional */
div.card .cta a,
div.card .cta a:link,
div.card .cta a:visited,
div.card .cta a:hover,
div.card .cta a:active {{
  all: unset;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  padding: 8px 14px;
  border-radius: 8px;
  font-weight: 650;
  font-size: 0.95rem;
  text-decoration: none !important;
  color: var(--cta-text) !important;
  background: var(--cta-bg);
  border: 1px solid var(--cta-border);
  backdrop-filter: blur(6px);
  box-shadow: 0 0 5px rgba(0,255,200,0.15);
  transition: all 0.25s ease;
}}

div.card .cta a:hover {{
  background: linear-gradient(135deg, var(--primary-color), #00a896);
  color: #ffffff !important;
  box-shadow: 0 0 10px rgba(0,255,200,0.35);
  transform: translateY(-2px);
}}

/* 💡 Mejora del contraste del botón en modo claro */
:root.light div.card .cta a {{
  background: rgba(0, 123, 123, 0.15);
  color: #111111 !important;
  border: 1px solid rgba(0, 123, 123, 0.35);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(4px);
  transition: all 0.25s ease;
}}

:root.light div.card .cta a:hover {{
  background: linear-gradient(135deg, #007b7b, #00bfa6);
  color: #ffffff !important;
  border-color: rgba(0, 123, 123, 0.4);
  box-shadow: 0 0 10px rgba(0, 123, 123, 0.35);
  transform: translateY(-2px);
}}

/* 🧩 Corrige los recuadros vacíos sobre tarjetas (compatible con Streamlit ≥1.39) */
div[data-testid="stVerticalBlock"] div:empty {{
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  background: none !important;
}}
div[data-testid="stVerticalBlock"] > div[role="region"]:has(div.card) > div:empty {{
  display: none !important;
}}
/* 🔧 Fuerza el estilo de los títulos encima de las tarjetas */
h4:has(+ div.card),
h4 + div.card > h4 {{
  display: inline-block !important;
  margin: 0 0 8px 0 !important;
  font-weight: 800 !important;
  font-size: 1.1rem !important;
  padding: 6px 12px !important;
  border-radius: 10px !important;
  background: rgba(255,255,255,0.06) !important;
  backdrop-filter: blur(6px) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  box-shadow: 0 0 6px rgba(0,0,0,0.25) !important;
  color: var(--text-color) !important;
}}

/* Modo claro */
:root.light h4:has(+ div.card) {{
  background: rgba(0,0,0,0.05) !important;
  border-color: rgba(0,0,0,0.08) !important;
  box-shadow: none !important;
}}
/* 🎯 Títulos de las tarjetas (con efecto glass y tamaño ajustado) */
h4:where(:first-child):is(:has(img), :has(span), :has(svg)),
h4:has(+ div),
h4:has(+ div[class*="card"]) {{
  display: inline-block !important;
  margin: 0 0 10px 0 !important;
  font-weight: 850 !important;
  font-size: 1.25rem !important;
  letter-spacing: -0.3px !important;
  padding: 8px 16px !important;
  border-radius: 12px !important;
  background: rgba(255,255,255,0.06) !important;
  backdrop-filter: blur(6px) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  box-shadow: 0 0 8px rgba(0,0,0,0.25) !important;
  color: var(--text-color) !important;
  transition: box-shadow 0.3s ease, transform 0.2s ease;
}}

h4:hover {{
  transform: translateY(-1px);
  box-shadow: 0 0 12px rgba(0,255,200,0.3) !important;
}}

:root.light h4 {{
  background: rgba(0,0,0,0.03) !important;
  border-color: rgba(0,0,0,0.05) !important;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;
}}

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

# ----------------------------------------
# Navegación entre páginas
# ----------------------------------------
selected_module = PAGES[st.session_state.current_page]
if selected_module != "00_Inicio":
    exec(Path(f"pages/{selected_module}.py").read_text(), globals())
    st.stop()

# ----------------------------------------
# Contenido principal (tu hero original)
# ----------------------------------------
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

# ============================================================
# BLOQUE TARJETAS CON MINI-GRÁFICAS (Inicio) — versión original + mapa centrado
# Requiere: st, pd, np, px, tpl, page_url ya definidos arriba
# ============================================================


# ----------------------------------------
# Helper: mini-fig safe
# ----------------------------------------
def _safe_read_csv(path, **kwargs):
    try:
        return pd.read_csv(path, **kwargs)
    except Exception:
        try:
            return pd.read_csv(path, engine="python", **kwargs)
        except Exception:
            return pd.DataFrame()

def _mini_chart(fig):
    fig.update_layout(template=tpl, margin=dict(l=10, r=10, t=10, b=10), height=180, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def _btn(page_name: str, label="Ver más →"):
    # colores según el tema actual
    if current_theme == "light":
        text_color = "#111111"
        bg_color = "rgba(0, 123, 123, 0.15)"   # más visible
        border_color = "rgba(0, 123, 123, 0.35)"
    else:
        text_color = "#ffffff"
        bg_color = "rgba(255,255,255,0.07)"
        border_color = "rgba(255,255,255,0.15)"

    button_html = f"""
    <div class='cta' style='text-align:left;'>
        <a href='{page_url(page_name)}' target='_self'
        style="
            display:inline-flex;
            align-items:center;
            justify-content:center;
            gap:8px;
            padding:10px 22px;
            border-radius:14px;
            font-weight:700;
            font-size:1rem;
            text-decoration:none;
            color:{text_color};
            background:{bg_color};
            border:1px solid {border_color};
            backdrop-filter:blur(10px);
            box-shadow:0 0 10px rgba(0,255,200,0.25);
            transition:all 0.25s ease;
        "
        onmouseover="this.style.background='linear-gradient(135deg, var(--primary-color), #00bfa6)'; this.style.color='#ffffff'; this.style.boxShadow='0 0 18px rgba(0,255,200,0.45)'; this.style.transform='translateY(-2px)';"
        onmouseout="this.style.background='{bg_color}'; this.style.color='{text_color}'; this.style.boxShadow='0 0 10px rgba(0,255,200,0.25)'; this.style.transform='translateY(0)';"
        >
        🔍 {label}
        </a>
    </div>
    """
    st.markdown(button_html, unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: Temperatura (línea, J-D, suavizada)
# ----------------------------------------
def card_temperatura():
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>🌡️ Temperatura</h4>", unsafe_allow_html=True)
        df = _safe_read_csv("data/temperatura/global_temperature_nasa.csv", skiprows=1)
        if df.empty:
            st.info("Datos no disponibles.")
        else:
            df = df[["Year","J-D"]].replace("***", np.nan).dropna()
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
            df["J-D"] = pd.to_numeric(df["J-D"], errors="coerce")
            df = df.dropna()
            y0, y1 = max(int(df["Year"].min()), int(df["Year"].max())-50), int(df["Year"].max())
            dd = df[(df["Year"].between(y0, y1))].copy()
            dd["Suav"] = dd["J-D"].rolling(3, center=True, min_periods=1).mean()
            fig = px.line(dd, x="Year", y="Suav", labels={"Suav":"Anomalía (°C)", "Year":"Año"})
            fig.update_traces(line=dict(width=3))
            _mini_chart(fig)
        st.caption("Anomalía global J-D (NASA GISTEMP), últimos ~50 años.")
        _btn("Temperatura")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: Gases efecto invernadero (línea CO₂)
# ----------------------------------------
def card_gases():
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>🧪 Gases de efecto invernadero</h4>", unsafe_allow_html=True)
        df = _safe_read_csv("data/gases/greenhouse_gas_co2_global.csv", comment="#")
        if df.empty:
            st.info("Datos no disponibles.")
        else:
            c = {x.lower(): x for x in df.columns}
            val = next((k for k in ["average","trend","value"] if k in c), None)
            if val:
                df = df.rename(columns={c.get("year","year"):"Year", val: "Value"})
                df = df[["Year","Value"]].dropna()
                df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
                y0, y1 = max(int(df["Year"].min()), int(df["Year"].max())-50), int(df["Year"].max())
                dd = df[df["Year"].between(y0, y1)]
                fig = px.bar(dd, x="Year", y="Value", labels={"Value":"CO₂ (ppm)"})
                fig.update_traces(marker_color=primary, opacity=0.85)
                _mini_chart(fig)
            else:
                st.info("Columna de valores no encontrada.")
        st.caption("CO₂ (ppm) global, últimos ~50 años.")
        _btn("Gases de efecto invernadero")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: Nivel del mar (línea anual media)
# ----------------------------------------
def card_nivel_mar():
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>🌊 Nivel del mar</h4>", unsafe_allow_html=True)
        df = _safe_read_csv("data/sea_level/sea_level_nasa.csv", skiprows=1, header=None, names=["Fecha","Nivel_mar"])
        if df.empty:
            st.info("Datos no disponibles.")
        else:
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
            df = df.dropna(subset=["Fecha","Nivel_mar"])
            df["Año"] = df["Fecha"].dt.year
            da = df.groupby("Año", as_index=False)["Nivel_mar"].mean()
            y0, y1 = max(int(da["Año"].min()), int(da["Año"].max())-50), int(da["Año"].max())
            dd = da[da["Año"].between(y0, y1)]
            fig = px.area(dd, x="Año", y="Nivel_mar", labels={"Nivel_mar":"mm"})
            fig.update_traces(line=dict(width=2.5), fillcolor="rgba(0,180,200,0.35)")
            _mini_chart(fig)
        st.caption("Nivel medio global (mm), promedio anual ~50 años.")
        _btn("Nivel del mar")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: Hielo marino (línea Ártico vs Antártico)
# ----------------------------------------
def card_hielo():
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>🧊 Hielo marino</h4>", unsafe_allow_html=True)
        def load(region):
            path = "data/hielo/arctic_sea_ice_extent.csv" if region == "Ártico" else "data/hielo/antarctic_sea_ice_extent.csv"
            d = _safe_read_csv(path)
            if d.empty:
                return d
            d.columns = d.columns.str.strip().str.lower()
            year_col = next((c for c in d.columns if "year" in c), None)
            extent_col = next((c for c in d.columns if "extent" in c or "area" in c), None)
            if not year_col or not extent_col:
                st.warning(f"No se detectaron columnas válidas en {region}. Columnas: {list(d.columns)}")
                return pd.DataFrame()
            d = d.rename(columns={year_col: "Año", extent_col: "Extensión"})
            d["Año"] = pd.to_numeric(d["Año"], errors="coerce")
            d["Extensión"] = pd.to_numeric(d["Extensión"], errors="coerce")
            d = d.dropna(subset=["Año", "Extensión"])
            return d.groupby("Año", as_index=False)["Extensión"].mean().assign(Región=region)
        a = load("Ártico"); b = load("Antártico")
        if a.empty and b.empty:
            st.info("Datos no disponibles.")
        else:
            df = pd.concat([a, b]).dropna()
            y0, y1 = max(int(df["Año"].min()), int(df["Año"].max())-50), int(df["Año"].max())
            dd = df[df["Año"].between(y0, y1)].copy()
            dd["Suav"] = dd.groupby("Región")["Extensión"].transform(lambda s: s.rolling(3, center=True, min_periods=1).mean())
            fig = px.line(dd, x="Año", y="Suav", color="Región", labels={"Suav":"M km²"})
            fig.update_traces(line=dict(width=3))
            _mini_chart(fig)
        st.caption("Extensión media anual — Ártico vs Antártico.")
        _btn("Hielo marino")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: Exploración socioeconómica (CO₂ total mundial)
# ----------------------------------------
def card_explora():
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>📉 Emisiones de CO₂ por país</h4>", unsafe_allow_html=True)
        df = _safe_read_csv("data/socioeconomico/co2_emissions_by_country.csv")
        if df.empty:
            st.info("Datos no disponibles.")
        else:
            df.columns = df.columns.str.strip().str.lower()
            ycol = next((c for c in df.columns if "year" in c), None)
            vcol = next((c for c in df.columns if "co2" in c or "emission" in c), None)
            if not (ycol and vcol):
                st.info("Columnas no detectadas.")
            else:
                dd = df.groupby(ycol)[vcol].sum(numeric_only=True).reset_index().rename(columns={ycol:"Year", vcol:"CO2"})
                y0, y1 = max(int(dd["Year"].min()), int(dd["Year"].max())-50), int(dd["Year"].max())
                dd = dd[dd["Year"].between(y0, y1)]
                fig = px.bar(dd, x="Year", y="CO2", labels={"CO2":"Mt CO₂"})
                fig.update_traces(marker_color=primary, opacity=0.85)
                _mini_chart(fig)
        st.caption("Emisiones globales agregadas (Mt CO₂).")
        _btn("Exploración socioeconómica")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: Población (suma mundial)
# ----------------------------------------
def card_poblacion():
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>👥 Población mundial</h4>", unsafe_allow_html=True)
        df = _safe_read_csv("data/socioeconomico/population_by_country.csv")
        if df.empty:
            st.info("Datos no disponibles.")
        else:
            df.columns = df.columns.str.strip().str.lower()
            if not {"country name","year","value"}.issubset(df.columns):
                st.info("Columnas no detectadas.")
            else:
                dd = df.groupby("year")["value"].sum(numeric_only=True).reset_index().rename(columns={"year":"Año","value":"Población"})
                y0, y1 = max(int(dd["Año"].min()), int(dd["Año"].max())-50), int(dd["Año"].max())
                dd = dd[dd["Año"].between(y0, y1)]
                fig = px.area(dd, x="Año", y="Población", labels={"Población":"Población"})
                fig.update_traces(line=dict(width=2.5), fillcolor="rgba(0,180,200,0.35)")
                _mini_chart(fig)
        st.caption("Población total mundial (1960+).")
        _btn("Población mundial")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: PIB (suma mundial, línea)
# ----------------------------------------
def card_pib():
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>💰 PIB por país</h4>", unsafe_allow_html=True)
        df = _safe_read_csv("data/socioeconomico/gdp_by_country.csv")
        if df.empty:
            st.info("Datos no disponibles.")
        else:
            df.columns = df.columns.str.strip().str.lower()
            ycol = next((c for c in df.columns if "year" in c), None)
            vcol = next((c for c in df.columns if "gdp" in c or "value" in c or "pib" in c), None)
            if not (ycol and vcol):
                st.info("Columnas no detectadas.")
            else:
                dd = df.groupby(ycol)[vcol].sum(numeric_only=True).reset_index().rename(columns={ycol:"Año", vcol:"PIB"})
                y0, y1 = max(int(dd["Año"].min()), int(dd["Año"].max())-50), int(dd["Año"].max())
                dd = dd[dd["Año"].between(y0, y1)]
                fig = px.line(dd, x="Año", y="PIB", labels={"PIB":"USD actuales"})
                fig.update_traces(line=dict(width=3))
                _mini_chart(fig)
        st.caption("PIB mundial agregado (USD actuales).")
        _btn("PIB y crecimiento económico")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: Consumo energético (área apilada de 4+ fuentes)
# ----------------------------------------
def card_energia():
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>⚡ Consumo energético</h4>", unsafe_allow_html=True)
        df = _safe_read_csv("data/energia/energy_consuption_by_source.csv")
        if df.empty:
            st.info("Datos no disponibles.")
        else:
            df.columns = df.columns.str.strip().str.lower()
            keep = ["coal_consumption","oil_consumption","gas_consumption","renewables_consumption","nuclear_consumption","hydro_consumption","wind_consumption","solar_consumption"]
            cols = [c for c in keep if c in df.columns]
            if "year" not in df.columns or not cols:
                st.info("Columnas no detectadas.")
            else:
                d = df.groupby("year")[cols].sum(numeric_only=True).reset_index().rename(columns={"year":"Año"})
                y0, y1 = max(int(d["Año"].min()), int(d["Año"].max())-50), int(d["Año"].max())
                dd = d[d["Año"].between(y0, y1)]
                dl = dd.melt(id_vars="Año", var_name="Fuente_raw", value_name="Consumo")
                map_names = {
                    "coal_consumption":"Carbón","oil_consumption":"Petróleo","gas_consumption":"Gas",
                    "renewables_consumption":"Renovables","nuclear_consumption":"Nuclear",
                    "hydro_consumption":"Hidro","wind_consumption":"Eólica","solar_consumption":"Solar"
                }
                dl["Fuente"] = dl["Fuente_raw"].map(map_names).fillna(dl["Fuente_raw"])
                fig = px.area(dl, x="Año", y="Consumo", color="Fuente", groupnorm=None)
                _mini_chart(fig)
        st.caption("Consumo energético global por fuente (TWh).")
        _btn("Consumo energético")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: Análisis multivariable (mini-scatter PIB vs CO₂ último año)
# ----------------------------------------
def card_multivariable():
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h4>🔗 Análisis multivariable</h4>", unsafe_allow_html=True)
        co2 = _safe_read_csv("data/socioeconomico/co2_emissions_by_country.csv")
        gdp = _safe_read_csv("data/socioeconomico/gdp_by_country.csv")
        if co2.empty or gdp.empty:
            st.info("Datos no disponibles.")
        else:
            co2.columns = co2.columns.str.strip().str.lower()
            gdp.columns = gdp.columns.str.strip().str.lower()
            y_co2 = next((c for c in co2.columns if "year" in c), None)
            c_co2 = next((c for c in co2.columns if "country" in c), None)
            v_co2 = next((c for c in co2.columns if "co2" in c or "emission" in c), None)
            y_gdp = next((c for c in gdp.columns if "year" in c), None)
            c_gdp = next((c for c in gdp.columns if "country" in c), None)
            v_gdp = next((c for c in gdp.columns if "gdp" in c or "value" in c or "pib" in c), None)
            if not all([y_co2, c_co2, v_co2, y_gdp, c_gdp, v_gdp]):
                st.info("Columnas insuficientes.")
            else:
                y_max = min(co2[y_co2].max(), gdp[y_gdp].max())
                a = co2[co2[y_co2]==y_max][[c_co2, v_co2]].rename(columns={c_co2:"Country", v_co2:"CO2"})
                b = gdp[gdp[y_gdp]==y_max][[c_gdp, v_gdp]].rename(columns={c_gdp:"Country", v_gdp:"GDP"})
                m = a.merge(b, on="Country").dropna()
                if m.empty:
                    st.info("Sin intersección de países en el último año.")
                else:
                    fig = px.scatter(m, x="GDP", y="CO2", hover_name="Country", labels={"GDP":"PIB (USD)", "CO2":"CO₂ (Mt)"})
                    fig.update_layout(xaxis_type="log", yaxis_type="log")
                    _mini_chart(fig)
        st.caption("Relación PIB–CO₂ (último año disponible).")
        _btn("Análisis multivariable")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------
# Tarjeta: Mapa global (mini-choropleth de PIB último año) — FULL WIDTH
# ----------------------------------------
def render_mapa_fullwidth():
    df = _safe_read_csv("data/socioeconomico/gdp_by_country.csv")
    if df.empty:
        st.info("Datos no disponibles para el mapa.")
        return
    df.columns = df.columns.str.strip().str.lower()
    ycol = next((c for c in df.columns if "year" in c), None)
    ccol = next((c for c in df.columns if "country" in c), None)
    vcol = next((c for c in df.columns if "gdp" in c or "value" in c or "pib" in c), None)
    if not (ycol and ccol and vcol):
        st.info("Columnas no detectadas para el mapa.")
        return
    y_max = int(df[ycol].max())
    m = df[df[ycol]==y_max].rename(columns={ccol:"Country", vcol:"Value"})
    m = m.dropna(subset=["Country","Value"])
    fig = px.choropleth(m, locations="Country", locationmode="country names",
                        color="Value", labels={"Value":"PIB"}, title=None)
    fig.update_layout(template=tpl, margin=dict(l=0, r=0, t=0, b=0), height=420, coloraxis_showscale=False)
    # Centrado: columna ancha al centro
    left, center, right = st.columns([1, 2.2, 1])
    with center:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("<p style='text-align:center;color:gray;'>PIB por país — último año disponible.</p>", unsafe_allow_html=True)
        # Botón centrado (sin f-string anidada)
        # 💡 Botón centrado con tema adaptativo
        if current_theme == "light":
            text_color = "#111111"
            bg_color = "rgba(0, 123, 123, 0.15)"  # turquesa claro, consistente con el resto
            border_color = "rgba(0, 123, 123, 0.35)"
        else:
            text_color = "#ffffff"
            bg_color = "rgba(255,255,255,0.07)"  # fondo translúcido
            border_color = "rgba(255,255,255,0.15)"

        btn_html = f"""
            <div class='cta' style='text-align:center;'>
                <a href='{page_url("Mapa global")}' target='_self'
                style="
                    display:inline-flex;
                    align-items:center;
                    justify-content:center;
                    gap:6px;
                    padding:10px 18px;
                    border-radius:10px;
                    font-weight:700;
                    text-decoration:none;
                    color:{text_color};
                    background:{bg_color};
                    border:1px solid {border_color};
                    backdrop-filter:blur(8px);
                    box-shadow:0 0 8px rgba(0,255,200,0.25);
                    transition:all 0.25s ease;
                "
                onmouseover="this.style.background='linear-gradient(135deg, var(--primary-color), #00bfa6)'; this.style.color='#ffffff'; this.style.boxShadow='0 0 16px rgba(0,255,200,0.45)'; this.style.transform='translateY(-2px)';"
                onmouseout="this.style.background='{bg_color}'; this.style.color='{text_color}'; this.style.boxShadow='0 0 8px rgba(0,255,200,0.25)'; this.style.transform='translateY(0)';"
                >
                🔎 Ver más →
                </a>
            </div>
        """

        st.markdown(btn_html, unsafe_allow_html=True)

# ----------------------------------------
# Rejilla de tarjetas (3 por fila) — SIN el mapa
# ----------------------------------------
cards = [
    card_temperatura, card_gases, card_nivel_mar,
    card_hielo, card_explora, card_poblacion,
    card_pib, card_energia, card_multivariable
]

# Render en filas de 3
for i in range(0, len(cards), 3):
    cols = st.columns(3, gap="large")
    for c, col in zip(cards[i:i+3], cols):
        with col:
            c()

# Separador y mapa centrado ancho completo
st.markdown("""
<div style='text-align:center; margin-top: 2.5rem;'>
  <h4 style='
    display: inline-block;
    font-weight: 850;
    font-size: 1.35rem;
    letter-spacing: -0.3px;
    padding: 10px 20px;
    border-radius: 12px;
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(6px);
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 0 8px rgba(0,0,0,0.25);
    color: var(--text-color);
    transition: box-shadow 0.3s ease, transform 0.2s ease;
  '>🗺️ Mapa global</h4>
</div>
""", unsafe_allow_html=True)

render_mapa_fullwidth()

# Footer
st.markdown("---")
st.markdown("""
<div style='
    display: flex;
    justify-content: center;
    margin-top: 2.5rem;
    margin-bottom: 1rem;
'>
  <div style='
      text-align: center;
      padding: 0.8rem 1.5rem;
      border-radius: 12px;
      background: rgba(255,255,255,0.06);
      backdrop-filter: blur(6px);
      border: 1px solid rgba(255,255,255,0.08);
      box-shadow: 0 0 6px rgba(0,0,0,0.2);
      color: var(--text-color);
      font-size: 0.9rem;
      letter-spacing: 0.2px;
      transition: all 0.25s ease;
  '>
    <b>TFM</b> · Marcos Abal Outeda · 2025
  </div>
</div>
""", unsafe_allow_html=True)
