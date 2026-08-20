# NIFTY 50 Intraday Quant & Strategy Engine

[![Pipeline](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)

This pipeline automates an intraday technical framework running a 31 & 5 EMA strategy verified by rolling volume checks and linear model parameters.

---

## Core Execution Status
- Last Engine Run: 2026-08-20 04:37:29 UTC
- NIFTY 50 Current Index: 24,209.30
- Model Target Prediction (Next 5-Min): 24,209.93
- Machine Learning Bias: **BULLISH (UP)**

## 31 & 5 EMA Execution Signals
- Trend Rule (Price vs 31 EMA): **UPTREND**
- Ribbon Alignment (5 EMA vs 31 EMA): **BULLISH (5 EMA > 31 EMA)**
- Volume Rule (Current vs Past 5 Candles): **NORMAL / LOW**
- Algorithmic Output: **NO SIGNAL / HOLD (Awaiting execution setup)**

### Secondary Micro Metrics
- RSI (14-Period): 79.86
- Fast Exponential Moving Average (5 EMA): 24,203.94
- Slow Exponential Moving Average (31 EMA): 24,127.89

### Live Intraday Chart Architecture
![Stock Trend](./trend_prediction.png)

---

## Technical Parameters

```text
Timeframe: 5-Minute Candle Bars
Primary Overlays: 5 EMA (Blue Track), 31 EMA (Orange Track)
Secondary Indicators: Underlaid Volume Bars
```
