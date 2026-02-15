import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import pickle
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Marketing Intelligence Suite", layout="wide")

# =========================================================
# 🔐 MULTI-USER LOGIN
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
# 🎨 DARK UI STYLING
# =========================================================
st.markdown("""
<style>
.stApp {background-color:#0E1117;color:#E6EDF3;}
.kpi-card {background: linear-gradient(145deg,#1E222B,#161B22); padding:20px;border-radius:15px;
 border:1px solid #2D333B; text-align:center;}
.kpi-title {color:#9CA3AF;font-size:14px;}
.kpi-value {color:#FFFFFF;font-size:26px;font-weight:bold;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 🏢 HEADER
# =========================================================
st.markdown(f"""
<div style='padding:10px 0px'>
<h1>📊 {user['company']} – Marketing Intelligence Dashboard</h1>
<p style='color:#9CA3AF;'>AI Powered Executive Analytics • Secure SaaS Platform</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 🗄 LOAD DATA FROM CSV
# =========================================================
csv_path = "campaigns.csv"
if not os.path.exists(csv_path):
    st.error(f"CSV file not found: {csv_path}. Upload campaigns.csv to repo root.")
    st.stop()

df = pd.read_csv(csv_path)
df['date'] = pd.to_datetime(df['date'])
df = df[df['campaign_id'].notnull()]  # safety

# =========================================================
# 🎛 SIDEBAR FILTERS
# =========================================================
st.sidebar.markdown("## 🎛 Executive Controls")
channels = df['channel'].unique().tolist()
selected_channel = st.sidebar.selectbox("Select Channel", ["All"] + channels)
min_date = df['date'].min()
max_date = df['date'].max()
start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date])

filtered_df = df.copy()
if selected_channel != "All":
    filtered_df = filtered_df[filtered_df['channel'] == selected_channel]
filtered_df = filtered_df[(filtered_df['date'] >= pd.to_datetime(start_date)) &
                          (filtered_df['date'] <= pd.to_datetime(end_date))]

# =========================================================
# 📊 FUNNEL KPI CARDS
# =========================================================
impressions = filtered_df['impressions'].sum()
clicks = filtered_df['clicks'].sum()
conversions = filtered_df['conversions'].sum()
total_spend = filtered_df['spend'].sum()
total_revenue = filtered_df['revenue'].sum()

st.subheader("📊 Funnel Overview")
col1,col2,col3,col4,col5 = st.columns(5)
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
with col4: kpi("Spend", f"₹ {total_spend:,.0f}")
with col5: kpi("Revenue", f"₹ {total_revenue:,.0f}")

# =========================================================
# 📈 PLOTLY GRAPHS
# =========================================================
st.markdown("---")
st.subheader("📈 Campaign Trends")

# Daily trend
daily_df = filtered_df.groupby('date').sum().reset_index()
fig = go.Figure()
fig.add_trace(go.Scatter(x=daily_df['date'], y=daily_df['impressions'], mode='lines+markers', name='Impressions'))
fig.add_trace(go.Scatter(x=daily_df['date'], y=daily_df['clicks'], mode='lines+markers', name='Clicks'))
fig.add_trace(go.Scatter(x=daily_df['date'], y=daily_df['conversions'], mode='lines+markers', name='Conversions'))
fig.update_layout(height=400, xaxis_title="Date", yaxis_title="Count", template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

# =========================================================
# 📄 PDF REPORT EXPORT
# =========================================================
st.markdown("---")
st.subheader("📄 Export Report")

def export_pdf(df):
    pdf_path = "campaign_report.pdf"
    doc = SimpleDocTemplate(pdf_path)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph(f"{user['company']} - Campaign Report", styles['Title']))
    elements.append(Spacer(1,12))
    table_data = [df.columns.tolist()] + df.values.tolist()
    table = Table(table_data)
    elements.append(table)
    doc.build(elements)
    return pdf_path

if st.button("Download PDF Report"):
    pdf_file = export_pdf(filtered_df)
    st.success(f"PDF generated: {pdf_file}")

# =========================================================
# 🤖 AI FORECAST (Admin Only)
# =========================================================
st.markdown("---")
st.subheader("🤖 AI Revenue Forecast")
if user["role"] == "Admin":
    if os.path.exists("roi_model.pkl"):
        model = pickle.load(open("roi_model.pkl","rb"))
        col1,col2,col3 = st.columns(3)
        input_impressions = col1.number_input("Expected Impressions",10000)
        input_clicks = col2.number_input("Expected Clicks",500)
        input_spend = col3.number_input("Expected Spend",2000)
        if st.button("Predict Revenue"):
            prediction = model.predict([[input_impressions,input_clicks,input_spend]])
            predicted_revenue = prediction[0]
            predicted_roi = ((predicted_revenue-input_spend)/input_spend)*100 if input_spend else 0
            kpi("Predicted Revenue", f"₹ {predicted_revenue:,.0f}")
            kpi("Predicted ROI (%)", f"{predicted_roi:.2f}%")
    else:
        st.warning("AI model (roi_model.pkl) not found. Upload to enable forecast.")
else:
    st.warning("Only Admin can access AI Forecast")
