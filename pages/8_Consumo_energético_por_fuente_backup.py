# ==========================================
# 8_Consumo_energético_por_fuente.py — COMPLETO (UI mejorada)
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
st.set_page_config(page_title="⚡ Consumo Energético por Fuente", layout="wide")

st.title("⚡ Evolución del consumo energético global")
with st.expander("📘 ¿Qué estás viendo? (clic para abrir)", expanded=True):
    st.markdown(
        """
        Analiza la evolución del **consumo mundial de energía por fuente** (carbón, petróleo, gas,
        renovables, nuclear, hidro, etc.).  
        Funcionalidades:
        - Comparación de fuentes y **tendencias lineales**.
        - **Medias por década** y **proyección** hasta 2100.
        - **Escala logarítmica** (para rangos muy dispares).
        - **Conclusiones automáticas** y exportación de **CSV** y **PNG/HTML**.
        """
    )

# ------------------------------------------
# UTILIDADES
# ------------------------------------------
NON_ENERGY_COLS = {
    "country", "country name", "iso_code", "iso code", "iso", "region",
    "year", "population", "gdp", "continent"
}

def es_columna_energetica(c: str) -> bool:
    """Detecta columnas de consumo/generación y evita per_capita/share/change."""
    c = c.lower()
    if c in NON_ENERGY_COLS:
        return False
    if any(x in c for x in ["per_capita", "share", "change_pct", "change_twh", "intensity", "pct"]):
        return False
    return (
        c.endswith("_consumption")
        or c.endswith("_electricity")
        or c.endswith("_generation")
        or c in ["renewables_consumption", "fossil_fuel_consumption"]
    )

NOMBRES_BONITOS = {
    "coal_consumption": "Carbón (TWh)",
    "oil_consumption": "Petróleo (TWh)",
    "gas_consumption": "Gas natural (TWh)",
    "renewables_consumption": "Renovables (TWh)",
    "nuclear_consumption": "Nuclear (TWh)",
    "hydro_consumption": "Hidroeléctrica (TWh)",
    "biofuel_consumption": "Biocombustibles (TWh)",
    "solar_consumption": "Solar (TWh)",
    "wind_consumption": "Eólica (TWh)",
    "electricity_consumption": "Electricidad total (TWh)",
    "coal_electricity": "Electricidad a partir de carbón (TWh)",
    "gas_electricity": "Electricidad a partir de gas (TWh)",
    "oil_electricity": "Electricidad a partir de petróleo (TWh)",
    "nuclear_electricity": "Electricidad nuclear (TWh)",
    "hydro_electricity": "Electricidad hidro (TWh)",
    "wind_electricity": "Electricidad eólica (TWh)",
    "solar_electricity": "Electricidad solar (TWh)",
    "biofuel_electricity": "Electricidad biocombustibles (TWh)",
    "renewables_electricity": "Electricidad renovable (TWh)",
}
def nombre_bonito(col: str) -> str:
    col_l = col.lower()
    if col_l in NOMBRES_BONITOS:
        return NOMBRES_BONITOS[col_l]
    return col_l.replace("_", " ").capitalize() + " (TWh)"

@st.cache_data
def cargar_datos_enegia_global():
    df = pd.read_csv("data/energia/energy_consuption_by_source.csv")
    df.columns = df.columns.str.strip().str.lower()

    if "year" not in df.columns:
        st.error("No se encontró la columna 'year' en el CSV de energía.")
        st.stop()

    # Agregación mundial por año
    agrupado = df.groupby("year").sum(numeric_only=True).reset_index()

    # Selección de columnas energéticas
    energy_cols = [c for c in agrupado.columns if es_columna_energetica(c)]
    if not energy_cols:
        st.error(
            "No se detectaron columnas energéticas válidas.\n\n"
            f"Columnas disponibles: {list(agrupado.columns)}"
        )
        st.stop()

    # Largo para Plotly
    largo = (
        agrupado[["year"] + energy_cols]
        .melt(id_vars="year", var_name="Fuente_raw", value_name="Consumo")
        .dropna()
    )

    # Numérico robusto
    largo["Consumo"] = pd.to_numeric(largo["Consumo"], errors="coerce")
    largo = largo.dropna(subset=["Consumo"])

    # Renombrados visibles
    largo = largo.rename(columns={"year": "Año"})
    largo["Fuente"] = largo["Fuente_raw"].apply(nombre_bonito)

    # Defaults sugeridos
    defaults_raw = [
        "coal_consumption", "oil_consumption", "gas_consumption",
        "renewables_consumption", "nuclear_consumption", "hydro_consumption",
    ]
    defaults_display = [nombre_bonito(c) for c in defaults_raw if c in energy_cols]
    if not defaults_display:
        top_media = (largo.groupby("Fuente")["Consumo"].mean().sort_values(ascending=False).head(5).index.tolist())
        defaults_display = top_media

    min_year, max_year = int(largo["Año"].min()), int(largo["Año"].max())
    return largo, sorted(largo["Fuente"].unique().tolist()), defaults_display, (min_year, max_year)

# Carga
df_long, fuentes_disponibles, defaults_display, (min_year, max_year) = cargar_datos_enegia_global()

# ------------------------------------------
# SIDEBAR
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

fuentes_sel = st.sidebar.multiselect(
    "Selecciona fuentes energéticas",
    options=fuentes_disponibles,
    default=defaults_display
)
rango = st.sidebar.slider(
    "Rango de años",
    min_value=min_year, max_value=max_year,
    value=(max(min_year, 1980), max_year)
)
tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área (apilada)", "Barras"])
usar_escala_log = st.sidebar.checkbox("🧮 Escala logarítmica", value=False)
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar líneas de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar medias por década", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir proyección hasta 2100", value=True)

# ------------------------------------------
# FILTRADO
# ------------------------------------------
df_f = df_long[(df_long["Fuente"].isin(fuentes_sel)) & (df_long["Año"].between(*rango))].copy()

# ------------------------------------------
# GRÁFICO PRINCIPAL (+ tendencia)
# ------------------------------------------
st.subheader("📊 Evolución por fuente")
if df_f.empty:
    st.info("Selecciona al menos una fuente y un rango de años con datos.")
else:
    if tipo_grafico == "Línea":
        fig = px.line(df_f, x="Año", y="Consumo", color="Fuente", markers=True,
                      labels={"Consumo": "Consumo (TWh)"})
    elif tipo_grafico == "Área (apilada)":
        fig = px.area(df_f, x="Año", y="Consumo", color="Fuente",
                      labels={"Consumo": "Consumo (TWh)"})
    else:
        fig = px.bar(df_f, x="Año", y="Consumo", color="Fuente",
                     labels={"Consumo": "Consumo (TWh)"})

    if usar_escala_log:
        fig.update_yaxes(type="log", title="Consumo (escala logarítmica)")

    # Tendencias por fuente
    if mostrar_tendencia:
        for fuente in fuentes_sel:
            df_src = df_f[df_f["Fuente"] == fuente]
            if len(df_src) > 1:
                x = df_src["Año"].values.reshape(-1, 1)
                y = df_src["Consumo"].values
                modelo = LinearRegression().fit(x, y)
                y_pred = modelo.predict(x)
                fig.add_scatter(
                    x=df_src["Año"], y=y_pred, mode="lines",
                    name=f"Tendencia {fuente}", line=dict(dash="dash", width=2)
                )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.subheader("🧾 Resumen automático del análisis")
if not df_f.empty:
    df_reciente = df_f[df_f["Año"] == df_f["Año"].max()]
    fuente_max = df_reciente.loc[df_reciente["Consumo"].idxmax(), "Fuente"]
    valor_max = df_reciente["Consumo"].max()
    st.markdown(
        f"⚡ En **{int(df_reciente['Año'].max())}**, la fuente con mayor consumo global fue **{fuente_max}** "
        f"con **{valor_max:,.0f} TWh**."
    )
else:
    st.info("Selecciona al menos una fuente y un rango válido para generar el resumen.")

# ------------------------------------------
# ANÁLISIS POR DÉCADAS
# ------------------------------------------
if mostrar_decadas and not df_f.empty:
    st.subheader("📊 Consumo medio por década")
    df_dec = df_f.copy()
    df_dec["Década"] = (df_dec["Año"] // 10) * 10
    tabla_dec = (
        df_dec.groupby(["Década", "Fuente"])["Consumo"]
        .mean().reset_index()
    )
    st.dataframe(tabla_dec.style.format({"Consumo": "{:,.0f}"}))
    fig_dec = px.bar(
        tabla_dec, x="Década", y="Consumo", color="Fuente", barmode="group",
        labels={"Consumo": "Consumo medio (TWh)", "Década": "Década"},
        title="Consumo medio por década (global)"
    )
    if usar_escala_log:
        fig_dec.update_yaxes(type="log")
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# PREDICCIÓN HASTA 2100
# ------------------------------------------
if mostrar_prediccion and fuentes_sel:
    st.subheader("🔮 Proyección global por fuente hasta 2100")
    fig_pred = px.line(labels={"x": "Año", "y": "Consumo energético (TWh)"},
                       title="Proyecciones por fuente (global)")
    for fuente in fuentes_sel:
        df_src_all = df_long[df_long["Fuente"] == fuente].copy()
        if len(df_src_all) > 1:
            x = df_src_all["Año"].values.reshape(-1, 1)
            y = df_src_all["Consumo"].values
            modelo = LinearRegression().fit(x, y)
            x_pred = np.arange(df_src_all["Año"].max() + 1, 2101).reshape(-1, 1)
            y_pred = modelo.predict(x_pred)
            fig_pred.add_scatter(x=x_pred.flatten(), y=y_pred, mode="lines", name=fuente)
    if usar_escala_log:
        fig_pred.update_yaxes(type="log")
    st.plotly_chart(fig_pred, use_container_width=True)

# ------------------------------------------
# CONCLUSIONES AUTOMÁTICAS CON COLOR
# ------------------------------------------
if not df_f.empty and len(fuentes_sel) > 0:
    st.subheader("🧩 Conclusiones automáticas")

    # Pendientes por fuente (TWh/año)
    pendientes = {}
    for fuente in fuentes_sel:
        df_src = df_f[df_f["Fuente"] == fuente]
        if len(df_src) > 1:
            x = df_src["Año"].values.reshape(-1, 1)
            y = df_src["Consumo"].values
            modelo = LinearRegression().fit(x, y)
            pendientes[fuente] = float(modelo.coef_[0])

    if pendientes:
        fuente_top = max(pendientes, key=pendientes.get)
        p_top = pendientes[fuente_top]
        tendencia = "ascendente" if p_top > 0 else "descendente" if p_top < 0 else "estable"

        color_fondo = "#ffcccc" if p_top > 0 else "#ccffcc" if p_top < 0 else "#e6e6e6"
        color_texto = "#222"

        # Década más activa (media general)
        df_d = df_f.copy()
        df_d["Década"] = (df_d["Año"] // 10) * 10
        medias_decadas = df_d.groupby("Década")["Consumo"].mean()
        decada_max = medias_decadas.idxmax()
        valor_max = medias_decadas.max()

        frase_tend = (
            "📈 **Aumento sostenido del consumo energético global.**" if p_top > 0 else
            "🟢 **Reducción o estabilización en el consumo energético.**" if p_top < 0 else
            "➖ **Sin cambios relevantes en el periodo analizado.**"
        )

        st.markdown(
            f"""
            <div style="background-color:{color_fondo}; color:{color_texto};
                        padding:15px; border-radius:12px; border:1px solid #bbb;">
                <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
                <ul>
                    <li>La fuente con <b>mayor variación</b> es <b>{fuente_top}</b>,
                        con una tendencia <b>{tendencia}</b> (≈ {p_top:,.2f} TWh/año).</li>
                    <li>La década más activa fue la de <b>{int(decada_max)}</b>,
                        con una media de <b>{valor_max:,.2f} TWh</b>.</li>
                </ul>
                <p>{frase_tend}</p>
                <p style="font-size:0.9em; color:#444;">
                    🔮 Estas conclusiones se actualizan automáticamente al modificar el rango o las fuentes seleccionadas.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("No hay datos suficientes para generar conclusiones.")
else:
    st.info("Selecciona al menos una fuente energética y un rango válido para generar conclusiones.")

# ------------------------------------------
# DESCARGAS (CSV + PNG/HTML)
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)

with col1:
    if not df_f.empty:
        try:
            csv = df_f.to_csv(index=False).encode("utf-8")
            st.download_button("📄 Descargar CSV (filtro actual)",
                               data=csv,
                               file_name="consumo_energetico_global_filtrado.csv",
                               mime="text/csv")
        except Exception as e:
            st.error(f"No se pudo generar el CSV: {e}")
    else:
        st.info("No hay datos filtrados para exportar.")

with col2:
    try:
        buffer = BytesIO()
        fig.write_image(buffer, format="png")  # Requiere `kaleido` local; en la nube suele fallar
        st.download_button("🖼️ Descargar gráfico principal (PNG)",
                           data=buffer,
                           file_name="grafico_consumo_energetico_global.png",
                           mime="image/png")
    except Exception:
        st.warning("⚠️ No se pudo generar PNG (Kaleido no disponible). Te dejo alternativa HTML interactiva.")
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button("🌐 Descargar gráfico (HTML interactivo)",
                           data=html_bytes,
                           file_name="grafico_consumo_energetico_global.html",
                           mime="text/html")
