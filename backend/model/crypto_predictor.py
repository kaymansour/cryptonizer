
import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

base_days = 100
future_days = 10

def predict_crypto(symbol: str):
    end = datetime.now()
    start = datetime(end.year - 5, end.month, end.day)

    data = yf.download(symbol, start=start, end=end)
    if data.empty:
        raise ValueError("No data available")

    closing_price = data[['Close']].dropna()
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(closing_price)

    x = []
    y = []
    for i in range(base_days, len(scaled)):
        x.append(scaled[i-base_days:i])
        y.append(scaled[i])
    x = np.array(x)
    y = np.array(y)

    x = x.reshape(x.shape[0], x.shape[1], 1)
    train_size = int(len(x) * 0.9)
    x_train, y_train = x[:train_size], y[:train_size]
    x_test, y_test = x[train_size:], y[train_size:]

    model = load_model(f"{symbol}_crypto_predictor.h5")

    preds = model.predict(x_test)
    inv_preds = scaler.inverse_transform(preds)
    inv_actual = scaler.inverse_transform(y_test)

    plotting_data = {
        "dates": closing_price.index[train_size + base_days:].strftime("%Y-%m-%d").tolist(),
        "actual": inv_actual.flatten().tolist(),
        "predicted": inv_preds.flatten().tolist()
    }

    # Future forecast
    last_100 = scaled[-100:].reshape(1, -1, 1)
    future_preds = []
    for _ in range(future_days):
        pred = model.predict(last_100, verbose=0)
        val = scaler.inverse_transform(pred)[0][0]
        future_preds.append(val)
        last_100 = np.append(last_100[:, 1:, :], pred.reshape(1, 1, -1), axis=1)

    future = {
        "days": list(range(1, 11)),
        "prices": [round(p, 2) for p in future_preds],
        "trend": "increase" if future_preds[-1] > future_preds[0] else "decrease"
    }

    return {
        "history": plotting_data,
        "future": future,
    }
