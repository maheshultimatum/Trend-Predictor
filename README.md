# NIFTY 50 Intraday Quant & Strategy Engine

[![Pipeline](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml/badge.svg)](https://github.com/maheshultimatum/Trend-Predictor/actions/workflows/pipeline.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)

This pipeline automates an intraday technical framework running a 31 & 5 EMA strategy verified by rolling volume checks and linear model parameters.

---

## Core Execution Status
- Last Engine Run: 2026-07-17 06:04:07 UTC
- NIFTY 50 Current Index: 24,248.80
- Model Target Prediction (Next 5-Min): 24,248.25
- Machine Learning Bias: **BEARISH (DOWN)**

## 31 & 5 EMA Execution Signals
- Trend Rule (Price vs 31 EMA): **UPTREND**
- Ribbon Alignment (5 EMA vs 31 EMA): **BULLISH (5 EMA > 31 EMA)**
- Volume Rule (Current vs Past 5 Candles): **NORMAL / LOW**
- Algorithmic Output: **NO SIGNAL / HOLD (Awaiting execution setup)**

### Secondary Micro Metrics
- RSI (14-Period): 58.49
- Fast Exponential Moving Average (5 EMA): 24,246.31
- Slow Exponential Moving Average (31 EMA): 24,221.08

### Live Intraday Chart Architecture
![Stock Trend](./trend_prediction.png)

---

## Technical Parameters

```text
Timeframe: 5-Minute Candle Bars
Primary Overlays: 5 EMA (Blue Track), 31 EMA (Orange Track)
Secondary Indicators: Underlaid Volume Bars
```
