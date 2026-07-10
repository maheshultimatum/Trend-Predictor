# NIFTY 50 Quant Predictor & Automated Pipeline

[![Pipeline](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)

This project is a hands-off, automated data pipeline that predicts short-term market trends for the NIFTY 50 index using Quantitative Finance indicators (RSI, Fibonacci, Volatility). It updates daily via GitHub Actions.

---

## Daily Market Insight
- **Last Updated:** 2026-07-10 12:41:39 UTC
- **NIFTY 50 Last Close:** 24,206.90
- **Predicted Next Close:** 24,097.93
- **Model Bias:** **BEARISH (DOWN)**

### Quantitative Signals
- **RSI (14-Day):** 55.80 (Neutral)
- **Immediate Fibonacci Resistance/Support (23.6%):** 24,243.69

### Current Trendline Plot
![Stock Trend](./trend_prediction.png)

---

## Running it Locally

```bash
git clone [https://github.com/maheshultimatum/Trend-Predictor.git](https://github.com/maheshultimatum/Trend-Predictor.git)
cd Trend-Predictor
pip install -r requirements.txt
python main.py
```
