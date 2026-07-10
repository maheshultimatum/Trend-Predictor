import os
import sys
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import pandas_ta as ta
from sklearn.linear_model import LinearRegression


def get_stock_data():
    """Pulls historical daily data for NIFTY 50 from Yahoo Finance."""
    try:
        import yfinance as yf
        # Browser disguise to bypass Yahoo Finance bot blocking
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        })
        
        ticker = yf.Ticker("^NSEI", session=session)
        df = ticker.history(period="6mo")
        
        if df.empty:
            raise ValueError("Yahoo Finance returned an empty DataFrame. Rate limit active.")
            
        df = df.rename(columns={'Close': 'close'})
        return df
    except Exception as e:
        print(f"CRITICAL ERROR fetching data from yfinance: {e}")
        sys.exit(1)


def add_technical_indicators(df):
    """Injects Quantitative Finance indicators into the dataset."""
    df = df.copy()
    
    # RSI (Relative Strength Index)
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    # Distance to Daily Extremes
    df['Dist_to_High'] = df['High'] - df['close']
    df['Dist_to_Low'] = df['close'] - df['Low']
    
    # Dynamic Fibonacci Retracement Levels (20-Day Swing)
    rolling_high = df['High'].rolling(window=20).max()
    rolling_low = df['Low'].rolling(window=20).min()
    diff = rolling_high - rolling_low
    
    df['Fib_23_6'] = rolling_high - (diff * 0.236)
    df['Fib_38_2'] = rolling_high - (diff * 0.382)
    df['Fib_61_8'] = rolling_high - (diff * 0.618)
    
    return df.dropna()


def train_and_predict(df):
    """Applies a simple ML model using quantitative features to predict tomorrow's close."""
    df = add_technical_indicators(df)
    df['Target'] = df['close'].shift(-1)
    
    train_df = df.dropna()
    features = ['close', 'RSI', 'Dist_to_High', 'Dist_to_Low', 'Fib_23_6', 'Fib_38_2', 'Fib_61_8']
    
    X = train_df[features]
    y = train_df['Target']
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict tomorrow using TODAY's technical indicators
    todays_data = df[features].iloc[-1].values.reshape(1, -1)
    predicted_price = model.predict(todays_data)[0]
    
    # Fit a simple time-series line just for the chart visualization
    plot_model = LinearRegression()
    plot_model.fit(np.arange(len(df)).reshape(-1, 1), df['close'])
    df['Trendline'] = plot_model.predict(np.arange(len(df)).reshape(-1, 1))
    
    return df, predicted_price


def update_readme(df, pred_price):
    """Generates the README showing off both basic prices and quant signals."""
    last_price = df['close'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    fib_23 = df['Fib_23_6'].iloc[-1]
    
    trend = "🚀 BULLISH (UP)" if pred_price > last_price else "📉 BEARISH (DOWN)"
    momentum = "🔥 Overbought" if rsi > 70 else "🧊 Oversold" if rsi < 30 else "⚖️ Neutral"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = [
        "# NIFTY 50 Quant Predictor & Automated Pipeline\n\n",
        "[![Pipeline](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)\n",
        "![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)\n",
        "![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)\n\n",
        "This project is a hands-off, automated data pipeline that predicts short-term market trends for the NIFTY 50 index using Quantitative Finance indicators (RSI, Fibonacci, Volatility). It updates daily via GitHub Actions.\n\n",
        "---\n\n",
        "## 📊 Daily Market Insight\n",
        f"- **Last Updated:** {timestamp}\n",
        f"- **NIFTY 50 Last Close:** {last_price:,.2f}\n",
        f"- **Predicted Next Close:** {pred_price:,.2f}\n",
        f"- **Model Bias:** **{trend}**\n\n",
        "### 🔬 Quantitative Signals\n",
        f"- **RSI (14-Day):** {rsi:.2f} ({momentum})\n",
        f"- **Immediate Fibonacci Resistance/Support (23.6%):** {fib_23:,.2f}\n\n",
        "### 📈 Current Trendline Plot\n",
        "![Stock Trend](./trend_prediction.png)\n\n",
        "---\n\n",
        "## ⚙️ Running it Locally\n\n",
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
    print("Fetching NIFTY data...")
    df = get_stock_data()
    
    print("Training Quant Model...")
    df_results, predicted_price = train_and_predict(df)
    
    # Plotting
    plt.figure(figsize=(10, 5))
    plt.plot(df_results.index, df_results['close'], label='NIFTY Actual Close', color='teal', linewidth=2)
    plt.plot(df_results.index, df_results['Trendline'], label='ML Trendline', color='orange', linestyle='--')
    
    # Overlay the Fibonacci level
    last_fib = df_results['Fib_23_6'].iloc[-1]
    plt.axhline(y=last_fib, color='purple', linestyle=':', alpha=0.6, label='Fib 23.6% Level')
    
    plt.title("NSE: NIFTY Price with Quant Features")
    plt.xlabel("Date")
    plt.ylabel("Index Points")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('trend_prediction.png')
    plt.close()
    
    # Update Dashboard
    update_readme(df_results, predicted_price)
    print("Pipeline executed successfully!")


if __name__ == "__main__":
    main()
