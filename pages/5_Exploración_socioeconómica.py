# ==========================================
# 5_Exploración_socioeconómica.py
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="📊 Exploración Socioeconómica", layout="wide")
st.title("📉 Evolución de las Emisiones de CO₂ por País")
st.markdown("""
Analiza la evolución de las emisiones de dióxido de carbono (CO₂) a nivel nacional.  
Explora diferencias entre países, tendencias históricas y proyecciones futuras hasta 2100.
""")

# ------------------------------------------
# CARGA ROBUSTA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/socioeconomico/co2_emissions_by_country.csv")
    df.columns = df.columns.str.strip().str.lower()

    year_col = next((c for c in df.columns if "year" in c), None)
    country_col = next((c for c in df.columns if "country" in c), None)
    emission_col = next((c for c in df.columns if "co2" in c or "emission" in c), None)

    if not all([year_col, country_col, emission_col]):
        st.error(f"No se encontraron columnas esperadas en el CSV.\n\nColumnas detectadas: {list(df.columns)}")
        st.stop()

    df = df.rename(columns={
        year_col: "Year",
        country_col: "Country",
        emission_col: "CO2_Emissions_Mt"
    })

    df = df[["Year", "Country", "CO2_Emissions_Mt"]].dropna()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["CO2_Emissions_Mt"] = pd.to_numeric(df["CO2_Emissions_Mt"], errors="coerce")

    return df

df = cargar_datos()

# ------------------------------------------
# SIDEBAR
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

paises = sorted(df["Country"].unique())
paises_seleccionados = st.sidebar.multiselect("Selecciona países", paises, default=["Spain", "United States"])

min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
rango = st.sidebar.slider("Selecciona el rango de años", min_year, max_year, (1980, max_year))

tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)
usar_escala_log = st.sidebar.checkbox("🧮 Escala logarítmica", value=False)

# ------------------------------------------
# FILTRADO DE DATOS
# ------------------------------------------
df_filtrado = df[(df["Country"].isin(paises_seleccionados)) & (df["Year"].between(*rango))]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
if tipo_grafico == "Línea":
    fig = px.line(df_filtrado, x="Year", y="CO2_Emissions_Mt", color="Country", markers=True,
                  labels={"CO2_Emissions_Mt": "Emisiones (Mt CO₂)", "Country": "País", "Year": "Año"},
                  title="Evolución de las emisiones de CO₂")
elif tipo_grafico == "Área":
    fig = px.area(df_filtrado, x="Year", y="CO2_Emissions_Mt", color="Country",
                  labels={"CO2_Emissions_Mt": "Emisiones (Mt CO₂)", "Country": "País", "Year": "Año"},
                  title="Evolución de las emisiones de CO₂")
else:
    fig = px.bar(df_filtrado, x="Year", y="CO2_Emissions_Mt", color="Country",
                 labels={"CO2_Emissions_Mt": "Emisiones (Mt CO₂)", "Country": "País", "Year": "Año"},
                 title="Evolución de las emisiones de CO₂")

if usar_escala_log:
    fig.update_yaxes(type="log")

# Línea de tendencia (solo si hay un país seleccionado)
if mostrar_tendencia and len(paises_seleccionados) == 1:
    pais = paises_seleccionados[0]
    df_pais = df_filtrado[df_filtrado["Country"] == pais]
    x = df_pais["Year"].values
    y = df_pais["CO2_Emissions_Mt"].values
    coef = np.polyfit(x, y, 1)
    tendencia = coef[0] * x + coef[1]
    fig.add_scatter(x=x, y=tendencia, mode="lines", name="Tendencia", line=dict(color="red", dash="dash"))

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.subheader("🧾 Resumen automático del análisis")

if not df_filtrado.empty:
    st.success("✅ Resumen generado dinámicamente según el rango y países seleccionados.")

    df_mean = df_filtrado.groupby("Country")["CO2_Emissions_Mt"].mean().sort_values(ascending=False)
    top_pais = df_mean.idxmax()
    top_val = df_mean.max()
    min_pais = df_mean.idxmin()
    min_val = df_mean.min()

    resumen = (
        f"🌍 Durante el periodo **{rango[0]}–{rango[1]}**, el país con mayores emisiones promedio fue **{top_pais}** "
        f"con aproximadamente **{top_val:.2f} Mt de CO₂** por año.\n\n"
        f"🌱 El país con menores emisiones promedio fue **{min_pais}**, con **{min_val:.2f} Mt de CO₂**."
    )

    # Tendencia global (promedio conjunto)
    df_global = df_filtrado.groupby("Year")["CO2_Emissions_Mt"].mean().reset_index()
    xg = df_global["Year"].values
    yg = df_global["CO2_Emissions_Mt"].values

    if len(xg) > 5:
        coefg = np.polyfit(xg, yg, 1)
        pendiente_global = coefg[0]

        if pendiente_global > 0:
            resumen += "\n\n📈 En conjunto, las emisiones globales muestran una **tendencia ascendente sostenida**."
        elif pendiente_global < 0:
            resumen += "\n\n🟢 Se observa una **reducción o estabilización** en las emisiones promedio globales."
        else:
            resumen += "\n\n➖ Las emisiones se han mantenido **relativamente estables** durante el periodo analizado."

    st.markdown(resumen)
else:
    st.info("Selecciona al menos un país y un rango válido para generar el resumen.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas:
    st.subheader("📊 Media de emisiones por década")

    df_decada = df_filtrado.copy()
    df_decada["Década"] = ((df_decada["Year"] // 10) * 10).astype(int)
    df_grouped = df_decada.groupby(["Década", "Country"])["CO2_Emissions_Mt"].mean().reset_index()

    st.dataframe(df_grouped.style.format({"CO2_Emissions_Mt": "{:.2f}"}), use_container_width=True)

    fig_dec = px.bar(df_grouped, x="Década", y="CO2_Emissions_Mt", color="Country",
                     labels={"CO2_Emissions_Mt": "Emisiones promedio (Mt CO₂)", "Country": "País"},
                     barmode="group",
                     title="Emisiones promedio por década")
    st.plotly_chart(fig_dec, use_container_width=True)

    # Década con mayor promedio global
    df_prom = df_grouped.groupby("Década")["CO2_Emissions_Mt"].mean()
    decada_max = df_prom.idxmax()
    valor_max = df_prom.max()
    st.markdown(
        f"📅 La década con mayores emisiones promedio fue la de **{int(decada_max)}**, "
        f"con una media global de **{valor_max:.2f} Mt de CO₂**."
    )

# ------------------------------------------
# MODELO PREDICTIVO (hasta 2100)
# ------------------------------------------
if mostrar_prediccion:
    st.subheader("🔮 Predicción de emisiones hasta 2100")

    if len(paises_seleccionados) == 1:
        df_pred = df[df["Country"] == paises_seleccionados[0]]
        serie = paises_seleccionados[0]
    else:
        df_pred = df[df["Country"].isin(paises_seleccionados)].groupby("Year")["CO2_Emissions_Mt"].mean().reset_index()
        serie = "Promedio Global"

    x = df_pred["Year"].values
    y = df_pred["CO2_Emissions_Mt"].values

    if len(x) > 5:
        coef = np.polyfit(x, y, 2)
        x_pred = np.arange(x.max() + 1, 2101)
        y_pred = np.polyval(coef, x_pred)

        fig_pred = px.line(x=x_pred, y=y_pred,
                           labels={"x": "Año", "y": "Emisiones (Mt CO₂)"},
                           title=f"Predicción futura de emisiones ({serie}) hasta 2100")
        st.plotly_chart(fig_pred, use_container_width=True)

        if coef[0] > 0:
            st.markdown("🌡️ **El modelo sugiere un incremento acelerado de las emisiones hacia finales de siglo.**")
        elif coef[0] < 0:
            st.markdown("🟢 **El modelo predice una disminución gradual en las próximas décadas.**")
        else:
            st.markdown("➖ **El modelo muestra estabilidad sin variaciones significativas.**")

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS CON COLOR
# ------------------------------------------
if not df_filtrado.empty and 'coefg' in locals() and 'decada_max' in locals():
    st.subheader("🧩 Conclusiones automáticas")

    pendiente = coefg[0] if isinstance(coefg, (list, np.ndarray)) else coefg
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"
    frase_tend = (
        "📈 **Aumento sostenido de las emisiones de CO₂.**" if pendiente > 0 else
        "🟢 **Reducción o estabilización en las emisiones globales.**" if pendiente < 0 else
        "➖ **Sin cambios relevantes en las emisiones.**"
    )

    color_fondo = "#ffcccc" if pendiente > 0 else "#ccffcc" if pendiente < 0 else "#e6e6e6"
    color_texto = "#222"

    st.markdown(
        f"""
        <div style="background-color:{color_fondo}; color:{color_texto}; padding:15px; border-radius:12px; border:1px solid #bbb;">
            <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
            <ul>
                <li>La tendencia global de emisiones es <b>{tendencia}</b> en el periodo analizado.</li>
                <li>La década más emisora fue la de <b>{int(decada_max)}</b>, con una media de <b>{valor_max:.2f} Mt CO₂</b>.</li>
            </ul>
            <p>{frase_tend}</p>
            <p style="font-size:0.9em; color:#444;">🔮 Estas conclusiones se actualizan automáticamente al modificar el rango o los países seleccionados.</p>
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
    st.download_button("📄 Descargar CSV", data=csv, file_name="emisiones_filtradas.csv", mime="text/csv")
with col2:
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("🖼️ Descargar gráfico", data=buffer, file_name="grafico_emisiones.png", mime="image/png")
