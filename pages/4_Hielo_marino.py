# ==========================================
# 4_Hielo_marino.py — versión final: resumen + filtros compactos + suavizado + predicción IC95% + comparativa
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="🧊 Hielo marino", layout="wide")
st.title("🧊 Evolución del hielo marino")

# ------------------------------------------
# ESTILO (acerca el bloque derecho y compacta espacios)
# ------------------------------------------
st.markdown(
    """
    <style>
    /* Subir la columna derecha (resumen + filtros) un poco */
    div[data-testid="column"]:nth-of-type(2) { margin-top: -5rem !important; }
    /* Reducir espacio entre el resumen y los filtros */
    div[data-testid="stMarkdown"] + div[data-testid="stMarkdown"] { margin-top: -1.0rem !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------
# AYUDA INICIAL
# ------------------------------------------
with st.expander("📘 ¿Qué muestra esta sección?", expanded=False):
    st.markdown("""
    Analiza la evolución de la **extensión del hielo marino** en el **Ártico** y el **Antártico** (1978–presente).

    🔍 **Incluye:**
    - Series interactivas (línea, área o barras) con **suavizado**.
    - **Tendencia lineal** y **medias por década**.
    - **Predicción hasta 2100** con **intervalo de confianza del 95 %**.
    - Comparativa **Ártico vs Antártico** (suavizada).
    - Conclusiones automáticas y exportación de datos y gráficos.
    """)

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos(region: str) -> pd.DataFrame:
    archivo = "data/hielo/arctic_sea_ice_extent.csv" if region == "Ártico" else "data/hielo/antarctic_sea_ice_extent.csv"
    df = pd.read_csv(archivo)
    df.columns = df.columns.str.strip()
    # Se esperan columnas Year, Month, Extent (NSIDC/NOAA formatos habituales)
    df = df.rename(columns={"Year": "Año", "Month": "Mes", "Extent": "Extensión"})
    # Limpieza
    df["Año"] = pd.to_numeric(df["Año"], errors="coerce")
    df["Mes"] = pd.to_numeric(df["Mes"], errors="coerce")
    df["Extensión"] = pd.to_numeric(df["Extensión"], errors="coerce")
    df = df.dropna(subset=["Año", "Mes", "Extensión"])
    # Agregado anual para evitar "escalones" y ruido mensual
    df_anual = df.groupby("Año", as_index=False)["Extensión"].mean()
    return df_anual

@st.cache_data
def cargar_datos_ambos() -> pd.DataFrame:
    artico = cargar_datos("Ártico").copy()
    artico["Región"] = "Ártico"
    antartico = cargar_datos("Antártico").copy()
    antartico["Región"] = "Antártico"
    return pd.concat([artico, antartico], ignore_index=True)

# ------------------------------------------
# ESTADO Y PARÁMETROS (filtros activos por defecto)
# ------------------------------------------
defaults = {
    "ui_show_filters": True,
    "region": "Ártico",
    "tipo_grafico": "Línea",
    "rango": (1980, 2024),          # se ajustará al rango real tras cargar
    "mostrar_tendencia": True,
    "mostrar_decadas": True,
    "mostrar_prediccion": True,
    "comparar_regiones": True,
    "window_roll": 3,               # ventana de suavizado (rolling)
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ------------------------------------------
# CARGA Y RANGO
# ------------------------------------------
region = st.session_state.region
df = cargar_datos(region)
min_year, max_year = int(df["Año"].min()), int(df["Año"].max())
# Si el rango por defecto no encaja con los datos, lo ajustamos
if "rango" not in st.session_state or st.session_state.rango[1] < min_year or st.session_state.rango[0] > max_year:
    st.session_state.rango = (max(min_year, 1980), max_year)

tipo_grafico = st.session_state.tipo_grafico
rango = st.session_state.rango
mostrar_tendencia = st.session_state.mostrar_tendencia
mostrar_decadas = st.session_state.mostrar_decadas
mostrar_prediccion = st.session_state.mostrar_prediccion
comparar_regiones = st.session_state.comparar_regiones
window_roll = max(1, int(st.session_state.window_roll))

df_filtrado = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])].copy()
# Serie suavizada (como en otras páginas)
df_filtrado["Suavizada"] = df_filtrado["Extensión"].rolling(window=window_roll, center=True, min_periods=1).mean()

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL + RESUMEN + FILTROS
# ------------------------------------------
st.subheader("📈 Evolución temporal")

if df_filtrado.empty:
    st.info("Selecciona un rango de años válido para visualizar los datos.")
else:
    col1, col2 = st.columns([3, 1], gap="large")

    # ----- Columna 1: Gráfico principal -----
    with col1:
        titulo = f"Evolución de la extensión del hielo marino — {region}"
        y_col = "Suavizada"  # usamos la suavizada para la línea principal

        if tipo_grafico == "Línea":
            fig = px.line(df_filtrado, x="Año", y=y_col,
                          labels={"Año": "Año", y_col: "Extensión (millones km²)"},
                          markers=True, title=titulo)
        elif tipo_grafico == "Área":
            fig = px.area(df_filtrado, x="Año", y=y_col,
                          labels={"Año": "Año", y_col: "Extensión (millones km²)"},
                          title=titulo)
        else:
            fig = px.bar(df_filtrado, x="Año", y=y_col,
                         labels={"Año": "Año", y_col: "Extensión (millones km²)"},
                         title=titulo)

        # Mostrar claramente la variable en la leyenda
        if fig.data:
            fig.data[0].name = region
            fig.update_traces(showlegend=True)

        fig.update_layout(
            xaxis_title_font=dict(size=17),
            yaxis_title_font=dict(size=17),
            font=dict(size=15),
            legend_title_text="Serie"
        )

        # Tendencia lineal sobre la serie suavizada
        coef = 0.0
        if mostrar_tendencia and len(df_filtrado) > 2:
            X = df_filtrado["Año"].values.reshape(-1, 1)
            Y = df_filtrado[y_col].values
            modelo = LinearRegression().fit(X, Y)
            y_pred = modelo.predict(X)
            coef = float(modelo.coef_[0])  # millones km² por año
            fig.add_scatter(x=df_filtrado["Año"], y=y_pred, mode="lines",
                            name="Tendencia", line=dict(color="red", dash="dash", width=2))

        st.plotly_chart(fig, use_container_width=True)

    # ----- Columna 2: Resumen + Filtros -----
    with col2:
        st.markdown("### 🧾 Resumen del período")
        inicio, fin = df_filtrado[y_col].iloc[0], df_filtrado[y_col].iloc[-1]
        cambio = fin - inicio
        media = df_filtrado[y_col].mean()
        # Para mínimo y máximo, usemos la columna original (Extensión) para no "ocultar" picos
        valor_min = df_filtrado["Extensión"].min()
        valor_max = df_filtrado["Extensión"].max()
        año_min = int(df_filtrado.loc[df_filtrado["Extensión"].idxmin(), "Año"])
        año_max = int(df_filtrado.loc[df_filtrado["Extensión"].idxmax(), "Año"])

        st.markdown(f"""
        - 📆 **Años:** {rango[0]}–{rango[1]}  
        - ❄️ **Media (suavizada):** {media:.2f} millones km²  
        - 🔽 **Mínimo (real):** {valor_min:.2f} millones km² (*{año_min}*)  
        - 🔼 **Máximo (real):** {valor_max:.2f} millones km² (*{año_max}*)  
        - 📊 **Cambio total (suav.):** {cambio:+.2f} millones km²  
        - 📈 **Tendencia:** {coef:+.4f} millones km²/año  
        """)

        # 🔧 Filtros compactos debajo del resumen (compatibles con el botón del header)
        if st.session_state.get("ui_show_filters", True):
            st.markdown("### ⚙️ Ajustar visualización")
            colf1, colf2 = st.columns(2)
            with colf1:
                st.selectbox("🌍 Región", ["Ártico", "Antártico"], key="region")
                st.selectbox("Tipo de gráfico", ["Línea", "Área", "Barras"], key="tipo_grafico")
                st.slider("Rango de años", min_year, max_year, st.session_state.rango, key="rango")
            with colf2:
                st.checkbox("📈 Mostrar tendencia", value=st.session_state.mostrar_tendencia, key="mostrar_tendencia")
                st.checkbox("📊 Media por décadas", value=st.session_state.mostrar_decadas, key="mostrar_decadas")
                st.checkbox("🔮 Predicción hasta 2100", value=st.session_state.mostrar_prediccion, key="mostrar_prediccion")
                st.checkbox("🌐 Comparar regiones", value=st.session_state.comparar_regiones, key="comparar_regiones")
                st.number_input("Ventana de suavizado", 1, 11, value=window_roll, step=2, key="window_roll")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_filtrado.empty:
    st.subheader("📊 Media de extensión por década")
    df_dec = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])].copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    df_grouped = df_dec.groupby("Década")["Extensión"].mean().reset_index()
    fig_dec = px.bar(df_grouped, x="Década", y="Extensión", color="Extensión",
                     color_continuous_scale="Blues",
                     labels={"Extensión": "Extensión promedio (millones km²)"},
                     title=f"Media por década — {region}")
    fig_dec.update_layout(xaxis_title_font=dict(size=16), yaxis_title_font=dict(size=16))
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# MODELO PREDICTIVO (IC 95 %)
# ------------------------------------------
if mostrar_prediccion and not df.empty:
    st.subheader("🔮 Proyección hasta 2100")
    # Usamos toda la serie anual (no solo el rango) para el modelo
    X_all = df["Año"].values.reshape(-1, 1)
    Y_all = df["Extensión"].values
    modelo_pred = LinearRegression().fit(X_all, Y_all)

    # Años futuros
    years_future = np.arange(df["Año"].max() + 1, 2101)
    X_future = years_future.reshape(-1, 1)
    y_pred = modelo_pred.predict(X_future)

    # Banda de confianza 95% (estimación simple con residuo global)
    resid = Y_all - modelo_pred.predict(X_all)
    s = np.std(resid)  # desviación de residuos
    y_upper = y_pred + 1.96 * s
    y_lower = y_pred - 1.96 * s

    fig_pred = px.line(x=years_future, y=y_pred,
                       labels={"x": "Año", "y": "Extensión (millones km²)"},
                       title=f"Predicción de la extensión — {region} (hasta 2100)")
    fig_pred.add_scatter(x=years_future, y=y_upper, mode="lines",
                         line=dict(width=1), name="IC 95 % (superior)")
    fig_pred.add_scatter(x=years_future, y=y_lower, mode="lines", fill="tonexty",
                         fillcolor="rgba(0, 0, 0, 0.08)", line=dict(width=1),
                         name="IC 95 % (inferior)")
    st.plotly_chart(fig_pred, use_container_width=True)

    pendiente_modelo = float(modelo_pred.coef_[0])
    if pendiente_modelo < 0:
        st.success("❄️ **El modelo proyecta una disminución sostenida** de la extensión hacia finales de siglo (IC 95 %).")
    elif pendiente_modelo > 0:
        st.info("📈 **El modelo proyecta un ligero aumento** de la extensión hacia finales de siglo (IC 95 %).")
    else:
        st.warning("➖ **El modelo no muestra variación significativa** a largo plazo (IC 95 %).")

# ------------------------------------------
# COMPARATIVA ENTRE REGIONES (suavizada)
# ------------------------------------------
if comparar_regiones:
    st.markdown("---")
    with st.expander("🌐 Comparativa entre regiones polares (suavizada)", expanded=False):
        df_comp = cargar_datos_ambos()
        df_comp = df_comp[(df_comp["Año"] >= rango[0]) & (df_comp["Año"] <= rango[1])].copy()
        # Suavizado por región
        df_comp["Suavizada"] = df_comp.groupby("Región")["Extensión"].transform(
            lambda s: s.rolling(window=window_roll, center=True, min_periods=1).mean()
        )
        fig_comp = px.line(df_comp, x="Año", y="Suavizada", color="Región",
                           title="Ártico vs Antártico — Extensión suavizada",
                           labels={"Suavizada": "Extensión (millones km²)", "Año": "Año"})
        fig_comp.update_traces(mode="lines+markers", line=dict(width=3))
        st.plotly_chart(fig_comp, use_container_width=True)

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS
# ------------------------------------------
st.subheader("🧩 Conclusiones automáticas")
if not df_filtrado.empty:
    tend = "descendente" if coef < 0 else "ascendente" if coef > 0 else "estable"
    color_box = "#006666" if coef < 0 else "#2e8b57" if coef > 0 else "#555555"
    texto = f"""
    📅 Entre **{rango[0]}** y **{rango[1]}**, la extensión del hielo marino en **{region}** muestra una tendencia **{tend}**.  
    En términos suavizados, el cambio total es de **{(df_filtrado['Suavizada'].iloc[-1]-df_filtrado['Suavizada'].iloc[0]):+.2f} millones km²**  
    con una variación media de **{coef:+.4f} millones km²/año**.  
    """
    st.markdown(
        f"<div style='background-color:{color_box};padding:1rem;border-radius:10px;color:white;'>{texto}</div>",
        unsafe_allow_html=True
    )

# ------------------------------------------
# EXPORTACIÓN
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)

with col1:
    # Exportamos el filtrado con valores suavizados
    out = df_filtrado.rename(columns={"Suavizada": "Extensión_suavizada"})
    csv = out.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📄 Descargar CSV (filtrado + suavizado)",
        data=csv,
        file_name=f"hielo_marino_{region.lower()}_filtrado.csv",
        mime="text/csv"
    )

with col2:
    import plotly.io as pio
    html_bytes = pio.to_html(fig, full_html=False).encode("utf-8")
    st.download_button(
        "🖼️ Descargar gráfico (HTML interactivo)",
        data=html_bytes,
        file_name=f"grafico_hielo_{region.lower()}.html",
        mime="text/html"
    )
