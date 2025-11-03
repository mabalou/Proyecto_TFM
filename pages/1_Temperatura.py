# ==========================================
# 1_Temperatura.py — versión mejorada (UI/UX)
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="🌡️ Evolución de la Temperatura Global", layout="wide")

st.title("🌍 Evolución de la Temperatura Global")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=True):
    st.markdown("""
    Esta sección analiza las **anomalías de temperatura global** reportadas por **NASA GISTEMP**.  
    Puedes comparar **estaciones del año**, detectar **tendencias lineales**, explorar **medias por década**  
    y generar una **predicción futura hasta el año 2100**.
    
    **Funciones principales:**
    - Selección de períodos y variables.
    - Cálculo de tendencias lineales y medias por década.
    - Modelo predictivo polinómico (hasta 2100).
    - Exportación de datos y gráficos (CSV, PNG o HTML interactivo).
    """)

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/temperatura/global_temperature_nasa.csv", skiprows=1)
    df = df[["Year", "J-D", "DJF", "MAM", "JJA", "SON"]]
    df = df.replace("***", np.nan)
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna()
    return df

df = cargar_datos()

# ------------------------------------------
# SIDEBAR DE OPCIONES
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
rango = st.sidebar.slider("Selecciona el rango de años", min_year, max_year, (1970, max_year))
series_disponibles = ["J-D", "DJF", "MAM", "JJA", "SON"]
series_seleccionadas = st.sidebar.multiselect("Variables a visualizar", series_disponibles, default=["J-D"])
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)
usar_escala_log = st.sidebar.checkbox("🧮 Escala logarítmica", value=False)

# ------------------------------------------
# FILTRADO DE DATOS
# ------------------------------------------
df_filtrado = df[(df["Year"] >= rango[0]) & (df["Year"] <= rango[1])]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
st.subheader("📊 Anomalías globales de temperatura")
if df_filtrado.empty:
    st.info("Selecciona al menos una variable y un rango válido para visualizar los datos.")
else:
    if tipo_grafico == "Línea":
        fig = px.line(df_filtrado, x="Year", y=series_seleccionadas, markers=True,
                      labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"},
                      title="Anomalía de temperatura global")
    elif tipo_grafico == "Área":
        fig = px.area(df_filtrado, x="Year", y=series_seleccionadas,
                      labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"},
                      title="Anomalía de temperatura global")
    else:
        fig = px.bar(df_filtrado, x="Year", y=series_seleccionadas,
                     labels={"value": "Anomalía (°C)", "variable": "Variable", "Year": "Año"},
                     title="Anomalía de temperatura global")

    if usar_escala_log:
        fig.update_yaxes(type="log")

    # Añadir tendencia si aplica
    if mostrar_tendencia and len(series_seleccionadas) == 1:
        y = df_filtrado[series_seleccionadas[0]].values
        x = df_filtrado["Year"].values
        coef = np.polyfit(x, y, 1)
        tendencia = coef[0] * x + coef[1]
        fig.add_scatter(x=x, y=tendencia, mode="lines", name="Tendencia",
                        line=dict(color="red", dash="dash", width=2))

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
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
        resumen += (
            "\n\n📈 **Tendencia ascendente en la temperatura global promedio.**" if pendiente_global > 0 else
            "\n\n🟢 **Tendencia descendente o estabilización térmica.**" if pendiente_global < 0 else
            "\n\n➖ **Estabilidad sin variaciones significativas.**"
        )

    st.success(resumen)
else:
    st.info("Configura las variables y rango para generar el resumen.")

# ------------------------------------------
# MÉTRICAS DESTACADAS
# ------------------------------------------
st.markdown("---")
st.subheader("🔎 Indicadores destacados")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📆 Rango seleccionado", f"{rango[0]}–{rango[1]}")
with col2:
    st.metric("🌡️ Variable más cálida", max_serie)
with col3:
    st.metric("🌍 Promedio global", f"{df_filtrado[series_seleccionadas].mean().mean():.3f} °C")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
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
    st.markdown(
        f"📅 La década más cálida fue **{int(decada_max)}**, con una anomalía media de **{valor_max:.3f} °C**."
    )

# ------------------------------------------
# PREDICCIÓN HASTA 2100
# ------------------------------------------
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

        fig_pred = px.line(x=x_pred, y=y_pred,
                           labels={"x": "Año", "y": "Anomalía (°C)"},
                           title=titulo)
        st.plotly_chart(fig_pred, use_container_width=True)

        if coef[0] > 0:
            st.markdown("🌡️ **El modelo sugiere un incremento acelerado de la temperatura hacia finales de siglo.**")
        elif coef[0] < 0:
            st.markdown("🟢 **El modelo predice un enfriamiento gradual en las próximas décadas.**")
        else:
            st.markdown("➖ **El modelo muestra estabilidad sin cambios notables.**")

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
if not df_filtrado.empty and 'coefg' in locals() and 'decada_max' in locals():
    st.subheader("🧩 Conclusiones automáticas")

    pendiente = coefg[0] if isinstance(coefg, (list, np.ndarray)) else coefg
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"

    color_fondo = "#ffcccc" if pendiente > 0 else "#ccffcc" if pendiente < 0 else "#e6e6e6"

    st.markdown(
        f"""
        <div style="background-color:{color_fondo}; color:#222; padding:15px; border-radius:12px; border:1px solid #bbb;">
            <h4>📋 <b>Conclusión Final ({rango[0]}–{rango[1]})</b></h4>
            <ul>
                <li>La tendencia global es <b>{tendencia}</b> según las anomalías promedio.</li>
                <li>La década más cálida fue <b>{int(decada_max)}</b> con una media de <b>{valor_max:.3f} °C</b>.</li>
            </ul>
            <p>📈 Estos resultados se actualizan automáticamente al cambiar el rango o las variables.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------------------------------
# EXPORTACIÓN DE DATOS Y GRÁFICOS
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)

with col1:
    try:
        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button("📄 Descargar CSV", data=csv,
                           file_name="temperatura_filtrada.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")

with col2:
    try:
        buffer = BytesIO()
        import plotly.io as pio
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer,
                           file_name="grafico_temperatura.png", mime="image/png")
    except Exception:
        st.warning("⚠️ No se pudo generar el PNG (Kaleido no disponible). Descarga el HTML interactivo:")
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)",
                           data=html_bytes, file_name="grafico_interactivo.html", mime="text/html")
