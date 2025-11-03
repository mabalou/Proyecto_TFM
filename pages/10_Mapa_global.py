# ==========================================
# 10_Mapa_global.py — Mapa climático global interactivo
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="🗺️ Mapa climático global", layout="wide")
st.title("🌍 Mapa climático global interactivo")
with st.expander("ℹ️ ¿Qué muestra esta página?"):
    st.markdown("""
**Visualiza la evolución espacial** de indicadores de clima y variables socioeconómicas por país.
- Arriba a la izquierda elige la **variable** (CO₂ total / per cápita / PIB / PIB per cápita / Población).
- A la derecha selecciona el **año** con el **slider manual**. Si marcas **“🎞️ Animar por años”**,
  verás la evolución automática.
- Debajo aparece un **Top-10** de países (solo países reales, sin agregados como *World* o *High income*).
- Al final verás la **tendencia temporal** del **Top-5** del año seleccionado.
""")

# -------------------------------
# Utilidades / limpieza
# -------------------------------
AGG_PATTERNS = [
    "world", "income", "ibrd", "ida", "oecd",
    "european union", "euro area",
    "east asia", "south asia", "north america",
    "latin america", "caribbean", "central asia",
    "middle east", "north africa", "sub-saharan",
    "small states", "pacific island", "post-demographic",
    "pre-demographic", "early-demographic", "late-demographic"
]

def es_pais_real(name: str) -> bool:
    if not isinstance(name, str) or not name.strip():
        return False
    n = name.strip().lower()
    return not any(pat in n for pat in AGG_PATTERNS)

@st.cache_data
def _safe_read_csv(path, **kwargs):
    try:
        return pd.read_csv(path, **kwargs)
    except Exception:
        try:
            return pd.read_csv(path, engine="python", **kwargs)
        except Exception:
            return pd.read_csv(path, engine="python", comment="#", **kwargs)

def _normaliza(df: pd.DataFrame, country_key=("country name","country"), year_key="year", value_key="value"):
    """Devuelve DataFrame con columnas: Country, Year, Value"""
    if df is None or df.empty:
        return pd.DataFrame(columns=["Country","Year","Value"])
    cols = {c.lower(): c for c in df.columns}
    # país
    ccol = None
    for k in country_key:
        if k in cols: ccol = cols[k]; break
    # año
    ycol = cols.get(year_key, None)
    # valor
    vcol = cols.get(value_key, None)
    if ccol is None or ycol is None or vcol is None:
        # si el CSV ya viene con nombres “bonitos”
        ccol = cols.get("country", ccol)
        ycol = cols.get("year", ycol)
        vcol = cols.get("value", vcol)
    out = df.rename(columns={ccol:"Country", ycol:"Year", vcol:"Value"})[["Country","Year","Value"]]
    out["Year"] = pd.to_numeric(out["Year"], errors="coerce")
    out["Value"] = pd.to_numeric(out["Value"], errors="coerce")
    out = out.dropna(subset=["Country","Year","Value"])
    # filtra agregados/regiones
    out = out[out["Country"].map(es_pais_real)]
    return out

# -------------------------------
# Carga de datos (según tus CSV)
# -------------------------------
@st.cache_data
def load_all():
    # CO2 total
    co2 = _safe_read_csv("data/socioeconomico/co2_emissions_by_country.csv")
    co2.columns = co2.columns.str.strip().str.lower()
    co2_total = _normaliza(co2.rename(columns={"co2":"value"}) if "co2" in co2.columns else co2)

    # CO2 per cápita (si existe)
    co2_pc = pd.DataFrame(columns=["Country","Year","Value"])
    for cand in ["co2_per_capita_t","co2_per_capita","co2_pc"]:
        if cand in co2.columns:
            co2_pc = _normaliza(co2.rename(columns={cand:"value"}))
            break

    # Intensidad CO2 por 1k USD (si existe)
    co2_int = pd.DataFrame(columns=["Country","Year","Value"])
    for cand in ["co2_intensity_t_per_1k_usd","co2_intensity", "co2_per_gdp"]:
        if cand in co2.columns:
            co2_int = _normaliza(co2.rename(columns={cand:"value"}))
            break

    # PIB
    gdp = _safe_read_csv("data/socioeconomico/gdp_by_country.csv")
    gdp.columns = gdp.columns.str.strip().str.lower()
    gdp_total = _normaliza(gdp)  # value ya suele ser el PIB total en USD
    gdp_pc = pd.DataFrame(columns=["Country","Year","Value"])
    for cand in ["gdp_per_capita_usd","gdp_per_capita"]:
        if cand in gdp.columns:
            gdp_pc = _normaliza(gdp.rename(columns={cand:"value"}))
            break

    # Población
    pop = _safe_read_csv("data/socioeconomico/population_by_country.csv")
    pop.columns = pop.columns.str.strip().str.lower()
    pop_df = _normaliza(pop)

    # Un diccionario con lo disponible (solo añadimos si no está vacío)
    variables = {}
    if not co2_total.empty: variables["CO₂ total (Mt)"] = co2_total
    if not co2_pc.empty:    variables["CO₂ per cápita (t)"] = co2_pc
    if not co2_int.empty:   variables["Intensidad CO₂ (t / 1k USD)"] = co2_int
    if not gdp_total.empty: variables["PIB (USD)"] = gdp_total
    if not gdp_pc.empty:    variables["PIB per cápita (USD)"] = gdp_pc
    if not pop_df.empty:    variables["Población"] = pop_df

    # min/max años globales
    if variables:
        miny = int(min(v["Year"].min() for v in variables.values()))
        maxy = int(max(v["Year"].max() for v in variables.values()))
    else:
        miny, maxy = 1960, 2022

    return variables, (miny, maxy)

variables, (min_year, max_year) = load_all()
if not variables:
    st.error("No se han podido cargar variables desde los CSV. Revisa las rutas y columnas.")
    st.stop()

# -------------------------------
# Sidebar de control
# -------------------------------
st.sidebar.header("🎛️ Controles")
var_name = st.sidebar.selectbox("Variable a visualizar", options=list(variables.keys()))
animar = st.sidebar.checkbox("🎞️ Animar por años", value=False)

year = st.sidebar.slider("Año", min_value=min_year, max_value=max_year, value=min(max_year, max_year))
dfv = variables[var_name]

# -------------------------------
# Mapa
# -------------------------------
st.subheader(f"{var_name} por país")
fmt = ",.2f" if "USD" in var_name or "CO₂" in var_name else ",.0f"

if animar:
    # Animación año a año
    mdf = dfv.copy()
    fig_map = px.choropleth(
        mdf, locations="Country", locationmode="country names",
        color="Value", hover_name="Country", animation_frame="Year",
        color_continuous_scale="Viridis",
        labels={"Value": var_name},
        title=None
    )
else:
    mdf = dfv[dfv["Year"] == year].copy()
    fig_map = px.choropleth(
        mdf, locations="Country", locationmode="country names",
        color="Value", hover_name="Country",
        color_continuous_scale="Viridis",
        labels={"Value": var_name},
        title=None
    )

fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))
fig_map.update_traces(hovertemplate="<b>%{hovertext}</b><br>" + var_name + ": %{z:," + (".2f" if fmt==",.2f" else ".0f") + "}")
st.plotly_chart(fig_map, use_container_width=True)

# -------------------------------
# 🏆 Top-10 países (año seleccionado)
# -------------------------------
st.subheader(f"🏆 Top 10 países — {year}")

top_df = (
    dfv[dfv["Year"] == year]
    .dropna(subset=["Value"])
    .sort_values("Value", ascending=False)
    .head(10)
    .rename(columns={"Country": "País", "Value": var_name})
)

if not top_df.empty:
    # ====== Formateo elegante ======
    top_df_display = top_df.copy()
    if "USD" in var_name:
        top_df_display[var_name] = top_df_display[var_name].apply(lambda x: f"${x:,.0f}")
    elif "CO2" in var_name or "CO₂" in var_name:
        top_df_display[var_name] = top_df_display[var_name].apply(lambda x: f"{x:,.0f} Mt CO₂")
    elif "Población" in var_name:
        top_df_display[var_name] = top_df_display[var_name].apply(lambda x: f"{x:,.0f} hab.")
    else:
        top_df_display[var_name] = top_df_display[var_name].apply(lambda x: f"{x:,.2f}")

    st.dataframe(top_df_display, use_container_width=True)

    # ====== Resumen automático ======
    pais_top = top_df.iloc[0]["País"]
    valor_top = top_df.iloc[0][var_name]
    texto_valor = (
        f"{valor_top:,.0f} Mt CO₂" if "CO2" in var_name or "CO₂" in var_name
        else f"{valor_top:,.0f} USD" if "USD" in var_name
        else f"{valor_top:,.0f} hab." if "Población" in var_name
        else f"{valor_top:,.2f}"
    )

    st.markdown(
        f"""
        **📊 Resumen:**  
        En **{year}**, el país con mayor **{var_name.replace('_', ' ')}** fue  
        **{pais_top}**, con un valor de **{texto_valor}**.
        """,
        unsafe_allow_html=True,
    )

else:
    st.info("No hay datos para el año seleccionado.")

# -------------------------------
# Tendencia temporal (Top-5 del año)
# -------------------------------
st.subheader("📈 Tendencia temporal del Top-5")
top5 = top_df["País"].head(5).tolist()
trend = dfv[dfv["Country"].isin(top5)].copy()
fig_line = px.line(
    trend, x="Year", y="Value", color="Country",
    labels={"Year": "Año", "Value": var_name, "Country": "País"},
    title=None, markers=True
)
st.plotly_chart(fig_line, use_container_width=True)

# -------------------------------
# Descargas
# -------------------------------
st.subheader("💾 Exportar")
c1, c2 = st.columns(2)
with c1:
    try:
        csv = mdf.rename(columns={"Country":"País","Year":"Año","Value":var_name}).to_csv(index=False).encode("utf-8")
        st.download_button("📄 Descargar datos (CSV)", data=csv, file_name="mapa_global_filtrado.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")
with c2:
    try:
        import plotly.io as pio
        from io import BytesIO
        buffer = BytesIO()
        fig_map.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar mapa (PNG)", data=buffer, file_name="mapa_global.png", mime="image/png")
    except Exception:
        html_bytes = fig_map.to_html().encode("utf-8")
        st.download_button("🌐 Descargar mapa (HTML interactivo)", data=html_bytes, file_name="mapa_global.html", mime="text/html")
