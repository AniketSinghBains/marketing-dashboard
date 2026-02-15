import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
import pickle
import io
from PIL import Image as PILImage
import matplotlib.pyplot as plt  # ✅ Top pe import

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
roi = ((total_revenue - total_spend)/total_spend)*100 if total_spend else 0

st.subheader("📊 Funnel Overview")
col1, col2, col3, col4, col5, col6 = st.columns(6)
def kpi(title,value): 
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div></div>", unsafe_allow_html=True)
with col1: kpi("Impressions", f"{total_impressions:,}")
with col2: kpi("Clicks", f"{total_clicks:,}")
with col3: kpi("Conversions", f"{total_conversions:,}")
with col4: kpi("Spend", f"₹ {total_spend:,.0f}")
with col5: kpi("Revenue", f"₹ {total_revenue:,.0f}")
with col6: kpi("ROI (%)", f"{roi:.2f}%")

# ---------------- GRAPHS ----------------
st.markdown("---")
st.subheader("📈 Campaign Analysis Charts")

# Bar Chart: Impressions vs Clicks
bar_fig = px.bar(
    filtered_df.groupby('channel')[['impressions','clicks']].sum().reset_index(),
    x='channel', y=['impressions','clicks'],
    barmode='group', title="Impressions vs Clicks per Channel",
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(bar_fig, use_container_width=True)

# Donut Chart: Conversions distribution
conv_fig = px.pie(
    filtered_df, values='conversions', names='channel',
    hole=0.5, title="Conversions Distribution by Channel",
    color_discrete_sequence=px.colors.sequential.Agsunset
)
st.plotly_chart(conv_fig, use_container_width=True)

# Line Chart: Revenue trend
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
st.subheader("📄 Generate Professional PDF Report")

report_company = st.text_input("Enter Company Name", value=user['company'])
report_team_lead = st.text_input("Enter Team Lead Name", value=user['team_lead'])

if st.button("Generate Report"):
    # Graph images for PDF
    bar_path = "temp_bar.png"
    donut_path = "temp_donut.png"
    line_path = "temp_line.png"

    # Bar chart
    bar_fig, ax = plt.subplots(figsize=(6,4))
    bar_data = filtered_df.groupby('channel')[['impressions','clicks']].sum()
    bar_data.plot(kind='bar', ax=ax, color=['#1f77b4','#ff7f0e'])
    ax.set_title("Impressions vs Clicks per Channel")
    plt.tight_layout()
    bar_fig.savefig(bar_path)
    plt.close(bar_fig)

    # Donut chart
    donut_fig, ax = plt.subplots(figsize=(6,4))
    donut_data = filtered_df.groupby('channel')['conversions'].sum()
    ax.pie(donut_data, labels=donut_data.index, autopct='%1.1f%%', startangle=90, wedgeprops={'width':0.4})
    ax.set_title("Conversions Distribution by Channel")
    plt.tight_layout()
    donut_fig.savefig(donut_path)
    plt.close(donut_fig)

    # Line chart
    line_fig, ax = plt.subplots(figsize=(6,4))
    rev_data = filtered_df.groupby('date')['revenue'].sum()
    ax.plot(rev_data.index, rev_data.values, marker='o', color='#2ca02c')
    ax.set_title("Revenue Trend Over Time")
    ax.set_ylabel("Revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()
    line_fig.savefig(line_path)
    plt.close(line_fig)

    # PDF generation
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    # Logo
    try:
        logo = PILImage.open("logo.png")
        logo.save("temp_logo.png")
        elements.append(Image("temp_logo.png", width=120, height=50))
    except:
        pass

    elements.append(Paragraph(f"{report_company} – Marketing Intelligence Report", styles['Title']))
    elements.append(Paragraph(f"Team Lead: {report_team_lead}", styles['Normal']))
    elements.append(Spacer(1,12))

    # Add graphs
    elements.append(Paragraph("📊 Impressions vs Clicks", styles['Heading2']))
    elements.append(Image(bar_path, width=400, height=250))
    elements.append(Spacer(1,12))

    elements.append(Paragraph("📊 Conversions Distribution", styles['Heading2']))
    elements.append(Image(donut_path, width=400, height=250))
    elements.append(Spacer(1,12))

    elements.append(Paragraph("📊 Revenue Trend Over Time", styles['Heading2']))
    elements.append(Image(line_path, width=400, height=250))
    elements.append(Spacer(1,12))

    # Campaign table
    elements.append(Paragraph("📋 Campaign Data Table", styles['Heading2']))
    table_data = [filtered_df.columns.tolist()] + filtered_df.values.tolist()
    table = Table(table_data, hAlign='LEFT')
    table.setStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('GRID',(0,0),(-1,-1),1,colors.black)
    ])
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    st.success("Report Generated Successfully ✅")
    st.download_button(
        label="Download PDF Report",
        data=buffer,
        file_name="Marketing_Report.pdf",
        mime="application/pdf"
    )
