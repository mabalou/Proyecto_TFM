# ==========================================
# 1_Temperatura.py
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="🌡️ Visualizador climático TFM", layout="wide")
st.title("🌍 Evolución de la Temperatura Global")
st.markdown("""
Analiza la evolución de las anomalías de temperatura global (NASA GISTEMP) de forma interactiva.  
Explora tendencias, variaciones por década y proyecciones futuras hasta el año 2100.
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
    st.success("✅ Resumen generado dinámicamente según el rango y variables seleccionadas.")

    df_mean = df_filtrado[series_seleccionadas].mean()
    max_serie = df_mean.idxmax()
    min_serie = df_mean.idxmin()
    max_val = df_mean.max()
    min_val = df_mean.min()

    resumen = (
        f"🌡️ Durante el periodo **{rango[0]}–{rango[1]}**, la variable con mayor anomalía promedio fue "
        f"**{max_serie}**, con aproximadamente **{max_val:.3f} °C**.\n\n"
        f"❄️ La variable con menor anomalía promedio fue **{min_serie}**, con **{min_val:.3f} °C**."
    )

    df_global = df_filtrado[["Year"] + series_seleccionadas].copy()
    df_global["Promedio"] = df_global[series_seleccionadas].mean(axis=1)
    xg = df_global["Year"].values
    yg = df_global["Promedio"].values

    if len(xg) > 5:
        coefg = np.polyfit(xg, yg, 1)
        pendiente_global = coefg[0]

        if pendiente_global > 0:
            resumen += "\n\n📈 En general, se observa una **tendencia ascendente** en la temperatura global promedio."
        elif pendiente_global < 0:
            resumen += "\n\n🟢 En conjunto, los datos muestran una **tendencia descendente**, indicando enfriamiento."
        else:
            resumen += "\n\n➖ Las anomalías se han mantenido **relativamente estables** durante el periodo analizado."

    st.markdown(resumen)
else:
    st.info("Selecciona al menos una variable y un rango de años válido para generar el resumen.")

# ------------------------------------------
# MÉTRICAS DESTACADAS
# ------------------------------------------
st.subheader("🔎 Indicadores destacados")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📆 Rango seleccionado", f"{rango[0]} - {rango[1]}")
with col2:
    st.metric("🌡️ Variable con mayor promedio", max_serie)
with col3:
    st.metric("🌍 Valor medio global", f"{df_filtrado[series_seleccionadas].mean().mean():.3f} °C")

st.markdown("""
🧭 **Observación general:** Las anomalías de temperatura global reflejan un calentamiento sostenido en las últimas décadas, 
especialmente en las estaciones más cálidas del hemisferio norte.
""")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas:
    st.subheader("📊 Media de anomalías por década")

    df_decada = df_filtrado.copy()
    df_decada["Década"] = ((df_decada["Year"] // 10) * 10).astype(int)
    df_grouped = df_decada.groupby("Década")[series_seleccionadas].mean().reset_index()

    st.dataframe(df_grouped.style.format("{:.3f}"), use_container_width=True)

    fig_dec = px.bar(
        df_grouped,
        x="Década",
        y=series_seleccionadas,
        labels={"value": "Anomalía promedio (°C)", "variable": "Variable"},
        barmode="group",
        title="Anomalías medias por década"
    )
    st.plotly_chart(fig_dec, use_container_width=True)

    decada_max = df_grouped.iloc[df_grouped[series_seleccionadas].mean(axis=1).idxmax()]["Década"]
    valor_max = df_grouped[series_seleccionadas].mean(axis=1).max()
    st.markdown(
        f"📅 La década con mayor anomalía media fue la de **{int(decada_max)}**, "
        f"con un promedio de **{valor_max:.3f} °C** sobre el valor de referencia."
    )

# ------------------------------------------
# MODELO PREDICTIVO (hasta 2100)
# ------------------------------------------
if mostrar_prediccion:
    st.subheader("🔮 Predicción de anomalías de temperatura hasta 2100")

    if len(series_seleccionadas) == 1:
        serie = series_seleccionadas[0]
        df_pred = df[["Year", serie]].dropna().sort_values("Year")
        titulo = f"Predicción futura de anomalía de temperatura ({serie})"
    else:
        df_pred = df[["Year"] + series_seleccionadas].copy()
        df_pred["Promedio"] = df_pred[series_seleccionadas].mean(axis=1)
        df_pred = df_pred[["Year", "Promedio"]].dropna().sort_values("Year")
        serie = "Promedio"
        titulo = "Predicción futura del promedio de anomalías seleccionadas"

    x = df_pred["Year"].values
    y = df_pred[serie].values

    if len(x) > 5:
        coef = np.polyfit(x, y, 2)
        x_pred = np.arange(x.max() + 1, 2101)
        y_pred = np.polyval(coef, x_pred)

        fig_pred = px.line(
            x=x_pred, y=y_pred,
            labels={"x": "Año", "y": "Anomalía (°C)"},
            title=titulo
        )
        st.plotly_chart(fig_pred, use_container_width=True)

        if coef[0] > 0:
            st.markdown("🌡️ **El modelo sugiere un incremento acelerado de la temperatura hacia finales de siglo.**")
        elif coef[0] < 0:
            st.markdown("🟢 **El modelo predice una tendencia de enfriamiento gradual en las próximas décadas.**")
        else:
            st.markdown("➖ **El modelo muestra una tendencia estable sin variaciones significativas.**")
    else:
        st.info("Datos insuficientes para generar la predicción.")

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS CON COLOR (legibles)
# ------------------------------------------
if not df_filtrado.empty and 'coefg' in locals() and 'decada_max' in locals():
    st.subheader("🧩 Conclusiones automáticas")

    pendiente = coefg[0] if isinstance(coefg, (list, np.ndarray)) else coefg

    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"
    frase_tend = (
        "📈 **Calentamiento global significativo.**" if pendiente > 0 else
        "🟢 **Tendencia a la estabilización o enfriamiento.**" if pendiente < 0 else
        "➖ **Sin variaciones térmicas relevantes.**"
    )

    # Colores mejor contrastados
    color_fondo = "#ffcccc" if pendiente > 0 else "#ccffcc" if pendiente < 0 else "#e6e6e6"
    color_texto = "#222"  # gris oscuro para buena legibilidad

    st.markdown(
        f"""
        <div style="background-color:{color_fondo}; color:{color_texto}; padding:15px; border-radius:12px; border:1px solid #bbb;">
            <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
            <ul>
                <li>La tendencia global es <b>{tendencia}</b>, basada en las anomalías promedio seleccionadas.</li>
                <li>La década más cálida fue la de <b>{int(decada_max)}</b>, con una anomalía media de <b>{valor_max:.3f} °C</b>.</li>
            </ul>
            <p>{frase_tend}</p>
            <p style="font-size:0.9em; color:#444;">🔮 Estas conclusiones se actualizan automáticamente al modificar el rango o las variables.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------
# DESCARGAS
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)
with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv, file_name="temperatura_filtrada.csv", mime="text/csv")
with col2:
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("🖼️ Descargar gráfico", data=buffer, file_name="grafico_temperatura.png", mime="image/png")
