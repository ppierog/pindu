import json
from urllib.request import urlopen

import altair as alt
import pandas as pd
import streamlit as st


API_URL = "https://api.dane.gov.pl/1.4/resources/2062954,dug-publiczny/data?page={page}"

COLUMN_MAP = {
    "col1": "date",
    "col2": "edp_debt_pln_bn",
    "col3": "deposits",
    "col4": "short_term_debt_securities",
    "col5": "long_term_debt_securities",
    "col6": "short_term_loans",
    "col7": "long_term_loans",
    "col8": "edp_debt_central_gov",
    "col9": "edp_debt_local_gov",
    "col10": "edp_debt_social_security",
    "col11": "edp_debt_pct_gdp",
    "col12": "public_debt_pln_bn",
    "col13": "public_debt_pct_gdp",
}

SERIES_OPTIONS = {
    "Dług publiczny (mld PLN)": "public_debt_pln_bn",
    "Europejski dług publiczny EDP (mld PLN)": "edp_debt_pln_bn",
    "Dług (% PKB)": "public_debt_pct_gdp",
    "Dług EDP (% PKB)": "edp_debt_pct_gdp",
    "Różnica EDP do Długu": "edp_to_public_diff",
    "Stosunek Różnicy Długu do EDP": "public_to_edp_ratio",
    "Ilość długu na Polaka (PLN)": "public_debt_per_pole_pln",
    "Ilość EDP na Polaka (PLN)": "edp_debt_per_pole_pln",
}


@st.cache_data(ttl=3600)
def load_public_debt_data() -> pd.DataFrame:
    page = 1
    rows: list[dict[str, float | str]] = []

    while True:
        with urlopen(API_URL.format(page=page), timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        for item in payload.get("data", []):
            attributes = item.get("attributes", {})
            row = {col: cell.get("val") for col, cell in attributes.items()}
            rows.append(row)

        if not payload.get("links", {}).get("next"):
            break
        page += 1

    df = pd.DataFrame(rows).rename(columns=COLUMN_MAP)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def format_latest_period(value: pd.Timestamp) -> str:
    if pd.isna(value):
        return "n/a"
    return value.strftime("%Y-%m-%d")


def main() -> None:
    st.set_page_config(page_title="Poland Public Debt", page_icon="📊", layout="wide")

    st.title("Dług publiczny Polski - dane.gov.pl")
    st.write(
        "Kwartalne dane z oficjalnego zbioru dane.gov.pl, zobacz https://dane.gov.pl/pl/dataset/849,dug-publiczny"
    )

    with st.sidebar:
        st.header("Dług publiczny Polski")
        population_mln = st.number_input(
            "Liczba ludności Polski (mln)",
            min_value=30.0,
            max_value=45.0,
            value=38.0,
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

    df_view = df[df["date"] >= pd.Timestamp("2006-01-01")].copy()
    if df_view.empty:
        st.warning("Brak danych od 2006 roku.")
        st.stop()

    # Positive value means EDP debt is higher than public debt in PLN bn.
    df_view["edp_to_public_diff"] = df_view["edp_debt_pln_bn"] - df_view["public_debt_pln_bn"]
    # Ratio expressed as a multiplier, e.g. 0.98 means 98%.
    df_view["public_to_edp_ratio"] = (df_view["edp_debt_pln_bn"] - df_view["public_debt_pln_bn"]) / df_view["edp_debt_pln_bn"]
    # PLN per person: (mld PLN * 1e9) / (mln people * 1e6) = value * 1000 / population_mln.
    df_view["public_debt_per_pole_pln"] = df_view["public_debt_pln_bn"] * 1000 / population_mln
    df_view["edp_debt_per_pole_pln"] = df_view["edp_debt_pln_bn"] * 1000 / population_mln

    series_column = SERIES_OPTIONS[series_label]
    latest = df_view.iloc[-1]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Najnowszy okres", format_latest_period(latest["date"]))
    c2.metric("Dług publiczny (mld PLN)", f"{latest['public_debt_pln_bn']:.1f}")
    c3.metric("Dług publiczny (% PKB)", f"{latest['public_debt_pct_gdp']:.1f}")
    c4.metric("Dług EDP (mld PLN)", f"{latest['edp_debt_pln_bn']:.1f}")
    c5.metric("Dług EDP (% PKB)", f"{latest['edp_debt_pct_gdp']:.1f}")

    st.subheader(f"{series_label} (od 2006)")
    chart_df = df_view[["date", series_column]].copy()

    line = alt.Chart(chart_df).mark_line().encode(
        x=alt.X("date:T", title="Data"),
        y=alt.Y(f"{series_column}:Q", title=series_label),
        tooltip=[alt.Tooltip("date:T", title="Data"), alt.Tooltip(f"{series_column}:Q", title=series_label, format=".2f")],
    )

    if series_column in {"edp_to_public_diff", "public_to_edp_ratio"}:
        covid_start = pd.Timestamp("2020-03-04")
        covid_df = pd.DataFrame({"date": [covid_start], "label": ["Start COVID-19 w Polsce"]})
        marker = alt.Chart(covid_df).mark_rule(color="red", strokeDash=[8, 6]).encode(x="date:T")
        marker_label = alt.Chart(covid_df).mark_text(align="left", dx=6, dy=-8, color="red").encode(
            x="date:T",
            y=alt.value(18),
            text="label:N",
        )
        st.altair_chart((line + marker + marker_label).interactive(), use_container_width=True)
    else:
        st.altair_chart(line.interactive(), use_container_width=True)

    st.subheader("Najnowsze rekordy")
    view_cols = ["date", "edp_debt_pln_bn", "public_debt_pln_bn", "edp_debt_pct_gdp", "public_debt_pct_gdp"]
    table_labels = {
        "date": "Data",
        "edp_debt_pln_bn": "Dług EDP (mld PLN)",
        "public_debt_pln_bn": "Dług publiczny (mld PLN)",
        "edp_debt_pct_gdp": "Dług EDP (% PKB)",
        "public_debt_pct_gdp": "Dług publiczny (% PKB)",
    }
    table_df = df_view[view_cols].tail(limit_rows).rename(columns=table_labels)
    st.dataframe(table_df, use_container_width=True)

    st.caption("Źródło: https://dane.gov.pl/pl/dataset/849,dug-publiczny")


if __name__ == "__main__":
    main()
