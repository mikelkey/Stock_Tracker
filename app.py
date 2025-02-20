import streamlit as st
import yfinance as yf
import pandas as pd
import time
import os
import requests
import schedule
from datetime import datetime

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
                alerts.append(alert_message)
    return alerts

# Function to send consolidated alerts
def send_consolidated_alerts(tickers, threshold):
    current_time = datetime.now().time()
    if current_time >= datetime.strptime("08:00", "%H:%M").time() and current_time <= datetime.strptime("16:00", "%H:%M").time():
        alert_messages = check_drop_alert(tickers, threshold)
        if alert_messages:
            consolidated_message = "\n".join(alert_messages)
            send_pushover_alert(consolidated_message)

# Function to detect patterns in stock data
def detect_pattern(tickers, period, predict_threshold):
    prediction_messages = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if len(hist) > 1:
            change_percentage = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
            if abs(change_percentage) >= predict_threshold:
                direction = "increased" if change_percentage > 0 else "decreased"
                prediction_message = f'{ticker} has {direction} by {change_percentage:.2f}% over the period {period}.'
                prediction_messages.append(prediction_message)
    return prediction_messages

# Streamlit UI
st.title('Stock Tracker and Drop Alert')

# Default list of top 100 stocks
default_tickers = "AAPL, MSFT, NVDA, AMZN, GOOGL, GOOG, BRK.B, META, TSLA, UNH, XOM, JNJ, V, WMT, LLY, JPM, MA, PG, HD, CVX, MRK, PEP, ABBV, KO, COST, AVGO, MCD, TSM, ORCL, PFE, CRM, NVO, ACN, ABT"

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

# Schedule the task every 30 minutes within the specified hours
schedule.every(30).minutes.do(send_consolidated_alerts, tickers=tickers, threshold=threshold)

# Schedule start and stop times
def start_app():
    while True:
        schedule.run_pending()
        time.sleep(1)

def stop_app():
    os._exit(0)

# Start the app at 8am CT (14:00 UTC) Monday to Friday
schedule.every().monday.at("14:00").do(start_app)
schedule.every().tuesday.at("14:00").do(start_app)
schedule.every().wednesday.at("14:00").do(start_app)
schedule.every().thursday.at("14:00").do(start_app)
schedule.every().friday.at("14:00").do(start_app)

# Stop the app at 4pm CT (22:00 UTC) Monday to Friday
schedule.every().monday.at("23:00").do(stop_app)
schedule.every().tuesday.at("23:00").do(stop_app)
schedule.every().wednesday.at("23:00").do(stop_app)
schedule.every().thursday.at("23:00").do(stop_app)
schedule.every().friday.at("23:00").do(stop_app)

while True:
    schedule.run_pending()
    time.sleep(1)
