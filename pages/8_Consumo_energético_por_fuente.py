# ==========================================
# 8_Consumo_energético_por_fuente.py — versión final sincronizada con la cabecera global
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
from io import BytesIO

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="⚡ Consumo Energético por Fuente", layout="wide")
st.title("⚡ Evolución del consumo energético global")

with st.expander("📘 Acerca de esta sección", expanded=False):
    st.markdown("""
    Analiza la evolución del **consumo mundial de energía por fuente** (carbón, petróleo, gas, renovables, nuclear, hidro, etc.).  
    Incluye línea de tendencia, medias por década, **proyecciones hasta 2100** y **conclusiones automáticas**.  
    Al final, puedes **exportar** los datos filtrados (CSV) y el gráfico (PNG/HTML).
    """)

# ------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------
def _safe_read_csv(path, **kwargs) -> pd.DataFrame:
    try:
        return pd.read_csv(path, **kwargs)
    except Exception:
        try:
            return pd.read_csv(path, engine="python", **kwargs)
        except Exception:
            try:
                return pd.read_csv(path, comment="#", engine="python", **kwargs)
            except Exception as e:
                st.error(f"❌ No se pudo leer el CSV '{path}': {e}")
                return pd.DataFrame()

NON_ENERGY_COLS = {
    "country", "country name", "iso_code", "iso code", "iso", "region",
    "year", "population", "gdp", "continent"
}

def es_columna_energetica(c: str) -> bool:
    c = c.lower()
    if c in NON_ENERGY_COLS:
        return False
    if any(x in c for x in ["per_capita", "share", "change_pct", "change_twh", "intensity", "pct"]):
        return False
    return (
        c.endswith("_consumption")
        or c.endswith("_electricity")
        or c.endswith("_generation")
        or c in ["renewables_consumption", "fossil_fuel_consumption"]
    )

NOMBRES_BONITOS = {
    "coal_consumption": "Carbón (TWh)",
    "oil_consumption": "Petróleo (TWh)",
    "gas_consumption": "Gas natural (TWh)",
    "renewables_consumption": "Renovables (TWh)",
    "nuclear_consumption": "Nuclear (TWh)",
    "hydro_consumption": "Hidroeléctrica (TWh)",
    "biofuel_consumption": "Biocombustibles (TWh)",
    "solar_consumption": "Solar (TWh)",
    "wind_consumption": "Eólica (TWh)",
    "electricity_consumption": "Electricidad total (TWh)",
    "coal_electricity": "Electricidad a partir de carbón (TWh)",
    "gas_electricity": "Electricidad a partir de gas (TWh)",
    "oil_electricity": "Electricidad a partir de petróleo (TWh)",
    "nuclear_electricity": "Electricidad nuclear (TWh)",
    "hydro_electricity": "Electricidad hidro (TWh)",
    "wind_electricity": "Electricidad eólica (TWh)",
    "solar_electricity": "Electricidad solar (TWh)",
    "biofuel_electricity": "Electricidad biocombustibles (TWh)",
    "renewables_electricity": "Electricidad renovable (TWh)",
    "fossil_fuel_consumption": "Fósiles (TWh)",
}

def nombre_bonito(col: str) -> str:
    col_l = col.lower()
    if col_l in NOMBRES_BONITOS:
        return NOMBRES_BONITOS[col_l]
    return col_l.replace("_", " ").capitalize() + " (TWh)"

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos_energia_global():
    df = _safe_read_csv("data/energia/energy_consuption_by_source.csv")
    if df.empty:
        st.stop()

    df.columns = df.columns.str.strip().str.lower()

    if "year" not in df.columns:
        st.error("❌ No se encontró la columna 'year' en el CSV.")
        st.stop()

    agrupado = df.groupby("year").sum(numeric_only=True).reset_index()

    energy_cols = [c for c in agrupado.columns if es_columna_energetica(c)]
    if not energy_cols:
        st.error("❌ No se detectaron columnas energéticas válidas.")
        st.stop()

    largo = (
        agrupado[["year"] + energy_cols]
        .melt(id_vars="year", var_name="Fuente_raw", value_name="Consumo")
        .dropna()
    )

    largo["Consumo"] = pd.to_numeric(largo["Consumo"], errors="coerce")
    largo = largo.dropna(subset=["Consumo"])
    largo = largo.rename(columns={"year": "Año"})
    largo["Fuente"] = largo["Fuente_raw"].apply(nombre_bonito)

    mapping_display_to_raw = dict(zip(largo["Fuente"], largo["Fuente_raw"]))

    min_year, max_year = int(largo["Año"].min()), int(largo["Año"].max())
    default_raw = [
        "coal_consumption", "oil_consumption", "gas_consumption",
        "renewables_consumption", "nuclear_consumption", "hydro_consumption"
    ]
    defaults_display = [nombre_bonito(c) for c in default_raw if c in energy_cols]
    if not defaults_display:
        top_media = (
            largo.groupby("Fuente")["Consumo"].mean().sort_values(ascending=False).head(5).index.tolist()
        )
        defaults_display = top_media

    return largo, sorted(largo["Fuente"].unique().tolist()), defaults_display, (min_year, max_year), mapping_display_to_raw

df_long, fuentes_disponibles, defaults_display, (min_year, max_year), display_to_raw = cargar_datos_energia_global()

# ------------------------------------------
# FILTROS (compatibles con la cabecera global)
# ------------------------------------------
defaults = {
    "fuentes_sel": defaults_display,
    "rango": (max(1980, min_year), max_year),
    "tipo_grafico": "Línea",
    "usar_escala_log": False,
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.get("ui_show_filters", False):
    with st.container(border=True):
        st.subheader("⚙️ Filtros de visualización")
        st.multiselect("Selecciona fuentes energéticas", fuentes_disponibles, key="fuentes_sel", default=defaults_display)
        st.slider("Selecciona el rango de años", min_year, max_year, st.session_state["rango"], key="rango")
        st.selectbox("Tipo de gráfico", ["Línea", "Área (apilada)", "Barras"], key="tipo_grafico")
        st.checkbox("🧮 Usar escala logarítmica", key="usar_escala_log")
        st.checkbox("📈 Mostrar línea de tendencia", key="mostrar_tendencia")
        st.checkbox("📊 Mostrar media por décadas", key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", key="mostrar_prediccion")

fuentes_sel = st.session_state["fuentes_sel"]
rango = st.session_state["rango"]
tipo_grafico = st.session_state["tipo_grafico"]
usar_escala_log = st.session_state["usar_escala_log"]
mostrar_tendencia = st.session_state["mostrar_tendencia"]
mostrar_decadas = st.session_state["mostrar_decadas"]
mostrar_prediccion = st.session_state["mostrar_prediccion"]

# ------------------------------------------
# FILTRADO
# ------------------------------------------
df_f = df_long[(df_long["Fuente"].isin(fuentes_sel)) & (df_long["Año"].between(*rango))].copy()

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
titulo = "Evolución del consumo energético por fuente (global)"
if tipo_grafico == "Línea":
    fig = px.line(df_f, x="Año", y="Consumo", color="Fuente", markers=True,
                  labels={"Consumo": "Consumo energético (TWh)", "Año": "Año"}, title=titulo)
elif tipo_grafico == "Área (apilada)":
    fig = px.area(df_f, x="Año", y="Consumo", color="Fuente",
                  labels={"Consumo": "Consumo energético (TWh)", "Año": "Año"}, title=titulo)
else:
    fig = px.bar(df_f, x="Año", y="Consumo", color="Fuente",
                 labels={"Consumo": "Consumo energético (TWh)", "Año": "Año"}, title=titulo)

if usar_escala_log:
    fig.update_yaxes(type="log", title="Consumo energético (escala logarítmica)")

# ------------------------------------------
# TENDENCIAS
# ------------------------------------------
tendencias = {}
if mostrar_tendencia or mostrar_prediccion:
    for fuente in fuentes_sel:
        df_src = df_f[df_f["Fuente"] == fuente]
        if len(df_src) > 1:
            x = df_src["Año"].values.reshape(-1, 1)
            y = df_src["Consumo"].values
            modelo = LinearRegression().fit(x, y)
            y_pred = modelo.predict(x)
            pendientes = modelo.coef_[0]
            tendencias[fuente] = pendientes
            if mostrar_tendencia:
                fig.add_scatter(x=df_src["Año"], y=y_pred, mode="lines", name=f"Tendencia {fuente}",
                                line=dict(dash="dash", width=2))

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.subheader("🧾 Resumen automático del análisis")
if not df_f.empty:
    df_reciente = df_f[df_f["Año"] == df_f["Año"].max()]
    fuente_max = df_reciente.loc[df_reciente["Consumo"].idxmax(), "Fuente"]
    valor_max = df_reciente["Consumo"].max()
    st.markdown(f"⚡ En **{int(df_reciente['Año'].max())}**, la fuente con mayor consumo fue **{fuente_max}** con **{valor_max:,.0f} TWh**.")
else:
    st.info("Selecciona al menos una fuente y un rango válido para visualizar resultados.")

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
if not df_f.empty and tendencias:
    st.markdown("---")
    st.subheader("🧩 Conclusiones automáticas")
    fuente_top = max(tendencias, key=tendencias.get)
    pendiente_top = tendencias[fuente_top]
    tendencia_txt = "ascendente" if pendiente_top > 0 else "descendente" if pendiente_top < 0 else "estable"
    color_fondo = "#ffcccc" if pendiente_top > 0 else "#ccffcc" if pendiente_top < 0 else "#e6e6e6"

    st.markdown(f"""
    <div style="background-color:{color_fondo}; color:#222;
                padding:15px; border-radius:12px; border:1px solid #bbb;">
        <h4>📋 <b>Conclusión final del análisis ({rango[0]}–{rango[1]})</b></h4>
        <ul>
            <li>La fuente con <b>mayor variación</b> es <b>{fuente_top}</b>, con una tendencia <b>{tendencia_txt}</b>.</li>
        </ul>
        <p>🔮 Estas conclusiones se actualizan automáticamente según el rango y las fuentes seleccionadas.</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------
# DESCARGAS
# ------------------------------------------
st.markdown("---")
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)

with col1:
    try:
        csv = df_f.to_csv(index=False).encode("utf-8")
        st.download_button("📄 Descargar CSV", data=csv, file_name="consumo_energetico_filtrado.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")

with col2:
    try:
        import plotly.io as pio
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer, file_name="grafico_consumo_energetico.png", mime="image/png")
    except Exception:
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico interactivo (HTML)", data=html_bytes, file_name="grafico_energetico_interactivo.html", mime="text/html")
