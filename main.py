import os
import sys
import datetime
import pandas as pd
import numpy as np
import mplfinance as mpf
import requests
import pandas_ta as ta
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import warnings

# Suppress Sklearn warnings for clean CI/CD logs
warnings.filterwarnings("ignore")

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
            raise ValueError("Yahoo Finance returned an empty DataFrame.")
            
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
            
        return df
    except Exception as e:
        print(f"CRITICAL ERROR fetching data: {e}")
        sys.exit(1)


def add_technical_indicators(df, fast_len, slow_len, rsi_len):
    """Injects dynamic indicators based on optimizer loop inputs."""
    df = df.copy()
    
    # Dynamic Moving Averages
    df['EMA_Fast'] = ta.ema(df['Close'], length=fast_len)
    df['EMA_Slow'] = ta.ema(df['Close'], length=slow_len)
    
    # Volume Confirmation (Rolling max of previous 5 candles)
    prev_5_vol_max = df['Volume'].shift(1).rolling(window=5).max()
    df['Vol_Confirmed'] = (df['Volume'] > prev_5_vol_max).astype(int)
    
    # Dynamic RSI
    df['RSI'] = ta.rsi(df['Close'], length=rsi_len)
    
    # Volatility Metrics
    df['Dist_to_High'] = df['High'] - df['Close']
    df['Dist_to_Low'] = df['Close'] - df['Low']
    
    return df.dropna()


def optimize_hyperparameters(df):
    """Loop Engineering Task: Grid Search for the best timeframes using Logistic Regression."""
    print("Initiating Grid Search Optimization Loop...")
    
    # Define the hyperparameter search space
    fast_ema_options = [3, 5, 7, 9]
    slow_ema_options = [20, 25, 31, 50]
    rsi_options = [10, 14, 21]
    
    best_accuracy = 0
    best_params = {'fast': 5, 'slow': 31, 'rsi': 14} # Default fallback
    
    # Nested loop to test all combinations
    for fast in fast_ema_options:
        for slow in slow_ema_options:
            if fast >= slow:
                continue # Fast EMA must be strictly less than Slow EMA
                
            for rsi in rsi_options:
                temp_df = add_technical_indicators(df, fast, slow, rsi)
                
                # Target: 1 if next close is strictly higher than current close, else 0
                temp_df['Target'] = np.where(temp_df['Close'].shift(-1) > temp_df['Close'], 1, 0)
                temp_df = temp_df.dropna()
                
                features = ['Close', 'EMA_Fast', 'EMA_Slow', 'RSI', 'Dist_to_High', 'Dist_to_Low', 'Vol_Confirmed']
                X = temp_df[features]
                y = temp_df['Target']
                
                # Split data to validate properly and avoid overfitting
                X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, shuffle=False)
                
                model = LogisticRegression(max_iter=500)
                model.fit(X_train, y_train)
                
                preds = model.predict(X_val)
                acc = accuracy_score(y_val, preds)
                
                if acc > best_accuracy:
                    best_accuracy = acc
                    best_params = {'fast': fast, 'slow': slow, 'rsi': rsi}
                    
    print(f"Optimization Complete. Best Accuracy: {best_accuracy:.2%}")
    print(f"Optimal Parameters: Fast EMA: {best_params['fast']}, Slow EMA: {best_params['slow']}, RSI: {best_params['rsi']}")
    
    return best_params, best_accuracy


def train_and_predict(df, best_params):
    """Trains final Logistic Regression model on entire dataset using optimized parameters."""
    fast, slow, rsi = best_params['fast'], best_params['slow'], best_params['rsi']
    df = add_technical_indicators(df, fast, slow, rsi)
    
    # Target definition for classification
    df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
    train_df = df.dropna()
    
    features = ['Close', 'EMA_Fast', 'EMA_Slow', 'RSI', 'Dist_to_High', 'Dist_to_Low', 'Vol_Confirmed']
    X = train_df[features]
    y = train_df['Target']
    
    # Train final model on 100% of available data
    final_model = LogisticRegression(max_iter=500)
    final_model.fit(X, y)
    
    # Predict the next unclosed interval
    todays_data = train_df[features].iloc[[-1]]
    prediction = final_model.predict(todays_data)[0]
    probability = final_model.predict_proba(todays_data)[0]
    
    # probability[1] is the confidence of an UP move, probability[0] is DOWN
    confidence = probability[1] if prediction == 1 else probability[0]
    
    return train_df, prediction, confidence


def update_readme(df, prediction, confidence, params, accuracy):
    """Generates the README incorporating Dynamic Classification Metrics."""
    last_row = df.iloc[-1]
    
    last_price = last_row['Close']
    ema_fast = last_row['EMA_Fast']
    ema_slow = last_row['EMA_Slow']
    vol_spike = bool(last_row['Vol_Confirmed'])
    rsi = last_row['RSI']
    
    macro_trend = "UPTREND" if last_price > ema_slow else "DOWNTREND"
    ema_alignment = f"BULLISH ({params['fast']} EMA > {params['slow']} EMA)" if ema_fast > ema_slow else f"BEARISH ({params['fast']} EMA < {params['slow']} EMA)"
    volume_status = "CONFIRMED SPIKE" if vol_spike else "NORMAL / LOW"
    
    # Rule evaluation based on dynamically selected EMAs
    if macro_trend == "UPTREND" and ema_fast > ema_slow and vol_spike:
        strategy_signal = "STRATEGY BUY SIGNAL CONFIRMED"
    elif macro_trend == "DOWNTREND" and ema_fast < ema_slow and vol_spike:
        strategy_signal = "STRATEGY SELL SIGNAL CONFIRMED"
    else:
        strategy_signal = "NO SIGNAL / HOLD (Awaiting setup)"
        
    ml_bias = "BULLISH (UP)" if prediction == 1 else "BEARISH (DOWN)"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = [
        "# NIFTY 50 Intraday Auto-Optimizing Pipeline\n\n",
        "[![Pipeline](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)\n",
        "![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)\n",
        "![Scikit-Learn Logistic Regression](https://img.shields.io/badge/ML-Logistic_Regression-orange.svg)\n\n",
        "This system executes a dynamic grid search to find the optimal exponential moving averages for the current market state, passing those weights into a Logistic Regression classification model for intraday forecasting.\n\n",
        "---\n\n",
        "## Logistic Regression Output\n",
        f"- Last Engine Run: {timestamp}\n",
        f"- NIFTY 50 Current Index: {last_price:,.2f}\n",
        f"- Historical Model Accuracy (Backtest): **{accuracy:.2%}**\n",
        f"- Directional Prediction (Next 5-Min): **{ml_bias}**\n",
        f"- Model Confidence: {confidence:.2%}\n\n",
        "## Dynamic Algorithmic Execution\n",
        f"- Loop Selected Timeframes: Fast EMA: **{params['fast']}** | Slow EMA: **{params['slow']}** | RSI: **{params['rsi']}**\n",
        f"- Trend Rule (Price vs Slow EMA): **{macro_trend}**\n",
        f"- Ribbon Alignment: **{ema_alignment}**\n",
        f"- Volume Rule (Current vs Past 5 Candles): **{volume_status}**\n",
        f"- Active Signal Status: **{strategy_signal}**\n\n",
        "### Live Execution Chart\n",
        "![Stock Trend](./trend_prediction.png)\n\n"
    ]
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    print("Fetching NIFTY 5-minute data...")
    df = get_stock_data()
    
    # 1. Loop Engineering Task
    best_params, backtest_accuracy = optimize_hyperparameters(df)
    
    # 2. Train Logistic Regression with Optimal Weights
    print("Executing Logistic Classification...")
    df_results, predicted_direction, prediction_confidence = train_and_predict(df, best_params)
    
    print("Compiling Visualization...")
    plot_df = df_results.tail(120) 
    
    ema_plots = [
        mpf.make_addplot(plot_df['EMA_Fast'], color='#29b6f6', width=1.0),
        mpf.make_addplot(plot_df['EMA_Slow'], color='#f57c00', width=1.2)
    ]
    
    mpf.plot(plot_df, 
             type='candle', 
             style='yahoo', 
             addplot=ema_plots,
             volume=True,
             title=f"NIFTY 50 Intraday - Opt. {best_params['fast']}/{best_params['slow']} EMA Strategy",
             ylabel="Index Points",
             ylabel_lower="Volume",
             savefig=dict(fname='trend_prediction.png', dpi=300, bbox_inches='tight'))
    
    print("Pushing updated telemetry to dashboard...")
    update_readme(df_results, predicted_direction, prediction_confidence, best_params, backtest_accuracy)
    print("Pipeline compilation executed cleanly!")


if __name__ == "__main__":
    main()
