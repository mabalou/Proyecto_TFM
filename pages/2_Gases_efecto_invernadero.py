# ==========================================
# 2_Gases_efecto_invernadero.py — versión final mejorada
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

# -------------------------------
# CONFIGURACIÓN DE PÁGINA
# -------------------------------
st.set_page_config(page_title="🌍 Gases de Efecto Invernadero", layout="wide")
st.title("🌍 Evolución de los Gases de Efecto Invernadero")

# -------------------------------
# ESTILO PERSONALIZADO
# -------------------------------
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

# -------------------------------
# DESCRIPCIÓN INICIAL
# -------------------------------
with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Esta sección analiza la **evolución global** de los principales gases de efecto invernadero:
    **CO₂**, **CH₄** y **N₂O**, con datos procedentes de la **NOAA**.

    🔍 Puedes:
    - Visualizar series interactivas (línea, área o barras).  
    - Calcular **tendencias lineales** y **medias por década**.  
    - Generar **predicciones hasta 2100** con **intervalo de confianza del 95 %**.  
    - Comparar la evolución **normalizada** de los tres gases.
    """)

# -------------------------------
# CARGA DE DATOS
# -------------------------------
@st.cache_data
def cargar_datos_gas(ruta_csv):
    with open(ruta_csv, "r", encoding="utf-8") as f:
        lineas = f.readlines()
    encabezado_index = next((i for i, l in enumerate(lineas) if "year" in l.lower() and "average" in l.lower()), 0)
    df = pd.read_csv(ruta_csv, skiprows=encabezado_index)
    df.columns = df.columns.str.strip().str.lower()
    df = df.rename(columns={
        "year": "Año",
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

# -------------------------------
# ESTADO Y PARÁMETROS INICIALES
# -------------------------------
defaults = {
    "ui_show_filters": True,
    "gas": "CO₂ (ppm)",
    "tipo_grafico": "Línea",
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

gas = st.session_state.gas
tipo_grafico = st.session_state.tipo_grafico
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion

df = cargar_datos_gas(RUTAS[gas])
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())
rango = st.session_state.get("rango", (1980, max_year))
df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]

# -------------------------------
# VISUALIZACIÓN PRINCIPAL
# -------------------------------
st.subheader(f"📈 Evolución global de {gas}")

if df_filtrado.empty:
    st.info("Selecciona un rango de años válido para visualizar los datos.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    with col1:
        eje_y = f"Concentración ({'ppm' if 'CO₂' in gas else 'ppb'})"

        # Agrupar por año para evitar efecto "escalera"
        df_plot = df_filtrado.groupby("Año", as_index=False)["Concentración"].mean()
        df_plot["Suavizada"] = df_plot["Concentración"].rolling(window=3, center=True, min_periods=1).mean()

        # Crear gráfico principal con nombre del gas visible
        if tipo_grafico == "Línea":
            fig = px.line(df_plot, x="Año", y="Suavizada",
                          labels={"Año": "Año", "Suavizada": eje_y},
                          markers=True)
        elif tipo_grafico == "Área":
            fig = px.area(df_plot, x="Año", y="Suavizada",
                          labels={"Año": "Año", "Suavizada": eje_y})
        else:
            fig = px.bar(df_plot, x="Año", y="Suavizada",
                         labels={"Año": "Año", "Suavizada": eje_y})

        # Forzar nombre correcto de la variable en la leyenda
        if fig.data:
            fig.data[0].name = gas
            fig.update_traces(showlegend=True)

        # Estilo del gráfico
        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15),
            legend_title_text="Variable"
        )

        # Tendencia lineal
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
        valor_min = df_filtrado["Concentración"].min()
        valor_max = df_filtrado["Concentración"].max()
        año_min = df_filtrado.loc[df_filtrado["Concentración"].idxmin(), "Año"]
        año_max = df_filtrado.loc[df_filtrado["Concentración"].idxmax(), "Año"]
        media = df_filtrado["Concentración"].mean()
        inicial, final = df_filtrado["Concentración"].iloc[0], df_filtrado["Concentración"].iloc[-1]
        cambio = ((final - inicial) / inicial) * 100

        st.markdown(f"""
        - 📆 **Años:** {rango[0]}–{rango[1]}  
        - 🔽 **Mínimo:** {valor_min:.2f} ({int(año_min)})  
        - 🔼 **Máximo:** {valor_max:.2f} ({int(año_max)})  
        - 🌍 **Media:** {media:.2f}  
        - 📊 **Cambio:** {cambio:+.2f}% en el período  
        """)

        # 🔧 Filtros debajo del resumen
        st.markdown("### ⚙️ Ajustar visualización")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.selectbox("Selecciona el gas", list(RUTAS.keys()), key="gas")
            st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
            st.slider("Selecciona el rango de años", min_year, max_year,
                      st.session_state.get("rango", (1980, max_year)), key="rango")
        with col_f2:
            st.checkbox("📈 Mostrar tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
            st.checkbox("📊 Media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
            st.checkbox("🔮 Incluir modelo predictivo", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")

# -------------------------------
# MEDIA POR DÉCADAS
# -------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Concentración media por década")
    df_decada = df_filtrado.copy()
    df_decada["Década"] = ((df_decada["Año"] // 10) * 10).astype(int)
    df_grouped = df_decada.groupby("Década")["Concentración"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="Concentración", color="Concentración",
                     color_continuous_scale="Reds", labels={"Concentración": eje_y})
    st.plotly_chart(fig_dec, use_container_width=True)

# -------------------------------
# PREDICCIÓN CON INTERVALO 95 %
# -------------------------------
if mostrar_prediccion and not df.empty:
    st.subheader("🔮 Proyección hasta 2100")
    x_full = df["Año"].values.reshape(-1, 1)
    y_full = df["Concentración"].values
    modelo_pred = LinearRegression().fit(x_full, y_full)
    años_futuros = np.arange(df["Año"].max() + 1, 2101).reshape(-1, 1)
    y_pred = modelo_pred.predict(años_futuros)

    resid = y_full - modelo_pred.predict(x_full)
    s = np.std(resid)
    y_upper = y_pred + 1.96 * s
    y_lower = y_pred - 1.96 * s

    fig_pred = px.line(x=años_futuros.ravel(), y=y_pred,
                       labels={"x": "Año", "y": eje_y},
                       title=f"Predicción futura de {gas} hasta 2100")
    fig_pred.add_scatter(x=años_futuros.ravel(), y=y_upper, mode="lines",
                         line=dict(color="cyan", width=1), name="IC 95 % (superior)")
    fig_pred.add_scatter(x=años_futuros.ravel(), y=y_lower, mode="lines",
                         fill="tonexty", fillcolor="rgba(0,191,255,0.2)",
                         line=dict(color="cyan", width=1), name="IC 95 % (inferior)")
    st.plotly_chart(fig_pred, use_container_width=True)

    st.success("🌡️ El modelo predice un **incremento sostenido** en la concentración hacia finales de siglo, con un **intervalo de confianza del 95 %**.")

# -------------------------------
# COMPARATIVA GLOBAL (suavizada igual que las gráficas principales)
# -------------------------------
st.markdown("---")
with st.expander("🌐 Comparativa global de gases de efecto invernadero", expanded=True):
    df_co2 = cargar_datos_gas(RUTAS["CO₂ (ppm)"])
    df_ch4 = cargar_datos_gas(RUTAS["CH₄ (ppb)"])
    df_n2o = cargar_datos_gas(RUTAS["N₂O (ppb)"])

    # Combinar datasets
    df_comp = (
        df_co2[["Año", "Concentración"]].rename(columns={"Concentración": "CO₂"})
        .merge(df_ch4[["Año", "Concentración"]].rename(columns={"Concentración": "CH₄"}), on="Año", how="inner")
        .merge(df_n2o[["Año", "Concentración"]].rename(columns={"Concentración": "N₂O"}), on="Año", how="inner")
    ).dropna()

    # 🔹 Agrupar por año para evitar efecto "escalera"
    df_comp = df_comp.groupby("Año", as_index=False).mean()

    # 🔹 Normalizar entre 0–1
    for g in ["CO₂", "CH₄", "N₂O"]:
        df_comp[g] = (df_comp[g] - df_comp[g].min()) / (df_comp[g].max() - df_comp[g].min())

    # 🔹 Suavizar las curvas (como en los gráficos principales)
    for g in ["CO₂", "CH₄", "N₂O"]:
        df_comp[f"{g}_Suavizada"] = df_comp[g].rolling(window=3, center=True, min_periods=1).mean()

    # 🔹 Calcular promedio global suavizado
    df_comp["Promedio"] = df_comp[[f"{g}_Suavizada" for g in ["CO₂", "CH₄", "N₂O"]]].mean(axis=1)

    # 🔹 Transformar a formato largo para graficar
    df_melt = df_comp.melt(
        id_vars="Año",
        value_vars=[f"{g}_Suavizada" for g in ["CO₂", "CH₄", "N₂O"]],
        var_name="Gas",
        value_name="Proporción relativa"
    )

    # Renombrar gases en el eje
    df_melt["Gas"] = df_melt["Gas"].str.replace("_Suavizada", "")

    # 🔹 Crear gráfico de líneas suaves (sin escalones)
    fig_comp = px.line(
        df_melt,
        x="Año",
        y="Proporción relativa",
        color="Gas",
        title="Comparativa normalizada (suavizada) de CO₂, CH₄ y N₂O (0–1)",
        labels={"Proporción relativa": "Proporción relativa"},
        color_discrete_map={
            "CO₂": "#00BFFF",   # Azul brillante
            "CH₄": "#32CD32",   # Verde intenso
            "N₂O": "#FF6347"    # Rojo coral
        }
    )

    # Añadir línea de promedio global
    fig_comp.add_scatter(
        x=df_comp["Año"],
        y=df_comp["Promedio"],
        mode="lines",
        name="Promedio global 🌍",
        line=dict(color="#FFD700", width=3, dash="dot")
    )

    # 🔹 Ajustes visuales coherentes con el resto del dashboard
    fig_comp.update_traces(mode="lines+markers", line=dict(width=3))
    fig_comp.update_layout(
        legend_title_text="Gas",
        font=dict(size=15),
        xaxis_title_font=dict(size=16),
        yaxis_title_font=dict(size=16),
        template="plotly_dark"
    )
    
    st.plotly_chart(fig_comp, use_container_width=True)

# -------------------------------
# CONCLUSIONES
# -------------------------------
st.subheader("🧩 Conclusiones automáticas")
if not df_filtrado.empty:
    color_box = "#006666" if pendiente > 0 else "#2e8b57" if pendiente < 0 else "#555555"
    tendencia = "ascendente" if pendiente > 0 else "descendente" if pendiente < 0 else "estable"
    texto_md = f"""
<div style='background-color:{color_box}; padding:1.2rem; border-radius:10px; color:white; font-size:17px; line-height:1.6;'>
📅 Entre **{rango[0]}** y **{rango[1]}**, la concentración de **{gas}** muestra una tendencia **{tendencia}**.  
Esto indica que los niveles del gas han {'aumentado de forma sostenida' if pendiente > 0 else 'disminuido gradualmente' if pendiente < 0 else 'permanecido estables'}  
en el periodo analizado, contribuyendo {'al incremento del efecto invernadero global.' if pendiente > 0 else 'a una ligera mejora del balance atmosférico.' if pendiente < 0 else 'a la estabilidad climática observada.'}

🌡️ **Estos resultados son coherentes con los informes globales de la NOAA y la NASA.**
</div>
"""
    st.markdown(texto_md, unsafe_allow_html=True)

# -------------------------------
# EXPORTACIÓN
# -------------------------------
st.markdown("---")
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)
with col1:
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Descargar CSV", data=csv, file_name="gases_filtrados.csv", mime="text/csv")

with col2:
    import plotly.io as pio
    html_bytes = pio.to_html(fig, full_html=False).encode("utf-8")
    st.download_button("🖼️ Descargar gráfico (HTML interactivo)",
                       data=html_bytes, file_name="grafico_gases.html", mime="text/html")
