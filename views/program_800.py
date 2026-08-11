import altair as alt
import pandas as pd
import streamlit as st


def render_program_800_view(
    df_view: pd.DataFrame,
    limit_rows: int,
    format_latest_period,
) -> None:
    st.subheader("Program 800+ (od 2024)")
    df_800 = df_view[df_view["date"] >= pd.Timestamp("2024-01-01")].copy()
    if df_800.empty:
        st.info("Brak danych od 2024 roku w obecnym zbiorze.")
        return

    latest_800 = df_800.iloc[-1]
    k1, k2, k3 = st.columns(3)
    k1.metric("Najnowszy okres", format_latest_period(latest_800["date"]))
    k2.metric("Dług publiczny na Polaka (KPLN)", f"{latest_800['public_debt_per_pole_pln']:.2f}")
    k3.metric("Dług EDP na Polaka (KPLN)", f"{latest_800['edp_debt_per_pole_pln']:.2f}")

    chart_800 = df_800[["date", "public_debt_per_pole_pln", "edp_debt_per_pole_pln"]].melt(
        id_vars="date",
        var_name="series",
        value_name="value",
    )
    chart_800["series"] = chart_800["series"].replace(
        {
            "public_debt_per_pole_pln": "Dług publiczny na Polaka",
            "edp_debt_per_pole_pln": "Dług EDP na Polaka",
        }
    )

    line_800 = alt.Chart(chart_800).mark_line().encode(
        x=alt.X("date:T", title="Data"),
        y=alt.Y("value:Q", title="KPLN"),
        color=alt.Color("series:N", title="Seria"),
        tooltip=[
            alt.Tooltip("date:T", title="Data"),
            alt.Tooltip("series:N", title="Seria"),
            alt.Tooltip("value:Q", title="Wartość", format=".2f"),
        ],
    )

    plus_500_df = pd.DataFrame({"date": [pd.Timestamp("2016-04-01")], "label": ["Start 500+"]})
    plus_800_df = pd.DataFrame({"date": [pd.Timestamp("2024-01-01")], "label": ["Start 800+"]})
    marker_500 = alt.Chart(plus_500_df).mark_rule(color="green", strokeDash=[8, 6]).encode(x="date:T")
    marker_500_label = alt.Chart(plus_500_df).mark_text(align="left", dx=6, dy=10, color="green").encode(
        x="date:T",
        y=alt.value(18),
        text="label:N",
    )
    marker_800 = alt.Chart(plus_800_df).mark_rule(color="blue", strokeDash=[8, 6]).encode(x="date:T")
    marker_800_label = alt.Chart(plus_800_df).mark_text(align="left", dx=6, dy=26, color="blue").encode(
        x="date:T",
        y=alt.value(18),
        text="label:N",
    )

    st.altair_chart((line_800 + marker_500 + marker_500_label + marker_800 + marker_800_label).interactive(), use_container_width=True)

    table_800 = df_800[
        [
            "date",
            "public_debt_per_pole_pln",
            "edp_debt_per_pole_pln",
            "public_debt_per_worker_pln",
            "edp_debt_per_worker_pln",
        ]
    ].tail(limit_rows)
    table_800 = table_800.rename(
        columns={
            "date": "Data",
            "public_debt_per_pole_pln": "Dług publiczny na Polaka (KPLN)",
            "edp_debt_per_pole_pln": "Dług EDP na Polaka (KPLN)",
            "public_debt_per_worker_pln": "Dług publiczny na osobę pracującą (KPLN)",
            "edp_debt_per_worker_pln": "Dług EDP na osobę pracującą (KPLN)",
        }
    )
    st.dataframe(table_800, use_container_width=True)
