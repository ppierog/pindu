import time

import pandas as pd
import streamlit as st

from app_data import (
    build_view_data,
    format_latest_period,
    load_public_debt_data,
)


SECONDS_PER_DAY = 86_400
TICK_SECONDS = 0.2

st.set_page_config(page_title="Aktualny dług polski", page_icon="💰", layout="wide")
st.title("Aktualny Dług Polski")
st.write("Szacunkowy, rosnący licznik długu publicznego na podstawie ostatnich danych kwartalnych.")

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
    rice_price_per_kg = st.number_input(
        "Cena ryżu (zł/kg)",
        min_value=1.0,
        max_value=50.0,
        value=5.0,
        step=0.5,
    )
    rice_portion_grams = st.slider(
        "Wielkość porcji ryżu (g)",
        min_value=50,
        max_value=300,
        value=150,
        step=10,
    )

try:
    df = load_public_debt_data()
except Exception as exc:
    st.error(f"Nie udało się pobrać danych z API: {exc}")
    st.stop()

df_view = build_view_data(df=df, population_mln=population_mln, workers_mln=workers_mln)
if df_view.empty or len(df_view) < 2:
    st.warning("Za mało danych, aby oszacować tempo wzrostu długu.")
    st.stop()

latest = df_view.iloc[-1]
previous = df_view.iloc[-2]

days_between = max((latest["date"] - previous["date"]).days, 1)
public_growth_per_day_bn = (latest["public_debt_pln_bn"] - previous["public_debt_pln_bn"]) / days_between
edp_growth_per_day_bn = (latest["edp_debt_pln_bn"] - previous["edp_debt_pln_bn"]) / days_between

public_growth_per_second_pln = public_growth_per_day_bn * 1e9 / SECONDS_PER_DAY
edp_growth_per_second_pln = edp_growth_per_day_bn * 1e9 / SECONDS_PER_DAY

base_public_pln = latest["public_debt_pln_bn"] * 1e9
base_edp_pln = latest["edp_debt_pln_bn"] * 1e9
base_timestamp = pd.Timestamp(latest["date"]).timestamp()

population_count = population_mln * 1e6
workers_count = workers_mln * 1e6
rice_price_per_gram = rice_price_per_kg / 1000
rice_portion_price = rice_price_per_gram * rice_portion_grams

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ostatni okres danych", format_latest_period(latest["date"]))
c2.metric("Dług publiczny (mld PLN)", f"{latest['public_debt_pln_bn']:.1f}")
c3.metric("Dług EDP (mld PLN)", f"{latest['edp_debt_pln_bn']:.1f}")
c4.metric("Dług publiczny (% PKB)", f"{latest['public_debt_pct_gdp']:.1f}")

g1, g2 = st.columns(2)
g1.metric("Tempo wzrostu DP (PLN/s)", f"{public_growth_per_second_pln:,.0f}")
g2.metric("Tempo wzrostu EDP (PLN/s)", f"{edp_growth_per_second_pln:,.0f}")

st.caption(
    "Licznik poniżej to ekstrapolacja liniowa między dwoma ostatnimi okresami — "
    "nie jest to oficjalna wartość bieżąca."
)

ticker_placeholder = st.empty()

while True:
    elapsed_seconds = max(time.time() - base_timestamp, 0.0)
    current_public = base_public_pln + public_growth_per_second_pln * elapsed_seconds
    current_edp = base_edp_pln + edp_growth_per_second_pln * elapsed_seconds

    with ticker_placeholder.container():
        t1, t2 = st.columns(2)
        t1.metric(
            "Szacunkowy dług publiczny (PLN)",
            f"{current_public:,.0f} zł",
        )
        t2.metric(
            "Szacunkowy dług EDP (PLN)",
            f"{current_edp:,.0f} zł",
        )
        p1, p2, p3, p4 = st.columns(4)
        p1.metric(
            "Dług publiczny na Polaka (PLN)",
            f"{current_public / population_count:,.2f} zł",
        )
        p2.metric(
            "Dług publiczny na osobę pracującą (PLN)",
            f"{current_public / workers_count:,.2f} zł",
        )
        p3.metric(
            f"Dług publiczny na Polaka (miski ryżu, {rice_portion_grams} g)",
            f"{current_public / population_count / rice_portion_price:,.0f} 🍚",
        )
        p4.metric(
            f"Dług publiczny na osobę pracującą (miski ryżu, {rice_portion_grams} g)",
            f"{current_public / workers_count / rice_portion_price:,.0f} 🍚",
        )
        e1, e2, e3, e4 = st.columns(4)
        e1.metric(
            "Dług EDP na Polaka (PLN)",
            f"{current_edp / population_count:,.2f} zł",
        )
        e2.metric(
            "Dług EDP na osobę pracującą (PLN)",
            f"{current_edp / workers_count:,.2f} zł",
        )
        e3.metric(
            f"Dług EDP na Polaka (miski ryżu, {rice_portion_grams} g)",
            f"{current_edp / population_count / rice_portion_price:,.0f} 🍚",
        )
        e4.metric(
            f"Dług EDP na osobę pracującą (miski ryżu, {rice_portion_grams} g)",
            f"{current_edp / workers_count / rice_portion_price:,.0f} 🍚",
        )

    time.sleep(TICK_SECONDS)
