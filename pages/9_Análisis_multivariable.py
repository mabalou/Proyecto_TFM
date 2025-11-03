# ==========================================
# 9_Análisis_multivariable.py  (robusto)
# ==========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="🔗 Análisis multivariable", layout="wide")
st.title("🔗 Análisis multivariable: clima ↔ sociedad")
st.markdown("""
Analiza **tendencias, correlaciones y predicciones** multivariables para entender el impacto humano en el cambio climático.
""")

# -------------------------------------------------
# UTILIDADES
# -------------------------------------------------
def _safe_read_csv(path, **kwargs):
    """
    Lectura robusta de CSV probando distintas estrategias.
    """
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
        st.warning(f"⚠️ Error cargando {path}: {e}")
        return pd.DataFrame()

def _lin_trend(x_year: pd.Series, y: pd.Series):
    """
    Pendiente de regresión lineal simple (Año → y).
    Devuelve (pendiente, modelo) o (nan, None) si no hay datos.
    """
    x_clean = pd.to_numeric(x_year, errors="coerce")
    y_clean = pd.to_numeric(y, errors="coerce")
    m = (~x_clean.isna()) & (~y_clean.isna())
    if m.sum() < 2:
        return np.nan, None
    X = x_clean[m].values.reshape(-1, 1)
    Y = y_clean[m].values
    lr = LinearRegression().fit(X, Y)
    return float(lr.coef_[0]), lr

def _zscore(df_num: pd.DataFrame):
    return (df_num - df_num.mean()) / df_num.std(ddof=0)

def _ensure_year_column(df, prefer="Año"):
    """
    Asegura que exista 'Año' a partir de posibles variantes ('year', 'Year').
    """
    if df.empty:
        return df
    cols_lower = {c.lower(): c for c in df.columns}
    if "año" in cols_lower:
        if "Año" not in df.columns:
            df = df.rename(columns={cols_lower["año"]: "Año"})
    elif "year" in cols_lower:
        df = df.rename(columns={cols_lower["year"]: "Año"})
    if "Año" not in df.columns:
        st.warning("⚠️ No se detectó columna 'Año' en un dataset. Revisar CSV.")
        return pd.DataFrame(columns=["Año"])
    return df

# -------------------------------------------------
# CARGA GLOBAL (clima + energía agregada mundial)
# -------------------------------------------------
@st.cache_data
def load_global_sources():
    dfs = []

    # 1) Temperatura global (distintos formatos)
    try:
        t = _safe_read_csv("data/temperatura/global_temperature_nasa.csv")
        if not t.empty:
            t.columns = t.columns.str.strip()
            # Caso típico NASA con 'Year' y columnas mensuales / J-D
            if "Year" in t.columns or "year" in t.columns:
                t = _ensure_year_column(t)
                # Tomamos media de todas las columnas numéricas excepto Año
                num_cols = [c for c in t.columns if c != "Año"]
                t["Temp_anom_C"] = pd.to_numeric(t[num_cols], errors="coerce").mean(axis=1)
                t = t[["Año", "Temp_anom_C"]].dropna()
            else:
                # Otra variante (p.ej. ya agregada anual)
                # Intentamos detectar una columna numérica principal
                num_cols = [c for c in t.columns if c.lower() not in {"año", "year"}]
                t = _ensure_year_column(t)
                if "Año" in t.columns and num_cols:
                    cand = pd.to_numeric(t[num_cols], errors="coerce")
                    t["Temp_anom_C"] = cand.mean(axis=1)
                    t = t[["Año", "Temp_anom_C"]].dropna()
                else:
                    t = pd.DataFrame(columns=["Año", "Temp_anom_C"])
        else:
            t = pd.DataFrame(columns=["Año", "Temp_anom_C"])
        if t.empty:
            st.warning("⚠️ No se detectó columna 'Año' en temperatura. Revisar CSV.")
        dfs.append(t)
    except Exception as e:
        st.warning(f"⚠️ Temperatura: {e}")
        dfs.append(pd.DataFrame(columns=["Año", "Temp_anom_C"]))

    # 2) GEI (NOAA-like). Buscamos fila de cabecera y leemos desde ahí.
    def _load_gas(path, out_col):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            start = 0
            for i, ln in enumerate(lines):
                low = ln.replace("\t", ",").lower()
                if "year" in low and ("average" in low or "trend" in low or "decimal" in low):
                    start = i
                    break
            df = _safe_read_csv(path, skiprows=start)
            df.columns = [c.strip().lower() for c in df.columns]
            if "year" not in df.columns:
                # plan B: usar engine python con separadores raros
                df = _safe_read_csv(path, skiprows=start, engine="python")
                df.columns = [c.strip().lower() for c in df.columns]
            # preferimos 'average', si no 'trend'
            val_col = "average" if "average" in df.columns else ("trend" if "trend" in df.columns else None)
            if val_col is None:
                return pd.DataFrame(columns=["Año", out_col])
            df = df[["year", val_col]].dropna()
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
            df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
            df = df.rename(columns={"year": "Año", val_col: out_col})
            return df.dropna()
        except Exception as e:
            st.warning(f"⚠️ Error cargando {path}: {e}")
            return pd.DataFrame(columns=["Año", out_col])

    co2 = _load_gas("data/gases/greenhouse_gas_co2_global.csv", "CO2_ppm")
    ch4 = _load_gas("data/gases/greenhouse_gas_ch4_global.csv", "CH4_ppb")
    n2o = _load_gas("data/gases/greenhouse_gas_n2o_global.csv", "N2O_ppb")
    dfs += [co2, ch4, n2o]

    # 3) Nivel del mar (NOAA mensual → anual)
    try:
        sl = _safe_read_csv(
            "data/sea_level/sea_level_nasa.csv",
            skiprows=1, header=None, names=["Fecha", "Nivel_mm"]
        )
        if not sl.empty:
            sl = sl[sl["Nivel_mm"].between(-3000, 3000)]
            sl["Fecha"] = pd.to_datetime(sl["Fecha"], errors="coerce")
            sl["Año"] = sl["Fecha"].dt.year
            sl = sl.groupby("Año", as_index=False)["Nivel_mm"].mean()
            sl = sl.rename(columns={"Nivel_mm": "SeaLevel_mm"})
        dfs.append(sl[["Año", "SeaLevel_mm"]] if "Año" in sl.columns else pd.DataFrame(columns=["Año", "SeaLevel_mm"]))
    except Exception as e:
        st.warning(f"⚠️ Nivel del mar: {e}")
        dfs.append(pd.DataFrame(columns=["Año", "SeaLevel_mm"]))

    # 4) Hielo marino (anual)
    def _load_ice(path, out_col):
        try:
            d = _safe_read_csv(path)
            d.columns = d.columns.str.strip()
            if {"Year", "Month", "Extent"}.issubset(d.columns) or {"year", "month", "extent"}.issubset([c.lower() for c in d.columns]):
                d = _ensure_year_column(d)
                d = d.rename(columns={"Extent": out_col, "extent": out_col})
                d = d.groupby("Año", as_index=False)[out_col].mean()
                return d[["Año", out_col]]
            else:
                # si ya viene anual (Año, Extensión)
                d = _ensure_year_column(d)
                if "Año" in d.columns:
                    # intentamos detectar la col de extensión
                    candidates = [c for c in d.columns if c.lower() not in {"año", "year"}]
                    if candidates:
                        val = candidates[0]
                        return d.rename(columns={val: out_col})[["Año", out_col]]
            return pd.DataFrame(columns=["Año", out_col])
        except Exception:
            return pd.DataFrame(columns=["Año", out_col])

    ice_ar = _load_ice("data/hielo/arctic_sea_ice_extent.csv", "Arctic_ice_Mkm2")
    ice_an = _load_ice("data/hielo/antarctic_sea_ice_extent.csv", "Antarctic_ice_Mkm2")
    dfs += [ice_ar, ice_an]

    # 5) Energía mundial agregada por año
    try:
        ene = _safe_read_csv("data/energia/energy_consuption_by_source.csv")
        if not ene.empty:
            ene.columns = ene.columns.str.strip().str.lower()
            if "year" in ene.columns:
                ene = ene.rename(columns={"year": "Año"})
            ene = _ensure_year_column(ene)
            if "Año" in ene.columns:
                # nos quedamos con *_consumption + algunas claves
                keep = [c for c in ene.columns if c.endswith("_consumption")] + ["electricity_consumption", "renewables_consumption", "fossil_fuel_consumption", "Año"]
                keep = list(dict.fromkeys([c for c in keep if c in ene.columns]))
                ene = ene[keep].groupby("Año", as_index=False).sum(numeric_only=True)
                nice = {
                    "coal_consumption":"Coal_TWh",
                    "oil_consumption":"Oil_TWh",
                    "gas_consumption":"Gas_TWh",
                    "nuclear_consumption":"Nuclear_TWh",
                    "hydro_consumption":"Hydro_TWh",
                    "biofuel_consumption":"Biofuel_TWh",
                    "solar_consumption":"Solar_TWh",
                    "wind_consumption":"Wind_TWh",
                    "electricity_consumption":"Electricity_TWh",
                    "renewables_consumption":"Renewables_TWh",
                    "fossil_fuel_consumption":"Fossils_TWh",
                }
                ene = ene.rename(columns={k:v for k,v in nice.items() if k in ene.columns})
            else:
                ene = pd.DataFrame(columns=["Año"])
        else:
            ene = pd.DataFrame(columns=["Año"])
        dfs.append(ene)
    except Exception as e:
        st.warning(f"⚠️ Energía: {e}")
        dfs.append(pd.DataFrame(columns=["Año"]))

    # Merge maestro por año (solo con DFS que tengan 'Año')
    df = None
    for d in dfs:
        if not d.empty and "Año" in d.columns:
            df = d if df is None else pd.merge(df, d, on="Año", how="outer")
    if df is None or df.empty:
        df = pd.DataFrame(columns=["Año"])
    return df.sort_values("Año").reset_index(drop=True)

# -------------------------------------------------
# CARGA POR PAÍS (PIB, Población, Emisiones CO2)
# -------------------------------------------------
@st.cache_data
def load_country_sources():
    # PIB
    gdp = _safe_read_csv("data/socioeconomico/gdp_by_country.csv")
    gdp.columns = gdp.columns.str.strip().str.lower()
    rename_gdp = {}
    if "country name" in gdp.columns or "country" in gdp.columns:
        rename_gdp[ "country name" if "country name" in gdp.columns else "country" ] = "País"
    if "year" in gdp.columns: rename_gdp["year"] = "Año"
    if "value" in gdp.columns: rename_gdp["value"] = "PIB_USD"
    gdp = gdp.rename(columns=rename_gdp)
    gdp = gdp[[c for c in ["Año", "País", "PIB_USD"] if c in gdp.columns]].dropna()

    # Población
    pop = _safe_read_csv("data/socioeconomico/population_by_country.csv")
    pop.columns = pop.columns.str.strip().str.lower()
    rename_pop = {}
    if "country name" in pop.columns or "country" in pop.columns:
        rename_pop[ "country name" if "country name" in pop.columns else "country" ] = "País"
    if "year" in pop.columns: rename_pop["year"] = "Año"
    if "value" in pop.columns: rename_pop["value"] = "Población"
    pop = pop.rename(columns=rename_pop)
    pop = pop[[c for c in ["Año", "País", "Población"] if c in pop.columns]].dropna()

    # CO2 por país
    co2c = _safe_read_csv("data/socioeconomico/co2_emissions_by_country.csv")
    co2c.columns = co2c.columns.str.strip().str.lower()
    rename_c = {}
    if "country name" in co2c.columns or "country" in co2c.columns:
        rename_c[ "country name" if "country name" in co2c.columns else "country" ] = "País"
    if "year" in co2c.columns: rename_c["year"] = "Año"
    # el valor puede estar en "value" o "co2"
    if "value" in co2c.columns: rename_c["value"] = "CO2_Mt"
    if "co2" in co2c.columns:   rename_c["co2"]   = "CO2_Mt"
    co2c = co2c.rename(columns=rename_c)
    co2c = co2c[[c for c in ["Año", "País", "CO2_Mt"] if c in co2c.columns]].dropna()

    return gdp, pop, co2c

# =================================================
# TABS
# =================================================
tab1, tab2 = st.tabs(["🌐 Global", "🗺️ Por país"])

# ---------------- GLOBAL -------------------------
with tab1:
    st.subheader("🌐 Variables globales combinadas")

    global_df = load_global_sources()
    if "Año" not in global_df.columns or global_df.empty:
        st.error("No se pudieron cargar variables globales con columna 'Año'. Revisa los CSV.")
        st.stop()

    miny, maxy = int(global_df["Año"].min()), int(global_df["Año"].max())

    # Variables numéricas disponibles
    vars_disp = [c for c in global_df.columns if c != "Año" and pd.api.types.is_numeric_dtype(global_df[c])]
    defaults = [v for v in ["Temp_anom_C", "CO2_ppm", "SeaLevel_mm", "Fossils_TWh", "Renewables_TWh"] if v in vars_disp] or vars_disp[:4]

    cols = st.multiselect("Selecciona variables globales a combinar", options=vars_disp, default=defaults)
    rmin, rmax = st.slider("Rango de años", min_value=miny, max_value=maxy, value=(max(miny, 1980), maxy))
    tipo = st.selectbox("Tipo de gráfico", ["Serie normalizada", "Dispersión (dos variables)", "Matriz de correlación"])

    dfg = global_df[global_df["Año"].between(rmin, rmax)].copy()

    if cols and not dfg.empty:
        if tipo == "Serie normalizada":
            z = _zscore(dfg[cols])
            z["Año"] = dfg["Año"].values
            z = z.melt(id_vars="Año", var_name="Variable", value_name="Z")
            fig = px.line(z, x="Año", y="Z", color="Variable", markers=True,
                          labels={"Z": "Valor normalizado (z-score)"},
                          title="Evolución normalizada por variable")
            st.plotly_chart(fig, use_container_width=True)

        elif tipo == "Dispersión (dos variables)":
            if len(cols) < 2:
                st.info("Selecciona al menos **dos** variables.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    xvar = st.selectbox("Eje X", cols, index=0)
                with c2:
                    yvar = st.selectbox("Eje Y", cols, index=1)
                df2 = dfg.dropna(subset=[xvar, yvar]).copy()
                fig = px.scatter(df2, x=xvar, y=yvar, labels={xvar: xvar, yvar: yvar},
                                 title=f"Relación {yvar} vs {xvar}")
                # Línea de regresión sin statsmodels
                m, model = _lin_trend(df2["Año"], df2[yvar]) if xvar == "Año" else _lin_trend(df2[xvar], df2[yvar])
                if model is not None:
                    xx = np.linspace(df2[xvar].min(), df2[xvar].max(), 100)
                    yy = model.predict(xx.reshape(-1, 1))
                    fig.add_scatter(x=xx, y=yy, mode="lines", name="Tendencia", line=dict(dash="dash"))
                st.plotly_chart(fig, use_container_width=True)

        else:
            dfc = dfg[cols].dropna(how="all")
            if dfc.shape[1] < 2:
                st.info("Selecciona **al menos dos** variables.")
            else:
                corr = dfc.corr(numeric_only=True)
                fig = px.imshow(corr, text_auto=".2f", aspect="auto", title="Matriz de correlación (Pearson)")
                st.plotly_chart(fig, use_container_width=True)

        # Conclusiones automáticas (global)
        st.subheader("🧩 Conclusiones automáticas")
        concl = []
        if cols:
            m, _ = _lin_trend(dfg["Año"], dfg[cols[0]])
            if pd.notna(m):
                tend = "ascendente" if m > 0 else "descendente" if m < 0 else "estable"
                concl.append(f"• La tendencia de **{cols[0]}** es **{tend}** en {rmin}–{rmax}.")
        if len(cols) >= 2:
            cmat = dfg[cols].corr().abs()
            iu = np.triu_indices_from(cmat, k=1)
            if len(iu[0]) > 0:
                best = np.argmax(cmat.values[iu])
                i, j = iu[0][best], iu[1][best]
                v1, v2 = cmat.index[i], cmat.columns[j]
                concl.append(f"• La pareja más correlacionada es **{v1}–{v2}** (|r|={cmat.values[iu][best]:.2f}).")
        if cols:
            tmp = dfg.copy()
            tmp["Década"] = (tmp["Año"] // 10) * 10
            z = _zscore(tmp[cols]).abs().mean(axis=1)
            tmp["act"] = z
            dec = tmp.groupby("Década")["act"].mean().idxmax()
            concl.append(f"• La década con mayor variación relativa fue **{int(dec)}**.")
        if concl:
            st.success("\n\n".join(concl))
        else:
            st.info("Selecciona variables y rango válidos para generar conclusiones.")

    else:
        st.info("Configura variables y rango para visualizar resultados.")

# ---------------- POR PAÍS -----------------------
with tab2:
    st.subheader("🗺️ Indicadores por país")
    gdp, pop, co2c = load_country_sources()

    # universo de países
    paises = sorted(set(gdp.get("País", pd.Series(dtype=str))) |
                    set(pop.get("País", pd.Series(dtype=str))) |
                    set(co2c.get("País", pd.Series(dtype=str))))
    sel = st.multiselect("Selecciona países/regiones", paises, default=[p for p in ["Spain", "United States"] if p in paises])

    # rango de años disponible
    def _minmax_year(df):
        return (df["Año"].min(), df["Año"].max()) if "Año" in df.columns and not df.empty else (np.nan, np.nan)

    minc = [x for x in _minmax_year(gdp) + _minmax_year(pop) + _minmax_year(co2c) if pd.notna(x)]
    if not minc:
        st.warning("No hay datos por país para construir el rango de años.")
        st.stop()
    miny, maxy = int(np.nanmin(minc)), int(np.nanmax(minc))
    rmin, rmax = st.slider("Rango de años", min_value=miny, max_value=maxy, value=(max(miny, 1980), maxy))

    # métricas disponibles según los CSV cargados
    all_metrics = []
    if "PIB_USD" in gdp.columns: all_metrics.append("PIB_USD")
    if "Población" in pop.columns: all_metrics.append("Población")
    if "CO2_Mt" in co2c.columns: all_metrics.append("CO2_Mt")
    metrica = st.multiselect("Selecciona métricas", options=all_metrics, default=all_metrics)

    # construir panel por país (merge outer por año)
    panel = pd.DataFrame()
    for p in sel:
        d = pd.DataFrame({"Año": list(range(rmin, rmax + 1))})
        d["País"] = p
        if "PIB_USD" in metrica and "PIB_USD" in gdp.columns:
            d = d.merge(gdp[(gdp["País"] == p) & (gdp["Año"].between(rmin, rmax))][["Año", "PIB_USD"]],
                        on="Año", how="left")
        if "Población" in metrica and "Población" in pop.columns:
            d = d.merge(pop[(pop["País"] == p) & (pop["Año"].between(rmin, rmax))][["Año", "Población"]],
                        on="Año", how="left")
        if "CO2_Mt" in metrica and "CO2_Mt" in co2c.columns:
            d = d.merge(co2c[(co2c["País"] == p) & (co2c["Año"].between(rmin, rmax))][["Año", "CO2_Mt"]],
                        on="Año", how="left")
        panel = pd.concat([panel, d], ignore_index=True) if not panel.empty else d

    vista = st.selectbox("Vista", ["Serie (normalizada)", "Dispersión (dos métricas)", "Correlación (por países)"])

    if not panel.empty and metrica:
        if vista == "Serie (normalizada)":
            dfp = panel.dropna(subset=metrica, how="all").copy()
            # z-score por país
            z_list = []
            for p in sel:
                sub = dfp[dfp["País"] == p].copy()
                if sub.empty: 
                    continue
                Z = _zscore(sub[metrica])
                Z["Año"] = sub["Año"].values
                Z["País"] = p
                z_list.append(Z)
            if z_list:
                z = pd.concat(z_list, ignore_index=True)
                z = z.melt(id_vars=["Año", "País"], var_name="Variable", value_name="Z")
                fig = px.line(z, x="Año", y="Z", color="País", facet_row="Variable",
                              height=500 + 120*max(0, len(metrica)-1),
                              title="Series normalizadas por país y métrica")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos suficientes para normalizar.")

        elif vista == "Dispersión (dos métricas)":
            if len(metrica) < 2:
                st.info("Selecciona al menos **dos** métricas.")
            else:
                xvar = st.selectbox("Eje X", metrica, index=0, key="xc")
                yvar = st.selectbox("Eje Y", metrica, index=1, key="yc")
                df2 = panel.dropna(subset=[xvar, yvar])
                fig = px.scatter(df2, x=xvar, y=yvar, color="País", hover_data=["Año"],
                                 title=f"{yvar} vs {xvar}")
                # tendencia global (todas las observaciones)
                m, model = _lin_trend(df2[xvar], df2[yvar])
                if model is not None:
                    xx = np.linspace(df2[xvar].min(), df2[xvar].max(), 100)
                    yy = model.predict(xx.reshape(-1, 1))
                    fig.add_scatter(x=xx, y=yy, mode="lines", name="Tendencia", line=dict(dash="dash"))
                st.plotly_chart(fig, use_container_width=True)

        else:  # correlación por países
            try:
                tabla = panel.groupby("País")[metrica].corr().reset_index().rename(columns={"level_1": "Variable2", 0: "r"})
                st.dataframe(tabla)
            except Exception:
                st.info("No se pudo calcular la correlación con los datos actuales.")

        # Conclusiones automáticas
        st.subheader("🧩 Conclusiones automáticas")
        outs = []
        for p in sel:
            sub = panel[panel["País"] == p]
            if sub.empty or not metrica:
                continue
            base = metrica[0]
            m, _ = _lin_trend(sub["Año"], sub[base])
            if pd.notna(m):
                tend = "creciente" if m > 0 else "decreciente" if m < 0 else "estable"
                outs.append(f"• **{p}**: {base} {tend} (pendiente media {m:,.0f} por año).")
        if outs:
            st.success("\n\n".join(outs))
        else:
            st.info("Selecciona países y métricas con datos válidos.")

    else:
        st.info("Configura países/métricas para visualizar resultados.")

# ------------------------------------------
# DESCARGAS SEGURAS (auto-detector de DataFrame)
# ------------------------------------------
st.subheader("💾 Exportar datos y gráficos")

col1, col2 = st.columns(2)

# Detecta automáticamente el DataFrame usado en la página
df_export = None
for var_name in ["df_f", "df_filtrado", "df", "df_fuentes", "df_resultado", "df_final"]:
    if var_name in locals():
        df_export = locals()[var_name]
        break

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
        from io import BytesIO
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
