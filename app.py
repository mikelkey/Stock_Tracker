import streamlit as st
import yfinance as yf
import pandas as pd
import time
import os
import requests
import schedule

# Set up Pushover API (replace with your credentials or store in Streamlit Secrets)
PUSHOVER_API_TOKEN = st.secrets["PUSHOVER_API_TOKEN"]
PUSHOVER_USER_KEY = st.secrets["PUSHOVER_USER_KEY"]

# Function to send Pushover alerts
def send_pushover_alert(message):
    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message
    }
    requests.post(url, data=payload)

# Function to check for drop alert
def check_drop_alert(tickers, threshold):
    alerts = []
    for ticker in tickers:
        stock = yf.TTicker(ticker)
        hist = stock.history(period='2d')
        if len(hist) >= 2:
            prev_close = hist['Close'].iloc[-2]
            curr_close = hist['Close'].iloc[-1]
            drop_percentage = ((prev_close - curr_close) / prev_close) * 100
            if drop_percentage >= threshold:
                alert_message = f'ALERT: {ticker} has dropped {drop_percentage:.2f}% today!'
                alerts.append(alert_message)
    return alerts

# Function to send consolidated alerts
def send_consolidated_alerts(tickers, threshold):
    alert_messages = check_drop_alert(tickers, threshold)
    if alert_messages:
        consolidated_message = "\n".join(alert_messages)
        send_pushover_alert(consolidated_message)

# Streamlit UI
st.title('Stock Tracker and Drop Alert')

# Default list of top 100 stocks
default_tickers = "AAPL, MSFT, NVDA, AMZN, GOOGL, GOOG, BRK.B, META, TSLA, UNH, XOM, JNJ, V, WMT, LLY, JPM, MA, PG, HD, CVX, MRK, PEP, ABBV, KO, COST, AVGO, MCD, TSM, ORCL, PFE, CRM, NVO, ACN, ABT, SH...

# User input for stock tickers
tickers = st.text_area('Enter Stock Tickers (comma-separated, e.g., AAPL, TSLA, MSFT):', default_tickers).upper().split(',')

tickers = [ticker.strip() for ticker in tickers]

# User input for drop threshold
threshold = st.number_input('Enter Drop Threshold Percentage:', min_value=1.0, max_value=100.0, value=10.0)

if st.button('Track Stocks'):
    with st.spinner('Fetching data...'):
        alert_messages = check_drop_alert(tickers, threshold)
        if alert_messages:
            for msg in alert_messages:
                st.error(msg)
        else:
            st.success('No stocks have dropped more than the threshold today.')

# Pattern detection section
st.header('Pattern Detection')
period = st.selectbox('Select Period for Prediction:', ['1d', '1wk', '1mo'])
predict_threshold = st.number_input('Enter Prediction Threshold Percentage:', min_value=1.0, max_value=100.0, value=5.0)

if st.button('Predict Stock Movements'):
    with st.spinner('Analyzing patterns...'):
        prediction_messages = detect_pattern(tickers, period, predict_threshold)
        for msg in prediction_messages:
            st.write(msg)

# Schedule the task every 30 minutes
schedule.every(30).minutes.do(send_consolidated_alerts, tickers=tickers, threshold=threshold)

while True:
    schedule.run_pending()
    time.sleep(1)
