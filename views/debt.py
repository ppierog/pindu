import altair as alt
import pandas as pd
import streamlit as st


def render_debt_view(
    df_view: pd.DataFrame,
    series_label: str,
    series_selection: str | list[str],
    series_legend_labels: dict[str, str],
    limit_rows: int,
    format_latest_period,
) -> None:
    latest = df_view.iloc[-1]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Najnowszy okres", format_latest_period(latest["date"]))
    c2.metric("Dług publiczny (mld PLN)", f"{latest['public_debt_pln_bn']:.1f}")
    c3.metric("Dług publiczny (% PKB)", f"{latest['public_debt_pct_gdp']:.1f}")
    c4.metric("Dług EDP (mld PLN)", f"{latest['edp_debt_pln_bn']:.1f}")
    c5.metric("Dług EDP (% PKB)", f"{latest['edp_debt_pct_gdp']:.1f}")

    period_start = df_view["date"].iloc[0].year
    period_end = df_view["date"].iloc[-1].year
    if period_end >= pd.Timestamp.today().year:
        period_label = f"od {period_start}"
    else:
        period_label = f"{period_start}-{period_end}"
    st.subheader(f"{series_label} ({period_label})")

    x_domain = [df_view["date"].min(), df_view["date"].max()]
    x_axis = alt.Axis(format="%Y", tickCount="year")
    x_scale = alt.Scale(domain=x_domain, clamp=True)

    if isinstance(series_selection, list):
        chart_df = df_view[["date", *series_selection]].copy()
        chart_long = chart_df.melt(id_vars="date", var_name="series", value_name="value")
        chart_long["series"] = chart_long["series"].replace(series_legend_labels)

        line = alt.Chart(chart_long).mark_line().encode(
            x=alt.X("date:T", title="Data", axis=x_axis, scale=x_scale),
            y=alt.Y("value:Q", title=series_label),
            color=alt.Color("series:N", title="Seria"),
            tooltip=[
                alt.Tooltip("date:T", title="Data"),
                alt.Tooltip("series:N", title="Seria"),
                alt.Tooltip("value:Q", title="Wartość", format=".2f"),
            ],
        )
        ofe_start = pd.Timestamp("2014-02-03")
        ofe_df = pd.DataFrame({"date": [ofe_start], "label": ["Reforma OFE"]})
        marker_ofe = alt.Chart(ofe_df).mark_rule(color="purple", strokeDash=[8, 6]).encode(x="date:T")
        marker_ofe_label = alt.Chart(ofe_df).mark_text(align="left", dx=6, dy=-8, color="purple").encode(
            x="date:T",
            y=alt.value(18),
            text="label:N",
        )

        plus_500_start = pd.Timestamp("2016-04-01")
        plus_500_df = pd.DataFrame({"date": [plus_500_start], "label": ["Start 500+"]})
        marker_500 = alt.Chart(plus_500_df).mark_rule(color="green", strokeDash=[8, 6]).encode(x="date:T")
        marker_500_label = alt.Chart(plus_500_df).mark_text(align="left", dx=6, dy=10, color="green").encode(
            x="date:T",
            y=alt.value(18),
            text="label:N",
        )

        plus_800_start = pd.Timestamp("2024-01-01")
        plus_800_df = pd.DataFrame({"date": [plus_800_start], "label": ["Start 800+"]})
        marker_800 = alt.Chart(plus_800_df).mark_rule(color="blue", strokeDash=[8, 6]).encode(x="date:T")
        marker_800_label = alt.Chart(plus_800_df).mark_text(align="left", dx=6, dy=26, color="blue").encode(
            x="date:T",
            y=alt.value(18),
            text="label:N",
        )

        st.altair_chart(
            (line + marker_ofe + marker_ofe_label + marker_500 + marker_500_label + marker_800 + marker_800_label).interactive(),
            use_container_width=True,
        )
    else:
        chart_df = df_view[["date", series_selection]].copy()
        line = alt.Chart(chart_df).mark_line().encode(
            x=alt.X("date:T", title="Data", axis=x_axis, scale=x_scale),
            y=alt.Y(f"{series_selection}:Q", title=series_label),
            tooltip=[
                alt.Tooltip("date:T", title="Data"),
                alt.Tooltip(f"{series_selection}:Q", title=series_label, format=".2f"),
            ],
        )

        if series_selection in {"edp_to_public_diff", "public_to_edp_ratio"}:
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
