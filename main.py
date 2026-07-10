import os
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import subprocess
import sys

# --- EMERGENCY BOOTSTRAP FOR CI RUNNERS ---
try:
    import pandas_ta as ta
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas-ta"])
    import pandas_ta as ta
    
try:
    import yfinance as yf
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
    import yfinance as yf

try:
    from sklearn.linear_model import LinearRegression
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"])
    from sklearn.linear_model import LinearRegression


def get_stock_data():
    """Pulls historical daily data for NIFTY 50 from Yahoo Finance using a browser disguise."""
    try:
        import requests
        
        # Create a custom session to bypass basic bot-blocking
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        })
        
        # Pass the disguised session into yfinance
        ticker = yf.Ticker("^NSEI", session=session)
        
        # FIX: Changed "6m" to "6mo" (6 months)
        df = ticker.history(period="6mo")
        
        if df.empty:
            raise ValueError("Yahoo Finance returned an empty DataFrame. Rate limit still active.")
            
        df = df.rename(columns={'Close': 'close'})
        return df.tail(100)
        
    except Exception as e:
        print(f"CRITICAL ERROR fetching data from yfinance: {e}")
        print("Stopping pipeline to prevent logging fake/stale data.")
        sys.exit(1)

def add_technical_indicators(df):
    """Injects Quantitative Finance indicators into the dataset."""
    df = df.copy()
    
    # 1. RSI (Relative Strength Index) - 14 Day Period
    # Measures momentum. Over 70 = Overbought, Under 30 = Oversold
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    # 2. Distance to Daily Extremes
    # Helps the model understand if the price is closing near the day's high or low
    df['Dist_to_High'] = df['High'] - df['close']
    df['Dist_to_Low'] = df['close'] - df['Low']
    
    # 3. Dynamic Fibonacci Retracement Levels (20-Day Swing)
    # Calculates support and resistance based on recent market swings
    rolling_high = df['High'].rolling(window=20).max()
    rolling_low = df['Low'].rolling(window=20).min()
    diff = rolling_high - rolling_low
    
    df['Fib_23_6'] = rolling_high - (diff * 0.236)
    df['Fib_38_2'] = rolling_high - (diff * 0.382)
    df['Fib_61_8'] = rolling_high - (diff * 0.618)
    
    # Drop the first 20 days since our moving averages/rolling windows need time to calculate
    df = df.dropna()
    
    return df

def train_and_predict(df):
    """Applies a simple ML model using quantitative features to predict tomorrow's close."""
    # First, run the data through our new Quant Engine
    df = add_technical_indicators(df)
    
    # The target we are trying to predict is STILL tomorrow's price
    df['Target'] = df['close'].shift(-1)
    
    # Create our training dataset
    train_df = df.dropna()
    
    # FEATURE SELECTION: The model now looks at RSI, Fibonacci, and Daily High/Lows!
    features = ['close', 'RSI', 'Dist_to_High', 'Dist_to_Low', 'Fib_23_6', 'Fib_38_2', 'Fib_61_8']
    
    X = train_df[features]
    y = train_df['Target']
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict tomorrow using TODAY's technical indicators
    todays_data = df[features].iloc[-1].values.reshape(1, -1)
    predicted_price = model.predict(todays_data)[0]
    
    # For the chart, we still want a visual trendline, so we'll fit a separate basic line just for plotting
    plot_model = LinearRegression()
    plot_model.fit(np.arange(len(df)).reshape(-1, 1), df['close'])
    df['Trendline'] = plot_model.predict(np.arange(len(df)).reshape(-1, 1))
    
    return df, predicted_price


def update_readme(last_price, pred_price):
    """Generates the README using a list of strings to prevent web-editor syntax errors."""
    trend = "🚀 BULLISH (UP)" if pred_price > last_price else "📉 BEARISH (DOWN)"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = [
        "# NIFTY 50 Trend Predictor & Automated Pipeline\n\n",
        "[![Pipeline](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)\n",
        "![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)\n",
        "![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)\n\n",
        "This project is a hands-off, automated data pipeline that predicts short-term market trends for the NIFTY 50 index. It updates daily via GitHub Actions.\n\n",
        "---\n\n",
        "## 📊 Daily Market Insight\n",
        f"- **Last Updated:** {timestamp}\n",
        f"- **NIFTY 50 Last Close:** {last_price:,.2f}\n",
        f"- **Predicted Next Close:** {pred_price:,.2f}\n",
        f"- **Model Bias:** **{trend}**\n\n",
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
    
    print("Training Model...")
    df_results, predicted_price = train_and_predict(df)
    last_actual_price = df['close'].iloc[-1]
    
    print(f"Last Price: {last_actual_price:.2f} -> Predicted Next Close: {predicted_price:.2f}")
    
    # Generate and save the visualization
    plt.figure(figsize=(10, 5))
    plt.plot(df.index, df['close'], label='NIFTY Actual Close', color='teal', linewidth=2)
    plt.plot(df.index, df_results['Trendline'], label='ML Trendline', color='orange', linestyle='--')
    plt.title("NSE: NIFTY Price & Linear Regression Trendline")
    plt.xlabel("Date")
    plt.ylabel("Index Points")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('trend_prediction.png')
    plt.close()
    
    # Update Dashboard
    update_readme(last_actual_price, predicted_price)
    print("Pipeline executed successfully!")


if __name__ == "__main__":
    main()
