
import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# =====================================
# LOAD DATASET
# =====================================

print("Loading MediPredict dataset...")

data = pd.read_csv("dataset/medipredict_100_diseases.csv")

print("Dataset shape:", data.shape)


# =====================================
# SEPARATE FEATURES AND TARGET
# =====================================

X = data.drop("disease", axis=1)
y = data["disease"]

# Store feature names in their original order
features = X.columns.tolist()

print("Number of symptoms:", len(features))
print("Number of diseases:", y.nunique())


# =====================================
# SPLIT DATASET
# =====================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training records:", len(X_train))
print("Testing records:", len(X_test))


# =====================================
# TRAIN RANDOM FOREST MODEL
# =====================================

print("\nTraining Random Forest model...")

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=25,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced_subsample"
)

model.fit(X_train, y_train)

print("Model training completed!")


# =====================================
# EVALUATE MODEL
# =====================================

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nModel Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# =====================================
# SAVE TRAINED MODEL
# =====================================

os.makedirs("model", exist_ok=True)

saved_data = {
    "model": model,
    "features": features
}

joblib.dump(
    saved_data,
    "model/disease_model.pkl"
)

print("\nMediPredict model saved successfully!")
