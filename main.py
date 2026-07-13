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
        df = ticker.history(period="60d", interval="5m")
        
        if df.empty:
            raise ValueError("Yahoo Finance returned an empty DataFrame. Rate limit active.")
            
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
            
        return df
    except Exception as e:
        print(f"CRITICAL ERROR fetching data from yfinance: {e}")
        sys.exit(1)


def add_technical_indicators(df):
    """Injects 31 & 5 EMA Strategy parameters with fib and RSI."""
    df = df.copy()
    
    # Core Strategy Indicators
    df['EMA_5'] = ta.ema(df['Close'], length=5)
    df['EMA_31'] = ta.ema(df['Close'], length=31)
    
    # Strategy Rule: Check if current volume is greater than previous 5 candles max
    prev_5_vol_max = df['Volume'].shift(1).rolling(window=5).max()
    df['Vol_Confirmed'] = df['Volume'] > prev_5_vol_max
    
    # Legacy Quant Features for Model Richness
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['Dist_to_High'] = df['High'] - df['Close']
    df['Dist_to_Low'] = df['Close'] - df['Low']
    
    rolling_high = df['High'].rolling(window=20).max()
    rolling_low = df['Low'].rolling(window=20).min()
    diff = rolling_high - rolling_low
    df['Fib_23_6'] = rolling_high - (diff * 0.236)
    
    return df.dropna()


def train_and_predict(df):
    """Trains the ML engine using core EMA strategy spacing and price metrics."""
    df = add_technical_indicators(df)
    df['Target'] = df['Close'].shift(-1)
    
    train_df = df.dropna()
    features = ['Close', 'EMA_5', 'EMA_31', 'RSI', 'Dist_to_High', 'Dist_to_Low', 'Fib_23_6']
    
    X = train_df[features]
    y = train_df['Target']
    
    model = LinearRegression()
    model.fit(X, y)
    
    todays_data = df[features].iloc[[-1]]
    predicted_price = model.predict(todays_data)[0]
    
    return df, predicted_price


def update_readme(df, pred_price):
    """Generates an enterprise-grade dashboard verifying the 31 & 5 EMA rule set."""
    last_row = df.iloc[-1]
    
    last_price = last_row['Close']
    ema_5 = last_row['EMA_5']
    ema_31 = last_row['EMA_31']
    vol_spike = last_row['Vol_Confirmed']
    rsi = last_row['RSI']
    
    # Strategy Rule Engine Evaluations
    macro_trend = "UPTREND" if last_price > ema_31 else "DOWNTREND"
    ema_alignment = "BULLISH (5 EMA > 31 EMA)" if ema_5 > ema_31 else "BEARISH (5 EMA < 31 EMA)"
    volume_status = "CONFIRMED SPIKE" if vol_spike else "NORMAL / LOW"
    
    # Final Action Recommendation
    if macro_trend == "UPTREND" and ema_5 > ema_31 and vol_spike:
        strategy_signal = "STRATEGY BUY SIGNAL CONFIRMED (Look for structural break)"
    elif macro_trend == "DOWNTREND" and ema_5 < ema_31 and vol_spike:
        strategy_signal = "STRATEGY SELL SIGNAL CONFIRMED (Look for structural break)"
    else:
        strategy_signal = "NO SIGNAL / HOLD (Awaiting execution setup)"
        
    ml_bias = "BULLISH (UP)" if pred_price > last_price else "BEARISH (DOWN)"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = [
        "# NIFTY 50 Intraday Quant & Strategy Engine\n\n",
        "[![Pipeline](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)\n",
        "![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)\n",
        "![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)\n\n",
        "This pipeline automates an intraday technical framework running a 31 & 5 EMA strategy verified by rolling volume checks and linear model parameters.\n\n",
        "---\n\n",
        "## Core Execution Status\n",
        f"- Last Engine Run: {timestamp}\n",
        f"- NIFTY 50 Current Index: {last_price:,.2f}\n",
        f"- Model Target Prediction (Next 5-Min): {pred_price:,.2f}\n",
        f"- Machine Learning Bias: **{ml_bias}**\n\n",
        "## 31 & 5 EMA Execution Signals\n",
        f"- Trend Rule (Price vs 31 EMA): **{macro_trend}**\n",
        f"- Ribbon Alignment (5 EMA vs 31 EMA): **{ema_alignment}**\n",
        f"- Volume Rule (Current vs Past 5 Candles): **{volume_status}**\n",
        f"- Algorithmic Output: **{strategy_signal}**\n\n",
        "### Secondary Micro Metrics\n",
        f"- RSI (14-Period): {rsi:.2f}\n",
        f"- Fast Exponential Moving Average (5 EMA): {ema_5:,.2f}\n",
        f"- Slow Exponential Moving Average (31 EMA): {ema_31:,.2f}\n\n",
        "### Live Intraday Chart Architecture\n",
        "![Stock Trend](./trend_prediction.png)\n\n",
        "---\n\n",
        "## Technical Parameters\n\n",
        "```text\n",
        "Timeframe: 5-Minute Candle Bars\n",
        "Primary Overlays: 5 EMA (Blue Track), 31 EMA (Orange Track)\n",
        "Secondary Indicators: Underlaid Volume Bars\n",
        "```\n"
    ]
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    print("Fetching NIFTY 5-minute data...")
    df = get_stock_data()
    
    print("Executing Feature Matrix & Strategy Models...")
    df_results, predicted_price = train_and_predict(df)
    
    print("Compiling Production Candlestick Visualizations...")
    plot_df = df_results.tail(120)  # Isolating 120 candles (~1-2 trading sessions) for clean scaling
    
    # Formulate overlay properties for the 5 and 31 EMA tracks
    ema_plots = [
        mpf.make_addplot(plot_df['EMA_5'], color='#29b6f6', width=1.0),   # Cyan/Blue line for fast tracking
        mpf.make_addplot(plot_df['EMA_31'], color='#f57c00', width=1.2)  # Amber/Orange line for slow tracking
    ]
    
    # Execute the chart rendering block complete with a volume subplot panel
    mpf.plot(plot_df, 
             type='candle', 
             style='yahoo', 
             addplot=ema_plots,
             volume=True,
             title="NIFTY 50 Intraday Execution Panel (5m)",
             ylabel="Index Points",
             ylabel_lower="Volume Traded",
             savefig=dict(fname='trend_prediction.png', dpi=300, bbox_inches='tight'))
    
    print("Pushing data metrics to dashboard profile...")
    update_readme(df_results, predicted_price)
    print("Pipeline compilation executed cleanly!")


if __name__ == "__main__":
    main()
