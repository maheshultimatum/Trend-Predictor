import os
import sys
import datetime
import pandas as pd
import numpy as np
import mplfinance as mpf
import requests
import pandas_ta as ta
from sklearn.linear_model import LinearRegression


def get_stock_data():
    """Pulls 5-minute interval data for NIFTY 50 from Yahoo Finance."""
    try:
        import yfinance as yf
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        })
        
        ticker = yf.Ticker("^NSEI", session=session)
        # Fetching 60 days of data at 5-minute intervals
        df = ticker.history(period="60d", interval="5m")
        
        if df.empty:
            raise ValueError("Yahoo Finance returned an empty DataFrame. Rate limit active.")
            
        # Ensure the index is timezone-aware for mplfinance
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
            
        return df
    except Exception as e:
        print(f"CRITICAL ERROR fetching data from yfinance: {e}")
        sys.exit(1)


def add_technical_indicators(df):
    """Injects Quantitative Finance indicators into the dataset."""
    df = df.copy()
    
    # RSI (Relative Strength Index)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    
    # Distance to Extremes
    df['Dist_to_High'] = df['High'] - df['Close']
    df['Dist_to_Low'] = df['Close'] - df['Low']
    
    # Dynamic Fibonacci Retracement Levels (20-period Swing)
    rolling_high = df['High'].rolling(window=20).max()
    rolling_low = df['Low'].rolling(window=20).min()
    diff = rolling_high - rolling_low
    
    df['Fib_23_6'] = rolling_high - (diff * 0.236)
    df['Fib_38_2'] = rolling_high - (diff * 0.382)
    df['Fib_61_8'] = rolling_high - (diff * 0.618)
    
    return df.dropna()


def train_and_predict(df):
    """Applies an ML model to predict the next 5-minute close."""
    df = add_technical_indicators(df)
    
    # Target is the next 5-minute close
    df['Target'] = df['Close'].shift(-1)
    
    train_df = df.dropna()
    features = ['Close', 'RSI', 'Dist_to_High', 'Dist_to_Low', 'Fib_23_6', 'Fib_38_2', 'Fib_61_8']
    
    X = train_df[features]
    y = train_df['Target']
    
    model = LinearRegression()
    model.fit(X, y)
    
    # FIX: Double brackets retains the column names as a DataFrame to fix the Sklearn warning
    todays_data = df[features].iloc[[-1]]
    predicted_price = model.predict(todays_data)[0]
    
    return df, predicted_price


def update_readme(df, pred_price):
    """Generates a professional, text-focused README dashboard."""
    last_price = df['Close'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    fib_23 = df['Fib_23_6'].iloc[-1]
    
    trend = "BULLISH (UP)" if pred_price > last_price else "BEARISH (DOWN)"
    momentum = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = [
        "# NIFTY 50 Intraday Quant Predictor\n\n",
        "[![Pipeline](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)\n",
        "![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)\n",
        "![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)\n\n",
        "This automated data pipeline predicts intraday market trends for the NIFTY 50 index using Quantitative Finance indicators applied to 5-minute interval data.\n\n",
        "---\n\n",
        "## Market Insight\n",
        f"- Last Updated: {timestamp}\n",
        f"- NIFTY 50 Last Close: {last_price:,.2f}\n",
        f"- Predicted Next 5-Min Close: {pred_price:,.2f}\n",
        f"- Model Bias: **{trend}**\n\n",
        "### Quantitative Signals\n",
        f"- RSI (14-Period): {rsi:.2f} ({momentum})\n",
        f"- Immediate Fibonacci Resistance/Support (23.6%): {fib_23:,.2f}\n\n",
        "### Intraday Chart (Last 150 Intervals)\n",
        "![Stock Trend](./trend_prediction.png)\n\n",
        "---\n\n",
        "## Running it Locally\n\n",
        "```bash\n",
        "git clone [https://github.com/maheshultimatum/Trend-Predictor.git](https://github.com/maheshultimatum/Trend-Predictor.git)\n",
        "cd Trend-Predictor\n",
        "pip install -r requirements.txt\n",
        "python main.py\n",
        "```\n"
    ]
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    print("Fetching NIFTY 5-minute data...")
    df = get_stock_data()
    
    print("Training Quant Model...")
    df_results, predicted_price = train_and_predict(df)
    
    print("Generating Candlestick Chart...")
    # Isolate the last 150 candles for readability
    plot_df = df_results.tail(150)
    
    # Extract latest Fibonacci level
    last_fib = plot_df['Fib_23_6'].iloc[-1]
    
    # Generate candlestick plot
    mpf.plot(plot_df, 
             type='candle', 
             style='yahoo', 
             title="NIFTY 50 (5-Minute Intervals)",
             ylabel="Index Points",
             hlines=dict(hlines=[last_fib], colors=['purple'], linestyle='-.', alpha=0.6),
             savefig=dict(fname='trend_prediction.png', dpi=300, bbox_inches='tight'))
    
    # Update Dashboard
    update_readme(df_results, predicted_price)
    print("Pipeline executed successfully!")


if __name__ == "__main__":
    main()
