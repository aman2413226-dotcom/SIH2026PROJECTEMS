"""
BHARATI ENERGY MANAGEMENT AI - LOAD FORECASTING MODEL
==========================================================
Real 5-saal ke Bharati weather data (IIG 2012-2016) pe train hota hai.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import matplotlib.pyplot as plt
import os

os.makedirs("models", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# ---------------------------------------------------------
# STEP 1: Data load karo
# ---------------------------------------------------------
df = pd.read_csv("data/processed/processed_data.csv")
df["datetime"] = pd.to_datetime(df["datetime"])

print(f"Total rows: {len(df)}")

# ---------------------------------------------------------
# STEP 2: Features aur Target decide karo
# ---------------------------------------------------------
feature_columns = [
    "tempr",           # temperature
    "rh",              # relative humidity
    "ws",              # wind speed
    "shortwave_radiation (W/m²)",
    "hour_sin",
    "hour_cos",
    "day_of_week",
    "month",
    "is_day",
]

target_column = "load_demand"

X = df[feature_columns]
y = df[target_column]

# ---------------------------------------------------------
# STEP 3: Train/Test split (time-series, isliye shuffle=False)
# ---------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=False
)

print(f"Training rows: {len(X_train)}, Testing rows: {len(X_test)}")

# ---------------------------------------------------------
# STEP 4: Model train karo
# ---------------------------------------------------------
model = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, random_state=42)
model.fit(X_train, y_train)

# ---------------------------------------------------------
# STEP 5: Evaluate karo
# ---------------------------------------------------------
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n📊 LOAD FORECASTING MODEL PERFORMANCE:")
print(f"MAE: {mae:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"R² Score: {r2:.3f}")

# ---------------------------------------------------------
# STEP 6: Feature importance
# ---------------------------------------------------------
importance_df = pd.DataFrame({
    "feature": feature_columns,
    "importance": model.feature_importances_
}).sort_values(by="importance", ascending=False)
print("\n🔑 Feature Importance:")
print(importance_df)

# ---------------------------------------------------------
# STEP 7: Graph
# ---------------------------------------------------------
plt.figure(figsize=(12, 5))
plt.plot(y_test.values[:200], label="Actual Load", color="blue")
plt.plot(y_pred[:200], label="Predicted Load", color="red", linestyle="--")
plt.title("Load Forecasting: Actual vs Predicted (Real Bharati Weather Data)")
plt.xlabel("Time (hours)")
plt.ylabel("Load Demand")
plt.legend()
plt.tight_layout()
plt.savefig("outputs/load_forecast_result.png")

# ---------------------------------------------------------
# STEP 8: Save model
# ---------------------------------------------------------
joblib.dump(model, "models/load_forecast_model.pkl")
print("\n✅ Model saved: models/load_forecast_model.pkl")
print("✅ Graph saved: outputs/load_forecast_result.png")