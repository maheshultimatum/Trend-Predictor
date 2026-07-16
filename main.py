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

warnings.filterwarnings("ignore")

PORTFOLIO = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank",
    "DRREDDY.NS": "Dr. Reddy's Labs",
    "TRENT.NS": "Trent Ltd"
}

def get_stock_data(ticker):
    try:
        import yfinance as yf
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        })
        
        df = yf.Ticker(ticker, session=session).history(period="60d", interval="5m")
        if df.empty:
            print(f"Warning: Empty DataFrame returned for {ticker}.")
            return None
            
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
            
        return df
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def add_technical_indicators(df, fast_len, slow_len, rsi_len):
    df = df.copy()
    df['EMA_Fast'] = ta.ema(df['Close'], length=fast_len)
    df['EMA_Slow'] = ta.ema(df['Close'], length=slow_len)
    
    prev_5_vol_max = df['Volume'].shift(1).rolling(window=5).max()
    df['Vol_Confirmed'] = (df['Volume'] > prev_5_vol_max).astype(int)
    
    df['RSI'] = ta.rsi(df['Close'], length=rsi_len)
    df['Dist_to_High'] = df['High'] - df['Close']
    df['Dist_to_Low'] = df['Close'] - df['Low']
    
    return df.dropna()

def optimize_hyperparameters(df):
    fast_ema_options = [3, 5, 7, 9]
    slow_ema_options = [20, 25, 31, 50]
    rsi_options = [10, 14, 21]
    
    best_accuracy = 0
    best_params = {'fast': 5, 'slow': 31, 'rsi': 14}
    
    for fast in fast_ema_options:
        for slow in slow_ema_options:
            if fast >= slow: continue
            for rsi in rsi_options:
                temp_df = add_technical_indicators(df, fast, slow, rsi)
                temp_df['Target'] = np.where(temp_df['Close'].shift(-1) > temp_df['Close'], 1, 0)
                temp_df = temp_df.dropna()
                
                features = ['Close', 'EMA_Fast', 'EMA_Slow', 'RSI', 'Dist_to_High', 'Dist_to_Low', 'Vol_Confirmed']
                X = temp_df[features]
                y = temp_df['Target']
                
                X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, shuffle=False)
                
                model = LogisticRegression(max_iter=500)
                model.fit(X_train, y_train)
                preds = model.predict(X_val)
                acc = accuracy_score(y_val, preds)
                
                if acc > best_accuracy:
                    best_accuracy = acc
                    best_params = {'fast': fast, 'slow': slow, 'rsi': rsi}
                    
    return best_params, best_accuracy

def train_and_predict(df, best_params):
    fast, slow, rsi = best_params['fast'], best_params['slow'], best_params['rsi']
    df = add_technical_indicators(df, fast, slow, rsi)
    
    df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
    train_df = df.dropna()
    
    features = ['Close', 'EMA_Fast', 'EMA_Slow', 'RSI', 'Dist_to_High', 'Dist_to_Low', 'Vol_Confirmed']
    X = train_df[features]
    y = train_df['Target']
    
    final_model = LogisticRegression(max_iter=500)
    final_model.fit(X, y)
    
    todays_data = train_df[features].iloc[[-1]]
    prediction = final_model.predict(todays_data)[0]
    probability = final_model.predict_proba(todays_data)[0]
    confidence = probability[1] if prediction == 1 else probability[0]
    
    return train_df, prediction, confidence

def generate_chart(df, ticker, company_name, params):
    plot_df = df.tail(120)
    
    ema_plots = [
        mpf.make_addplot(plot_df['EMA_Fast'], color='#29b6f6', width=1.0),
        mpf.make_addplot(plot_df['EMA_Slow'], color='#f57c00', width=1.2)
    ]
    
    filename = f"chart_{ticker.replace('.NS', '')}.png"
    
    mpf.plot(plot_df, 
             type='candle', 
             style='yahoo', 
             addplot=ema_plots,
             volume=True,
             title=f"{company_name} | {params['fast']}/{params['slow']} EMA",
             ylabel="Price (INR)",
             ylabel_lower="Volume",
             savefig=dict(fname=filename, dpi=300, bbox_inches='tight'))
    
    return filename

def build_readme(dashboard_data, image_files):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = [
        "# Quantitative Execution Screener\n\n",
        f"**Last Update:** {timestamp}\n\n",
        "---\n\n",
        "| Asset | Price (INR) | Opt. EMAs | Trend | Vol | Strategy Signal | ML Output | Confidence |\n",
        "|---|---|---|---|---|---|---|---|\n"
    ]
    
    for row in dashboard_data:
        lines.append(f"| **{row['name']}** | {row['price']:,.2f} | {row['fast']}/{row['slow']} | {row['trend']} | {row['vol']} | **{row['signal']}** | {row['ml_bias']} | {row['conf']:.2%} |\n")
        
    lines.append("\n---\n\n")
    
    for name, img in image_files.items():
        lines.append(f"![{name} Chart](./{img})\n\n")
        
    with open("README.md", "w", encoding="utf-8") as f:
        f.writelines(lines)

def main():
    dashboard_data = []
    image_files = {}
    
    for ticker, name in PORTFOLIO.items():
        print(f"\n[{name}] Pulling Market Data...")
        df = get_stock_data(ticker)
        
        if df is None:
            continue
            
        print(f"[{name}] Executing Hyperparameter Grid Search...")
        best_params, backtest_acc = optimize_hyperparameters(df)
        
        print(f"[{name}] Training Dynamic Classification Model...")
        df_results, prediction, confidence = train_and_predict(df, best_params)
        
        print(f"[{name}] Rendering Technical Visualizations...")
        chart_filename = generate_chart(df_results, ticker, name, best_params)
        image_files[name] = chart_filename
        
        last_row = df_results.iloc[-1]
        fast, slow = best_params['fast'], best_params['slow']
        
        trend = "UPTREND" if last_row['Close'] > last_row['EMA_Slow'] else "DOWNTREND"
        vol_status = "SPIKE" if last_row['Vol_Confirmed'] else "LOW"
        
        # Core Signal Logic handling specific instruction
        if trend == "UPTREND" and last_row['EMA_Fast'] > last_row['EMA_Slow'] and last_row['Vol_Confirmed']:
            signal = "BUY SETUP"
        elif trend == "DOWNTREND" and last_row['EMA_Fast'] < last_row['EMA_Slow'] and last_row['Vol_Confirmed']:
            signal = "SELL SETUP"
        else:
            signal = "HOLD (Wait for next gap)"
            
        ml_bias = "UP" if prediction == 1 else "DOWN"
        
        dashboard_data.append({
            "name": name,
            "price": last_row['Close'],
            "fast": fast,
            "slow": slow,
            "trend": trend,
            "vol": vol_status,
            "signal": signal,
            "ml_bias": ml_bias,
            "conf": confidence,
            "acc": backtest_acc
        })
        
    print("\nCompiling Master README Screener...")
    build_readme(dashboard_data, image_files)
    print("Multi-Asset Compilation Cleanly Executed!")

if __name__ == "__main__":
    main()
