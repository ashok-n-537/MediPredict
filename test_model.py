import joblib
import pandas as pd

# Load saved model
saved_data = joblib.load("model/disease_model.pkl")

model = saved_data["model"]
features = saved_data["features"]

print("Model loaded successfully!")
print("Features:", features)

# Test symptoms
sample = pd.DataFrame(
    [[1, 1, 0, 1, 0]],
    columns=features
)

prediction = model.predict(sample)

print("Prediction:", prediction[0])