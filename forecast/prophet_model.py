from prophet import Prophet
import pandas as pd

def prepare_data_for_prophet(invoices):
    df = pd.DataFrame(invoices)
    df['ds'] = pd.to_datetime(df['invoice_date'], errors='coerce')
    df['y'] = df['amount']
    df = df[['ds', 'y']].sort_values('ds')
    df = df.dropna(subset=['ds'])
    return df

def run_prophet_forecast(invoices, periods=6):
    df = prepare_data_for_prophet(invoices)
    m = Prophet()
    # Correctly add monthly seasonality:
    m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    m.fit(df)
    future = m.make_future_dataframe(periods=periods, freq='M')
    forecast = m.predict(future)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
