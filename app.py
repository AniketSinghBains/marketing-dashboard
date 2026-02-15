import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import pickle
import io

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Marketing Intelligence Suite", layout="wide", page_icon="📊")

# =========================================================
# 🔐 SAAS MULTI-USER LOGIN
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None

users_db = {
    "admin@abc.com": {"password": "admin123", "role": "Admin", "company": "ABC Pvt Ltd", "team_lead": "Rahul Sharma"},
    "manager@abc.com": {"password": "manager123", "role": "Manager", "company": "ABC Pvt Ltd", "team_lead": "Rahul Sharma"},
    "admin@xyz.com": {"password": "admin123", "role": "Admin", "company": "XYZ Marketing", "team_lead": "Neha Verma"},
}

if st.session_state.user is None:
    st.title("🔐 Marketing Intelligence Suite – Secure Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email in users_db and users_db[email]["password"] == password:
            st.session_state.user = users_db[email]
            st.experimental_rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

user = st.session_state.user

# Sidebar User Info
st.sidebar.markdown("## 👤 User Info")
st.sidebar.write(f"**Company:** {user['company']}")
st.sidebar.write(f"**Role:** {user['role']}")
st.sidebar.write(f"**Team Lead:** {user['team_lead']}")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.experimental_rerun()

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
    text-align:center;margin-bottom:15px;
}
.kpi-title {color:#9CA3AF;font-size:14px;}
.kpi-value {color:#FFFFFF;font-size:26px;font-weight:bold;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER WITH LOGO
# =========================================================
st.markdown(f"""
<div style='display:flex;align-items:center;gap:15px;'>
    <img src='https://upload.wikimedia.org/wikipedia/commons/1/1b/ABC_logo.png' width='60'/>
    <div>
        <h1>📊 {user['company']} – Marketing Intelligence Dashboard</h1>
        <p style='color:#9CA3AF;margin:0;'>Team Lead: {user['team_lead']} | AI Powered Executive Analytics</p>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE CONNECTION
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
# SIDEBAR FILTERS
# =========================================================
st.sidebar.markdown("## 🎛 Filters")

# Channels
channel_query = f"SELECT DISTINCT channel FROM dbo.campaigns WHERE company='{user['company']}'"
channel_list = pd.read_sql(channel_query, engine)['channel'].tolist()
selected_channel = st.sidebar.selectbox("Select Channel", ["All"] + channel_list)

# Date range
date_query = f"SELECT MIN(date) as min_date, MAX(date) as max_date FROM dbo.campaigns WHERE company='{user['company']}'"
date_df = pd.read_sql(date_query, engine)
min_date = pd.to_datetime(date_df['min_date'][0])
max_date = pd.to_datetime(date_df['max_date'][0])
start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# =========================================================
# FILTER LOGIC
# =========================================================
company_filter = f"company='{user['company']}'"
if selected_channel == "All":
    filter_condition = f"{company_filter} AND date BETWEEN '{start_date}' AND '{end_date}'"
else:
    filter_condition = f"{company_filter} AND channel='{selected_channel}' AND date BETWEEN '{start_date}' AND '{end_date}'"

query = f"SELECT * FROM dbo.campaigns WHERE {filter_condition}"
df = pd.read_sql(query, engine)

# =========================================================
# KPI CARDS (FUNNEL)
# =========================================================
st.subheader("📊 Funnel Overview")
col1, col2, col3 = st.columns(3)
def kpi(title, value):
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-title'>{title}</div>
        <div class='kpi-value'>{value}</div>
    </div>
    """, unsafe_allow_html=True)

kpi("Impressions", f"{df['impressions'].sum():,}")
kpi("Clicks", f"{df['clicks'].sum():,}")
kpi("Conversions", f"{df['conversions'].sum():,}")

# =========================================================
# INTERACTIVE GRAPHS
# =========================================================
st.subheader("📈 Marketing Analysis")

# 1️⃣ Bar chart: Impressions & Clicks per channel
bar_df = df.groupby('channel')[['impressions','clicks']].sum().reset_index()
fig_bar = px.bar(bar_df, x='channel', y=['impressions','clicks'], barmode='group',
                 title="Impressions & Clicks per Channel", color_discrete_sequence=px.colors.qualitative.T10)
st.plotly_chart(fig_bar, use_container_width=True)

# 2️⃣ Donut chart: Conversion Rate per channel
df['conversion_rate'] = df['conversions'] / df['impressions'] * 100
donut_df = df.groupby('channel')['conversion_rate'].mean().reset_index()
fig_donut = px.pie(donut_df, values='conversion_rate', names='channel', hole=0.5,
                   title="Average Conversion Rate per Channel", color_discrete_sequence=px.colors.sequential.Plasma)
st.plotly_chart(fig_donut, use_container_width=True)

# 3️⃣ Scatter: Revenue vs Spend
fig_scatter = px.scatter(df, x='spend', y='revenue', color='channel', size='clicks',
                         title="Revenue vs Spend", hover_data=['impressions','conversions'],
                         color_discrete_sequence=px.colors.qualitative.Vivid)
st.plotly_chart(fig_scatter, use_container_width=True)

# =========================================================
# AI REVENUE FORECAST (ADMIN ONLY)
# =========================================================
st.markdown("---")
st.subheader("🤖 AI Revenue Forecast")
if user['role']=="Admin":
    try:
        model = pickle.load(open("roi_model.pkl","rb"))
        col7,col8,col9 = st.columns(3)
        input_impressions = col7.number_input("Expected Impressions", 10000)
        input_clicks = col8.number_input("Expected Clicks", 500)
        input_spend = col9.number_input("Expected Spend", 2000)
        if st.button("Predict Revenue"):
            prediction = model.predict([[input_impressions,input_clicks,input_spend]])
            predicted_revenue = prediction[0]
            predicted_roi = ((predicted_revenue-input_spend)/input_spend)*100 if input_spend else 0
            kpi("Predicted Revenue", f"₹ {predicted_revenue:,.0f}")
            kpi("Predicted ROI (%)", f"{predicted_roi:.2f}%")
    except FileNotFoundError:
        st.error("ROI model file 'roi_model.pkl' not found. Upload in repo root.")
else:
    st.warning("Only Admin can access AI Forecast")

# =========================================================
# PDF REPORT EXPORT
# =========================================================
st.markdown("---")
st.subheader("📄 Export PDF Report")
def create_pdf(df, company, team_lead):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"{company} – Marketing Intelligence Report", styles['Title']))
    elements.append(Paragraph(f"Team Lead: {team_lead}", styles['Normal']))
    elements.append(Spacer(1,12))

    metrics_table = [
        ['Metric','Value'],
        ['Impressions', f"{df['impressions'].sum():,}"],
        ['Clicks', f"{df['clicks'].sum():,}"],
        ['Conversions', f"{df['conversions'].sum():,}"],
        ['Spend', f"{df['spend'].sum():,.2f}"],
        ['Revenue', f"{df['revenue'].sum():,.2f}"],
    ]
    t = Table(metrics_table)
    elements.append(t)
    elements.append(Spacer(1,12))
    doc.build(elements)
    buffer.seek(0)
    return buffer

if st.button("Download PDF"):
    pdf_file = create_pdf(df, user['company'], user['team_lead'])
    st.download_button("Download Report", data=pdf_file, file_name="marketing_report.pdf", mime="application/pdf")
