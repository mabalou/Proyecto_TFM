# ==========================================
# 8_Consumo_energético_por_fuente.py — versión final sincronizada y completa
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
    """)

# ------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------
def _safe_read_csv(path, **kwargs) -> pd.DataFrame:
    """Lee un CSV manejando errores comunes de codificación."""
    try:
        return pd.read_csv(path, **kwargs)
    except Exception:
        try:
            return pd.read_csv(path, engine="python", **kwargs)
        except Exception:
            return pd.read_csv(path, comment="#", engine="python", **kwargs)

def es_columna_energetica(c: str) -> bool:
    """Detecta columnas relevantes de consumo energético."""
    c = c.lower()
    if c in ["country", "year", "iso_code", "population", "gdp"]:
        return False
    if any(x in c for x in ["per_capita", "share", "change", "pct"]):
        return False
    return "consumption" in c or "electricity" in c

NOMBRES_BONITOS = {
    "coal_consumption": "Carbón (TWh)",
    "oil_consumption": "Petróleo (TWh)",
    "gas_consumption": "Gas natural (TWh)",
    "renewables_consumption": "Renovables (TWh)",
    "nuclear_consumption": "Nuclear (TWh)",
    "hydro_consumption": "Hidroeléctrica (TWh)",
    "wind_consumption": "Eólica (TWh)",
    "solar_consumption": "Solar (TWh)",
}

def nombre_bonito(col: str) -> str:
    return NOMBRES_BONITOS.get(col.lower(), col.replace("_", " ").capitalize() + " (TWh)")

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = _safe_read_csv("data/energia/energy_consuption_by_source.csv")
    df.columns = df.columns.str.strip().str.lower()
    df = df.groupby("year").sum(numeric_only=True).reset_index()
    df_long = df.melt(id_vars="year", var_name="Fuente_raw", value_name="Consumo")
    df_long = df_long[df_long["Fuente_raw"].apply(es_columna_energetica)]
    df_long["Año"] = df_long["year"].astype(int)
    df_long["Fuente"] = df_long["Fuente_raw"].apply(nombre_bonito)
    df_long = df_long.dropna(subset=["Consumo"])
    return df_long, sorted(df_long["Fuente"].unique()), (int(df_long["Año"].min()), int(df_long["Año"].max()))

df_long, fuentes_disponibles, (min_year, max_year) = cargar_datos()

# ------------------------------------------
# ESTADO Y FILTROS
# ------------------------------------------
defaults = {
    "ui_show_filters": False,
    "fuentes_sel": fuentes_disponibles[:5],
    "rango": (max(1980, min_year), max_year),
    "tipo_grafico": "Línea",
    "usar_escala_log": False,
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# Asegura que el botón de filtros funcione
st.session_state.setdefault("ui_show_filters", False)

if st.session_state.ui_show_filters:
    with st.container(border=True):
        st.subheader("⚙️ Filtros de visualización")
        st.multiselect("Selecciona fuentes energéticas", fuentes_disponibles, key="fuentes_sel")
        st.slider("Rango de años", min_year, max_year, st.session_state.rango, key="rango")
        st.selectbox("Tipo de gráfico", ["Línea", "Área (apilada)", "Barras"], key="tipo_grafico")
        st.checkbox("📈 Mostrar línea de tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Mostrar media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")
        st.checkbox("🧮 Escala logarítmica", value=st.session_state.usar_escala_log, key="usar_escala_log")

fuentes_sel = st.session_state.fuentes_sel
rango = st.session_state.rango
tipo_grafico = st.session_state.tipo_grafico
usar_escala_log = st.session_state.usar_escala_log
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion

df_f = df_long[(df_long["Fuente"].isin(fuentes_sel)) & (df_long["Año"].between(*rango))]

# ------------------------------------------
# VISUALIZACIÓN Y RESUMEN LATERAL
# ------------------------------------------
st.subheader("📊 Consumo energético global por fuente")

if df_f.empty:
    st.info("Selecciona al menos una fuente y un rango válido para visualizar resultados.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    with col1:
        if tipo_grafico == "Línea":
            fig = px.line(df_f, x="Año", y="Consumo", color="Fuente", markers=True)
        elif tipo_grafico == "Área (apilada)":
            fig = px.area(df_f, x="Año", y="Consumo", color="Fuente")
        else:
            fig = px.bar(df_f, x="Año", y="Consumo", color="Fuente")

        fig.update_layout(
            xaxis_title="Año",
            yaxis_title="Consumo energético (TWh)",
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15)
        )

        if usar_escala_log:
            fig.update_yaxes(type="log")

        tendencias = {}
        if mostrar_tendencia:
            for fuente in fuentes_sel:
                df_src = df_f[df_f["Fuente"] == fuente]
                if len(df_src) > 1:
                    x = df_src["Año"].values.reshape(-1, 1)
                    y = df_src["Consumo"].values
                    modelo = LinearRegression().fit(x, y)
                    y_pred = modelo.predict(x)
                    tendencias[fuente] = modelo.coef_[0]
                    fig.add_scatter(x=df_src["Año"], y=y_pred, mode="lines", name=f"Tendencia {fuente}",
                                    line=dict(color="red", dash="dash", width=2))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🧾 Resumen del período")
        df_periodo = df_f.groupby("Fuente")["Consumo"].mean().sort_values(ascending=False).reset_index()
        fuente_max = df_periodo.iloc[0]["Fuente"]
        fuente_min = df_periodo.iloc[-1]["Fuente"]
        media_total = df_periodo["Consumo"].mean()
        st.markdown(f"""
        - 🔝 **Mayor consumo promedio:** {fuente_max}  
        - 🔻 **Menor consumo promedio:** {fuente_min}  
        - ⚖️ **Media global del período:** {media_total:,.0f} TWh  
        - 🗓️ **Período:** {rango[0]}–{rango[1]}  
        """)

# ------------------------------------------
# MEDIA POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_f.empty:
    st.subheader("📊 Media del consumo por década")
    df_dec = df_f.copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    df_grouped = df_dec.groupby(["Década", "Fuente"])["Consumo"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="Consumo", color="Fuente", barmode="group",
                     labels={"Consumo": "Consumo medio (TWh)"})
    fig_dec.update_layout(xaxis_title_font=dict(size=16), yaxis_title_font=dict(size=16))
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# PROYECCIÓN FUTURA
# ------------------------------------------
if mostrar_prediccion and not df_f.empty:
    st.subheader("🔮 Proyección del consumo energético hasta 2100")
    fig_pred = px.line(title="Proyección futura del consumo energético")
    for fuente in fuentes_sel:
        df_src = df_long[df_long["Fuente"] == fuente]
        if len(df_src) > 5:
            x = df_src["Año"].values.reshape(-1, 1)
            y = df_src["Consumo"].values
            modelo = LinearRegression().fit(x, y)
            x_pred = np.arange(x.max() + 1, 2101).reshape(-1, 1)
            y_pred = modelo.predict(x_pred)
            fig_pred.add_scatter(x=x_pred.flatten(), y=y_pred, mode="lines", name=fuente)
    st.plotly_chart(fig_pred, use_container_width=True)

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
if not df_f.empty and tendencias:
    st.subheader("🧩 Conclusiones automáticas")
    fuente_top = max(tendencias, key=tendencias.get)
    pendiente_top = tendencias[fuente_top]
    tendencia_txt = "ascendente" if pendiente_top > 0 else "descendente" if pendiente_top < 0 else "estable"
    color_box = "#006666" if pendiente_top > 0 else "#2e8b57" if pendiente_top < 0 else "#555555"

    texto = f"""
    ⚡ En el período **{rango[0]}–{rango[1]}**, la fuente con mayor variación es **{fuente_top}**,  
    mostrando una tendencia **{tendencia_txt}** a lo largo de las décadas.
    """

    st.markdown(f"<div style='background-color:{color_box};padding:1rem;border-radius:10px;color:white;'>{texto}</div>",
                unsafe_allow_html=True)

# ------------------------------------------
# DESCARGAS
# ------------------------------------------
st.markdown("---")
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)
with col1:
    csv = df_f.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv, file_name="consumo_energetico_filtrado.csv", mime="text/csv")
with col2:
    import plotly.io as pio
    # Exportar gráfico como HTML interactivo (compatible con Streamlit Cloud)
    html_bytes = pio.to_html(fig, full_html=False).encode("utf-8")
    st.download_button(
        "🖼️ Descargar gráfico (HTML interactivo)",
        data=html_bytes,
        file_name="grafico_energetico.html",
        mime="text/html"
    )
