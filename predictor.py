import pandas as pd
from sklearn.ensemble import RandomForestClassifier

def train_random_forest(data_df: pd.DataFrame):
    """Train a RandomForest classifier to predict next-day movement.
    data_df should contain columns: 'Date', 'Close', 'AvgSentiment' for each trading day.
    We'll derive the target (next day up/down) from 'Close'."""
    # Ensure data is sorted by Date
    data_df = data_df.sort_values("Date")
    # Compute target: whether next day's Close is higher (1) or not (0)
    prices = list(data_df["Close"])
    # We will create a list of targets for all but the last day
    target = []
    for i in range(len(prices) - 1):
        next_day = prices[i+1]
        today = prices[i]
        target.append(1 if next_day > today else 0)
    # Feature is AvgSentiment of each day (except last, since last has no next day label in our data)
    features = list(data_df["AvgSentiment"])  # this is a list of sentiment scores aligned with dates
    features = features[:-1]  # exclude last day's feature since no label for it
    if not features or not target:
        raise ValueError("Not enough data to train the model.")
    # Prepare feature matrix X and target vector y
    import numpy as np
    X = np.array(features).reshape(-1, 1)
    y = np.array(target)
    # Train Random Forest (using a fixed small number of trees for speed, e.g., 100)
    clf = RandomForestClassifier(n_estimators=100, random_state=0)
    clf.fit(X, y)
    return clf

def predict_next_day(model: RandomForestClassifier, features_df):
    """Use the trained model to predict next-day movement based on the last day's features.
    features_df is a DataFrame or array with the feature(s) for the last day (AvgSentiment)."""
    # We assume features_df is a one-row DataFrame or array of shape (1, n_features)
    # For our case, n_features = 1 (average sentiment)
    if isinstance(features_df, pd.DataFrame):
        X_new = features_df.values.reshape(-1, 1)
    else:
        # If it's already a numpy array or list
        import numpy as np
        X_new = np.array(features_df).reshape(-1, 1)
    # Predict class (0 or 1)
    pred = model.predict(X_new)
    return int(pred[0])
