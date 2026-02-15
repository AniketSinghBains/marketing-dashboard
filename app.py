import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# 🏢 PROFESSIONAL DYNAMIC HEADER
# =========================================================
st.markdown(f"""
<div style='padding:10px 0px'>
<h1>📊 {user['company']} – Marketing Intelligence Dashboard</h1>
<p style='color:#9CA3AF;'>AI Powered Executive Analytics • Secure SaaS Platform</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 🗄 LOAD DATA FROM CSV (INSTEAD OF SQL SERVER)
# =========================================================
# campaigns.csv should be in repo root
df = pd.read_csv("campaigns.csv")

# Filter only for the logged-in user's company
df = df[df['campaign_id'].notnull()]  # optional safety

# =========================================================
# 🎛 SIDEBAR FILTERS
# =========================================================
st.sidebar.markdown("## 🎛 Executive Controls")

# Channel Filter
channels = df['channel'].unique().tolist()
selected_channel = st.sidebar.selectbox("Select Channel", ["All"] + channels)

# Date Filter
df['date'] = pd.to_datetime(df['date'])
min_date = df['date'].min()
max_date = df['date'].max()
start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# =========================================================
# 🏢 FILTER LOGIC
# =========================================================
filtered_df = df.copy()

# Channel filter
if selected_channel != "All":
    filtered_df = filtered_df[filtered_df['channel'] == selected_channel]

# Date range filter
filtered_df = filtered_df[(filtered_df['date'] >= pd.to_datetime(start_date)) &
                          (filtered_df['date'] <= pd.to_datetime(end_date))]

# =========================================================
# 📊 FUNNEL DATA
# =========================================================
impressions = filtered_df['impressions'].sum()
clicks = filtered_df['clicks'].sum()
conversions = filtered_df['conversions'].sum()

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

