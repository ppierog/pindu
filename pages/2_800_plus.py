import json
from urllib.request import Request, urlopen

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Program 800+", page_icon="👨‍👩‍👧‍👦", layout="wide")
st.title("Program 800+")
st.write("Kalkulator skumulowanej kwoty świadczenia 800+ w zależności od wieku dziecka.")

AMOUNT_PER_MONTH = 800
MAX_AGE_YEARS = 18
MAX_MONTHS = MAX_AGE_YEARS * 12
STOOQ_10Y_URL = "https://stooq.pl/q/d/l/?s=10yply.b&i=d"
WGB_COUNTRY_URL = "https://www.worldgovernmentbonds.com/country/poland/"
WGB_MAIN_API_URL = "https://www.worldgovernmentbonds.com/wp-json/country/v1/main"


def _parse_float(value: str) -> float:
    return float(value.strip().replace(" ", "").replace(",", "."))


@st.cache_data(ttl=3600, show_spinner=False)
def load_latest_10y_yield() -> tuple[float, str]:
    post_body = {
        "GLOBALVAR": {
            "JS_VARIABLE": "jsGlobalVars",
            "FUNCTION": "Country",
            "DOMESTIC": True,
            "ENDPOINT": "https://www.worldgovernmentbonds.com/wp-json/country/v1/historical",
            "DATE_RIF": "2099-12-31",
            "OBJ": None,
            "COUNTRY1": {
                "SYMBOL": "20",
                "PAESE": "Poland",
                "PAESE_UPPERCASE": "POLAND",
                "BANDIERA": "pl",
                "URL_PAGE": "poland",
            },
            "COUNTRY2": None,
            "OBJ1": None,
            "OBJ2": None,
        }
    }
    payload = json.dumps(post_body).encode("utf-8")
    req = Request(
        WGB_MAIN_API_URL,
        data=payload,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Content-Type": "application/json",
            "Origin": "https://www.worldgovernmentbonds.com",
            "Referer": WGB_COUNTRY_URL,
        },
        method="POST",
    )
    with urlopen(req, timeout=15) as response:
        raw = response.read().decode("utf-8", errors="ignore")

    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("success") is not True:
        raise RuntimeError("WorldGovernmentBonds zwrócił niepoprawną odpowiedź.")

    bond_10y = data.get("bond10y")
    date_value = data.get("lastDataValDesc") or data.get("lastTimeValDesc")
    if bond_10y is None or date_value is None:
        raise RuntimeError("Brak wartości rentowności 10Y lub daty rekordu.")

    return _parse_float(str(bond_10y)), str(date_value)


stooq_rate = None
stooq_date = None
stooq_error = None
try:
    stooq_rate, stooq_date = load_latest_10y_yield()
except Exception as exc:  # noqa: BLE001
    stooq_error = str(exc)

default_interest = 8.0
if stooq_rate is not None:
    default_interest = min(max(round(stooq_rate, 1), 0.0), 30.0)

with st.sidebar:
    st.header("Dane wejściowe")
    age_years = st.slider("Wiek dziecka (lata)", min_value=0, max_value=17, value=5)
    age_months = st.slider("Miesiące", min_value=0, max_value=11, value=0)
    st.header("Parametry kredytu")
    annual_interest_pct = st.slider(
        "Oprocentowanie roczne (%)",
        min_value=0.0,
        max_value=30.0,
        value=default_interest,
        step=0.1,
    )
    installments = st.slider("Liczba rat (miesięcy)", min_value=6, max_value=360, value=120, step=6)

months_elapsed = age_years * 12 + age_months
months_remaining = max(MAX_MONTHS - months_elapsed, 0)

paid_so_far = months_elapsed * AMOUNT_PER_MONTH
remaining_to_18 = months_remaining * AMOUNT_PER_MONTH
total_until_18 = MAX_MONTHS * AMOUNT_PER_MONTH

st.subheader("Aktualny wiek dziecka")
age_c1, age_c2 = st.columns(2)
age_c1.metric("Wiek (lata)", f"{age_years}")
age_c2.metric("Miesiące", f"{age_months}")

c1, c2, c3 = st.columns(3)
c1.metric("Wypłacone skumulowanie do dziś", f"{paid_so_far:,.0f} zł")
c2.metric("Pozostało do 18 lat", f"{remaining_to_18:,.0f} zł")
c3.metric("Maksymalnie do 18 lat", f"{total_until_18:,.0f} zł")

st.subheader("Rozkład świadczenia 800+")
st.caption(f"Aktualny podział dla wieku: {age_years} lat i {age_months} mies.")
benefit_df = pd.DataFrame(
    [
        {"Pozycja": "Wypłacone do dziś", "Kwota": paid_so_far},
        {"Pozycja": "Pozostało do 18 lat", "Kwota": remaining_to_18},
    ]
)
benefit_bar_base = alt.Chart(benefit_df).encode(
    x=alt.X("Pozycja:N", title="Składnik"),
    y=alt.Y("Kwota:Q", title="Kwota (zł)", scale=alt.Scale(domain=[0, total_until_18])),
    color=alt.Color("Pozycja:N", legend=None),
    tooltip=[alt.Tooltip("Pozycja:N", title="Pozycja"), alt.Tooltip("Kwota:Q", title="Kwota", format=",.0f")],
)
benefit_bar_chart = benefit_bar_base.mark_bar()
benefit_labels = benefit_bar_base.mark_text(dy=-8, color="black").encode(text=alt.Text("Kwota:Q", format=",.0f"))

benefit_pie_chart = alt.Chart(benefit_df).mark_arc(innerRadius=45).encode(
    theta=alt.Theta("Kwota:Q"),
    color=alt.Color("Pozycja:N", title="Udział"),
    tooltip=[alt.Tooltip("Pozycja:N", title="Pozycja"), alt.Tooltip("Kwota:Q", title="Kwota", format=",.0f")],
)

col_benefit_bar, col_benefit_pie = st.columns(2)
benefit_key = f"benefit_{age_years}_{age_months}_{months_elapsed}"
with col_benefit_bar:
    st.altair_chart((benefit_bar_chart + benefit_labels), use_container_width=True, key=f"{benefit_key}_bar")
with col_benefit_pie:
    st.altair_chart(benefit_pie_chart, use_container_width=True, key=f"{benefit_key}_pie")

principal = float(total_until_18)
monthly_rate = annual_interest_pct / 12 / 100
if installments > 0 and principal > 0:
    if monthly_rate == 0:
        monthly_payment = principal / installments
    else:
        monthly_payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** (-installments))
else:
    monthly_payment = 0.0

total_repayment = monthly_payment * installments
total_interest = total_repayment - principal

st.subheader("Symulacja spłaty pełnej kwoty skumulowanej jako kredytu")
st.caption("Ta sekcja zawsze liczy kredyt od pełnej kwoty 800+ do 18 lat, niezależnie od wieku dziecka.")
if stooq_rate is not None:
    source_c1, source_c2 = st.columns(2)
    source_c1.metric("Aktualna rentowność 10Y", f"{stooq_rate:.2f}%")
    source_c2.metric("Użyte oprocentowanie", f"{annual_interest_pct:.2f}%")
    st.caption(f"Źródło: {WGB_COUNTRY_URL} | Data rekordu: {stooq_date}")
else:
    st.warning("Nie pobrano aktualnej rentowności 10Y. Użyto domyślnie 8.0%.")
    st.caption(f"Źródło: {WGB_COUNTRY_URL} | Powód: {stooq_error}")

k1, k2, k3 = st.columns(3)
k1.metric("Rata miesięczna", f"{monthly_payment:,.2f} zł")
k2.metric("Łącznie do oddania", f"{total_repayment:,.2f} zł")
k3.metric("Koszt odsetek", f"{total_interest:,.2f} zł")

st.subheader("Porównanie wartości")
loan_df = pd.DataFrame(
    [
        {"Pozycja": "Kapitał", "Kwota": principal},
        {"Pozycja": "Odsetki", "Kwota": total_interest},
        {"Pozycja": "Do oddania", "Kwota": total_repayment},
    ]
)
bar_chart = alt.Chart(loan_df).mark_bar().encode(
    x=alt.X("Pozycja:N", title="Składnik"),
    y=alt.Y("Kwota:Q", title="Kwota (zł)"),
    color=alt.Color("Pozycja:N", legend=None),
    tooltip=[alt.Tooltip("Pozycja:N", title="Pozycja"), alt.Tooltip("Kwota:Q", title="Kwota", format=",.2f")],
)

loan_pie_df = pd.DataFrame(
    [
        {"Pozycja": "Kapitał", "Kwota": principal},
        {"Pozycja": "Odsetki", "Kwota": total_interest},
    ]
)
pie_chart = alt.Chart(loan_pie_df).mark_arc(innerRadius=45).encode(
    theta=alt.Theta("Kwota:Q"),
    color=alt.Color("Pozycja:N", title="Udział"),
    tooltip=[alt.Tooltip("Pozycja:N", title="Pozycja"), alt.Tooltip("Kwota:Q", title="Kwota", format=",.2f")],
)

col_bar, col_pie = st.columns(2)
loan_key = f"loan_{age_years}_{age_months}_{annual_interest_pct}_{installments}_{int(principal)}"
with col_bar:
    st.altair_chart(bar_chart, use_container_width=True, key=f"{loan_key}_bar")
with col_pie:
    st.altair_chart(pie_chart, use_container_width=True, key=f"{loan_key}_pie")

st.info(
    "Założenie kalkulatora: 800 zł miesięcznie przez cały okres od urodzenia do 18 roku życia. "
    "To uproszczenie matematyczne do szybkiego oszacowania kwoty skumulowanej. "
    "Część kredytowa używa rat równych (annuitetowych) od pełnej kwoty skumulowanej do 18 lat."
)
