import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import pickle
import io

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Marketing Intelligence Suite", layout="wide")

# ---------------- USER LOGIN ----------------
if "user" not in st.session_state:
    st.session_state.user = None

users_db = {
    "admin@abc.com": {"password": "admin123", "role": "Admin", "company": "ABC Pvt Ltd", "team_lead": "Rahul Sharma"},
    "manager@abc.com": {"password": "manager123", "role": "Manager", "company": "ABC Pvt Ltd", "team_lead": "Rahul Sharma"},
    "admin@xyz.com": {"password": "admin123", "role": "Admin", "company": "XYZ Marketing", "team_lead": "Priya Verma"},
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

# ---------------- SIDEBAR USER INFO ----------------
st.sidebar.markdown("## 👤 User Info")
st.sidebar.write(f"**Company:** {user['company']}")
st.sidebar.write(f"**Role:** {user['role']}")
st.sidebar.write(f"**Team Lead:** {user['team_lead']}")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# ---------------- DARK UI ----------------
st.markdown("""
<style>
.stApp {background-color:#0E1117;color:#E6EDF3;}
.kpi-card {background: linear-gradient(145deg,#1E222B,#161B22); padding:20px; border-radius:15px; border:1px solid #2D333B; text-align:center;}
.kpi-title {color:#9CA3AF;font-size:14px;}
.kpi-value {color:#FFFFFF;font-size:26px;font-weight:bold;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown(f"""
<div style='padding:10px 0px'>
<h1>📊 {user['company']} – Marketing Intelligence Dashboard</h1>
<p style='color:#9CA3AF;'>Team Lead: {user['team_lead']} | AI Powered Executive Analytics</p>
</div>
""", unsafe_allow_html=True)

# ---------------- LOAD CSV ----------------
df = pd.read_csv("campaigns.csv")
df['date'] = pd.to_datetime(df['date'])

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.markdown("## 🎛 Filters")
channels = df['channel'].unique().tolist()
selected_channel = st.sidebar.selectbox("Select Channel", ["All"] + channels)
start_date, end_date = st.sidebar.date_input(
    "Select Date Range", 
    [df['date'].min(), df['date'].max()]
)

# Filter dataframe
filtered_df = df[
    ((df['channel'] == selected_channel) | (selected_channel == "All")) &
    (df['date'] >= pd.to_datetime(start_date)) &
    (df['date'] <= pd.to_datetime(end_date))
]

# ---------------- KPIs ----------------
total_impressions = filtered_df['impressions'].sum()
total_clicks = filtered_df['clicks'].sum()
total_conversions = filtered_df['conversions'].sum()
total_spend = filtered_df['spend'].sum()
total_revenue = filtered_df['revenue'].sum()

st.subheader("📊 Funnel Overview")
col1, col2, col3, col4, col5 = st.columns(5)
def kpi(title,value): st.markdown(f"<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div></div>", unsafe_allow_html=True)
with col1: kpi("Impressions", f"{total_impressions:,}")
with col2: kpi("Clicks", f"{total_clicks:,}")
with col3: kpi("Conversions", f"{total_conversions:,}")
with col4: kpi("Spend", f"₹ {total_spend:,.0f}")
with col5: kpi("Revenue", f"₹ {total_revenue:,.0f}")

# ---------------- GRAPHS ----------------
st.markdown("---")
st.subheader("📈 Campaign Analysis Charts")

# 1️⃣ Bar Chart: Impressions vs Clicks
bar_fig = px.bar(
    filtered_df.groupby('channel')[['impressions','clicks']].sum().reset_index(),
    x='channel', y=['impressions','clicks'],
    barmode='group', title="Impressions vs Clicks per Channel",
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(bar_fig, use_container_width=True)

# 2️⃣ Donut Chart: Conversions distribution
conv_fig = px.pie(
    filtered_df, values='conversions', names='channel',
    hole=0.5, title="Conversions Distribution by Channel",
    color_discrete_sequence=px.colors.sequential.Agsunset
)
st.plotly_chart(conv_fig, use_container_width=True)

# 3️⃣ Line Chart: Revenue trend
rev_fig = px.line(
    filtered_df.groupby('date')['revenue'].sum().reset_index(),
    x='date', y='revenue', title="Revenue Trend Over Time",
    markers=True, line_shape='spline', color_discrete_sequence=['#00CC96']
)
st.plotly_chart(rev_fig, use_container_width=True)

# ---------------- AI FORECAST ----------------
st.markdown("---")
st.subheader("🤖 AI Revenue Forecast")
if user["role"] == "Admin":
    try:
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
    except FileNotFoundError:
        st.warning("ROI model file not found. Please upload roi_model.pkl")
else:
    st.warning("Only Admin can access AI Forecast")

# ---------------- PDF REPORT ----------------
st.markdown("---")
st.subheader("📄 Download Report")

def generate_pdf(df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph(f"{user['company']} – Marketing Intelligence Report", styles['Title']))
    elements.append(Paragraph(f"Team Lead: {user['team_lead']}", styles['Normal']))
    elements.append(Spacer(1,12))
    table_data = [df.columns.tolist()] + df.values.tolist()
    table = Table(table_data)
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

if st.button("Download PDF"):
    pdf_file = generate_pdf(filtered_df)
    st.download_button(label="Download PDF", data=pdf_file, file_name="Marketing_Report.pdf", mime="application/pdf")
