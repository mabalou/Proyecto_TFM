# ==========================================
# 2_Gases_efecto_invernadero.py — versión sincronizada con header
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="🌍 Gases de Efecto Invernadero", layout="wide")
st.title("🌍 Evolución de los Gases de Efecto Invernadero")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Esta sección permite analizar la **evolución global** de los principales gases de efecto invernadero:
    **CO₂**, **CH₄** y **N₂O**, con datos procedentes de la **NOAA**.

    🔍 Puedes:
    - Visualizar series temporales interactivas (línea, área o barras).
    - Calcular tendencias lineales y medias por década.
    - Generar predicciones lineales hasta 2100.
    - Comparar la evolución de los tres gases normalizados.
    """)

# ------------------------------------------
# CARGA DE DATOS
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
# ESTADO Y FILTROS
# ------------------------------------------
defaults = {
    "ui_show_filters": False,
    "gas": "CO₂ (ppm)",
    "tipo_grafico": "Línea",
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# Sincronía con el botón del header (ya gestionado por 00_Inicio)
# Si ui_show_filters es True → se muestran los controles
if st.session_state.ui_show_filters:
    with st.container(border=True):
        st.subheader("⚙️ Filtros de visualización")

        st.selectbox("Selecciona el gas", list(RUTAS.keys()), key="gas")
        st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")

        df_temp = cargar_datos_gas(RUTAS[st.session_state.gas])
        min_year, max_year = int(df_temp["Año"].min()), int(df_temp["Año"].max())
        st.slider("Selecciona el rango de años", min_year, max_year, (1980, max_year), key="rango")

        st.checkbox("📈 Mostrar línea de tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Mostrar media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")

# -------------------------------
# USO DE FILTROS
# -------------------------------
gas = st.session_state.gas
tipo_grafico = st.session_state.tipo_grafico
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion

df = cargar_datos_gas(RUTAS[gas])
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())
rango = st.session_state.get("rango", (1980, max_year))
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
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
    with st.expander("📊 Media de concentraciones por década", expanded=True):
        df_decada = df_filtrado.copy()
        df_decada["Década"] = ((df_decada["Año"] // 10) * 10).astype(int)
        df_grouped = df_decada.groupby("Década")["Concentración"].mean().reset_index()

        st.dataframe(df_grouped.style.format({"Concentración": "{:.2f}"}), use_container_width=True)
        fig_dec = px.bar(df_grouped, x="Década", y="Concentración",
                         labels={"Concentración": eje_y},
                         title=f"Concentración promedio por década ({gas})",
                         color="Concentración", color_continuous_scale="Reds")
        st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# MODELO PREDICTIVO (hasta 2100)
# ------------------------------------------
if mostrar_prediccion:
    st.markdown("---")
    with st.expander("🔮 Proyección hasta 2100", expanded=True):
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
# COMPARATIVA GLOBAL ENTRE GASES
# ------------------------------------------
st.markdown("---")
with st.expander("🌐 Comparativa global de gases de efecto invernadero", expanded=True):
    df_co2 = cargar_datos_gas(RUTAS["CO₂ (ppm)"])
    df_ch4 = cargar_datos_gas(RUTAS["CH₄ (ppb)"])
    df_n2o = cargar_datos_gas(RUTAS["N₂O (ppb)"])

    df_comp = (
        df_co2[["Año", "Concentración"]].rename(columns={"Concentración": "CO₂"})
        .merge(df_ch4[["Año", "Concentración"]].rename(columns={"Concentración": "CH₄"}), on="Año", how="inner")
        .merge(df_n2o[["Año", "Concentración"]].rename(columns={"Concentración": "N₂O"}), on="Año", how="inner")
    ).dropna()

    for g in ["CO₂", "CH₄", "N₂O"]:
        df_comp[g] = (df_comp[g] - df_comp[g].min()) / (df_comp[g].max() - df_comp[g].min())

    df_melt = df_comp.melt(id_vars="Año", var_name="Gas", value_name="Concentración Normalizada")
    fig_comp = px.line(df_melt, x="Año", y="Concentración Normalizada", color="Gas",
                       title="Comparativa normalizada de CO₂, CH₄ y N₂O (0–1)",
                       labels={"Concentración Normalizada": "Proporción relativa"})
    st.plotly_chart(fig_comp, use_container_width=True)

# ------------------------------------------
# EXPORTACIÓN
# ------------------------------------------
st.markdown("---")
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)
with col1:
    try:
        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button("📄 Descargar CSV", data=csv, file_name="gases_filtrados.csv", mime="text/csv")
    except Exception as e:
        st.error(f"No se pudo generar el CSV: {e}")
with col2:
    try:
        import plotly.io as pio
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer, file_name="grafico_gases.png", mime="image/png")
    except Exception:
        st.warning("⚠️ No se pudo generar la imagen (Kaleido no disponible). Descarga el HTML interactivo:")
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)", data=html_bytes,
                           file_name="grafico_interactivo.html", mime="text/html")
