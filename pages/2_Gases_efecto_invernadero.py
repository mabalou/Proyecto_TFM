# ==========================================
# 2_Gases_efecto_invernadero.py — versión mejorada (UI/UX)
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from sklearn.linear_model import LinearRegression

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="🌍 Gases de Efecto Invernadero", layout="wide")

st.title("🌍 Evolución de los Gases de Efecto Invernadero")

with st.expander("📘 Acerca de esta sección", expanded=True):
    st.markdown("""
    Esta página permite analizar la **evolución global** de los principales gases de efecto invernadero:
    **CO₂**, **CH₄** y **N₂O**, procedentes de mediciones NOAA.

    🔍 **Puedes:**
    - Visualizar series temporales interactivas (línea, área o barras).  
    - Calcular tendencias lineales y medias por década.  
    - Generar predicciones lineales hasta el año 2100.  
    - Comparar la evolución de los tres gases de forma normalizada.  
    - Exportar gráficos e información en formato **CSV**, **PNG** o **HTML interactivo**.
    """)

# ------------------------------------------
# CARGA DE DATOS ROBUSTA
# ------------------------------------------
@st.cache_data
def cargar_datos_gas(ruta_csv):
    with open(ruta_csv, "r", encoding="utf-8") as f:
        lineas = f.readlines()
    encabezado_index = next((i for i, l in enumerate(lineas) if "year" in l.lower() and "average" in l.lower()), 0)
    df = pd.read_csv(ruta_csv, skiprows=encabezado_index)
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={
        "year": "Año",
        "decimal": "Año_decimal",
        "average": "Concentración",
        "trend": "Tendencia"
    })
    df = df.dropna(subset=["Año", "Concentración"])
    df["Año"] = df["Año"].astype(int)
    return df

RUTAS = {
    "CO₂ (ppm)": "data/gases/greenhouse_gas_co2_global.csv",
    "CH₄ (ppb)": "data/gases/greenhouse_gas_ch4_global.csv",
    "N₂O (ppb)": "data/gases/greenhouse_gas_n2o_global.csv"
}

# ------------------------------------------
# SIDEBAR DE CONFIGURACIÓN
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

gas = st.sidebar.selectbox("Selecciona un gas", list(RUTAS.keys()))
tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])

df_temp = cargar_datos_gas(RUTAS[gas])
min_year, max_year = int(df_temp["Año"].min()), int(df_temp["Año"].max())
rango = st.sidebar.slider("Selecciona el rango de años", min_year, max_year, (1980, max_year))

mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)

# ------------------------------------------
# FILTRADO Y VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
df = df_temp.copy()
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

st.subheader(f"📈 Evolución global de {gas}")

if df_filtrado.empty:
    st.info("Selecciona un rango de años válido para visualizar los datos.")
else:
    eje_y = f"Concentración ({'ppm' if 'CO₂' in gas else 'ppb'})"
    if tipo_grafico == "Línea":
        fig = px.line(df_filtrado, x="Año", y="Concentración", markers=True,
                      labels={"Año": "Año", "Concentración": eje_y}, title=f"{gas} — Serie temporal")
    elif tipo_grafico == "Área":
        fig = px.area(df_filtrado, x="Año", y="Concentración",
                      labels={"Año": "Año", "Concentración": eje_y}, title=f"{gas} — Evolución acumulada")
    else:
        fig = px.bar(df_filtrado, x="Año", y="Concentración",
                     labels={"Año": "Año", "Concentración": eje_y}, title=f"{gas} — Variación anual")

    # Línea de tendencia
    if mostrar_tendencia:
        x = df_filtrado["Año"].values.reshape(-1, 1)
        y = df_filtrado["Concentración"].values
        modelo = LinearRegression().fit(x, y)
        y_pred = modelo.predict(x)
        fig.add_scatter(x=df_filtrado["Año"], y=y_pred, mode="lines",
                        name="Tendencia", line=dict(color="red", dash="dash", width=2))
        pendiente = modelo.coef_[0]

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.subheader("🧾 Resumen automático del análisis")

if not df_filtrado.empty:
    inicial, final = df_filtrado["Concentración"].iloc[0], df_filtrado["Concentración"].iloc[-1]
    cambio = final - inicial
    signo = "incremento" if cambio > 0 else "reducción" if cambio < 0 else "estabilidad"

    resumen = (
        f"📅 Entre **{rango[0]}** y **{rango[1]}**, la concentración de **{gas}** mostró un **{signo}** "
        f"de aproximadamente **{abs(cambio):.2f} unidades**. Actualmente se sitúa en **{final:.2f}** "
        f"frente a **{inicial:.2f}** al inicio del rango."
    )
    st.success(resumen)
else:
    st.info("Configura un rango válido para generar el resumen.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.markdown("---")
    st.subheader("📊 Media de concentraciones por década")

    df_decada = df_filtrado.copy()
    df_decada["Década"] = ((df_decada["Año"] // 10) * 10).astype(int)
    df_grouped = df_decada.groupby("Década")["Concentración"].mean().reset_index()

    st.dataframe(df_grouped.style.format({"Concentración": "{:.2f}"}), use_container_width=True)

    fig_dec = px.bar(df_grouped, x="Década", y="Concentración",
                     labels={"Concentración": eje_y},
                     title=f"Concentración promedio por década ({gas})",
                     color="Concentración", color_continuous_scale="Reds")
    st.plotly_chart(fig_dec, use_container_width=True)

    decada_max = df_grouped.loc[df_grouped["Concentración"].idxmax(), "Década"]
    valor_max = df_grouped["Concentración"].max()

    st.markdown(f"🌡️ La década con mayor concentración promedio fue **{int(decada_max)}**, con **{valor_max:.2f} {eje_y.split('(')[1]}**.")

# ------------------------------------------
# MODELO PREDICTIVO (hasta 2100)
# ------------------------------------------
if mostrar_prediccion:
    st.markdown("---")
    st.subheader("🔮 Predicción de concentración hasta 2100")

    if not df.empty:
        x_full = df["Año"].values.reshape(-1, 1)
        y_full = df["Concentración"].values
        modelo_pred = LinearRegression().fit(x_full, y_full)
        coefg = modelo_pred.coef_[0]

        años_futuros = np.arange(df["Año"].max() + 1, 2101).reshape(-1, 1)
        predicciones = modelo_pred.predict(años_futuros)

        fig_pred = px.line(x=años_futuros.ravel(), y=predicciones,
                           labels={"x": "Año", "y": eje_y},
                           title=f"Predicción futura de {gas} hasta 2100")
        st.plotly_chart(fig_pred, use_container_width=True)

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
if not df_filtrado.empty and 'coefg' in locals() and 'decada_max' in locals():
    st.markdown("---")
    st.subheader("🧩 Conclusiones automáticas")

    pendiente = coefg
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"
    frase_tend = (
        "📈 **Aumento sostenido de las concentraciones atmosféricas.**" if pendiente > 0 else
        "🟢 **Reducción o estabilización de los niveles globales.**" if pendiente < 0 else
        "➖ **Sin cambios significativos detectados.**"
    )

    color_fondo = "#ffcccc" if pendiente > 0 else "#ccffcc" if pendiente < 0 else "#e6e6e6"
    st.markdown(
        f"""
        <div style="background-color:{color_fondo}; color:#222; padding:15px; border-radius:12px; border:1px solid #bbb;">
            <h4>📋 <b>Conclusión Final ({rango[0]}–{rango[1]})</b></h4>
            <ul>
                <li>La tendencia de <b>{gas}</b> es <b>{tendencia}</b>.</li>
                <li>La década más concentrada fue <b>{int(decada_max)}</b> con <b>{valor_max:.2f}</b> unidades.</li>
            </ul>
            <p>{frase_tend}</p>
            <p style="font-size:0.9em;">🔮 Las conclusiones se actualizan automáticamente según el rango o gas seleccionado.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------------------------------
# COMPARATIVA GLOBAL ENTRE GASES
# ------------------------------------------
st.markdown("---")
st.subheader("🌐 Comparativa global de gases de efecto invernadero")

df_co2 = cargar_datos_gas(RUTAS["CO₂ (ppm)"])
df_ch4 = cargar_datos_gas(RUTAS["CH₄ (ppb)"])
df_n2o = cargar_datos_gas(RUTAS["N₂O (ppb)"])

df_comp = (
    df_co2[["Año", "Concentración"]].rename(columns={"Concentración": "CO₂"})
    .merge(df_ch4[["Año", "Concentración"]].rename(columns={"Concentración": "CH₄"}), on="Año", how="inner")
    .merge(df_n2o[["Año", "Concentración"]].rename(columns={"Concentración": "N₂O"}), on="Año", how="inner")
).dropna()

# Normalización 0–1
for g in ["CO₂", "CH₄", "N₂O"]:
    df_comp[g] = (df_comp[g] - df_comp[g].min()) / (df_comp[g].max() - df_comp[g].min())

df_melt = df_comp.melt(id_vars="Año", var_name="Gas", value_name="Concentración Normalizada")

fig_comp = px.line(df_melt, x="Año", y="Concentración Normalizada", color="Gas",
                   title="Comparativa normalizada de CO₂, CH₄ y N₂O (0–1)",
                   labels={"Concentración Normalizada": "Proporción relativa"})
st.plotly_chart(fig_comp, use_container_width=True)

# Determinar el gas con mayor crecimiento relativo
pendientes = {}
for g in ["CO₂", "CH₄", "N₂O"]:
    modelo_temp = LinearRegression().fit(df_comp[["Año"]], df_comp[g])
    pendientes[g] = modelo_temp.coef_[0]

gas_mas_rapido = max(pendientes, key=pendientes.get)
st.info(f"🚀 El gas con mayor tasa de crecimiento relativo es **{gas_mas_rapido}**, reflejando su impacto creciente en el cambio climático.")

# ------------------------------------------
# EXPORTACIÓN DE DATOS Y GRÁFICOS
# ------------------------------------------
st.markdown("---")
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)

with col1:
    try:
        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button("📄 Descargar CSV", data=csv,
                           file_name="gases_filtrados.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")

with col2:
    try:
        import plotly.io as pio
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer,
                           file_name="grafico_gases.png", mime="image/png")
    except Exception:
        st.warning("⚠️ No se pudo generar la imagen (Kaleido no disponible). Descarga el HTML interactivo:")
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)",
                           data=html_bytes, file_name="grafico_interactivo.html", mime="text/html")
