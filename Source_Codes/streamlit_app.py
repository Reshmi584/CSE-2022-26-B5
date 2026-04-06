import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

st.set_page_config(
    page_title="Heart Monitoring Dashboard",
    layout="wide"
)

# ---------------- HEADER ----------------

st.markdown("""
<style>

.main-title{
font-size:40px;
font-weight:bold;
text-align:center;
color:#2E86C1;
}

.subtitle{
text-align:center;
font-size:18px;
color:gray;
margin-bottom:20px;
}

.metric-card{
background-color:#F8F9F9;
padding:15px;
border-radius:10px;
box-shadow:0px 2px 8px rgba(0,0,0,0.1);
}

.section-title{
font-size:26px;
font-weight:bold;
margin-top:10px;
}

</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>Real-Time Heart Monitoring Dashboard</div>", unsafe_allow_html=True)

st.caption(f"Last Updated : {datetime.now().strftime('%d %B %Y  %H:%M:%S')}")

st.divider()

# ---------------- DATA SOURCE ----------------

sheet_url = "https://docs.google.com/spreadsheets/d/1L_v7n8TSMOwjCN-UTkwDJy7pglPcAIfeLlzbZ6twBlE/export?format=csv&gid=1758725495"

@st.cache_data(ttl=5)
def load_data():

    df = pd.read_csv(sheet_url)

    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce").dt.strftime("%H:%M:%S")

    df = df.dropna(subset=["Date"])

    return df

df = load_data()

if df.empty:
    st.warning("No data available yet")
    st.stop()

# ---------------- CURRENT STATUS ----------------

latest = df.iloc[-1]

st.markdown("<div class='section-title'>Current Health Status</div>", unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)

c1.metric("RR Interval (RR)", latest["Avg_RR(ms)"], latest.get("RR_Status",""))
c2.metric("Heart Rate (HR)", latest["Avg_HR(bpm)"], latest.get("HR_Status",""))
c3.metric("Blood Oxygen (SpO₂)", latest["Avg_SpO2(%)"], latest.get("SpO2_Status",""))
c4.metric("Overall Health Status", latest.get("Final",""))

st.divider()

# ---------------- DAILY TREND ----------------

st.markdown("<div class='section-title'>Daily Health Trends</div>", unsafe_allow_html=True)

today = datetime.today().date()

daily = df[df["Date"].dt.date == today]
daily = daily.tail(6)

col1,col2,col3 = st.columns(3)

fig = px.line(
    daily,
    x="Time",
    y="Avg_RR(ms)",
    title="RR Interval Trend (Daily)",
    markers=True
)
fig.update_traces(line=dict(width=4))
fig.update_yaxes(range=[400,1300])
fig.update_layout(height=400)
col1.plotly_chart(fig, width="stretch")

fig = px.line(
    daily,
    x="Time",
    y="Avg_HR(bpm)",
    title="Heart Rate Trend (Daily)",
    markers=True
)
fig.update_traces(line=dict(width=4))
fig.update_yaxes(range=[40,130])
fig.update_layout(height=400)
col2.plotly_chart(fig, width="stretch")

fig = px.line(
    daily,
    x="Time",
    y="Avg_SpO2(%)",
    title="Blood Oxygen Trend (Daily)",
    markers=True
)
fig.update_traces(line=dict(width=4))
fig.update_yaxes(range=[80,100])
fig.update_layout(height=400)
col3.plotly_chart(fig, width="stretch")

st.divider()

# ---------------- WEEKLY TREND ----------------

st.markdown("<div class='section-title'>Weekly Health Trends</div>", unsafe_allow_html=True)

weekly = df.copy()

weekly["Week"] = weekly["Date"].dt.to_period("W").apply(lambda r: r.start_time)

weekly_chart = weekly.groupby("Week").agg({
    "Avg_RR(ms)":"mean",
    "Avg_HR(bpm)":"mean",
    "Avg_SpO2(%)":"mean"
}).reset_index()

weekly_chart["Week_Label"] = weekly_chart["Week"].dt.strftime("%d %b")

weekly_chart = weekly_chart.tail(6)

col1,col2,col3 = st.columns(3)

fig = px.line(weekly_chart, x="Week_Label", y="Avg_RR(ms)", title="RR Interval Trend (Weekly)", markers=True)
fig.update_traces(line=dict(width=4))
fig.update_yaxes(range=[400,1300])
fig.update_layout(height=400)
col1.plotly_chart(fig, width="stretch")

fig = px.line(weekly_chart, x="Week_Label", y="Avg_HR(bpm)", title="Heart Rate Trend (Weekly)", markers=True)
fig.update_traces(line=dict(width=4))
fig.update_yaxes(range=[40,130])
fig.update_layout(height=400)
col2.plotly_chart(fig, width="stretch")

fig = px.line(weekly_chart, x="Week_Label", y="Avg_SpO2(%)", title="Blood Oxygen Trend (Weekly)", markers=True)
fig.update_traces(line=dict(width=4))
fig.update_yaxes(range=[80,100])
fig.update_layout(height=400)
col3.plotly_chart(fig, width="stretch")

st.divider()

# ---------------- MONTHLY TREND ----------------

st.markdown("<div class='section-title'>Monthly Health Trends</div>", unsafe_allow_html=True)

monthly = df.copy()

monthly["Month"] = monthly["Date"].dt.to_period("M")

monthly_chart = monthly.groupby("Month").agg({
    "Avg_RR(ms)":"mean",
    "Avg_HR(bpm)":"mean",
    "Avg_SpO2(%)":"mean"
}).reset_index()

monthly_chart["Month_Label"] = monthly_chart["Month"].dt.strftime("%b %Y")

monthly_chart = monthly_chart.sort_values("Month")
monthly_chart = monthly_chart.tail(6)

col1,col2,col3 = st.columns(3)

fig = px.line(monthly_chart, x="Month_Label", y="Avg_RR(ms)", title="RR Interval Trend (Monthly)", markers=True)
fig.update_traces(line=dict(width=4))
fig.update_yaxes(range=[400,1300])
fig.update_layout(height=400)
col1.plotly_chart(fig, width="stretch")

fig = px.line(monthly_chart, x="Month_Label", y="Avg_HR(bpm)", title="Heart Rate Trend (Monthly)", markers=True)
fig.update_traces(line=dict(width=4))
fig.update_yaxes(range=[40,130])
fig.update_layout(height=400)
col2.plotly_chart(fig, width="stretch")

fig = px.line(monthly_chart, x="Month_Label", y="Avg_SpO2(%)", title="Blood Oxygen Trend (Monthly)", markers=True)
fig.update_traces(line=dict(width=4))
fig.update_yaxes(range=[80,100])
fig.update_layout(height=400)
col3.plotly_chart(fig, width="stretch")

st.divider()

# ---------------- STATUS SUMMARY ----------------

def calculate_status(series):

    if (series == "HIGH").any():
        return "HIGH"
    elif (series == "MEDIUM").any():
        return "MEDIUM"
    else:
        return "LOW"

today = datetime.today()

current_week = df[
    (df["Date"].dt.isocalendar().week == today.isocalendar().week) &
    (df["Date"].dt.year == today.year)
]

if current_week.empty:
    last_week = df["Date"].dt.to_period("W").max()
    weekly_data = df[df["Date"].dt.to_period("W") == last_week]
else:
    weekly_data = current_week

weekly_status = calculate_status(weekly_data["Final"])

current_month = df[
    (df["Date"].dt.month == today.month) &
    (df["Date"].dt.year == today.year)
]

if current_month.empty:
    last_month = df["Date"].dt.to_period("M").max()
    monthly_data = df[df["Date"].dt.to_period("M") == last_month]
else:
    monthly_data = current_month

monthly_status = calculate_status(monthly_data["Final"])

st.markdown("<div class='section-title'>Health Risk Summary</div>", unsafe_allow_html=True)

c1,c2,c3 = st.columns(3)

c1.metric("Current Status", latest["Final"])
c2.metric("Weekly Status", weekly_status)
c3.metric("Monthly Status", monthly_status)

st.divider()

# ---------------- FOOTER ----------------

st.markdown("""
---
Real-Time Heart Monitoring System  
RR Interval • Heart Rate • Blood Oxygen Monitoring
""")

st.caption("Dashboard auto refreshes every 5 seconds")

# AUTO REFRESH

time.sleep(5)
st.rerun()
