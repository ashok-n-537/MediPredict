import pandas as pd

# Load the dataset
data = pd.read_csv("dataset/disease_data.csv")

# Display the dataset
print("MediPredict Dataset")
print(data)

# Display first five records
print("\nFirst five records:")
print(data.head())

# Display dataset information
print("\nDataset information:")
print(data.info())

# Check missing values
print("\nMissing values:")
print(data.isnull().sum())

# Count disease records
print("\nDisease distribution:")
print(data["disease"].value_counts())