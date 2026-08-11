import streamlit as st

from app_data import (
    SERIES_LEGEND_LABELS,
    SERIES_OPTIONS,
    build_view_data,
    format_latest_period,
    load_public_debt_data,
)
from views.debt import render_debt_view


st.set_page_config(page_title="Dług polski", page_icon="📊", layout="wide")
st.title("Dług publiczny Polski")
st.write("Widok analizy długu publicznego i EDP od 2006 roku.")

with st.sidebar:
    st.header("Parametry")
    population_mln = st.number_input(
        "Liczba ludności Polski (mln)",
        min_value=30.0,
        max_value=45.0,
        value=38.0,
        step=0.1,
    )
    workers_mln = st.number_input(
        "Liczba osób pracujących (mln)",
        min_value=10.0,
        max_value=25.0,
        value=17.5,
        step=0.1,
    )
    series_label = st.selectbox("Seria", options=list(SERIES_OPTIONS.keys()))
    limit_rows = st.slider("Liczba wierszy", min_value=10, max_value=120, value=30, step=10)
    if st.button("Odśwież dane"):
        st.cache_data.clear()
        st.rerun()

try:
    df = load_public_debt_data()
except Exception as exc:
    st.error(f"Nie udało się pobrać danych z API: {exc}")
    st.stop()

df_view = build_view_data(df=df, population_mln=population_mln, workers_mln=workers_mln)
if df_view.empty:
    st.warning("Brak danych od 2006 roku.")
    st.stop()

series_selection = SERIES_OPTIONS[series_label]
render_debt_view(
    df_view=df_view,
    series_label=series_label,
    series_selection=series_selection,
    series_legend_labels=SERIES_LEGEND_LABELS,
    limit_rows=limit_rows,
    format_latest_period=format_latest_period,
)

st.caption("Źródło: https://dane.gov.pl/pl/dataset/849,dug-publiczny")
