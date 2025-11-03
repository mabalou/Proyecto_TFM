# ==========================================
# 2_Gases_efecto_invernadero.py
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
st.markdown("""
Analiza la evolución de la concentración global de los principales gases de efecto invernadero — **CO₂**, **CH₄** y **N₂O** — en la atmósfera.  
Explora tendencias, variaciones por décadas, predicciones futuras y comparativas globales.
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
# SIDEBAR
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

gas = st.sidebar.selectbox("Selecciona un gas", list(RUTAS.keys()))
tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"])

# Mover el rango de años aquí (debajo del tipo de gráfico)
df_temp = cargar_datos_gas(RUTAS[gas])
min_year, max_year = int(df_temp["Año"].min()), int(df_temp["Año"].max())
rango = st.sidebar.slider("Selecciona el rango de años", min_year, max_year, (1980, max_year))

# Opciones avanzadas debajo
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)

# ------------------------------------------
# CARGA FINAL Y FILTRADO
# ------------------------------------------
df = df_temp.copy()
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
titulo = f"Evolución global de {gas}"
eje_y = f"Concentración ({'ppm' if 'CO₂' in gas else 'ppb'})"

if tipo_grafico == "Línea":
    fig = px.line(df_filtrado, x="Año", y="Concentración", markers=True,
                  labels={"Año": "Año", "Concentración": eje_y}, title=titulo)
elif tipo_grafico == "Área":
    fig = px.area(df_filtrado, x="Año", y="Concentración",
                  labels={"Año": "Año", "Concentración": eje_y}, title=titulo)
else:
    fig = px.bar(df_filtrado, x="Año", y="Concentración",
                 labels={"Año": "Año", "Concentración": eje_y}, title=titulo)

# Línea de tendencia
if mostrar_tendencia and not df_filtrado.empty:
    x = df_filtrado["Año"].values.reshape(-1, 1)
    y = df_filtrado["Concentración"].values
    modelo = LinearRegression()
    modelo.fit(x, y)
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
        f"📅 Entre **{rango[0]}** y **{rango[1]}**, la concentración global de **{gas}** mostró un **{signo}** "
        f"de aproximadamente **{abs(cambio):.2f} unidades**.\n\n"
        f"📈 La concentración actual se sitúa en torno a **{final:.2f}**, frente a **{inicial:.2f}** en los primeros años del rango."
    )
    st.markdown(resumen)
else:
    st.info("Selecciona un rango de años válido para generar el resumen.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas:
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

    st.markdown(f"🌡️ La década con mayor concentración promedio fue la de **{int(decada_max)}**, con **{valor_max:.2f} {eje_y.split('(')[1]}**.")

# ------------------------------------------
# MODELO PREDICTIVO (hasta 2100)
# ------------------------------------------
if mostrar_prediccion and not df.empty:
    st.subheader("🔮 Predicción de concentración hasta 2100")

    x_full = df["Año"].values.reshape(-1, 1)
    y_full = df["Concentración"].values
    modelo_pred = LinearRegression()
    modelo_pred.fit(x_full, y_full)
    coefg = modelo_pred.coef_[0]

    años_futuros = np.arange(df["Año"].max() + 1, 2101).reshape(-1, 1)
    predicciones = modelo_pred.predict(años_futuros)

    fig_pred = px.line(x=años_futuros.ravel(), y=predicciones,
                       labels={"x": "Año", "y": eje_y},
                       title=f"Predicción futura de concentración de {gas} hasta 2100")
    st.plotly_chart(fig_pred, use_container_width=True)

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS CON COLOR
# ------------------------------------------
if not df_filtrado.empty and 'coefg' in locals() and 'decada_max' in locals():
    st.subheader("🧩 Conclusiones automáticas")

    pendiente = coefg
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"
    frase_tend = (
        "📈 **Aumento sostenido de las concentraciones atmosféricas.**" if pendiente > 0 else
        "🟢 **Reducción o estabilización de los niveles globales.**" if pendiente < 0 else
        "➖ **Sin cambios significativos detectados.**"
    )

    color_fondo = "#ffcccc" if pendiente > 0 else "#ccffcc" if pendiente < 0 else "#e6e6e6"
    color_texto = "#222"

    st.markdown(
        f"""
        <div style="background-color:{color_fondo}; color:{color_texto}; padding:15px; border-radius:12px; border:1px solid #bbb;">
            <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
            <ul>
                <li>La tendencia global de <b>{gas}</b> es <b>{tendencia}</b> durante el periodo analizado.</li>
                <li>La década con mayor concentración fue la de <b>{int(decada_max)}</b>, con un promedio de <b>{valor_max:.2f}</b>.</li>
            </ul>
            <p>{frase_tend}</p>
            <p style="font-size:0.9em; color:#444;">🔮 Estas conclusiones se actualizan automáticamente al modificar el gas o el rango temporal.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------------------------------
# COMPARATIVA GLOBAL ENTRE GASES
# ------------------------------------------
st.subheader("📊 Comparativa global de gases de efecto invernadero")

df_co2 = cargar_datos_gas(RUTAS["CO₂ (ppm)"])
df_ch4 = cargar_datos_gas(RUTAS["CH₄ (ppb)"])
df_n2o = cargar_datos_gas(RUTAS["N₂O (ppb)"])

# Combinar por año usando inner join (solo años comunes)
df_comp = (
    df_co2[["Año", "Concentración"]].rename(columns={"Concentración": "CO₂"})
    .merge(df_ch4[["Año", "Concentración"]].rename(columns={"Concentración": "CH₄"}), on="Año", how="inner")
    .merge(df_n2o[["Año", "Concentración"]].rename(columns={"Concentración": "N₂O"}), on="Año", how="inner")
)

# Eliminar posibles valores nulos
df_comp = df_comp.dropna()

# Normalizar concentraciones (0–1)
for g in ["CO₂", "CH₄", "N₂O"]:
    df_comp[g] = (df_comp[g] - df_comp[g].min()) / (df_comp[g].max() - df_comp[g].min())

# Reorganizar para gráfico
df_comp_melt = df_comp.melt(id_vars="Año", var_name="Gas", value_name="Concentración Normalizada")

# Gráfico comparativo
fig_comp = px.line(
    df_comp_melt,
    x="Año",
    y="Concentración Normalizada",
    color="Gas",
    title="Comparativa normalizada de gases de efecto invernadero (CO₂, CH₄, N₂O)",
    labels={"Concentración Normalizada": "Proporción (0–1)"}
)
st.plotly_chart(fig_comp, use_container_width=True)

# Determinar el gas con mayor pendiente
pendientes = {}
for g in ["CO₂", "CH₄", "N₂O"]:
    X = df_comp[["Año"]].values
    y = df_comp[g].values
    modelo_temp = LinearRegression()
    modelo_temp.fit(X, y)
    pendientes[g] = modelo_temp.coef_[0]

gas_mas_rapido = max(pendientes, key=pendientes.get)

st.markdown(
    f"🚀 **El gas con mayor tasa de crecimiento relativo en el periodo analizado es {gas_mas_rapido},** "
    f"lo que indica un impacto creciente sobre el calentamiento global."
)

# ------------------------------------------
# DESCARGAS
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)
with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv,
                       file_name=f"{gas.replace(' ', '_')}_filtrado.csv", mime="text/csv")
with col2:
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("🖼️ Descargar gráfico", data=buffer,
                       file_name=f"{gas.replace(' ', '_')}_grafico.png", mime="image/png")
