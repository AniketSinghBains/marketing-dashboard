import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import pickle

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Marketing Intelligence Suite", layout="wide")

# =========================================================
# 🔐 SAAS STYLE MULTI-USER LOGIN (STEP 1)
# =========================================================

if "user" not in st.session_state:
    st.session_state.user = None

users_db = {
    "admin@abc.com": {"password": "admin123", "role": "Admin", "company": "ABC Pvt Ltd"},
    "manager@abc.com": {"password": "manager123", "role": "Manager", "company": "ABC Pvt Ltd"},
    "admin@xyz.com": {"password": "admin123", "role": "Admin", "company": "XYZ Marketing"},
}

if st.session_state.user is None:
    st.title("🔐 Marketing Intelligence Suite – Secure Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email in users_db and users_db[email]["password"] == password:
            st.session_state.user = users_db[email]
            st.rerun()
        else:
            st.error("Invalid Credentials")

    st.stop()

user = st.session_state.user

# Sidebar User Info
st.sidebar.markdown("## 👤 User Info")
st.sidebar.write(f"**Company:** {user['company']}")
st.sidebar.write(f"**Role:** {user['role']}")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# =========================================================
# 🎨 DARK PREMIUM UI
# =========================================================
st.markdown("""
<style>
.stApp {background-color:#0E1117;color:#E6EDF3;}
.kpi-card {
    background: linear-gradient(145deg,#1E222B,#161B22);
    padding:20px;border-radius:15px;
    border:1px solid #2D333B;
    text-align:center;
}
.kpi-title {color:#9CA3AF;font-size:14px;}
.kpi-value {color:#FFFFFF;font-size:26px;font-weight:bold;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🏢 PROFESSIONAL DYNAMIC HEADER (STEP 3)
# =========================================================
st.markdown(f"""
<div style='padding:10px 0px'>
<h1>📊 {user['company']} – Marketing Intelligence Dashboard</h1>
<p style='color:#9CA3AF;'>AI Powered Executive Analytics • Secure SaaS Platform</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 🗄 DATABASE CONNECTION
# =========================================================
server = "localhost\\SQLEXPRESS"
database = "marketing_mis"

connection_string = (
    f"mssql+pyodbc://@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = create_engine(connection_string)

# =========================================================
# 🎛 SIDEBAR FILTERS
# =========================================================
st.sidebar.markdown("## 🎛 Executive Controls")

channel_query = f"""
SELECT DISTINCT channel 
FROM dbo.campaigns
WHERE company = '{user['company']}'
"""
channel_list = pd.read_sql(channel_query, engine)['channel'].tolist()

selected_channel = st.sidebar.selectbox("Select Channel", ["All"] + channel_list)

date_query = f"""
SELECT MIN(date) as min_date, MAX(date) as max_date
FROM dbo.campaigns
WHERE company = '{user['company']}'
"""
date_df = pd.read_sql(date_query, engine)

min_date = pd.to_datetime(date_df['min_date'][0])
max_date = pd.to_datetime(date_df['max_date'][0])

start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# =========================================================
# 🏢 COMPANY FILTER LOGIC (STEP 2 - Multi Tenant)
# =========================================================

company_filter = f"company = '{user['company']}'"

if selected_channel == "All":
    filter_condition = f"{company_filter} AND date BETWEEN '{start_date}' AND '{end_date}'"
else:
    filter_condition = f"{company_filter} AND channel='{selected_channel}' AND date BETWEEN '{start_date}' AND '{end_date}'"

# =========================================================
# 📊 FUNNEL DATA
# =========================================================
funnel_query = f"""
SELECT SUM(impressions) as impressions,
       SUM(clicks) as clicks,
       SUM(conversions) as conversions
FROM dbo.campaigns
WHERE {filter_condition}
"""
funnel_df = pd.read_sql(funnel_query, engine)

impressions = funnel_df['impressions'][0] or 0
clicks = funnel_df['clicks'][0] or 0
conversions = funnel_df['conversions'][0] or 0

# KPI Cards
st.subheader("📊 Funnel Overview")
col1,col2,col3 = st.columns(3)

def kpi(title,value):
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-title'>{title}</div>
        <div class='kpi-value'>{value}</div>
    </div>
    """, unsafe_allow_html=True)

with col1: kpi("Impressions", f"{int(impressions):,}")
with col2: kpi("Clicks", f"{int(clicks):,}")
with col3: kpi("Conversions", f"{int(conversions):,}")

# =========================================================
# 🤖 AI FORECAST (STEP 4 - Role Restricted)
# =========================================================
st.markdown("---")
st.subheader("🤖 AI Revenue Forecast")

if user["role"] == "Admin":

    model = pickle.load(open("roi_model.pkl","rb"))

    col7,col8,col9 = st.columns(3)
    input_impressions = col7.number_input("Expected Impressions",10000)
    input_clicks = col8.number_input("Expected Clicks",500)
    input_spend = col9.number_input("Expected Spend",2000)

    if st.button("Predict Revenue"):
        prediction = model.predict([[input_impressions,input_clicks,input_spend]])
        predicted_revenue = prediction[0]
        predicted_roi = ((predicted_revenue-input_spend)/input_spend)*100 if input_spend else 0

        kpi("Predicted Revenue", f"₹ {predicted_revenue:,.0f}")
        kpi("Predicted ROI (%)", f"{predicted_roi:.2f}%")

else:
    st.warning("Only Admin can access AI Forecast")

