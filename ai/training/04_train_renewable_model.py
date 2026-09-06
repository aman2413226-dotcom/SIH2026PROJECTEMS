"""
BHARATI ENERGY MANAGEMENT AI - RENEWABLE (SOLAR + WIND) PREDICTION MODEL
============================================================================
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

# ---------------------------------------------------------
# STEP 2: Features - sirf weather (forecast se pehle pata hota hai)
# ---------------------------------------------------------
feature_columns = [
    "tempr",
    "ws",
    "shortwave_radiation (W/m²)",
    "hour_sin",
    "hour_cos",
    "month",
]

X = df[feature_columns]

# ---------------------------------------------------------
# STEP 3: Solar aur Wind - dono ke liye alag model
# ---------------------------------------------------------
for target_name in ["solar_power_output", "wind_power_output"]:
    y = df[target_name]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )

    model = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0, None)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"\n📊 {target_name} MODEL PERFORMANCE:")
    print(f"MAE: {mae:.2f}, RMSE: {rmse:.2f}, R² Score: {r2:.3f}")

    joblib.dump(model, f"models/{target_name}_model.pkl")

    plt.figure(figsize=(12, 4))
    plt.plot(y_test.values[:200], label="Actual", color="blue")
    plt.plot(y_pred[:200], label="Predicted", color="green", linestyle="--")
    plt.title(f"{target_name}: Actual vs Predicted (Real Bharati Data)")
    plt.xlabel("Time (hours)")
    plt.ylabel("Power Output")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"outputs/{target_name}_result.png")

print("\n✅ Dono models train aur save ho gaye (models/ folder mein)")
print("✅ Graphs bhi save ho gaye (outputs/ folder mein)")