# ==========================================
# 8_Consumo_energético_por_fuente.py — versión final homogénea con IC95%, filtros y estilo global
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
import plotly.io as pio

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="⚡ Consumo Energético por Fuente", layout="wide")
st.title("⚡ Evolución del consumo energético global")

with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Analiza la **evolución del consumo energético mundial por fuente** (carbón, petróleo, gas, renovables, nuclear, hidro, etc.).  

    🔍 **Incluye:**
    - Gráficos interactivos (línea, área apilada o barras).  
    - Cálculo de **tendencias lineales** por fuente y media global.  
    - **Proyecciones hasta 2100 con intervalo de confianza del 95 %**.  
    - Resumen lateral y conclusiones automáticas.  
    """)

# ------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------
def _safe_read_csv(path, **kwargs):
    try:
        return pd.read_csv(path, **kwargs)
    except Exception:
        return pd.read_csv(path, engine="python", **kwargs)

def es_columna_energetica(c: str) -> bool:
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

def nombre_bonito(col):
    return NOMBRES_BONITOS.get(col.lower(), col.replace("_", " ").capitalize() + " (TWh)")

# ------------------------------------------
# CARGA DE DATOS DESDE MONGODB
# ------------------------------------------
from pymongo import MongoClient

@st.cache_data
def cargar_datos():
    uri = "mongodb+srv://marcosabal:parausarentfm123@tfmcc.qfbhjbv.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri)
    db = client["tfm_datos"]
    collection = db["energia_energy_consuption_by_source"]

    # Leemos todos los documentos (sin _id)
    docs = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(docs)

    # Normalizamos nombres de columnas a minúsculas
    df.columns = df.columns.str.strip().str.lower()

    # Aseguramos que year es numérico
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])

    # Agregamos por año (como antes con el CSV)
    df = df.groupby("year", as_index=False).sum(numeric_only=True)

    # Pasamos a formato largo
    df_long = df.melt(id_vars="year", var_name="fuente_raw", value_name="Consumo")

    # Nos quedamos solo con columnas energéticas
    df_long = df_long[df_long["fuente_raw"].apply(es_columna_energetica)]

    # Campos derivados
    df_long["Año"] = df_long["year"].astype(int)
    df_long["Fuente"] = df_long["fuente_raw"].apply(nombre_bonito)

    # Nos aseguramos de que Consumo es numérico y sin NaN
    df_long["Consumo"] = pd.to_numeric(df_long["Consumo"], errors="coerce")
    df_long = df_long.dropna(subset=["Consumo"])

    # Devolvemos exactamente lo que espera el resto del script
    min_year = int(df_long["Año"].min())
    max_year = int(df_long["Año"].max())
    fuentes = sorted(df_long["Fuente"].unique())

    return df_long, fuentes, (min_year, max_year)

# llamada
df_long, fuentes_disponibles, (min_year, max_year) = cargar_datos()

# ------------------------------------------
# ESTADO Y FILTROS
# ------------------------------------------
defaults = {
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

        # Tendencias lineales por fuente
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
                    fig.add_scatter(x=df_src["Año"], y=y_pred, mode="lines",
                                    name=f"Tendencia {fuente}",
                                    line=dict(dash="dash", width=2))

        # Línea de consumo medio global
        df_global = df_f.groupby("Año")["Consumo"].mean().reset_index()
        fig.add_scatter(x=df_global["Año"], y=df_global["Consumo"], mode="lines",
                        name="Consumo medio global", line=dict(color="gray", dash="dot", width=3))

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

        # 🔧 Filtros debajo del resumen (sincronizados con el botón global)
        if st.session_state.get("ui_show_filters", True):
            st.markdown("### ⚙️ Ajustar visualización")
            colf1, colf2 = st.columns(2)
            with colf1:
                st.multiselect("⚡ Fuentes energéticas", fuentes_disponibles, default=fuentes_sel, key="fuentes_sel")
                st.selectbox("📊 Tipo de gráfico", ["Línea", "Área (apilada)", "Barras"], key="tipo_grafico")
                st.slider("📆 Rango de años", min_year, max_year,
                        st.session_state.get("rango", (1980, max_year)), key="rango")
            with colf2:
                st.checkbox("📈 Mostrar tendencia", value=mostrar_tendencia, key="mostrar_tendencia")
                st.checkbox("📊 Media por décadas", value=mostrar_decadas, key="mostrar_decadas")
                st.checkbox("🔮 Incluir modelo predictivo", value=mostrar_prediccion, key="mostrar_prediccion")
                st.checkbox("🧮 Escala logarítmica", value=usar_escala_log, key="usar_escala_log")

# ------------------------------------------
# MEDIA POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_f.empty:
    st.subheader("📊 Media del consumo por década")
    df_dec = df_f.copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    df_grouped = df_dec.groupby(["Década", "Fuente"])["Consumo"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="Consumo", color="Fuente",
                     barmode="group", labels={"Consumo": "Consumo medio (TWh)", "Década": "Década"})
    fig_dec.update_layout(xaxis_title_font=dict(size=16), yaxis_title_font=dict(size=16))
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# PROYECCIÓN FUTURA CON IC95%
# ------------------------------------------
if mostrar_prediccion and not df_f.empty:
    st.subheader("🔮 Proyección del consumo energético hasta 2100 (con IC 95 %)")
    fig_pred = px.line(title="Proyección futura del consumo energético")
    for fuente in fuentes_sel:
        df_src = df_long[df_long["Fuente"] == fuente]
        if len(df_src) > 5:
            x = df_src["Año"].values.reshape(-1, 1)
            y = df_src["Consumo"].values
            modelo = LinearRegression().fit(x, y)
            x_pred = np.arange(x.max() + 1, 2101).reshape(-1, 1)
            y_pred = modelo.predict(x_pred)

            resid = y - modelo.predict(x)
            s = np.std(resid)
            y_upper = y_pred + 1.96 * s
            y_lower = y_pred - 1.96 * s

            fig_pred.add_scatter(x=x_pred.flatten(), y=y_pred, mode="lines",
                                 name=f"{fuente} (proyección)",
                                 line=dict(dash="dash", width=2))
            fig_pred.add_scatter(x=x_pred.flatten(), y=y_upper, mode="lines",
                                 line=dict(color="red", width=1), name="IC 95 % (sup)")
            fig_pred.add_scatter(x=x_pred.flatten(), y=y_lower, mode="lines",
                                 fill="tonexty", fillcolor="rgba(255,0,0,0.1)",
                                 line=dict(color="red", width=1), name="IC 95 % (inf)")

    st.plotly_chart(fig_pred, use_container_width=True)
    st.success("📈 Las proyecciones muestran las posibles trayectorias del consumo con un **intervalo de confianza del 95 %**.")

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
    html_bytes = pio.to_html(fig, full_html=False).encode("utf-8")
    st.download_button("🖼️ Descargar gráfico (HTML interactivo)",
                       data=html_bytes, file_name="grafico_energetico.html", mime="text/html")
