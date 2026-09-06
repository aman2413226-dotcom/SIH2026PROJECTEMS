"""
BHARATI ENERGY MANAGEMENT AI - DECISION ENGINE (v2 - Minimum Runtime Rule)
================================================================================
NAYA RULE: Diesel generator ek baar ON hone ke baad, kam se kam
MIN_RUNTIME_HOURS tak chalega - chahe beech mein deficit khatam bhi ho jaye.

KYUN? Real diesel generators baar-baar ON/OFF hone se (short-cycling):
  - Engine ki wear-and-tear badh jaati hai (maintenance jaldi chahiye)
  - Har "start" mein extra fuel burn hota hai (cold-start inefficiency)
  - Generator ki lifespan kam ho jaati hai

TRADE-OFF: Generator thoda "idle" bhi chalega jab zaroorat na ho (thoda
extra fuel), lekin overall generator ki health/lifespan better rahegi.
"""

import pandas as pd
import numpy as np
import joblib
import os

os.makedirs("outputs", exist_ok=True)

# ---------------------------------------------------------
# STEP 1: Predictions load karo
# ---------------------------------------------------------
df = pd.read_csv("data/processed/processed_data.csv")
df["datetime"] = pd.to_datetime(df["datetime"])

load_model = joblib.load("models/load_forecast_model.pkl")
solar_model = joblib.load("models/solar_power_output_model.pkl")
wind_model = joblib.load("models/wind_power_output_model.pkl")

df["load_pred"] = load_model.predict(df[load_model.feature_names_in_])
df["solar_pred"] = np.clip(solar_model.predict(df[solar_model.feature_names_in_]), 0, None)
df["wind_pred"] = np.clip(wind_model.predict(df[wind_model.feature_names_in_]), 0, None)
df["renewable_pred"] = df["solar_pred"] + df["wind_pred"]

# ---------------------------------------------------------
# STEP 2: Battery temperature-derating curve (cold-aware)
# ---------------------------------------------------------
TEMP_POINTS =     [-40,  -30,  -20,  -10,   0,   10,   25]
CAPACITY_FACTOR = [0.15, 0.30, 0.50, 0.70, 0.85, 0.95, 1.00]
RATE_FACTOR =     [0.20, 0.35, 0.55, 0.75, 0.90, 1.00, 1.00]

def capacity_factor(temp):
    return np.interp(temp, TEMP_POINTS, CAPACITY_FACTOR)

def rate_factor(temp):
    return np.interp(temp, TEMP_POINTS, RATE_FACTOR)

# ---------------------------------------------------------
# STEP 3: System parameters
# ---------------------------------------------------------
NOMINAL_CAPACITY = 500
NOMINAL_CHARGE_RATE = 100
NOMINAL_DISCHARGE_RATE = 100
CHARGE_EFFICIENCY = 0.95
DISCHARGE_EFFICIENCY = 0.95
FUEL_RATE = 0.3              # litre per kWh jab load supply kar raha ho
IDLE_FUEL_RATE = 3.0         # litre per hour jab generator ON hai lekin load nahi de raha (idle)
CRITICAL_RESERVE_PERCENT = 0.15
MIN_RUNTIME_HOURS = 3        # <-- NAYA RULE: ek baar ON hone pe kam se kam itne ghante chalega

# ---------------------------------------------------------
# STEP 4: DECISION ENGINE with minimum-runtime rule
# ---------------------------------------------------------
def decision_engine(df, enforce_min_runtime=True):
    battery_soc = NOMINAL_CAPACITY * 0.5
    diesel_status = "OFF"
    hours_since_on = 0
    records = []
    start_events = 0  # kitni baar generator START hua (short-cycling track karne ke liye)

    for _, row in df.iterrows():
        temp = row["tempr"]
        cap_factor = capacity_factor(temp)
        r_factor = rate_factor(temp)

        effective_capacity = NOMINAL_CAPACITY * cap_factor
        critical_reserve = effective_capacity * CRITICAL_RESERVE_PERCENT
        max_charge = NOMINAL_CHARGE_RATE * r_factor
        max_discharge = NOMINAL_DISCHARGE_RATE * r_factor

        battery_soc = min(battery_soc, effective_capacity)

        net = row["renewable_pred"] - row["load_pred"]
        diesel_kwh = 0
        diesel_liters = 0

        if diesel_status == "ON":
            hours_since_on += 1

            if net >= 0:
                # Surplus hai - battery charge karo, diesel ko load dene ki zarurat nahi
                charge_amount = min(net, (effective_capacity - battery_soc) / CHARGE_EFFICIENCY, max_charge)
                battery_soc += charge_amount * CHARGE_EFFICIENCY
                diesel_liters = IDLE_FUEL_RATE  # generator chal raha hai but idle - thoda fuel burn
                action = "DIESEL_IDLE (ON but not needed)"
            else:
                deficit = -net
                diesel_kwh = deficit
                diesel_liters = diesel_kwh * FUEL_RATE
                action = "DIESEL_SUPPLYING_LOAD"

            # Ab check karo - kya generator OFF kar sakte hain?
            if enforce_min_runtime:
                can_turn_off = (hours_since_on >= MIN_RUNTIME_HOURS) and (net >= 0)
            else:
                can_turn_off = (net >= 0)  # purana rule - turant off kar do jaise hi zarurat khatam

            if can_turn_off:
                diesel_status = "OFF"
                hours_since_on = 0

        else:
            # Diesel OFF hai - pehle battery try karo
            if net >= 0:
                charge_amount = min(net, (effective_capacity - battery_soc) / CHARGE_EFFICIENCY, max_charge)
                battery_soc += charge_amount * CHARGE_EFFICIENCY
                action = "CHARGE_BATTERY"
            else:
                deficit = -net
                usable_soc = max(0, battery_soc - critical_reserve)
                discharge_amount = min(deficit, usable_soc * DISCHARGE_EFFICIENCY, max_discharge)
                battery_soc -= discharge_amount / DISCHARGE_EFFICIENCY
                deficit -= discharge_amount

                if deficit > 0:
                    diesel_status = "ON"
                    hours_since_on = 1
                    start_events += 1
                    diesel_kwh = deficit
                    diesel_liters = diesel_kwh * FUEL_RATE
                    action = "DIESEL_START"
                else:
                    action = "DISCHARGE_BATTERY"

        battery_soc = np.clip(battery_soc, 0, effective_capacity)

        records.append({
            "datetime": row["datetime"],
            "tempr": temp,
            "load_pred": row["load_pred"],
            "renewable_pred": row["renewable_pred"],
            "battery_soc": battery_soc,
            "diesel_status": diesel_status,
            "diesel_kwh": diesel_kwh,
            "diesel_liters": diesel_liters,
            "action": action,
        })

    return pd.DataFrame(records), start_events


# ---------------------------------------------------------
# STEP 5: Compare - OLD rule (bar bar on/off) vs NEW rule (min runtime)
# ---------------------------------------------------------
print("Running OLD rule (no minimum runtime - reactive on/off)...")
old_result, old_starts = decision_engine(df, enforce_min_runtime=False)

print("Running NEW rule (minimum runtime enforced)...")
new_result, new_starts = decision_engine(df, enforce_min_runtime=True)

old_total_fuel = old_result["diesel_liters"].sum()
new_total_fuel = new_result["diesel_liters"].sum()

print("\n" + "="*60)
print("🎯 DECISION ENGINE - OLD vs NEW RULE COMPARISON")
print("="*60)
print(f"{'Metric':<35}{'OLD (reactive)':<20}{'NEW (min-runtime)'}")
print(f"{'Generator START events':<35}{old_starts:<20}{new_starts}")
print(f"{'Total diesel used (litres)':<35}{old_total_fuel:,.0f}{'':<10}{new_total_fuel:,.0f}")
print("="*60)
print(f"\n✅ Generator starts kam hue: {old_starts - new_starts} times "
      f"({((old_starts - new_starts) / old_starts * 100):.1f}% reduction)")
print("   -> Isse engine wear-and-tear kam hogi, maintenance kam baar chahiye hogi")

fuel_diff = new_total_fuel - old_total_fuel
print(f"\n⚠️  Thoda extra fuel laga (idle running ki wajah se): {fuel_diff:,.0f} litres "
      f"({(fuel_diff/old_total_fuel)*100:.2f}% zyada)")
print("   -> Ye trade-off hai: thoda zyada fuel, lekin generator ki lambi life")

new_result.to_csv("data/processed/decision_engine_output.csv", index=False)
print("\n✅ Saved: data/processed/decision_engine_output.csv")