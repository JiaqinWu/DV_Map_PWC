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

st.set_page_config(
        page_title="DV Map - Prince William County",
        page_icon="https://github.com/JiaqinWu/GRIT_Website/raw/main/logo1.png", 
        layout="centered"
    ) 

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
    /* Sidebar font */
    section[data-testid="stSidebar"] * {
        font-family: 'Times New Roman', Times, serif !important;
    }
    /* Main page selectbox and widget labels */
    section.main label {
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 16px !important;
        font-weight: bold;
    }
    /* Main page selectbox dropdowns */
    div[data-baseweb="select"] * {
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
st.sidebar.header("Select A Provider and Assign Intercept(s)")
all_providers = df["Provider(s)"].dropna().unique().tolist()
all_providers.sort(key=lambda x: x.lower())

# Add "Add New Provider" option to the list
provider_options = ["Add New Provider"] + all_providers
selected_provider = st.sidebar.selectbox("Select Provider", provider_options, key="provider_select")

# Show name input field if "Add New Provider" is selected
if selected_provider == "Add New Provider":
    new_provider_name = st.sidebar.text_input("Enter New Provider Name:", key="new_provider_name")
    if new_provider_name:
        selected_provider = new_provider_name
    new_primary_contact = st.sidebar.text_input("Enter Primary Contact Person (Name; Email):", key="new_primary_contact")
    if new_primary_contact:
        new_primary_contact = new_primary_contact
        new_primary_contact_email = new_primary_contact_email
    new_description_of_services = st.sidebar.text_input("Enter Description of Services, Intervention, or Activity:", key="new_description_of_services")
    if new_description_of_services:
        new_description_of_services = new_description_of_services
    new_recipients = st.sidebar.text_input("Enter Recipients:", key="new_recipients")
    if new_recipients:
        new_recipients = new_recipients
    new_criteria_for_who_receives_the_service = st.sidebar.text_input("Enter Criteria for Who Receives the Service:", key="new_criteria_for_who_receives_the_service")
    if new_criteria_for_who_receives_the_service:
        new_criteria_for_who_receives_the_service = new_criteria_for_who_receives_the_service
    new_research_or_best_practice_supported_practice = st.sidebar.text_input("Enter Research or Best Practice Supported Practice:", key="new_research_or_best_practice_supported_practice")
    if new_research_or_best_practice_supported_practice:
        new_research_or_best_practice_supported_practice = new_research_or_best_practice_supported_practice
    new_legally_mandated_practice = st.sidebar.text_input("Enter Legally Mandated Practice:", key="new_legally_mandated_practice")
    if new_legally_mandated_practice:
        new_legally_mandated_practice = new_legally_mandated_practice
    new_notes = st.sidebar.text_input("Enter Notes:", key="new_notes")
    if new_notes:
        new_notes = new_notes
    new_gaps = st.sidebar.text_input("Enter Gaps:", key="new_gaps")
    if new_gaps:
        new_gaps = new_gaps

intercept_options = list(intercepts_labels.values())
selected_intercepts = st.sidebar.multiselect("Assign Intercepts", intercept_options, key="intercepts_select")


if st.sidebar.button("Update Assignment"):
    if selected_provider and isinstance(selected_provider, str) and selected_provider != "Add New Provider":
        # Check if this is a new provider (not in existing list)
        if selected_provider not in all_providers:
            # Add new provider to the sheet
            if new_provider_name and selected_intercepts:
                try:
                    # Get the headers from the first row
                    headers = worksheet1.row_values(1)
                    
                    # Create a new row with the provider name and intercepts
                    intercept_keys = [k for k, v in intercepts_labels.items() if v in selected_intercepts]
                    new_row = [""] * len(headers)  
                    new_row[0] = selected_provider  
                    new_row[1] = new_primary_contact
                    new_row[2] = new_description_of_services
                    new_row[3] = new_recipients
                    new_row[4] = new_criteria_for_who_receives_the_service
                    new_row[5] = new_research_or_best_practice_supported_practice
                    new_row[6] = new_legally_mandated_practice
                    new_row[7] = new_notes
                    new_row[8] = ",".join(intercept_keys)
                    new_row[9] = new_gaps
                    
                    # Append the new row
                    worksheet1.append_row(new_row)
                    st.sidebar.success(f"New provider '{selected_provider}' added successfully!")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error adding new provider: {str(e)}")
            else:
                st.sidebar.error("Please enter a provider name and select at least one intercept.")
        else:
            # Update existing provider
            provider_cells = worksheet1.findall(selected_provider)
            if provider_cells:
                row = provider_cells[0].row
                intercept_keys = [k for k, v in intercepts_labels.items() if v in selected_intercepts]
                INTERCEPTS_COLUMN_INDEX = 9
                worksheet1.update_cell(row, INTERCEPTS_COLUMN_INDEX, ",".join(intercept_keys))
                st.sidebar.success("Assignment updated!")
                time.sleep(2)
                st.rerun()
            else:
                st.sidebar.error("Provider not found in sheet.")
    else:
        st.sidebar.error("Please select a provider and enter a name if adding new provider.")


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
        axis=alt.Axis(
            labelAngle=45,
            labelFontSize=8,
            labelLimit=400,
            labelPadding=10,
            orient="top"
        )
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
        axis=alt.Axis(
            labelAngle=45,
            labelFontSize=8,
            labelLimit=400,
            labelPadding=10,
            orient="top"
        )
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
    width=1000,
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

# --- Provider Details Section ---
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h2 style='font-family: \"Times New Roman\", Times, serif;'>View Provider Details</h2>", unsafe_allow_html=True)

provider_detail_fields = [
    "Provider(s)",
    "Primary Contact Person (Name; Email)",
    "Description of Services, Intervention, or Activity",
    "Recipients",
    "Criteria for Who Receives the Service",
    "Research or Best Practice Supported Practice?",
    "Legally Mandated Practice?",
    "Notes",
    "Gaps"
]


# Update all_providers list for the provider details section
updated_all_providers = sorted(df["Provider(s)"].dropna().unique())
provider_detail_select = st.selectbox("Select a provider to view details:", updated_all_providers, key="provider_detail_select")

provider_row = df[df["Provider(s)"] == provider_detail_select]

if not provider_row.empty:
    for field in provider_detail_fields:
        value = provider_row.iloc[0][field] if field in provider_row.columns else "NA"
        if pd.isna(value) or value == "":
            value = "NA"
        st.markdown(f"<span style='font-family: \"Times New Roman\", Times, serif;'><b>{field}:</b> {value}</span>", unsafe_allow_html=True)
else:
    st.info("No details available for the selected provider.")