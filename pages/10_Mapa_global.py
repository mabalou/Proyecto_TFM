# ==========================================
# 10_Mapa_global.py — Mapa climático global PRO (con filtros avanzados)
# Compatible con el botón de Filtros del header (st.session_state.ui_show_filters)
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="🗺️ Mapa climático global", layout="wide")
st.title("🗺️ Mapa climático global interactivo")

with st.expander("ℹ️ ¿Qué muestra esta página?"):
    st.markdown("""
**Explora mapas y tendencias** de indicadores de clima y variables socioeconómicas por país,
y concentraciones globales de gases.  
Usa el **botón de Filtros de la cabecera** para personalizar: variable, año, países, animación,
escala logarítmica y más.
""")

# -------------------------------
# Utilidades / limpieza
# -------------------------------
AGG_PATTERNS = [
    "world", "income", "ibrd", "ida", "oecd",
    "european union", "euro area",
    "east asia", "south asia", "north america",
    "latin america", "caribbean", "central asia",
    "middle east", "north africa", "sub-saharan",
    "small states", "pacific island", "post-demographic",
    "pre-demographic", "early-demographic", "late-demographic"
]
def es_pais_real(name: str) -> bool:
    if not isinstance(name, str) or not name.strip():
        return False
    n = name.strip().lower()
    return not any(pat in n for pat in AGG_PATTERNS)

@st.cache_data
def _safe_read_csv(path, **kwargs):
    try:
        return pd.read_csv(path, **kwargs)
    except Exception:
        try:
            return pd.read_csv(path, engine="python", **kwargs)
        except Exception:
            try:
                return pd.read_csv(path, engine="python", comment="#", **kwargs)
            except Exception:
                return pd.DataFrame()

def _normaliza(df: pd.DataFrame, country_key=("country name","country"), year_key="year", value_key="value"):
    """Devuelve DataFrame con columnas: Country, Year, Value"""
    if df is None or df.empty:
        return pd.DataFrame(columns=["Country","Year","Value"])
    cols = {c.lower(): c for c in df.columns}
    # país
    ccol = None
    for k in country_key:
        if k in cols:
            ccol = cols[k]
            break
    # año
    ycol = cols.get(year_key, None)
    # valor
    vcol = cols.get(value_key, None)
    # fallback por si ya vienen "bonitos"
    if ccol is None:
        ccol = cols.get("country", None)
    if ycol is None:
        ycol = cols.get("year", None)
    if vcol is None:
        vcol = cols.get("value", None)
    if any(v is None for v in (ccol, ycol, vcol)):
        return pd.DataFrame(columns=["Country","Year","Value"])
    out = df.rename(columns={ccol:"Country", ycol:"Year", vcol:"Value"})[["Country","Year","Value"]]
    out["Year"] = pd.to_numeric(out["Year"], errors="coerce")
    out["Value"] = pd.to_numeric(out["Value"], errors="coerce")
    out = out.dropna(subset=["Country","Year","Value"])
    # filtra agregados/regiones
    out = out[out["Country"].map(es_pais_real)]
    return out

# -------------------------------
# Carga de datos DESDE MONGODB
# -------------------------------
@st.cache_data
def load_all_sources():
    from pymongo import MongoClient

    # --- Conexión ---
    uri = "mongodb+srv://marcosabal:parausarentfm123@tfmcc.qfbhjbv.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri)
    db = client["tfm_datos"]

    def _load_coll(name: str) -> pd.DataFrame:
        docs = list(db[name].find({}, {"_id": 0}))
        if not docs:
            return pd.DataFrame()
        df = pd.DataFrame(docs)
        df.columns = df.columns.str.strip().str.lower()
        return df

    # ---------------------------------
    # 1) CO₂ POR PAÍS (total y per cápita)
    # ---------------------------------
    co2c_raw = _load_coll("socioeconomico_co2_emissions_by_country")
    co2c     = pd.DataFrame(columns=["Country", "Year", "Value"])
    co2c_pc  = pd.DataFrame(columns=["Country", "Year", "Value"])

    if not co2c_raw.empty:
        if "co2" in co2c_raw.columns:
            co2c = _normaliza(co2c_raw.rename(columns={"co2": "value"}))
        elif "value" in co2c_raw.columns:
            co2c = _normaliza(co2c_raw)

        for cand in ["co2_per_capita", "co2_per_capita_t", "co2_pc"]:
            if cand in co2c_raw.columns:
                co2c_pc = _normaliza(co2c_raw.rename(columns={cand: "value"}))
                break
    # ---------------------------------
    # CH4 por país
    # ---------------------------------
    ch4_raw = _load_coll("gases_ch4_by_country")
    ch4 = pd.DataFrame(columns=["Country", "Year", "Value"])
    if not ch4_raw.empty:
        ch4 = _normaliza(ch4_raw)

    # ---------------------------------
    # N2O por país
    # ---------------------------------
    n2o_raw = _load_coll("gases_n2o_by_country")
    n2o = pd.DataFrame(columns=["Country", "Year", "Value"])
    if not n2o_raw.empty:
        n2o = _normaliza(n2o_raw)

    # ---------------------------------
    # 2) PIB
    # ---------------------------------
    gdp_raw = _load_coll("socioeconomico_gdp_by_country")
    gdp     = pd.DataFrame(columns=["Country", "Year", "Value"])
    gdp_pc  = pd.DataFrame(columns=["Country", "Year", "Value"])

    if not gdp_raw.empty:
        gdp = _normaliza(gdp_raw)
        for cand in ["gdp_per_capita_usd", "gdp_per_capita"]:
            if cand in gdp_raw.columns:
                gdp_pc = _normaliza(gdp_raw.rename(columns={cand: "value"}))
                break

    # ---------------------------------
    # 3) Población
    # ---------------------------------
    pop_raw = _load_coll("socioeconomico_population_by_country")
    pop     = pd.DataFrame(columns=["Country", "Year", "Value"])
    if not pop_raw.empty:
        pop = _normaliza(pop_raw)

    # ---------------------------------
    # 4) Gases GLOBALALES
    # ---------------------------------
    def _load_gas(coll_name: str, label: str):
        df = _load_coll(coll_name)
        if df.empty:
            return pd.DataFrame(columns=["Year", "Value", "Label"])

        df.columns = df.columns.str.lower()

        val_col = None
        for cand in ["average", "trend", "value"]:
            if cand in df.columns:
                val_col = cand
                break
        if val_col is None or "year" not in df.columns:
            return pd.DataFrame(columns=["Year", "Value", "Label"])

        aux = df.rename(columns={"year": "Year", val_col: "Value"})[["Year", "Value"]]
        aux["Year"] = pd.to_numeric(aux["Year"], errors="coerce")
        aux["Value"] = pd.to_numeric(aux["Value"], errors="coerce")
        aux = aux.dropna()
        aux["Label"] = label
        return aux

    co2_g = _load_gas("gases_greenhouse_gas_co2_global", "CO₂ (ppm)")
    ch4_g = _load_gas("gases_greenhouse_gas_ch4_global", "CH₄ (ppb)")
    n2o_g = _load_gas("gases_greenhouse_gas_n2o_global", "N₂O (ppb)")

    gases_globales = pd.concat([co2_g, ch4_g, n2o_g], ignore_index=True)

    # ---------------------------------
    # 4b) Gases POR PAÍS
    # ---------------------------------
    co2p_raw = _load_coll("gases_co2_by_country")
    ch4p_raw = _load_coll("gases_ch4_by_country")
    n2op_raw = _load_coll("gases_n2o_by_country")

    co2p = _normaliza(co2p_raw, value_key="value") if not co2p_raw.empty else pd.DataFrame(columns=["Country","Year","Value"])
    ch4p = _normaliza(ch4p_raw, value_key="value") if not ch4p_raw.empty else pd.DataFrame(columns=["Country","Year","Value"])
    n2op = _normaliza(n2op_raw, value_key="value") if not n2op_raw.empty else pd.DataFrame(columns=["Country","Year","Value"])


    # ---------------------------------
    # 5) Catálogo de variables por país
    # ---------------------------------
    variables = {}

    if not co2c.empty:    variables["CO₂ (socioeconómico, Mt) por país"] = co2c
    if not co2c_pc.empty: variables["CO₂ per cápita (t) por país"]        = co2c_pc
    if not gdp.empty:     variables["PIB (USD) por país"]                = gdp
    if not gdp_pc.empty:  variables["PIB per cápita (USD) por país"]     = gdp_pc
    if not pop.empty:     variables["Población por país"]                = pop
    if not ch4.empty: variables["Metano CH₄ (kt) por país"] = ch4
    if not n2o.empty: variables["Óxido nitroso N₂O (kt) por país"] = n2o
    if not co2p.empty: variables["CO₂ (kt) por país"] = co2p


    # ---------------------------------
    # 6) Rango de años
    # ---------------------------------
    years = []
    if variables:
        years += [int(v["Year"].min()) for v in variables.values()]
        years += [int(v["Year"].max()) for v in variables.values()]
    if not gases_globales.empty:
        years += [int(gases_globales["Year"].min()), int(gases_globales["Year"].max())]

    if years:
        min_year, max_year = min(years), max(years)
    else:
        min_year, max_year = 1960, 2024

    return variables, gases_globales, (min_year, max_year)
# -------------------------------
# Cargar datos (Mongo)
# -------------------------------
variables, gases_globales, (min_year, max_year) = load_all_sources()

# -------------------------------
# Estado inicial y Filtros (integrado con el header)
# -------------------------------
defaults = {
    # Si hay gases globales disponibles, empezamos en CO₂ global
    "map_var": "CO₂ (ppm) — global" if True else next(iter(variables.keys())),
    "year": max_year,
    "animate": False,
    "use_log": False,
    "countries_sel": [],
    "show_global_series": False,  # para gases globales
    "tipo_var": "🌍 Gases globales",  # nuevo: garantiza coherencia visual
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# Panel de filtros SOLO si el toggle global está activo (desde el header)
if st.session_state.get("ui_show_filters", False):
    with st.container(border=True):
        st.subheader("🎛️ Filtros")
        c1, c2 = st.columns([2, 1])

        with c1:
            tipo_var = st.radio(
                "Tipo de variable",
                ["🌍 Gases globales", "🏳️ Variables por país"],
                horizontal=True,
                key="tipo_var"
            )

            if tipo_var == "🌍 Gases globales":
                gases_opciones = ["CO₂ (ppm) — global", "CH₄ (ppb) — global", "N₂O (ppb) — global"]
                map_var = st.selectbox(
                    "Variable global a visualizar",
                    options=gases_opciones,
                    index=gases_opciones.index(st.session_state.map_var)
                    if st.session_state.map_var in gases_opciones else 0,
                    key="map_var"
                )
            else:
                pais_opciones = list(variables.keys())
                map_var = st.selectbox(
                    "Variable por país a visualizar",
                    options=pais_opciones,
                    index=pais_opciones.index(st.session_state.map_var)
                    if st.session_state.map_var in pais_opciones else 0,
                    key="map_var"
                )

        with c2:
            animate = st.checkbox("🎞️ Animar por años", value=st.session_state.animate, key="animate")
            use_log = st.checkbox("🧮 Escala logarítmica", value=st.session_state.use_log, key="use_log")
        # Si la variable es "por país", mostramos selector de países (corregido y estable)
        es_global = "— global" in st.session_state.map_var

        # 🔹 Asegura que siempre exista la clave countries_sel
        if "countries_sel" not in st.session_state:
            st.session_state.countries_sel = []

        if not es_global:
            # --- Variables por país ---
            dfv = variables.get(st.session_state.map_var, pd.DataFrame(columns=["Country", "Year", "Value"]))
            paises = sorted(dfv["Country"].unique().tolist()) if not dfv.empty else []

            # Filtra selección previa: elimina países no disponibles
            prev_sel = [p for p in st.session_state.get("countries_sel", []) if p in paises]

            st.multiselect(
                "Filtrar países (opcional)",
                paises,
                key="countries_sel",
                default=prev_sel,
            )
        else:
            # --- Gases globales ---
            # Limpia selección de países al cambiar a vista global (sin romper estado)
            st.session_state.countries_sel = []

        # --- Ajustar rango de años según la variable actual ---
        if "— global" in st.session_state.map_var:
            # Cargar los datos globales AQUÍ para que df exista
            label_tmp = st.session_state.map_var.replace("— global", "").replace("- global", "").strip()

            if "CO₂" in label_tmp or "CO2" in label_tmp:
                path_tmp = "data/gases/greenhouse_gas_co2_global.csv"
            elif "CH₄" in label_tmp or "CH4" in label_tmp:
                path_tmp = "data/gases/greenhouse_gas_ch4_global.csv"
            else:
                path_tmp = "data/gases/greenhouse_gas_n2o_global.csv"

            df_tmp = _safe_read_csv(path_tmp)
            df_tmp.columns = df_tmp.columns.str.strip().str.lower()

            # identifica la columna de valor
            val_col = next((c for c in ["average", "trend", "value", "global"] if c in df_tmp.columns), None)

            if val_col:
                df_tmp = df_tmp.rename(columns={"year": "Year", val_col: "Value"})
                df_tmp["Year"] = pd.to_numeric(df_tmp["Year"], errors="coerce")
                df_tmp = df_tmp.dropna()

                slider_min = int(df_tmp["Year"].min())
                slider_max = int(df_tmp["Year"].max())
            else:
                slider_min, slider_max = min_year, max_year

        else:
            # Caso: variable por país
            dfv = variables.get(st.session_state.map_var, pd.DataFrame())
            if dfv.empty:
                slider_min, slider_max = min_year, max_year
            else:
                slider_min = int(dfv["Year"].min())
                slider_max = int(dfv["Year"].max())

        # Slider usando el rango adecuado
        year = st.slider(
            "Año",
            min_value=slider_min,
            max_value=slider_max,
            value=min(slider_max, st.session_state.year),
            key="year",
        )

else:
    # Garantiza consistencia interna aunque no se muestren filtros
    map_var = st.session_state.map_var
    animate = st.session_state.animate
    use_log = st.session_state.use_log
    year = st.session_state.year


# -------------------------------
# LÓGICA: Global vs Por País
# -------------------------------
def _fmt_value(var_name: str, v: float) -> str:
    if v is None or pd.isna(v):
        return "—"
    if "USD" in var_name:
        return f"${v:,.0f}"
    if "CO₂" in var_name or "CO2" in var_name:
        if "per cápita" in var_name:
            return f"{v:,.2f} t"
        return f"{v:,.0f} Mt"
    if "Población" in var_name:
        return f"{v:,.0f} hab."
    if "(ppm)" in var_name or "(ppb)" in var_name:
        return f"{v:,.2f}"
    return f"{v:,.2f}"

# ------------- Caso A: GASES GLOBALES -------------
if isinstance(st.session_state.map_var, str) and "— global" in st.session_state.map_var:
    # Detectamos qué gas se seleccionó
    label = st.session_state.map_var.replace("— global", "").replace("- global", "").strip()
    if "CO₂" in label or "CO2" in label:
        path = "data/gases/greenhouse_gas_co2_global.csv"
        unidad = "ppm"
    elif "CH₄" in label or "CH4" in label:
        path = "data/gases/greenhouse_gas_ch4_global.csv"
        unidad = "ppb"
    else:
        path = "data/gases/greenhouse_gas_n2o_global.csv"
        unidad = "ppb"

    # Leer CSV local
    df = _safe_read_csv(path, comment="#")
    if df.empty:
        st.warning(f"No se pudo leer el archivo: {path}")
        st.stop()

    # Intentar localizar columna de valores
    df.columns = df.columns.str.strip().str.lower()
    val_col = None
    for cand in ["average", "trend", "value", "global"]:
        if cand in df.columns:
            val_col = cand
            break
    if val_col is None:
        st.warning(f"No se encontró columna de valores en {path}")
        st.stop()

    # Normalizar columnas
    df = df.rename(columns={"year": "Year", val_col: "Value"})[["Year", "Value"]]
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.dropna()

    if df.empty:
        st.info("No hay datos válidos para esta serie global.")
        st.stop()

    # 🔹 Año seleccionado desde el slider
    selected_year = st.session_state.year
    # Buscar valor del año seleccionado o el más cercano
    if selected_year not in df["Year"].values:
        closest_year = df.iloc[(df["Year"] - selected_year).abs().argsort().iloc[0]]["Year"]
    else:
        closest_year = selected_year

    val_actual = df.loc[df["Year"] == closest_year, "Value"].iloc[0]
    val_inicial = df.loc[df["Year"] == df["Year"].min(), "Value"].iloc[0]
    variacion = ((val_actual - val_inicial) / val_inicial) * 100

    # Crear "globo" coloreado (simbólico): todos los países con el valor de ese año
    world = px.data.gapminder().query("year == 2007")[["country"]].drop_duplicates()
    world["Value"] = val_actual

    st.subheader(f"{label} — Concentración global ({unidad})")
    c1, c2 = st.columns([3, 1], gap="large")

    with c1:
        fig = px.choropleth(
            world,
            locations="country",
            locationmode="country names",
            color="Value",
            color_continuous_scale="Viridis",
            range_color=[df["Value"].min(), df["Value"].max()],
            labels={"Value": f"{label} ({unidad})"},
            title=None
        )
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("### 🧾 Resumen")
        st.markdown(f"""
        - 📆 **Año seleccionado:** {int(closest_year)}  
        - 🌍 **Valor global:** {val_actual:.2f} {unidad}  
        - 📉 **Cambio desde {int(df['Year'].min())}:** {variacion:+.1f}%
        """)

    # ==============================================================
# 🔥 A + B → Top-10 real por país (solo cuando la variable es GLOBAL)
# ==============================================================

if "— global" in st.session_state.map_var:

    st.markdown("---")
    st.subheader(f"🏆 Top-10 países por emisiones reales de {label} en {selected_year}")

    # Seleccionar dataset correcto según el gas GLOBAL
    if "CO₂" in label or "CO2" in label:
        df_country = variables.get("CO₂ (kt) por país", pd.DataFrame())
        unidad_country = "kt"

    elif "CH₄" in label or "CH4" in label:
        df_country = variables.get("Metano CH₄ (kt) por país", pd.DataFrame())
        unidad_country = "kt"

    elif "N₂O" in label or "N2O" in label:
        df_country = variables.get("Óxido nitroso N₂O (kt) por país", pd.DataFrame())
        unidad_country = "kt"


    # 🚨 Verificar que el dataset por país existe y tiene columnas obligatorias
    if df_country.empty or not all(c in df_country.columns for c in ["Country", "Year", "Value"]):
        st.info("⚠️ No existen datos por país para este gas. Solo hay valores globales.")
    else:
        # Filtrar año
        year_df = df_country[df_country["Year"] == selected_year].dropna(subset=["Value"])

        if not year_df.empty:

            # --- Top-10 ---
            top10 = (
                year_df.sort_values("Value", ascending=False)
                .head(10)
                .rename(columns={"Country": "País", "Value": f"Emisiones ({unidad_country})"})
            )

            # --- Gráfico horizontal ---
            fig_top = px.bar(
                top10,
                x=f"Emisiones ({unidad_country})",
                y="País",
                orientation="h",
                title=None
            )

            fig_top.update_layout(
                height=450,
                template="plotly_dark",
                yaxis=dict(categoryorder="total ascending")
            )

            st.plotly_chart(fig_top, use_container_width=True)

            # --- Resumen ---
            pais_max = top10.iloc[0]["País"]
            val_max = top10.iloc[0][f"Emisiones ({unidad_country})"]

            st.success(
                f"🌎 En **{selected_year}**, el país con más emisiones de **{label}** "
                f"fue **{pais_max}** con **{val_max:,.2f} {unidad_country}**."
            )

        else:
            st.info("No hay datos por país para este año.")

    # ==============================================================
    # 📈 Serie temporal global (normalizada y suavizada)
    # ==============================================================
    st.subheader("📈 Serie temporal global (normalizada y suavizada)")

    df_norm = df.copy()
    # Normalizar entre 0–1
    df_norm["Norm"] = (df_norm["Value"] - df_norm["Value"].min()) / (df_norm["Value"].max() - df_norm["Value"].min())
    # Agrupar por año por si hay duplicados
    df_norm = df_norm.groupby("Year", as_index=False)["Norm"].mean()

    # Interpolar para suavizar años faltantes
    df_norm = df_norm.set_index("Year").reindex(
        range(int(df_norm["Year"].min()), int(df_norm["Year"].max()) + 1)
    )
    df_norm["Norm"] = df_norm["Norm"].interpolate(method="linear")

    # Suavizado adicional (ventana móvil)
    df_norm["Suavizada"] = df_norm["Norm"].rolling(window=5, center=True, min_periods=1).mean()
    df_norm = df_norm.reset_index().rename(columns={"index": "Year"})

    # Crear gráfico (mismo estilo que en gases)
    fig_line = px.line(
        df_norm,
        x="Year",
        y="Suavizada",
        title=f"Evolución normalizada de {label}",
        labels={"Year": "Año", "Suavizada": "Proporción relativa (0–1)"},
        color_discrete_sequence=["#00BFFF"]
    )

    # Añadir punto del año seleccionado
    y_point = df_norm.loc[df_norm["Year"] == closest_year, "Suavizada"].iloc[0]
    fig_line.add_scatter(
        x=[closest_year],
        y=[y_point],
        mode="markers+text",
        text=["Año seleccionado"],
        textposition="top center",
        marker=dict(color="red", size=10),
        name="Año actual"
    )

    # Tendencia lineal (ajustada como en gases)
    from sklearn.linear_model import LinearRegression
    x = df_norm["Year"].values.reshape(-1, 1)
    y = df_norm["Suavizada"].values
    modelo = LinearRegression().fit(x, y)
    y_pred = modelo.predict(x)
    fig_line.add_scatter(
        x=df_norm["Year"],
        y=y_pred,
        mode="lines",
        line=dict(color="orange", dash="dash"),
        name="Tendencia"
    )

    # Estilo coherente con los otros módulos
    fig_line.update_layout(
        template="plotly_dark",
        font=dict(size=15),
        xaxis_title_font=dict(size=16),
        yaxis_title_font=dict(size=16),
        legend_title_text="Indicador"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    
    # ==============================================================
    # 💾 Exportaciones
    # ==============================================================
    st.markdown("---")
    st.subheader("💾 Exportar")
    c1, c2 = st.columns(2)
    with c1:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📄 Descargar datos (CSV)",
            data=csv,
            file_name=f"{label.replace(' ', '_')}_global.csv",
            mime="text/csv"
        )
    with c2:
        import plotly.io as pio
        html_bytes = pio.to_html(fig_line, full_html=False).encode("utf-8")
        st.download_button(
            "🖼️ Descargar gráfico (HTML interactivo)",
            data=html_bytes,
            file_name=f"{label.replace(' ', '_')}_global.html",
            mime="text/html"
        )

# ------------- Caso B: INDICADORES POR PAÍS -------------
else:
    var_name = st.session_state.map_var
    dfv = variables.get(var_name, pd.DataFrame(columns=["Country","Year","Value"]))
    if dfv.empty:
        st.info("No hay datos para la variable seleccionada.")
        st.stop()

    # Aplicar filtro de países (si hay selección)
    if st.session_state.countries_sel:
        dfv = dfv[dfv["Country"].isin(st.session_state.countries_sel)]

    st.subheader(f"{var_name}")
    fmt_two = (".2f" if any(s in var_name for s in ["USD","CO₂","CO2","(ppm)","(ppb)","per cápita"]) else ".0f")

    # Choropleth
    if animate:
        fig_map = px.choropleth(
            dfv, locations="Country", locationmode="country names",
            color="Value", hover_name="Country", animation_frame="Year",
            color_continuous_scale="Viridis",
            labels={"Value": var_name}, title=None
        )
    else:
        mdf = dfv[dfv["Year"] == st.session_state.year].copy()
        fig_map = px.choropleth(
            mdf, locations="Country", locationmode="country names",
            color="Value", hover_name="Country",
            color_continuous_scale="Viridis",
            labels={"Value": var_name}, title=None
        )
    if use_log:
        fig_map.update_coloraxes(colorbar_title=var_name, colorscale="Viridis")
        fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0))

    # ✅ Añadimos resumen lateral como en el resto de páginas
    c1, c2 = st.columns([3, 1], gap="large")

    with c1:
        st.plotly_chart(fig_map, use_container_width=True)

    with c2:
        st.markdown("### 🧾 Resumen")
        mdf = dfv[dfv["Year"] == st.session_state.year].dropna(subset=["Value"])
        if not mdf.empty:
            vmin, vmax = mdf["Value"].min(), mdf["Value"].max()
            media = mdf["Value"].mean()
            pais_min = mdf.loc[mdf["Value"].idxmin(), "Country"]
            pais_max = mdf.loc[mdf["Value"].idxmax(), "Country"]

            st.markdown(f"""
            - 📆 **Año:** {st.session_state.year}  
            - 🔼 **Máximo:** {_fmt_value(var_name, vmax)} (*{pais_max}*)  
            - 🔽 **Mínimo:** {_fmt_value(var_name, vmin)} (*{pais_min}*)  
            - 📊 **Media mundial:** {_fmt_value(var_name, media)}
            """)
        else:
            st.info("No hay datos válidos para el año seleccionado.")

# -------------------------------
# TOP-10 SOLO PARA VARIABLES POR PAÍS
# -------------------------------
if "— global" not in st.session_state.map_var:

    st.subheader(f"🏆 Top 10 países — {st.session_state.year}")

    # df_original = todos los países SIN filtro del multiselect
    df_original = variables.get(var_name, pd.DataFrame()).copy()

    # Si el usuario filtró países → top solo sobre esos países
    if st.session_state.countries_sel:
        base_df = df_original[df_original["Country"].isin(st.session_state.countries_sel)].copy()
    else:
        base_df = df_original

    year_df = base_df[base_df["Year"] == st.session_state.year].dropna(subset=["Value"])

    top_df = (
        year_df.sort_values("Value", ascending=False)  # mayor → menor
        .head(10)
        .rename(columns={"Country": "País", "Year": "Año", "Value": var_name})
    )

    if not top_df.empty:

        # --- Gráfico horizontal SIN TEXTOS dentro de las barras ---
        import plotly.express as px
        fig_top = px.bar(
            top_df,
            x=var_name,
            y="País",
            orientation="h",
            title=None
        )

        fig_top.update_layout(
            height=500,
            margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_dark",
            yaxis=dict(categoryorder="total ascending")   # ← ESTA LÍNEA
        )

        st.plotly_chart(fig_top, use_container_width=True)

        # Resumen debajo del gráfico
        pais_top = top_df.iloc[0]["País"]
        valor_top = top_df.iloc[0][var_name]
        st.success(
            f"📊 En **{st.session_state.year}**, el valor más alto de **{var_name}** "
            f"lo tiene **{pais_top}** con **{_fmt_value(var_name, valor_top)}**."
        )

    else:
        st.info("No hay datos suficientes para generar el Top-10 este año.")

    # Tendencia temporal del Top-5 del año
    st.subheader("📈 Tendencia temporal del Top-5")

    top5 = top_df["País"].head(5).tolist() if not top_df.empty else []

    # Para la serie temporal usamos SIEMPRE todos los años disponibles
    # de esos países (df_original, sin filtrar por selection del año)
    trend = df_original[df_original["Country"].isin(top5)].copy()

    if not trend.empty and len(top5) > 0:
        fig_line = px.line(
            trend,
            x="Year",
            y="Value",
            color="Country",
            labels={"Year": "Año", "Value": var_name, "Country": "País"},
            title=None,
            markers=True,
        )
        if use_log:
            fig_line.update_yaxes(type="log")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Selecciona un año con datos para construir el Top-5 y su serie temporal.")

    # Conclusiones automáticas
    st.subheader("🧩 Conclusiones automáticas")
    concl = []
    if not top_df.empty:
        concl.append(f"• **{top_df.iloc[0]['País']}** lidera **{var_name}** en {st.session_state.year}.")
    try:
        # Tendencia media global (sobre el df ORIGINAL, no filtrado)
        gseries = df_original.groupby("Year")["Value"].mean().dropna()
        if len(gseries) > 2:
            x = gseries.index.values
            y = gseries.values
            coef = np.polyfit(x, y, 1)[0]
            tend = "ascendente" if coef > 0 else "descendente" if coef < 0 else "estable"
            concl.append(f"• Tendencia promedio global **{tend}** en el periodo ({coef:,.3g} por año).")
    except Exception:
        pass

    if concl:
        st.success("\n\n".join(concl))
    else:
        st.info("Ajusta los filtros para generar conclusiones útiles.")

    # Exportaciones (datos + mapa)
    st.markdown("---")
    st.subheader("💾 Exportar")
    c1, c2 = st.columns(2)
    with c1:
        try:
            if animate:
                export_df = dfv.copy()
            else:
                export_df = dfv[dfv["Year"] == st.session_state.year].copy()
            csv = (
                export_df
                .rename(columns={"Country": "País", "Year": "Año", "Value": var_name})
                .to_csv(index=False)
                .encode("utf-8")
            )
            st.download_button(
                "📄 Descargar datos (CSV)",
                data=csv,
                file_name="mapa_global_filtrado.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.error(f"No se pudo generar el CSV: {e}")
    with c2:
        import plotly.io as pio
        html_bytes = pio.to_html(fig_map, full_html=False).encode("utf-8")
        st.download_button(
            "🖼️ Descargar mapa (HTML interactivo)",
            data=html_bytes,
            file_name="mapa_global.html",
            mime="text/html",
        )