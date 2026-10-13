"""Forecast hourly order counts; Prophet is needed only when fitting."""
import pickle
from pathlib import Path
import pandas as pd

MODEL_PATH = "./demand_model.pkl"


def preprocess_data(order_history):
    if not order_history:
        return pd.DataFrame(columns=["ds", "y"])
    timestamps = pd.to_datetime(pd.DataFrame(order_history)["order_time"], utc=True)
    counts = timestamps.dt.floor("h").value_counts().sort_index()
    hours = pd.date_range(counts.index.min(), counts.index.max(), freq="h")
    counts = counts.reindex(hours, fill_value=0)
    return pd.DataFrame({"ds": counts.index.tz_localize(None), "y": counts.to_numpy()})


def train_prophet_model(df):
    from prophet import Prophet
    if len(df) < 2:
        raise ValueError("At least two hourly observations are required")
    model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
    model.fit(df)
    save_model(model)
    return model


def save_model(model):
    with Path(MODEL_PATH).open("wb") as file:
        pickle.dump(model, file)


def load_model():
    path = Path(MODEL_PATH)
    if not path.exists():
        return None
    # Only load model files produced by this app from a trusted directory.
    with path.open("rb") as file:
        return pickle.load(file)


def predict_demand(model, data=None, future_periods=5):
    if future_periods < 0:
        raise ValueError("future_periods must be non-negative")
    return model.predict(model.make_future_dataframe(periods=future_periods, freq="h"))


def predict_demand_from_data(order_history, future_periods=5):
    data = preprocess_data(order_history)
    model = load_model() or train_prophet_model(data)
    return predict_demand(model, data, future_periods)
