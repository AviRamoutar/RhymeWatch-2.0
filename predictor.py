import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def train_random_forest(features_df: pd.DataFrame, targets: np.ndarray):
    if len(features_df) != len(targets):
        raise ValueError("Features and targets must have the same length")

    if len(features_df) < 5:
        raise ValueError("Need at least 5 data points to train the model")

    X = features_df.values
    y = targets

    if len(X) >= 20:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    else:
        X_train, y_train = X, y

    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )

    clf.fit(X_train, y_train)

    if len(X) >= 20:
        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model accuracy on test set: {accuracy:.2f}")

    return clf

def predict_next_day(model: RandomForestClassifier, features_df: pd.DataFrame):
    if features_df.empty:
        raise ValueError("Features DataFrame cannot be empty")

    X_new = features_df.values
    prediction = model.predict(X_new)
    probabilities = model.predict_proba(X_new)
    confidence = np.max(probabilities[0])

    print(f"Prediction confidence: {confidence:.2f}")

    return bool(prediction[0])

def create_features_from_sentiment_and_price(sentiments: list, prices: list):
    if len(sentiments) == 0 or len(prices) < 2:
        raise ValueError("Need sentiment data and at least 2 price points")

    sentiment_scores = []
    for sentiment in sentiments:
        if sentiment == 'positive':
            sentiment_scores.append(1)
        elif sentiment == 'negative':
            sentiment_scores.append(-1)
        else:
            sentiment_scores.append(0)

    targets = []
    for i in range(1, len(prices)):
        targets.append(1 if prices[i] > prices[i-1] else 0)

    features = []
    window_size = min(5, len(sentiment_scores))

    for i in range(len(targets)):
        start_idx = max(0, i + 1 - window_size)
        end_idx = i + 1

        if end_idx <= len(sentiment_scores):
            avg_sentiment = np.mean(sentiment_scores[start_idx:end_idx])
        else:
            avg_sentiment = np.mean(sentiment_scores)

        features.append([avg_sentiment])

    min_length = min(len(features), len(targets))
    features = features[:min_length]
    targets = targets[:min_length]

    features_df = pd.DataFrame(features, columns=['avg_sentiment'])
    targets_array = np.array(targets)

    return features_df, targets_array