# ==========================================
# 1_Temperatura.py — usa el botón de la cabecera
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="🌡️ Evolución de la Temperatura Global", layout="wide")
st.title("🌍 Evolución de la Temperatura Global")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Esta sección analiza las **anomalías de temperatura global** reportadas por **NASA GISTEMP**.  
    Puedes comparar **estaciones del año**, detectar **tendencias**, explorar **medias por década**
    y generar una **proyección hasta 2100**.
    """)

@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/temperatura/global_temperature_nasa.csv", skiprows=1)
    df = df[["Year", "J-D", "DJF", "MAM", "JJA", "SON"]]
    df = df.replace("***", np.nan)
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna()

df = cargar_datos()
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
series_disponibles = ["J-D", "DJF", "MAM", "JJA", "SON"]

# -------------------------------
# Estado (persistente) y sincronía con header
# -------------------------------
defaults = {
    "ui_show_filters": False,
    "tipo_grafico": "Línea",
    "rango": (max(1970, min_year), max_year),
    "series_seleccionadas": ["J-D"],
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
    "usar_escala_log": False,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# Si viene el query param 'filters', ya lo leyó 00_Inicio y actualizó st.session_state.ui_show_filters

# -------------------------------
# (Quitamos el toggle duplicado de la página)
# -------------------------------
# Antes estaba: st.toggle("⚙️ Filtros", key="ui_show_filters")
# Ahora se controla desde el encabezado.

# -------------------------------
# Panel de filtros
# -------------------------------
if st.session_state.ui_show_filters:
    with st.container(border=True):
        st.subheader("⚙️ Filtros de visualización")
        st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
        st.slider("Selecciona el rango de años", min_year, max_year, st.session_state.rango, key="rango")
        st.multiselect("Variables a visualizar", series_disponibles, default=st.session_state.series_seleccionadas, key="series_seleccionadas")
        st.checkbox("📈 Mostrar línea de tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Mostrar media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")
        st.checkbox("🧮 Escala logarítmica", value=st.session_state.usar_escala_log, key="usar_escala_log")

# -------------------------------
# USO DE VALORES
# -------------------------------
tipo_grafico        = st.session_state.tipo_grafico
rango               = st.session_state.rango
series_seleccionadas= st.session_state.series_seleccionadas
mostrar_tendencia   = st.session_state.mostrar_tendencia
mostrar_decadas     = st.session_state.mostrar_decadas
mostrar_prediccion  = st.session_state.mostrar_prediccion
usar_escala_log     = st.session_state.usar_escala_log

df_filtrado = df[(df["Year"] >= rango[0]) & (df["Year"] <= rango[1])]

st.subheader("📊 Anomalías globales de temperatura")
if df_filtrado.empty or len(series_seleccionadas) == 0:
    st.info("Configura los filtros para visualizar los datos.")
else:
    if tipo_grafico == "Línea":
        fig = px.line(df_filtrado, x="Year", y=series_seleccionadas, markers=True,
                      labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"})
    elif tipo_grafico == "Área":
        fig = px.area(df_filtrado, x="Year", y=series_seleccionadas,
                      labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"})
    else:
        fig = px.bar(df_filtrado, x="Year", y=series_seleccionadas,
                     labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"})
    if usar_escala_log:
        fig.update_yaxes(type="log")
    if mostrar_tendencia and len(series_seleccionadas) == 1:
        y = df_filtrado[series_seleccionadas[0]].values
        x = df_filtrado["Year"].values
        if len(x) > 1:
            coef = np.polyfit(x, y, 1)
            tendencia = coef[0] * x + coef[1]
            fig.add_scatter(x=x, y=tendencia, mode="lines", name="Tendencia",
                            line=dict(color="red", dash="dash", width=2))
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🧾 Resumen automático del análisis")
if not df_filtrado.empty:
    df_mean = df_filtrado[series_seleccionadas].mean()
    max_serie = df_mean.idxmax()
    min_serie = df_mean.idxmin()
    max_val = df_mean.max()
    min_val = df_mean.min()
    resumen = (
        f"🌡️ Entre **{rango[0]}–{rango[1]}**, la variable con mayor anomalía promedio fue "
        f"**{max_serie}** (**{max_val:.3f} °C**), mientras que la menor fue **{min_serie}** (**{min_val:.3f} °C**)."
    )
    df_global = df_filtrado[["Year"] + series_seleccionadas].copy()
    df_global["Promedio"] = df_global[series_seleccionadas].mean(axis=1)
    xg, yg = df_global["Year"].values, df_global["Promedio"].values
    if len(xg) > 5:
        coefg = np.polyfit(xg, yg, 1)
        pendiente_global = coefg[0]
        resumen += ("\n\n📈 **Tendencia ascendente en la temperatura global promedio.**" if pendiente_global > 0
                    else "\n\n🟢 **Tendencia descendente o estabilización térmica.**" if pendiente_global < 0
                    else "\n\n➖ **Estabilidad sin variaciones significativas.**")
    st.success(resumen)
else:
    st.info("Configura las variables y rango para generar el resumen.")

st.markdown("---")
st.subheader("🔎 Indicadores destacados")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📆 Rango seleccionado", f"{rango[0]}–{rango[1]}")
with col2:
    st.metric("🌡️ Variable más cálida", max_serie if not df_filtrado.empty else "—")
with col3:
    st.metric("🌍 Promedio global", f"{df_filtrado[series_seleccionadas].mean().mean():.3f} °C" if not df_filtrado.empty else "—")

if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Media de anomalías por década")
    df_decada = df_filtrado.copy()
    df_decada["Década"] = ((df_decada["Year"] // 10) * 10).astype(int)
    df_grouped = df_decada.groupby("Década")[series_seleccionadas].mean().reset_index()
    st.dataframe(df_grouped.style.format("{:.3f}"), use_container_width=True)
    fig_dec = px.bar(df_grouped, x="Década", y=series_seleccionadas,
                     labels={"value": "Anomalía promedio (°C)", "variable": "Variable"},
                     barmode="group", title="Anomalías medias por década")
    st.plotly_chart(fig_dec, use_container_width=True)
    decada_max = df_grouped.iloc[df_grouped[series_seleccionadas].mean(axis=1).idxmax()]["Década"]
    valor_max = df_grouped[series_seleccionadas].mean(axis=1).max()
    st.markdown(f"📅 La década más cálida fue **{int(decada_max)}**, con una anomalía media de **{valor_max:.3f} °C**.")

if mostrar_prediccion:
    st.subheader("🔮 Proyección hasta 2100")
    if len(series_seleccionadas) == 1:
        serie = series_seleccionadas[0]
        df_pred = df[["Year", serie]].dropna().sort_values("Year")
        titulo = f"Predicción futura ({serie})"
    else:
        df_pred = df[["Year"] + series_seleccionadas].copy()
        df_pred["Promedio"] = df_pred[series_seleccionadas].mean(axis=1)
        df_pred = df_pred[["Year", "Promedio"]].dropna().sort_values("Year")
        serie = "Promedio"
        titulo = "Predicción futura (promedio de series seleccionadas)"
    x, y = df_pred["Year"].values, df_pred[serie].values
    if len(x) > 5:
        coef = np.polyfit(x, y, 2)
        x_pred = np.arange(x.max() + 1, 2101)
        y_pred = np.polyval(coef, x_pred)
        fig_pred = px.line(x=x_pred, y=y_pred, labels={"x": "Año", "y": "Anomalía (°C)"}, title=titulo)
        st.plotly_chart(fig_pred, use_container_width=True)
        st.markdown("🌡️ **El modelo sugiere un incremento acelerado de la temperatura hacia finales de siglo.**" if coef[0] > 0
                    else "🟢 **El modelo predice un enfriamiento gradual en las próximas décadas.**" if coef[0] < 0
                    else "➖ **El modelo muestra estabilidad sin cambios notables.**")

# Exportación (sin cambios)
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)
with col1:
    try:
        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button("📄 Descargar CSV", data=csv, file_name="temperatura_filtrada.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")
with col2:
    try:
        buffer = BytesIO()
        import plotly.io as pio
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer, file_name="grafico_temperatura.png", mime="image/png")
    except Exception:
        st.warning("⚠️ No se pudo generar el PNG (Kaleido no disponible). Descarga el HTML interactivo:")
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)", data=html_bytes, file_name="grafico_interactivo.html", mime="text/html")
