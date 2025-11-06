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
# Carga de datos (según tus CSV)
# -------------------------------
@st.cache_data
def load_all_sources():
    # CO2 por país (total y per cápita si existe)
    co2c_raw = _safe_read_csv("data/socioeconomico/co2_emissions_by_country.csv")
    co2c = pd.DataFrame(columns=["Country","Year","Value"])
    co2c_pc = pd.DataFrame(columns=["Country","Year","Value"])
    if not co2c_raw.empty:
        co2c_raw.columns = co2c_raw.columns.str.strip().str.lower()
        # total
        if "co2" in co2c_raw.columns:
            co2c = _normaliza(co2c_raw.rename(columns={"co2":"value"}))
        elif "value" in co2c_raw.columns:
            co2c = _normaliza(co2c_raw)
        # per cápita si existe
        for cand in ["co2_per_capita", "co2_per_capita_t", "co2_pc"]:
            if cand in co2c_raw.columns:
                co2c_pc = _normaliza(co2c_raw.rename(columns={cand:"value"}))
                break

    # PIB
    gdp_raw = _safe_read_csv("data/socioeconomico/gdp_by_country.csv")
    gdp = pd.DataFrame(columns=["Country","Year","Value"])
    gdp_pc = pd.DataFrame(columns=["Country","Year","Value"])
    if not gdp_raw.empty:
        gdp_raw.columns = gdp_raw.columns.str.strip().str.lower()
        gdp = _normaliza(gdp_raw)  # suele venir 'value' como PIB total
        for cand in ["gdp_per_capita_usd","gdp_per_capita"]:
            if cand in gdp_raw.columns:
                gdp_pc = _normaliza(gdp_raw.rename(columns={cand:"value"}))
                break

    # Población
    pop_raw = _safe_read_csv("data/socioeconomico/population_by_country.csv")
    pop = pd.DataFrame(columns=["Country","Year","Value"])
    if not pop_raw.empty:
        pop_raw.columns = pop_raw.columns.str.strip().str.lower()
        pop = _normaliza(pop_raw)

    # Gases globales (concentraciones)
    def _load_gas(path, label):
        df = _safe_read_csv(path, comment="#")
        if df.empty:
            return pd.DataFrame(columns=["Year","Value"])
        df.columns = df.columns.str.strip().str.lower()
        if "year" not in df.columns:
            return pd.DataFrame(columns=["Year","Value"])
        val_col = None
        for cand in ["average", "trend", "value"]:
            if cand in df.columns:
                val_col = cand
                break
        if val_col is None:
            return pd.DataFrame(columns=["Year","Value"])
        aux = df.rename(columns={"year":"Year", val_col:"Value"})[["Year","Value"]]
        aux["Year"] = pd.to_numeric(aux["Year"], errors="coerce")
        aux["Value"] = pd.to_numeric(aux["Value"], errors="coerce")
        aux = aux.dropna()
        aux["Label"] = label
        return aux

    co2_g = _load_gas("data/gases/greenhouse_gas_co2_global.csv", "CO₂ (ppm)")
    ch4_g = _load_gas("data/gases/greenhouse_gas_ch4_global.csv", "CH₄ (ppb)")
    n2o_g = _load_gas("data/gases/greenhouse_gas_n2o_global.csv", "N₂O (ppb)")

    # Construir catálogo de variables disponibles
    variables = {}
    if not co2c.empty:    variables["CO₂ (socioeconómico, Mt) por país"] = co2c
    if not co2c_pc.empty: variables["CO₂ per cápita (t) por país"] = co2c_pc
    if not gdp.empty:     variables["PIB (USD) por país"] = gdp
    if not gdp_pc.empty:  variables["PIB per cápita (USD) por país"] = gdp_pc
    if not pop.empty:     variables["Población por país"] = pop

    gases_globales = pd.concat([co2_g, ch4_g, n2o_g], ignore_index=True)
    # Rango años global para los selectores
    min_year = 1960
    max_year = 2024
    years = []
    if variables:
        years += [int(v["Year"].min()) for v in variables.values() if not v.empty]
        years += [int(v["Year"].max()) for v in variables.values() if not v.empty]
    if not gases_globales.empty:
        years += [int(gases_globales["Year"].min()), int(gases_globales["Year"].max())]
    if years:
        min_year, max_year = min(years), max(years)

    return variables, gases_globales, (min_year, max_year)

variables, gases_globales, (min_year, max_year) = load_all_sources()
if not variables and gases_globales.empty:
    st.error("No se han podido cargar datos. Revisa las rutas y columnas de los CSV.")
    st.stop()

# -------------------------------
# Estado inicial y Filtros (integrado con el header)
# -------------------------------
# Defaults robustos
defaults = {
    "map_var": next(iter(variables.keys())) if variables else "CO₂ (ppm) — global",
    "year": max_year,
    "animate": False,
    "use_log": False,
    "countries_sel": [],
    "show_global_series": False,  # para gases globales
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

        # Si la variable es "por país", mostramos selector de países
        es_global = "— global" in st.session_state.map_var
        if not es_global:
            dfv = variables.get(st.session_state.map_var, pd.DataFrame(columns=["Country","Year","Value"]))
            paises = sorted(dfv["Country"].unique().tolist()) if not dfv.empty else []
            st.session_state.countries_sel = st.multiselect(
                "Filtrar países (opcional)",
                paises,
                default=st.session_state.countries_sel
            )

        # Slider de año
        year = st.slider("Año", min_value=min_year, max_value=max_year, value=max_year, key="year")
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
    label = st.session_state.map_var.replace(" — global", "")
    g = gases_globales[gases_globales["Label"] == label.replace(" (ppm)", "").replace(" (ppb)", "")] if " (" in label else gases_globales[gases_globales["Label"] == label]
    if g.empty:
        st.info("No hay datos globales para esta serie.")
    else:
        st.subheader(f"{label} — Serie temporal global")
        fig = px.line(g, x="Year", y="Value", markers=True, labels={"Year":"Año","Value":label})
        if use_log:
            fig.update_yaxes(type="log")
        st.plotly_chart(fig, use_container_width=True)

        # Resumen
        g_year = g[g["Year"] == min(max_year, st.session_state.year)]
        if not g_year.empty:
            val = g_year["Value"].iloc[0]
            st.success(f"📅 En **{int(st.session_state.year)}**, el valor de **{label}** fue **{_fmt_value(label, val)}**.")

        # Exportaciones sencillas
        st.markdown("---")
        st.subheader("💾 Exportar")
        c1, c2 = st.columns(2)
        with c1:
            try:
                csv = g.to_csv(index=False).encode("utf-8")
                st.download_button("📄 Descargar datos (CSV)", data=csv, file_name=f"{label}_global.csv", mime="text/csv")
            except Exception as e:
                st.error(f"No se pudo exportar CSV: {e}")
        with c2:
            try:
                from io import BytesIO
                import plotly.io as pio
                buffer = BytesIO()
                fig.write_image(buffer, format="png")
                st.download_button("🖼️ Descargar gráfico (PNG)", data=buffer, file_name=f"{label}_global.png", mime="image/png")
            except Exception:
                html_bytes = fig.to_html().encode("utf-8")
                st.download_button("🌐 Descargar gráfico (HTML interactivo)", data=html_bytes, file_name=f"{label}_global.html", mime="text/html")

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


    # Top-10 del año
    st.subheader(f"🏆 Top 10 países — {st.session_state.year}")
    top_df = (
        dfv[dfv["Year"] == st.session_state.year]
        .dropna(subset=["Value"])
        .sort_values("Value", ascending=False)
        .head(10)
        .rename(columns={"Country":"País","Year":"Año","Value":var_name})
    )
    if not top_df.empty:
        # Formato agradable
        top_show = top_df.copy()
        top_show[var_name] = top_show[var_name].apply(lambda x: _fmt_value(var_name, x))
        st.dataframe(top_show, use_container_width=True)
        # Resumen
        pais_top = top_df.iloc[0]["País"]
        valor_top = top_df.iloc[0][var_name]
        st.success(f"📊 En **{st.session_state.year}**, el valor más alto de **{var_name}** lo tiene **{pais_top}** con **{_fmt_value(var_name, valor_top)}**.")
    else:
        st.info("No hay datos para este año tras aplicar los filtros.")

    # Tendencia temporal del Top-5 del año
    st.subheader("📈 Tendencia temporal del Top-5")
    top5 = top_df["País"].head(5).tolist() if not top_df.empty else []
    trend = dfv[dfv["Country"].isin(top5)].copy()
    if not trend.empty and len(top5) > 0:
        fig_line = px.line(
            trend, x="Year", y="Value", color="Country",
            labels={"Year":"Año", "Value":var_name, "Country":"País"},
            title=None, markers=True
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
    # pendiente media global sobre el rango disponible
    try:
        gseries = dfv.groupby("Year")["Value"].mean().dropna()
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
            csv = export_df.rename(columns={"Country":"País","Year":"Año","Value":var_name}).to_csv(index=False).encode("utf-8")
            st.download_button("📄 Descargar datos (CSV)", data=csv, file_name="mapa_global_filtrado.csv", mime="text/csv")
        except Exception as e:
            st.error(f"No se pudo generar el CSV: {e}")
    with c2:
        import plotly.io as pio
        # Exportar el mapa en formato HTML interactivo (compatible con Streamlit Cloud)
        html_bytes = pio.to_html(fig_map, full_html=False).encode("utf-8")
        st.download_button(
            "🖼️ Descargar mapa (HTML interactivo)",
            data=html_bytes,
            file_name="mapa_global.html",
            mime="text/html"
        )