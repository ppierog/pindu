import json
from urllib.request import urlopen

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
    "Dług publiczny DP (mld PLN)": "public_debt_pln_bn",
    "Europejski dług publiczny EDP (mld PLN)": "edp_debt_pln_bn",
    "Dług DP (% PKB)": "public_debt_pct_gdp",
    "Dług EDP (% PKB)": "edp_debt_pct_gdp",
    "Różnica EDP do DP (mld PLN)": "edp_to_public_diff",
    "Stosunek Różnicy do EDP (%)": "public_to_edp_ratio",
    "Ilość długu: Polak vs osoba pracująca (KPLN)": [
        "public_debt_per_pole_pln",
        "public_debt_per_worker_pln",
    ],
    "Ilość EDP: Polak vs osoba pracująca (KPLN)": [
        "edp_debt_per_pole_pln",
        "edp_debt_per_worker_pln",
    ],
}

SERIES_LEGEND_LABELS = {
    "public_debt_per_pole_pln": "Dług na Polaka",
    "public_debt_per_worker_pln": "Dług na osobę pracującą",
    "edp_debt_per_pole_pln": "EDP na Polaka",
    "edp_debt_per_worker_pln": "EDP na osobę pracującą",
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


def build_view_data(df: pd.DataFrame, population_mln: float, workers_mln: float) -> pd.DataFrame:
    df_view = df[df["date"] >= pd.Timestamp("2006-01-01")].copy()
    if df_view.empty:
        return df_view

    df_view["edp_to_public_diff"] = df_view["edp_debt_pln_bn"] - df_view["public_debt_pln_bn"]
    df_view["public_to_edp_ratio"] = 100 * (df_view["edp_debt_pln_bn"] - df_view["public_debt_pln_bn"]) / df_view["edp_debt_pln_bn"]
    df_view["public_debt_per_pole_pln"] = df_view["public_debt_pln_bn"] / population_mln
    df_view["edp_debt_per_pole_pln"] = df_view["edp_debt_pln_bn"] / population_mln
    df_view["public_debt_per_worker_pln"] = df_view["public_debt_pln_bn"] / workers_mln
    df_view["edp_debt_per_worker_pln"] = df_view["edp_debt_pln_bn"] / workers_mln
    return df_view
