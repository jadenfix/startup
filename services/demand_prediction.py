# `services/demand_prediction.py`

import pandas as pd
from prophet import Prophet
import pickle
import os
import logging

MODEL_PATH = "./demand_model.pkl"  # Path to store the trained model

logger = logging.getLogger("backend_logger")

def train_prophet_model(df):
    try:
        model = Prophet(
               yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True
             )
        model.fit(df)
        save_model(model) # persist the model once trained.
        return model
    except Exception as e:
        logger.error(f"Error during prophet model training {e}")
        return None

def save_model(model):
     try:
       with open(MODEL_PATH, "wb") as f:
         pickle.dump(model, f)
       logger.info(f'Model saved to: {MODEL_PATH}')
     except Exception as e:
         logger.error(f'Error saving model: {e}')

def load_model():
   try:
    if os.path.exists(MODEL_PATH):
       with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)
    else:
      logger.error('No persisted model found, training a new model')
      return None

   except Exception as e:
        logger.error(f'Could not load existing model : {e}')
        return None



def predict_demand(model, data, future_periods=5):
    try:
         future = model.make_future_dataframe(periods=future_periods, freq='h')
         forecast = model.predict(future)
         return forecast
    except Exception as e:
        logger.error(f"Error during demand prediction {e}")
        return None

def preprocess_data(order_history):
    try:
      df = pd.DataFrame(order_history)
      df['order_time'] = pd.to_datetime(df['order_time'])
      df = (df.set_index('order_time').resample('h').size()
            .rename('y').rename_axis('ds').reset_index())
      return df
    except KeyError as e:
      logger.error(f"KeyError preprocessing the data: {e}")
      return None
    except Exception as e:
      logger.error(f"Error when pre-processing data: {e}")
      return None

# You can use this method if you have no saved models, or if you wish to retrain periodically.
def predict_demand_from_data(order_history, future_periods=5):
     df = preprocess_data(order_history)
     if df is not None:
          model = load_model()
          if model is None:
            model = train_prophet_model(df)
          if model is not None:
             forecast = predict_demand(model, df, future_periods)
             return forecast
          else:
            logger.error('Could not train model or load persisted model')
            return None
     else:
         logger.error('Could not preprocess data')
         return None