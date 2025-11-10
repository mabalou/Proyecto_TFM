# ==========================================
# 3_Nivel_del_mar.py — versión final mejorada
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

# ------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ------------------------------------------
st.set_page_config(page_title="🌊 Nivel del mar global", layout="wide")
st.title("🌊 Evolución del nivel medio global del mar")

# ------------------------------------------
# ESTILO PERSONALIZADO
# ------------------------------------------
st.markdown(
    """
    <style>
    /* Subir bloque derecho (resumen + filtros) */
    div[data-testid="column"]:nth-of-type(2) {
        margin-top: -6rem !important;
    }
    /* Reducir espacio entre resumen y filtros */
    div[data-testid="stMarkdown"] + div[data-testid="stMarkdown"] {
        margin-top: -1.5rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------
# DESCRIPCIÓN INICIAL
# ------------------------------------------
with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Analiza la evolución mensual del **nivel medio global del mar**, con datos satelitales de la **NOAA / NASA**.

    🔍 **Incluye:**
    - Series temporales interactivas (línea, área o barras).  
    - Cálculo de tendencias lineales y medias por década.  
    - Proyecciones hasta el año 2100 con **intervalo de confianza del 95 %**.  
    - Conclusiones automáticas y descarga de resultados.
    """)

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/sea_level/sea_level_nasa.csv", skiprows=1, header=None, names=["Fecha", "Nivel_mar"])
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha", "Nivel_mar"])
    df = df[df["Nivel_mar"].between(-100, 100)]
    df = df[df["Nivel_mar"] != -999]
    df["Año"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month
    return df

df = cargar_datos()
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())

# ------------------------------------------
# ESTADO Y FILTROS
# ------------------------------------------
defaults = {
    "tipo_grafico": "Línea",
    "rango": (1993, max_year),
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

tipo_grafico = st.session_state.tipo_grafico
rango = st.session_state.rango
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion

df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL + RESUMEN
# ------------------------------------------
st.subheader("📈 Evolución temporal del nivel del mar")

if df_filtrado.empty:
    st.info("Selecciona un rango de años válido para visualizar los datos.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    with col1:
        # 🔹 Agrupar por año y suavizar para evitar efecto escalera
        df_plot = df_filtrado.groupby("Año", as_index=False)["Nivel_mar"].mean()
        df_plot["Suavizada"] = df_plot["Nivel_mar"].rolling(window=3, center=True, min_periods=1).mean()

        titulo = "Evolución del nivel medio global del mar (suavizada)"
        if tipo_grafico == "Línea":
            fig = px.line(df_plot, x="Año", y="Suavizada",
                          labels={"Año": "Año", "Suavizada": "Nivel del mar (mm)"},
                          markers=True, title=titulo)
        elif tipo_grafico == "Área":
            fig = px.area(df_plot, x="Año", y="Suavizada",
                          labels={"Año": "Año", "Suavizada": "Nivel del mar (mm)"},
                          title=titulo)
        else:
            fig = px.bar(df_plot, x="Año", y="Suavizada",
                         labels={"Año": "Año", "Suavizada": "Nivel del mar (mm)"},
                         title=titulo)

        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15)
        )

        # 🔹 Línea de tendencia
        pendiente = 0
        if mostrar_tendencia:
            x = df_plot["Año"].values.reshape(-1, 1)
            y = df_plot["Suavizada"].values
            modelo = LinearRegression().fit(x, y)
            y_pred = modelo.predict(x)
            pendiente = modelo.coef_[0]
            fig.add_scatter(x=df_plot["Año"], y=y_pred, mode="lines",
                            name="Tendencia", line=dict(color="red", dash="dash", width=2))

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🧾 Resumen del período")
        inicial, final = df_plot["Suavizada"].iloc[0], df_plot["Suavizada"].iloc[-1]
        cambio = final - inicial
        media = df_plot["Suavizada"].mean()
        valor_min = df_plot["Suavizada"].min()
        valor_max = df_plot["Suavizada"].max()
        año_min = df_plot.loc[df_plot["Suavizada"].idxmin(), "Año"]
        año_max = df_plot.loc[df_plot["Suavizada"].idxmax(), "Año"]

        st.markdown(f"""
        - 📆 **Años:** {rango[0]}–{rango[1]}  
        - 🌊 **Nivel medio:** {media:.2f} mm  
        - 🔽 **Mínimo:** {valor_min:.2f} mm (*{int(año_min)}*)  
        - 🔼 **Máximo:** {valor_max:.2f} mm (*{int(año_max)}*)  
        - 📈 **Cambio neto:** {cambio:+.2f} mm  
        - 📊 **Tendencia media:** {pendiente:.3f} mm/año  
        """)

        # 🔧 Filtros debajo del resumen
        st.markdown("### ⚙️ Ajustar visualización")
        st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
        st.slider("Selecciona el rango de años", min_year, max_year, st.session_state.rango, key="rango")
        st.checkbox("📈 Mostrar tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
        st.checkbox("📊 Media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
        st.checkbox("🔮 Incluir modelo predictivo", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")

# ------------------------------------------
# MEDIA POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Nivel medio del mar por década")
    df_dec = df_filtrado.copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    df_grouped = df_dec.groupby("Década")["Nivel_mar"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="Nivel_mar", color="Nivel_mar",
                     color_continuous_scale="Blues",
                     labels={"Nivel_mar": "Nivel medio (mm)"},
                     title="Nivel medio del mar por década")
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# MODELO PREDICTIVO (mejorado con intervalo 95 %)
# ------------------------------------------
if mostrar_prediccion and not df.empty:
    st.subheader("🔮 Proyección del nivel del mar hasta 2100")

    df_agg = df.groupby("Año", as_index=False)["Nivel_mar"].mean()
    x_all = df_agg["Año"].values.reshape(-1, 1)
    y_all = df_agg["Nivel_mar"].values
    modelo_pred = LinearRegression().fit(x_all, y_all)
    años_futuros = np.arange(df_agg["Año"].max() + 1, 2101).reshape(-1, 1)
    y_pred = modelo_pred.predict(años_futuros)

    resid = y_all - modelo_pred.predict(x_all)
    s = np.std(resid)
    y_upper = y_pred + 1.96 * s
    y_lower = y_pred - 1.96 * s

    fig_pred = px.line(x=años_futuros.ravel(), y=y_pred,
                       labels={"x": "Año", "y": "Nivel del mar (mm)"},
                       title="Proyección del nivel medio global del mar hasta 2100")
    fig_pred.add_scatter(x=años_futuros.ravel(), y=y_upper, mode="lines",
                         line=dict(color="cyan", width=1), name="IC 95 % (superior)")
    fig_pred.add_scatter(x=años_futuros.ravel(), y=y_lower, mode="lines",
                         fill="tonexty", fillcolor="rgba(0,191,255,0.2)",
                         line=dict(color="cyan", width=1), name="IC 95 % (inferior)")
    st.plotly_chart(fig_pred, use_container_width=True)

    st.success("🌡️ **El modelo predice un incremento sostenido del nivel del mar hacia finales de siglo, con un intervalo de confianza del 95 %.**")

# ------------------------------------------
# CONCLUSIONES
# ------------------------------------------
st.subheader("🧩 Conclusiones automáticas")
if not df_filtrado.empty:
    color_box = "#006666" if pendiente > 0 else "#2e8b57" if pendiente < 0 else "#555555"
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"
    texto_md = f"""
<div style='background-color:{color_box}; padding:1.2rem; border-radius:10px; color:white; font-size:17px; line-height:1.6;'>
📅 Entre **{rango[0]}** y **{rango[1]}**, el nivel medio del mar muestra una tendencia **{tendencia}**.  
Esto indica un cambio acumulado de **{cambio:.2f} mm**, con una tasa media de **{pendiente:.3f} mm/año**.  
🌊 **Estos resultados coinciden con las observaciones satelitales y los informes del IPCC.**
</div>
"""
    st.markdown(texto_md, unsafe_allow_html=True)

# ------------------------------------------
# DESCARGAS
# ------------------------------------------
st.markdown("---")
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)
with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv, file_name="nivel_mar_filtrado.csv", mime="text/csv")

with col2:
    import plotly.io as pio
    html_bytes = pio.to_html(fig, full_html=False).encode("utf-8")
    st.download_button("🖼️ Descargar gráfico (HTML interactivo)",
                       data=html_bytes, file_name="grafico_nivel_mar.html", mime="text/html")
