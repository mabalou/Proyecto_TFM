# ==========================================
# 8_Consumo_energético_por_fuente.py — GLOBAL (versión unificada)
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
from io import BytesIO

# ------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------
st.set_page_config(page_title="⚡ Consumo Energético por Fuente", layout="wide")
st.title("⚡ Evolución del consumo energético global")
with st.expander("📘 Acerca de esta sección", expanded=False):
    st.markdown("""
    Analiza la evolución del **consumo mundial de energía por fuente** (carbón, petróleo, gas, renovables, nuclear, hidro, etc.).  
    Incluye línea de tendencia, medias por década, **proyecciones hasta 2100** y **conclusiones automáticas**.  
    Al final, puedes **exportar** los datos filtrados (CSV) y el gráfico (PNG/HTML).
    """)

# ------------------------------------------
# UTILIDADES
# ------------------------------------------
def _safe_read_csv(path, **kwargs) -> pd.DataFrame:
    """Lectura robusta probando varios modos."""
    try:
        return pd.read_csv(path, **kwargs)
    except Exception:
        pass
    try:
        return pd.read_csv(path, engine="python", **kwargs)
    except Exception:
        pass
    try:
        return pd.read_csv(path, comment="#", engine="python", **kwargs)
    except Exception as e:
        st.error(f"❌ No se pudo leer el CSV '{path}': {e}")
        return pd.DataFrame()

# Columnas NO energéticas a ignorar
NON_ENERGY_COLS = {
    "country", "country name", "iso_code", "iso code", "iso", "region",
    "year", "population", "gdp", "continent"
}

# Patrones que SÍ queremos (consumos / electricidad totales)
# Evitamos *_per_capita, *_share_*, *_change_*, *_intensity, *_pct
def es_columna_energetica(c: str) -> bool:
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

# Nombres bonitos para mostrar
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
    # variantes de electricidad por fuente
    "coal_electricity": "Electricidad a partir de carbón (TWh)",
    "gas_electricity": "Electricidad a partir de gas (TWh)",
    "oil_electricity": "Electricidad a partir de petróleo (TWh)",
    "nuclear_electricity": "Electricidad nuclear (TWh)",
    "hydro_electricity": "Electricidad hidro (TWh)",
    "wind_electricity": "Electricidad eólica (TWh)",
    "solar_electricity": "Electricidad solar (TWh)",
    "biofuel_electricity": "Electricidad biocombustibles (TWh)",
    "renewables_electricity": "Electricidad renovable (TWh)",
    # agregados por si aparecen
    "fossil_fuel_consumption": "Fósiles (TWh)",
}

def nombre_bonito(col: str) -> str:
    col_l = col.lower()
    if col_l in NOMBRES_BONITOS:
        return NOMBRES_BONITOS[col_l]
    return col_l.replace("_", " ").capitalize() + " (TWh)"

# ------------------------------------------
# CARGA DE DATOS
# ------------------------------------------
@st.cache_data
def cargar_datos_energia_global():
    # Cargar CSV
    df = _safe_read_csv("data/energia/energy_consuption_by_source.csv")
    if df.empty:
        st.stop()

    # Normalizar encabezados
    df.columns = df.columns.str.strip()
    cols_lower = {c.lower(): c for c in df.columns}

    # Asegurar 'year'
    if "year" not in cols_lower:
        # intentar detectar 'año' o similar
        cand_year = next((c for c in df.columns if c.strip().lower() in {"año", "ano", "yr"}), None)
        if cand_year is None:
            st.error("❌ No se encontró la columna 'year' (o 'Año') en el CSV de energía.")
            st.stop()
        df = df.rename(columns={cand_year: "year"})
    else:
        df = df.rename(columns={cols_lower["year"]: "year"})

    # Bajar a minúsculas para filtrar por patrones
    df.columns = df.columns.str.lower()

    # Agregación global por año (sumando columnas numéricas)
    agrupado = df.groupby("year").sum(numeric_only=True).reset_index()

    # Filtrar columnas energéticas relevantes
    energy_cols = [c for c in agrupado.columns if es_columna_energetica(c)]
    if not energy_cols:
        st.error(
            "❌ No se detectaron columnas energéticas válidas.\n\n"
            f"Columnas disponibles:\n{list(agrupado.columns)}"
        )
        st.stop()

    # Pasar a formato largo
    largo = (
        agrupado[["year"] + energy_cols]
        .melt(id_vars="year", var_name="Fuente_raw", value_name="Consumo")
        .dropna()
    )

    # Coerción a numérico
    largo["Consumo"] = pd.to_numeric(largo["Consumo"], errors="coerce")
    largo = largo.dropna(subset=["Consumo"])

    # Renombrar y añadir nombre bonito
    largo = largo.rename(columns={"year": "Año"})
    largo["Fuente"] = largo["Fuente_raw"].apply(nombre_bonito)

    # Diccionario display->raw por si lo necesitamos
    mapping_display_to_raw = dict(zip(largo["Fuente"], largo["Fuente_raw"]))

    # Defaults sugeridos
    min_year, max_year = int(largo["Año"].min()), int(largo["Año"].max())
    default_raw = [
        "coal_consumption", "oil_consumption", "gas_consumption",
        "renewables_consumption", "nuclear_consumption", "hydro_consumption"
    ]
    defaults_display = [nombre_bonito(c) for c in default_raw if c in energy_cols]
    if not defaults_display:
        # si no existen esas, elegimos las 5 con mayor media
        top_media = (
            largo.groupby("Fuente")["Consumo"]
            .mean()
            .sort_values(ascending=False)
            .head(5)
            .index.tolist()
        )
        defaults_display = top_media

    return (
        largo,
        sorted(largo["Fuente"].unique().tolist()),
        defaults_display,
        (min_year, max_year),
        mapping_display_to_raw,
    )

df_long, fuentes_disponibles, defaults_display, (min_year, max_year), display_to_raw = cargar_datos_energia_global()

# ------------------------------------------
# SIDEBAR
# ------------------------------------------
st.sidebar.header("🔧 Personaliza la visualización")

fuentes_sel = st.sidebar.multiselect(
    "Selecciona fuentes energéticas",
    options=fuentes_disponibles,
    default=defaults_display,
    help="Puedes elegir varias fuentes para comparar."
)

rango = st.sidebar.slider(
    "Selecciona el rango de años",
    min_value=min_year,
    max_value=max_year,
    value=(max(min_year, 1980), max_year)
)

tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Línea", "Área (apilada)", "Barras"])
usar_escala_log = st.sidebar.checkbox("🧮 Usar escala logarítmica", value=False)
mostrar_tendencia = st.sidebar.checkbox("📈 Mostrar línea de tendencia", value=True)
mostrar_decadas = st.sidebar.checkbox("📊 Mostrar media por décadas", value=True)
mostrar_prediccion = st.sidebar.checkbox("🔮 Incluir modelo predictivo", value=True)

# ------------------------------------------
# FILTRADO
# ------------------------------------------
df_f = df_long[(df_long["Fuente"].isin(fuentes_sel)) & (df_long["Año"].between(*rango))].copy()

# ------------------------------------------
# VISUALIZACIÓN PRINCIPAL
# ------------------------------------------
titulo = "Evolución del consumo energético por fuente (global)"
if tipo_grafico == "Línea":
    fig = px.line(
        df_f, x="Año", y="Consumo", color="Fuente", markers=True,
        labels={"Consumo": "Consumo energético (TWh)", "Año": "Año"},
        title=titulo
    )
elif tipo_grafico == "Área (apilada)":
    fig = px.area(
        df_f, x="Año", y="Consumo", color="Fuente",
        labels={"Consumo": "Consumo energético (TWh)", "Año": "Año"},
        title=titulo
    )
else:
    fig = px.bar(
        df_f, x="Año", y="Consumo", color="Fuente",
        labels={"Consumo": "Consumo energético (TWh)", "Año": "Año"},
        title=titulo
    )

if usar_escala_log:
    fig.update_yaxes(type="log", title="Consumo energético (escala logarítmica)")

# ------------------------------------------
# TENDENCIAS (por fuente seleccionada)
# ------------------------------------------
tendencias = {}  # Fuente -> pendiente (TWh/año)
if mostrar_tendencia or mostrar_prediccion:
    for fuente in fuentes_sel:
        df_src = df_f[df_f["Fuente"] == fuente]
        if len(df_src) > 1:
            x = df_src["Año"].values.reshape(-1, 1)
            y = df_src["Consumo"].values
            modelo = LinearRegression().fit(x, y)
            y_pred = modelo.predict(x)
            pendiente = float(modelo.coef_[0])
            tendencias[fuente] = pendiente

            if mostrar_tendencia:
                fig.add_scatter(
                    x=df_src["Año"], y=y_pred, mode="lines",
                    name=f"Tendencia {fuente}",
                    line=dict(dash="dash", width=2)
                )

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# RESUMEN AUTOMÁTICO
# ------------------------------------------
st.subheader("🧾 Resumen automático del análisis")
if not df_f.empty:
    df_reciente = df_f[df_f["Año"] == df_f["Año"].max()]
    fuente_max_reciente = df_reciente.loc[df_reciente["Consumo"].idxmax(), "Fuente"]
    valor_max_reciente = df_reciente["Consumo"].max()
    st.markdown(
        f"⚡ En **{int(df_reciente['Año'].max())}**, la fuente con mayor consumo global fue **{fuente_max_reciente}** "
        f"con **{valor_max_reciente:,.0f} TWh**."
    )

    if tendencias:
        tendencia_media = float(np.mean(list(tendencias.values())))
        simbolo = "📈" if tendencia_media > 0 else "📉" if tendencia_media < 0 else "⚖️"
        st.markdown(f"{simbolo} **Cambio medio agregado:** {tendencia_media:,.2f} TWh/año.")
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
        df_dec.groupby(["Década", "Fuente"], as_index=False)["Consumo"].mean()
    )
    st.dataframe(tabla_dec.style.format({"Consumo": "{:,.0f}"}), use_container_width=True)

    fig_dec = px.bar(
        tabla_dec, x="Década", y="Consumo", color="Fuente", barmode="group",
        labels={"Consumo": "Consumo medio (TWh)", "Década": "Década"},
        title="Consumo energético medio por década (global)"
    )
    if usar_escala_log:
        fig_dec.update_yaxes(type="log")
    st.plotly_chart(fig_dec, use_container_width=True)

# ------------------------------------------
# PREDICCIÓN HASTA 2100
# ------------------------------------------
if mostrar_prediccion and fuentes_sel:
    st.subheader("🔮 Proyección global por fuente hasta 2100")
    fig_pred = px.line(
        labels={"x": "Año", "y": "Consumo energético (TWh)"},
        title="Proyecciones por fuente (global)"
    )
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
# 🧩 CONCLUSIONES AUTOMÁTICAS CON COLOR
# ------------------------------------------
if not df_f.empty and len(fuentes_sel) > 0:
    st.subheader("🧩 Conclusiones automáticas")

    pendientes = {}
    for fuente in fuentes_sel:
        try:
            df_src = df_f[df_f["Fuente"] == fuente]
            x = df_src["Año"].values.reshape(-1, 1)
            y = df_src["Consumo"].values
            if len(y) < 2 or np.all(np.isnan(y)):
                continue
            modelo = LinearRegression().fit(x, y)
            pendientes[fuente] = float(modelo.coef_[0])
        except Exception:
            continue

    if pendientes:
        fuente_top = max(pendientes, key=pendientes.get)
        pend_top = pendientes[fuente_top]
        tendencia_txt = "ascendente" if pend_top > 0 else "descendente" if pend_top < 0 else "estable"

        color_fondo = "#ffcccc" if pend_top > 0 else "#ccffcc" if pend_top < 0 else "#e6e6e6"
        color_texto = "#222"

        # Década más activa (media de consumo más alta dentro del filtro)
        df_decada = df_f.copy()
        df_decada["Década"] = (df_decada["Año"] // 10) * 10
        medias_decadas = df_decada.groupby("Década")["Consumo"].mean()
        decada_max = int(medias_decadas.idxmax())
        valor_max = float(medias_decadas.max())

        frase_tend = (
            "📈 **Aumento sostenido del consumo energético global.**" if pend_top > 0 else
            "🟢 **Reducción o estabilización en el consumo energético.**" if pend_top < 0 else
            "➖ **Sin cambios relevantes en el periodo analizado.**"
        )

        st.markdown(
            f"""
            <div style="background-color:{color_fondo}; color:{color_texto};
                        padding:15px; border-radius:12px; border:1px solid #bbb;">
                <h4>📋 <b>Conclusión Final del Análisis ({rango[0]}–{rango[1]})</b></h4>
                <ul>
                    <li>La fuente con <b>mayor variación</b> es <b>{fuente_top}</b>,
                        con una tendencia <b>{tendencia_txt}</b> (pendiente media).</li>
                    <li>La década más activa fue la de <b>{decada_max}</b>,
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
        st.info("No hay datos válidos suficientes para generar conclusiones automáticas.")
else:
    st.info("Selecciona al menos una fuente energética y un rango válido para generar conclusiones.")

# ------------------------------------------
# DESCARGAS SEGURAS (CSV + PNG/HTML)
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")
col1, col2 = st.columns(2)

# Detectar DataFrame principal para exportar
df_export = df_f if "df_f" in locals() else None

# 📄 Descarga de CSV
with col1:
    if df_export is not None and not df_export.empty:
        try:
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📄 Descargar CSV",
                data=csv,
                file_name="consumo_energetico_filtrado.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"No se pudo generar el CSV: {e}")
    else:
        st.info("⚠️ No hay datos disponibles para exportar.")

# 🖼️ Descarga de imagen (con fallback a HTML interactivo)
with col2:
    try:
        import plotly.io as pio
        buffer = BytesIO()
        fig.write_image(buffer, format="png")
        st.download_button(
            "🖼️ Descargar gráfico (PNG)",
            data=buffer,
            file_name="grafico_consumo_energetico.png",
            mime="image/png"
        )
    except Exception:
        st.warning("⚠️ No se pudo generar la imagen (Kaleido no disponible en Streamlit Cloud).")
        html_bytes = fig.to_html().encode("utf-8")
        st.download_button(
            "🌐 Descargar gráfico (HTML interactivo)",
            data=html_bytes,
            file_name="grafico_interactivo.html",
            mime="text/html"
        )
