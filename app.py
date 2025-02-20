import streamlit as st
import yfinance as yf
import pandas as pd
import time
import os
import requests

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
        stock = yf.Ticker(ticker)
        hist = stock.history(period='2d')
        if len(hist) >= 2:
            prev_close = hist['Close'].iloc[-2]
            curr_close = hist['Close'].iloc[-1]
            drop_percentage = ((prev_close - curr_close) / prev_close) * 100
            if drop_percentage >= threshold:
                alert_message = f'ALERT: {ticker} has dropped {drop_percentage:.2f}% today!'
                send_pushover_alert(alert_message)
                alerts.append(alert_message)
    return alerts

# Function for pattern detection
def detect_pattern(tickers, period, threshold):
    predictions = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        hist['Returns'] = hist['Close'].pct_change() * 100
        predicted_change = hist['Returns'].mean()
        
        if abs(predicted_change) >= threshold:
            direction = 'rise' if predicted_change > 0 else 'fall'
            prediction_message = f'Prediction: {ticker} is likely to {direction} by more than {threshold}% over the next {period}.'
            send_pushover_alert(prediction_message)
            predictions.append(prediction_message)
    return predictions

# Streamlit UI
st.title('Stock Tracker and Drop Alert')

# Default list of top 100 stocks
default_tickers = "AAPL, MSFT, NVDA, AMZN, GOOGL, GOOG, BRK.B, META, TSLA, UNH, XOM, JNJ, V, WMT, LLY, JPM, MA, PG, HD, CVX, MRK, PEP, ABBV, KO, COST, AVGO, MCD, TSM, ORCL, PFE, CRM, NVO, ACN, ABT, SHEL, LIN, AMD, DHR, CMCSA, NKE, MDT, BAC, WFC, T, DIS, BABA, VZ, TXN, SCHW, UPS, PM, BMY, RTX, IBM, QCOM, MS, HON, AMGN, TMUS, UNP, SNY, LOW, SPY, CAT, AZN, CVS, GILD, SBUX, MMM, GE, BLK, INTU, AMT, ISRG, TMO, BKNG, NOW, DE, C, LMT, ADP, ELV, MDLZ, SYK, PGR, CB, ZTS, USB, PLD, CI, EQIX, MMC, MO, NOC, HDB, ADBE, GS, ADI, MUFG, SONY, HCA"

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

# Auto-refresh every 60 seconds
REFRESH_INTERVAL = 60
while True:
    time.sleep(REFRESH_INTERVAL)
    alert_messages = check_drop_alert(tickers, threshold)
    if alert_messages:
        for msg in alert_messages:
            st.error(msg)
