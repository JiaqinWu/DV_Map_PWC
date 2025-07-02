import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(layout="wide")
st.markdown(
    "<h1 style='text-align: center;'>DV Map -- Prince William County</h1>",
    unsafe_allow_html=True
)
st.markdown("") 

df = pd.read_csv("dv_intercepts_cleaned.csv")

intercepts_labels = {
    "0": "Community Services",
    "1": "Law Enforcement",
    "2": "Detention & Hearings",
    "3": "Jails/Courts",
    "4": "Reentry",
    "5": "Comm Corrections"
}
ordered_intercepts = [intercepts_labels[k] for k in sorted(intercepts_labels.keys())]

df["Intercept"] = df["Intercept"].astype(str).str.split(",")
df = df.explode("Intercept")
df["Intercept"] = df["Intercept"].str.strip()
df["Intercept Label"] = df["Intercept"].map(intercepts_labels)

all_providers = sorted(df["Provider(s)"].dropna().unique())

full_matrix = pd.MultiIndex.from_product(
    [all_providers, ordered_intercepts],
    names=["Provider(s)", "Intercept Label"]
).to_frame(index=False)

df["assigned"] = 1
merged = pd.merge(full_matrix, df[["Provider(s)", "Intercept Label", "assigned"]],
                  on=["Provider(s)", "Intercept Label"], how="left")
merged["assigned"] = merged["assigned"].fillna(0)

merged["Provider(s)"] = pd.Categorical(merged["Provider(s)"], categories=all_providers, ordered=True)
merged["Intercept Label"] = pd.Categorical(merged["Intercept Label"], categories=ordered_intercepts, ordered=True)

base = alt.Chart(merged).mark_rect().encode(
    x=alt.X(
        "Intercept Label:N",
        sort=[
            "Community Services", "Law Enforcement", "Detention & Hearings",
            "Jails/Courts", "Reentry", "Comm Corrections"
        ],
        title='',
        axis=alt.Axis(labelAngle=0, labelFontSize=12, labelLimit=350, labelPadding=10)
    ),
    y=alt.Y("Provider(s):N", title=''),
    color=alt.value("#eeeeee") 
)

highlight = alt.Chart(merged[merged["assigned"] == 1]).mark_rect().encode(
    x=alt.X(
        "Intercept Label:N",
        sort=[
            "Community Services", "Law Enforcement", "Detention & Hearings",
            "Jails/Courts", "Reentry", "Comm Corrections"
        ],
        title='',
        axis=alt.Axis(labelAngle=0, labelFontSize=12, labelLimit=350, labelPadding=10)
    ),
    y=alt.Y("Provider(s):N"),
    color=alt.Color(
        "Intercept Label:N",
        scale=alt.Scale(scheme='tableau10'),
        sort=[
            "Community Services", "Law Enforcement", "Detention & Hearings",
            "Jails/Courts", "Reentry", "Comm Corrections"
        ],
        legend=None
    ),
    tooltip=["Provider(s):N", "Intercept Label:N"]
)

chart = (base + highlight).properties(
    width=800,
    height=28 * len(all_providers)
).configure_axis(
    labelFontSize=12,
    titleFontSize=12,
    labelLimit=350
).configure_view(
    strokeWidth=0
)

st.altair_chart(chart, use_container_width=True)