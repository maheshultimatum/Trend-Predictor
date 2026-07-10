# NIFTY 50 Intraday Quant Predictor

[![Pipeline](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)

This automated data pipeline predicts intraday market trends for the NIFTY 50 index using Quantitative Finance indicators applied to 5-minute interval data.

---

## Market Insight
- Last Updated: 2026-07-10 12:52:37 UTC
- NIFTY 50 Last Close: 24,211.65
- Predicted Next 5-Min Close: 24,210.96
- Model Bias: **BEARISH (DOWN)**

### Quantitative Signals
- RSI (14-Period): 57.16 (Neutral)
- Immediate Fibonacci Resistance/Support (23.6%): 24,215.28

### Intraday Chart (Last 150 Intervals)
![Stock Trend](./trend_prediction.png)

---

## Running it Locally

```bash
git clone [https://github.com/maheshultimatum/Trend-Predictor.git](https://github.com/maheshultimatum/Trend-Predictor.git)
cd Trend-Predictor
pip install -r requirements.txt
python main.py
```
