"""
Machine Learning Models for Stock Analysis

Implements:
- LSTM for price prediction
- Random Forest for trend classification
- XGBoost for feature importance
- Anomaly detection for unusual market activity
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

from src.utils import logger

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available. Install with: pip install xgboost")

try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    Sequential = None  # Placeholder for type hints
    logger.warning("TensorFlow/Keras not available. Install with: pip install tensorflow")


class LSTMPricePredictor:
    """LSTM model for price prediction"""

    def __init__(self, lookback: int = 60, forecast_horizon: int = 5):
        """
        Args:
            lookback: Number of days to look back
            forecast_horizon: Days to forecast ahead
        """
        if not KERAS_AVAILABLE:
            raise ImportError("TensorFlow/Keras required for LSTM")

        self.lookback = lookback
        self.forecast_horizon = forecast_horizon
        self.model = None
        self.scaler = StandardScaler()

    def prepare_data(self, df: pd.DataFrame, target_col: str = 'Close') -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM"""
        data = df[target_col].values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(data)

        X, y = [], []
        for i in range(self.lookback, len(scaled_data) - self.forecast_horizon):
            X.append(scaled_data[i - self.lookback:i, 0])
            y.append(scaled_data[i + self.forecast_horizon, 0])

        return np.array(X), np.array(y)

    def build_model(self, input_shape: tuple) -> Sequential:
        """Build LSTM architecture"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])

        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def train(self, df: pd.DataFrame, epochs: int = 50, batch_size: int = 32, validation_split: float = 0.2):
        """Train LSTM model"""
        X, y = self.prepare_data(df)
        X = X.reshape((X.shape[0], X.shape[1], 1))

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=validation_split, shuffle=False)

        self.model = self.build_model((X_train.shape[1], 1))

        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            verbose=0
        )

        train_loss = history.history['loss'][-1]
        val_loss = history.history['val_loss'][-1]

        logger.info(f"LSTM trained - Train loss: {train_loss:.4f}, Val loss: {val_loss:.4f}")

        return history

    def predict(self, df: pd.DataFrame, n_steps: int = 30) -> np.ndarray:
        """Predict future prices"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        data = df['Close'].values[-self.lookback:].reshape(-1, 1)
        scaled_data = self.scaler.transform(data)

        predictions = []
        current_sequence = scaled_data.copy()

        for _ in range(n_steps):
            X_pred = current_sequence.reshape((1, self.lookback, 1))
            pred = self.model.predict(X_pred, verbose=0)
            predictions.append(pred[0, 0])

            # Update sequence
            current_sequence = np.append(current_sequence[1:], pred)

        # Inverse transform predictions
        predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

        return predictions.flatten()


class TrendClassifier:
    """Random Forest for trend classification"""

    def __init__(self, n_estimators: int = 100):
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
        self.scaler = StandardScaler()
        self.feature_names = []

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical features for classification"""
        features = pd.DataFrame(index=df.index)

        # Price-based features
        features['returns'] = df['Close'].pct_change()
        features['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))

        # Moving averages
        for window in [5, 10, 20, 50]:
            features[f'sma_{window}'] = df['Close'].rolling(window).mean()
            features[f'ema_{window}'] = df['Close'].ewm(span=window).mean()

        # Volatility
        features['volatility_20'] = df['Close'].pct_change().rolling(20).std()

        # Volume features
        features['volume_change'] = df['Volume'].pct_change()
        features['volume_sma_20'] = df['Volume'].rolling(20).mean()

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        features['macd'] = exp1 - exp2
        features['macd_signal'] = features['macd'].ewm(span=9).mean()

        return features.dropna()

    def create_labels(self, df: pd.DataFrame, forward_days: int = 5) -> pd.Series:
        """Create trend labels (0=down, 1=neutral, 2=up)"""
        future_returns = df['Close'].pct_change(forward_days).shift(-forward_days)

        labels = pd.Series(index=df.index, dtype=int)
        labels[future_returns < -0.02] = 0  # Down
        labels[(future_returns >= -0.02) & (future_returns <= 0.02)] = 1  # Neutral
        labels[future_returns > 0.02] = 2  # Up

        return labels

    def train(self, df: pd.DataFrame, forward_days: int = 5, test_size: float = 0.2):
        """Train Random Forest classifier"""
        features = self.create_features(df)
        labels = self.create_labels(df, forward_days)

        # Align features and labels
        common_idx = features.index.intersection(labels.index)
        features = features.loc[common_idx]
        labels = labels.loc[common_idx]

        # Remove NaN
        valid_idx = ~(features.isna().any(axis=1) | labels.isna())
        features = features[valid_idx]
        labels = labels[valid_idx]

        self.feature_names = features.columns.tolist()

        # Scale features
        X_scaled = self.scaler.fit_transform(features)

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, labels, test_size=test_size, random_state=42, shuffle=False
        )

        # Train model
        self.model.fit(X_train, y_train)

        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        logger.info(f"Random Forest trained - Train acc: {train_score:.3f}, Test acc: {test_score:.3f}")

        return {'train_accuracy': train_score, 'test_accuracy': test_score}

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predict trend direction"""
        features = self.create_features(df)
        X_scaled = self.scaler.transform(features)
        return self.model.predict(X_scaled)

    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance rankings"""
        importances = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        })
        return importances.sort_values('importance', ascending=False)


class XGBoostPredictor:
    """XGBoost for regression with feature importance"""

    def __init__(self, n_estimators: int = 100, learning_rate: float = 0.1):
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not available")

        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=6,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_names = []

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features similar to Random Forest"""
        features = pd.DataFrame(index=df.index)

        # Technical indicators
        features['returns'] = df['Close'].pct_change()
        features['high_low_ratio'] = df['High'] / df['Low']
        features['close_open_ratio'] = df['Close'] / df['Open']

        for window in [5, 10, 20, 50]:
            features[f'sma_{window}'] = df['Close'].rolling(window).mean()
            features[f'std_{window}'] = df['Close'].rolling(window).std()

        features['volume_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()

        return features.dropna()

    def train(self, df: pd.DataFrame, target_col: str = 'Close', forward_days: int = 1, test_size: float = 0.2):
        """Train XGBoost model"""
        features = self.create_features(df)
        target = df[target_col].pct_change(forward_days).shift(-forward_days)

        # Align
        common_idx = features.index.intersection(target.index)
        features = features.loc[common_idx]
        target = target.loc[common_idx]

        # Remove NaN
        valid_idx = ~(features.isna().any(axis=1) | target.isna())
        features = features[valid_idx]
        target = target[valid_idx]

        self.feature_names = features.columns.tolist()

        # Scale
        X_scaled = self.scaler.fit_transform(features)

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, target, test_size=test_size, random_state=42, shuffle=False
        )

        # Train
        self.model.fit(X_train, y_train)

        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        logger.info(f"XGBoost trained - Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")

        return {'train_r2': train_score, 'test_r2': test_score}

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Predict returns"""
        features = self.create_features(df)
        X_scaled = self.scaler.transform(features)
        return self.model.predict(X_scaled)

    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance from XGBoost"""
        importances = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        })
        return importances.sort_values('importance', ascending=False)


class AnomalyDetector:
    """Isolation Forest for anomaly detection"""

    def __init__(self, contamination: float = 0.1):
        """
        Args:
            contamination: Expected proportion of outliers
        """
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = StandardScaler()

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for anomaly detection"""
        features = pd.DataFrame(index=df.index)

        # Price movements
        features['returns'] = df['Close'].pct_change()
        features['abs_returns'] = features['returns'].abs()

        # Volume anomalies
        features['volume_zscore'] = (df['Volume'] - df['Volume'].rolling(20).mean()) / df['Volume'].rolling(20).std()

        # Price range
        features['daily_range'] = (df['High'] - df['Low']) / df['Close']

        # Volatility
        features['volatility'] = df['Close'].pct_change().rolling(20).std()

        return features.dropna()

    def fit(self, df: pd.DataFrame):
        """Fit anomaly detector"""
        features = self.create_features(df)
        X_scaled = self.scaler.fit_transform(features)
        self.model.fit(X_scaled)

        logger.info("Anomaly detector fitted")

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies

        Returns:
            DataFrame with anomaly scores and labels
        """
        features = self.create_features(df)
        X_scaled = self.scaler.transform(features)

        # Get predictions (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)

        results = pd.DataFrame(index=features.index)
        results['anomaly'] = predictions == -1
        results['anomaly_score'] = scores
        results['returns'] = df.loc[features.index, 'Close'].pct_change()

        return results

    def get_anomalies(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Get top N anomalous days"""
        results = self.detect(df)
        anomalies = results[results['anomaly']].copy()
        anomalies = anomalies.nsmallest(top_n, 'anomaly_score')

        # Add date and price info
        anomalies['date'] = anomalies.index
        anomalies['close'] = df.loc[anomalies.index, 'Close']

        return anomalies
