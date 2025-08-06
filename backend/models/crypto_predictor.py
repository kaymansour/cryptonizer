import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime
from keras.models import Sequential
from keras.layers import Dense, LSTM
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import io
import base64

def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def predict_crypto(symbol: str):
    end = datetime.now()
    start = datetime(end.year - 5, end.month, end.day)

    stock_data = yf.download(f"{symbol}-USD", start=start, end=end)
    if stock_data.empty:
        raise ValueError("No data found")

    closing_price = stock_data[['Close']].dropna()

    # Plot: Raw Close Price
    fig1, ax1 = plt.subplots(figsize=(15, 6))
    ax1.plot(closing_price.index, closing_price['Close'], label='Close Price', color='blue')
    ax1.set_title(f"Close price of {symbol} over time")
    close_price_plot = plot_to_base64(fig1)
    plt.close(fig1)

    # Moving Averages
    closing_price['MA_365'] = closing_price['Close'].rolling(window=365).mean()
    closing_price['MA_100'] = closing_price['Close'].rolling(window=100).mean()

    fig2 = plt.figure(figsize=(15, 6))
    plt.plot(closing_price.index, closing_price['Close'], label='Close Price')
    plt.plot(closing_price.index, closing_price['MA_365'], label='365-Day MA')
    plt.plot(closing_price.index, closing_price['MA_100'], label='100-Day MA')
    plt.legend()
    ma_plot = plot_to_base64(fig2)
    plt.close(fig2)

    # LSTM prediction
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(closing_price[['Close']].values)

    x_data, y_data = [], []
    base_days = 100
    for i in range(base_days, len(scaled_data)):
        x_data.append(scaled_data[i - base_days:i])
        y_data.append(scaled_data[i])

    x_data, y_data = np.array(x_data), np.array(y_data)
    x_data = x_data.reshape(x_data.shape[0], x_data.shape[1], 1)

    split = int(len(x_data) * 0.9)
    x_train, y_train = x_data[:split], y_data[:split]
    x_test, y_test = x_data[split:], y_data[split:]

    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(x_train.shape[1], 1)),
        LSTM(64),
        Dense(25),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    model.fit(x_train, y_train, epochs=10, batch_size=32, verbose=0)

    predictions = model.predict(x_test)
    inv_predictions = scaler.inverse_transform(predictions)
    inv_y_test = scaler.inverse_transform(y_test)

    # Plot: Prediction vs Actual
    test_index = closing_price.index[split + base_days:]
    fig3 = plt.figure(figsize=(15, 6))
    plt.plot(test_index, inv_y_test, label='Actual')
    plt.plot(test_index, inv_predictions, label='Prediction')
    plt.legend()
    prediction_plot = plot_to_base64(fig3)
    plt.close(fig3)

    # Future forecast
    last_100 = scaled_data[-100:].reshape(1, -1, 1)
    future_predictions = []
    for _ in range(10):
        next_day = model.predict(last_100, verbose=0)
        future_predictions.append(scaler.inverse_transform(next_day)[0][0])
        last_100 = np.append(last_100[:, 1:, :], next_day.reshape(1, 1, -1), axis=1)

    # Plot: Future Prediction
    fig4 = plt.figure(figsize=(15, 6))
    plt.plot(range(1, 11), future_predictions, marker="o")
    future_plot = plot_to_base64(fig4)
    plt.close(fig4)


    return {
    "history": {
        "dates": [str(d.date()) for d in test_index],
        "actual": [float(x) for x in inv_y_test.flatten()],
        "predicted": [float(x) for x in inv_predictions.flatten()]
    },
    "future": {
        "days": list(range(1, 11)),
        "prices": [float(round(p, 2)) for p in future_predictions],
        "trend": "increase" if future_predictions[-1] > future_predictions[0] else "decrease"
    },
    "plots": {
        "close_price": close_price_plot,
        "moving_average": ma_plot,
        "prediction": prediction_plot,
        "future": future_plot
    }
}
