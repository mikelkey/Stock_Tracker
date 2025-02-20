import streamlit as st
import yfinance as yf
import pandas as pd
import time
from pushbullet import Pushbullet

# Set up Pushbullet API key (replace with your API key)
PB_API_KEY = 'your_pushbullet_api_key'
pb = Pushbullet(PB_API_KEY)

# Function to fetch stock data
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period='1d', interval='1m')
    return hist

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
                pb.push_note("Stock Alert", alert_message)
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
            pb.push_note("Stock Prediction", prediction_message)
            predictions.append(prediction_message)
    return predictions

# Streamlit UI
st.title('Stock Tracker and Drop Alert')

# User input for stock tickers
tickers = st.text_area('Enter Stock Tickers (comma-separated, e.g., AAPL, TSLA, MSFT):', 'AAPL, TSLA').upper().split(',')

tickers = [ticker.strip() for ticker in tickers]

# User input for drop threshold
threshold = st.number_input('Enter Drop Threshold Percentage:', min_value=1.0, max_value=100.0, value=10.0)

if st.button('Track Stocks'):
    with st.spinner('Fetching data...'):
        for ticker in tickers:
            stock_data = get_stock_data(ticker)
            st.write(f'Latest Data for {ticker}:')
            st.dataframe(stock_data.tail(10))
        
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
