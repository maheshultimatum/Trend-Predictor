import datetime

def generate_readme_template(last_price, pred_price, trend):
    """Returns the formatted markdown string for the README repository file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    return f"""# NIFTY 50 Trend Predictor & Automated Pipeline

[![Pipeline Status](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)

This project is a hands-off, automated data pipeline that predicts short-term market trends for the NIFTY 50 index. Every evening, it pulls the latest daily candle data directly, runs it through a linear regression model to map the current momentum, updates a visualization chart, and pushes the new insights directly to this README.

The whole pipeline runs serverless using GitHub Actions, meaning it requires zero server maintenance or manual intervention to keep updated.

---

## 📊 Daily Market Insight
- **Last Updated:** `{timestamp}`
- **NIFTY 50 Last Close:** `{last_price:,.2f}`
- **Predicted Next Close:** `{pred_price:,.2f}`
- **Model Bias:** **{trend}**

### 📈 Current Trendline Plot
![Stock Trend](./trend_prediction.png)

---

## 🏗️ How It Works

The system is fully automated and executes the following steps Monday through Friday at **9:00 PM IST**:

1. **Data Fetching:** A GitHub Actions workflow spins up a temporary virtual environment and uses `yfinance` to fetch the most recent daily price data for NIFTY. 
2. **Feature Setup:** The script organizes the historical closing prices and creates chronological time indexes to map out recent price velocity.
3. **Model Training:** A simple Scikit-Learn Linear Regression model fits a trendline over the historical data to calculate where the price momentum is leaning for the next trading session.
4. **Auto-Commit:** The script generates an updated chart (`trend_prediction.png`) and rewrites the stats block above. The GitHub Actions bot then commits the updated files directly back to the repository using a `[skip ci]` tag to avoid triggering an infinite build loop.

---

## 🛠️ Tech Stack

- **Language:** Python 3.10
- **Data Source:** Yahoo Finance (`yfinance`)
- **Data Processing:** Pandas & NumPy
- **Machine Learning:** Scikit-Learn (Linear Regression)
- **Plotting:** Matplotlib
- **Automation:** GitHub Actions (scheduled via cron)

---

## ⚙️ Running it Locally

If you want to clone this repository and run the prediction engine manually on your machine:

1. Clone the repository:
   ```bash
   git clone [https://github.com/maheshultimatum/Trend-Predictor.git](https://github.com/maheshultimatum/Trend-Predictor.git)
   cd Trend-Predictor
