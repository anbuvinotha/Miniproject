import streamlit as st
import requests
import pandas as pd
import altair as alt

API_BASE_URL = "http://localhost:8000"
st.title("Smart AI CFO Dashboard")

uploaded_file = st.file_uploader("Upload Invoice (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"])
if uploaded_file is not None:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    with st.spinner("Uploading and parsing invoice..."):
        res = requests.post(f"{API_BASE_URL}/upload-invoice", files=files)
        if res.ok:
            data = res.json()
            st.success("Invoice uploaded successfully!")
            st.json(data["parsed_fields"])
        else:
            st.error(f"Failed to upload: {res.text}")

st.markdown("---")
st.header("Expense Trends")
try:
    resp = requests.get(f"{API_BASE_URL}/insights/expense-trends")
    resp.raise_for_status()
    invoices = resp.json()
    if invoices:
        df = pd.DataFrame(invoices)
        df['month'] = pd.to_datetime(df['month'].astype(str)).dt.to_timestamp()
        chart = alt.Chart(df).mark_line().encode(
            x='month:T',
            y='amount:Q',
            color='vendor:N', tooltip=['vendor', 'amount', 'month']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("No expense data available.")
except Exception as e:
    st.error(f"Error fetching expense trends: {e}")

st.markdown("---")
st.header("Potential Duplicate Invoices")
try:
    dup_resp = requests.get(f"{API_BASE_URL}/fraud/detect-duplicates")
    dup_resp.raise_for_status()
    duplicates = dup_resp.json()
    if duplicates:
        st.dataframe(pd.DataFrame(duplicates))
    else:
        st.write("No duplicates detected.")
except Exception as e:
    st.error(f"Error fetching duplicates: {e}")

st.markdown("---")
st.header("Cashflow Forecast")
forecast_period = st.slider("Forecast Months", min_value=1, max_value=12, value=6)
try:
    forcast_resp = requests.get(f"{API_BASE_URL}/forecast", params={"periods": forecast_period})
    forcast_resp.raise_for_status()
    forecast_data = forcast_resp.json()
    df_forecast = pd.DataFrame(forecast_data)
    df_forecast['ds'] = pd.to_datetime(df_forecast['ds'])
    forecast_chart = alt.Chart(df_forecast).mark_line().encode(
        x='ds:T',
        y='yhat:Q',
        tooltip=['ds', 'yhat', 'yhat_lower', 'yhat_upper']
    ).interactive()
    st.altair_chart(forecast_chart, use_container_width=True)
except Exception as e:
    st.error(f"Error fetching forecast: {e}")
