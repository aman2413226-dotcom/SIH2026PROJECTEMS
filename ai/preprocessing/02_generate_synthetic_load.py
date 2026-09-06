"""
BHARATI ENERGY MANAGEMENT AI - SYNTHETIC LOAD/RENEWABLE GENERATOR
=====================================================================
Real load/battery/diesel data abhi station se nahi mila hai, isliye hum
realistic formula se generate karte hain - REAL 5-saal ke Bharati weather
data (2012-2016) ke upar. Jab bhi real energy data mile, sirf ye script
skip karke seedha real data use kar sakte ho - baaki pipeline same rahega.
"""

import pandas as pd
import numpy as np

np.random.seed(42)

# ---------------------------------------------------------
# STEP 1: Processed weather data load karo
# ---------------------------------------------------------
df = pd.read_csv("data/processed/processed_data.csv")
df["datetime"] = pd.to_datetime(df["datetime"])

print(f"Loaded {len(df)} rows of real Bharati weather data")

temp = df["tempr"]
radiation = df["shortwave_radiation (W/m²)"]
wind_speed_kmh = df["ws"] * 3.6  # IIG ka wind speed m/s mein hai, ise km/h mein convert kar rahe hain

# ---------------------------------------------------------
# STEP 2: LOAD DEMAND generate karo (realistic formula)
# ---------------------------------------------------------
base_load = 300                          # station ka minimum base load (kWh)
heating_effect = (0 - temp) * 4.5        # jitna thanda, utna zyada heating load
night_effect = df["is_day"].apply(lambda d: 0 if d == 1 else 40)
weekday_effect = df["day_of_week"].apply(lambda d: 20 if d < 5 else 0)
noise = np.random.normal(0, 15, len(df))

load_demand = base_load + heating_effect + night_effect + weekday_effect + noise
df["load_demand"] = load_demand.clip(lower=100)

# ---------------------------------------------------------
# STEP 3: SOLAR POWER OUTPUT (radiation se directly related)
# ---------------------------------------------------------
panel_efficiency = 0.20
panel_area = 4000  # sq meters - station-scale solar array
solar_noise = np.random.normal(0, 5, len(df))
df["solar_power_output"] = (radiation * panel_efficiency * panel_area / 1000 + solar_noise).clip(lower=0)

# ---------------------------------------------------------
# STEP 4: WIND POWER OUTPUT (wind speed se directly related)
# ---------------------------------------------------------
wind_noise = np.random.normal(0, 5, len(df))
df["wind_power_output"] = (2.5 * (wind_speed_kmh ** 1.5) + wind_noise).clip(lower=0)

# ---------------------------------------------------------
# STEP 5: Total generation aur energy status
# ---------------------------------------------------------
df["total_generation"] = df["solar_power_output"] + df["wind_power_output"]
df["energy_balance"] = df["total_generation"] - df["load_demand"]
df["energy_status"] = df["energy_balance"].apply(lambda x: "Surplus" if x >= 0 else "Deficit")

# ---------------------------------------------------------
# STEP 6: Save
# ---------------------------------------------------------
df.to_csv("data/processed/processed_data.csv", index=False)

print("✅ load_demand, solar_power_output, wind_power_output add ho gaye")
print(f"✅ processed_data.csv update ho gayi with {len(df)} rows")
print("\nPreview:")
print(df[["datetime", "tempr", "load_demand", "solar_power_output", "wind_power_output", "energy_status"]].head(10))
print("\nSeasonal check - month-wise average load aur renewable:")
print(df.groupby("month")[["load_demand", "total_generation"]].mean().round(1))