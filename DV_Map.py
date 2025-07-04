import streamlit as st
import pandas as pd
import altair as alt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import time
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
#creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
# Use Streamlit's secrets management
creds_dict = st.secrets["gcp_service_account"]
# Extract individual attributes needed for ServiceAccountCredentials
credentials = {
    "type": creds_dict.type,
    "project_id": creds_dict.project_id,
    "private_key_id": creds_dict.private_key_id,
    "private_key": creds_dict.private_key,
    "client_email": creds_dict.client_email,
    "client_id": creds_dict.client_id,
    "auth_uri": creds_dict.auth_uri,
    "token_uri": creds_dict.token_uri,
    "auth_provider_x509_cert_url": creds_dict.auth_provider_x509_cert_url,
    "client_x509_cert_url": creds_dict.client_x509_cert_url,
}

# Create JSON string for credentials
creds_json = json.dumps(credentials)

# Load credentials and authorize gspread
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
client = gspread.authorize(creds)

try:
    spreadsheet1 = client.open('dv_intercepts_cleaned')
    worksheet1 = spreadsheet1.worksheet('sheet1')
    df = pd.DataFrame(worksheet1.get_all_records())
except Exception as e:
    st.error(f"Error fetching data from Google Sheets: {str(e)}")

st.set_page_config(layout="wide")
st.markdown(
    "<div style='text-align: center;'><img src='https://github.com/JiaqinWu/GRIT_Website/raw/main/logo1.png' width='200'></div>",
    unsafe_allow_html=True
)
st.markdown(
    "<h1 style='text-align: center; font-family: \"Times New Roman\", Times, serif;'>DV Map - Prince William County</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    /* Set font for the sidebar */
    section[data-testid="stSidebar"] * {
        font-family: 'Times New Roman', Times, serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("") 


intercepts_labels = {
    "1": "Community Services",
    "2": "Law Enforcement",
    "3": "Detention & Hearings",
    "4": "Jails/Courts",
    "5": "Reentry",
    "6": "Comm Corrections"
}
ordered_intercepts = [intercepts_labels[k] for k in sorted(intercepts_labels.keys())]

# Sidebar UI
st.sidebar.header("Select A Provider and Assign Intercepts")
all_providers = df["Provider(s)"].dropna().unique().tolist()
selected_provider = st.sidebar.selectbox("Select Provider", all_providers)
intercept_options = list(intercepts_labels.values())
selected_intercepts = st.sidebar.multiselect("Assign Intercepts", intercept_options)

if st.sidebar.button("Update Assignment"):
    # Find the row in the worksheet for the selected provider
    provider_cells = worksheet1.findall(selected_provider)
    if provider_cells:
        row = provider_cells[0].row
        intercept_keys = [k for k, v in intercepts_labels.items() if v in selected_intercepts]
        INTERCEPTS_COLUMN_INDEX = 9
        worksheet1.update_cell(row, INTERCEPTS_COLUMN_INDEX, ",".join(intercept_keys))
        st.sidebar.success("Assignment updated!")
        time.sleep(3)
        st.rerun()
    else:
        st.sidebar.error("Provider not found in sheet.")


def smart_split(val):
    val = str(val).strip()
    if "," in val:
        return [v.strip() for v in val.split(",") if v.strip() != ""]
    elif val.isdigit():
        return list(val)
    else:
        return [val] if val else []

df1 = df.copy()
df1["Intercept"] = df1["Intercept"].apply(smart_split)
df1 = df1.explode("Intercept")
df1["Intercept"] = df1["Intercept"].str.strip()
df1["Intercept Label"] = df1["Intercept"].map(intercepts_labels)


all_providers = sorted(df1["Provider(s)"].dropna().unique())

full_matrix = pd.MultiIndex.from_product(
    [all_providers, ordered_intercepts],
    names=["Provider(s)", "Intercept Label"]
).to_frame(index=False)

df1["assigned"] = 1
merged = pd.merge(full_matrix, df1[["Provider(s)", "Intercept Label", "assigned"]],
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
    )
)

chart = (base + highlight).properties(
    width=800,
    height=28 * len(all_providers)
).configure_axis(
    labelFontSize=12,
    titleFontSize=10,
    labelLimit=350,
    labelFont='Times New Roman',
    titleFont='Times New Roman'
).configure_title(
    font='Times New Roman'
).configure_legend(
    labelFont='Times New Roman',
    titleFont='Times New Roman'
).configure_view(
    strokeWidth=0
)

st.altair_chart(chart, use_container_width=True)