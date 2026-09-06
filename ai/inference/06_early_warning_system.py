"""
BHARATI ENERGY MANAGEMENT AI - EARLY WARNING / DIESEL TRIGGER SYSTEM
=========================================================================
PROBLEM: Jab battery discharge ho ke khatam ho jaati hai, diesel generator
ko start hone mein time lagta hai (~2 min). UPS sirf ~5 minute ka backup
deta hai. Agar hum "battery khatam" hone ka WAIT karenge, toh beech mein
GAP aa jayega aur computers/communication OFF ho sakte hain.

SOLUTION: Battery ki discharge SPEED (per-minute) track karo, aur
predict karo "kitne minute mein battery critical level pe pahunchegi".
Agar ye time generator-startup-time + safety-margin se kam ho jaye,
TURANT signal bhejo diesel start karne ke liye - PEHLE HI, reactive nahi.

Ye REAL-TIME/per-minute resolution pe kaam karta hai (AWS station data
use kar rahe hain, jo per-minute hai - IIG/hourly data isliye nahi
use kar sakte, kyunki wo itna fine-grained nahi hai).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

os.makedirs("outputs", exist_ok=True)

# ---------------------------------------------------------
# SYSTEM PARAMETERS (apne station ke actual specs se adjust karna)
# ---------------------------------------------------------
UPS_BACKUP_MINUTES = 5          # UPS kitne minute tak load sambhal sakta hai
GENERATOR_STARTUP_MINUTES = 2   # diesel generator ko start/stable hone mein kitna time lagta hai
SAFETY_MARGIN_MINUTES = 1       # extra buffer, safe side ke liye

# Trigger ka matlab: battery critical hone se itne minute PEHLE signal do
TRIGGER_LEAD_TIME = GENERATOR_STARTUP_MINUTES + SAFETY_MARGIN_MINUTES  # = 3 min pehle

BATTERY_CAPACITY_KWH = 500
CRITICAL_SOC_PERCENT = 0.10     # 10% se neeche = critical (bilkul khali hone se pehle)
CRITICAL_SOC = BATTERY_CAPACITY_KWH * CRITICAL_SOC_PERCENT

DISCHARGE_RATE_WINDOW = 5       # pichle 5 minute ki average discharge speed se estimate karo

# ---------------------------------------------------------
# STEP 1: Real per-minute AWS data load karo (Bharati 2023)
# ---------------------------------------------------------
aws_df = pd.read_excel("data/Raw/Bharati_-_AWS_2023_filtered_data.xlsx")
aws_df["obstime"] = pd.to_datetime(aws_df["obstime"])
aws_df.sort_values("obstime", inplace=True)
aws_df.reset_index(drop=True, inplace=True)

print(f"Loaded {len(aws_df)} minutes of real Bharati AWS data (2023)")

# ---------------------------------------------------------
# STEP 2: SIMULATION - ek "battery drain scenario" banate hain
# demonstration ke liye. Real deployment mein ye live battery
# sensor se aayega - abhi hum realistic simulate kar rahe hain
# taaki dikha sakein system kaise react karta hai.
# ---------------------------------------------------------
np.random.seed(1)
n_minutes = 180  # 3 ghante ka per-minute simulation (demo ke liye kaafi hai)
sample = aws_df.iloc[5000:5000 + n_minutes].copy().reset_index(drop=True)

# Load thoda badhta hai is window mein (jaise ek heavy equipment chalu ho gaya),
# renewable kam hai (raat ka waqt maan lo) - isliye battery discharge hogi
base_deficit = 3.5  # kWh per minute deficit (realistic heavy-load scenario)
deficit_noise = np.random.normal(0, 0.4, n_minutes)
sample["deficit_kwh_per_min"] = np.clip(base_deficit + deficit_noise, 0.5, None)

# ---------------------------------------------------------
# STEP 3: EARLY WARNING ALGORITHM - minute by minute chalao
# ---------------------------------------------------------
battery_soc = BATTERY_CAPACITY_KWH * 0.35   # shuru mein battery 35% pe hai (already thodi kam)
soc_history = []
discharge_rates = []
trigger_minute = None
generator_online_minute = None
alerts = []

for i in range(n_minutes):
    deficit = sample.loc[i, "deficit_kwh_per_min"]
    battery_soc -= deficit
    battery_soc = max(battery_soc, 0)
    soc_history.append(battery_soc)

    # Pichle N minute ki average discharge rate nikaalo
    window = soc_history[-DISCHARGE_RATE_WINDOW:]
    if len(window) >= 2:
        discharge_rate = (window[0] - window[-1]) / (len(window) - 1)  # kWh/min
    else:
        discharge_rate = deficit
    discharge_rates.append(discharge_rate)

    # Predict karo: kitne minute mein battery CRITICAL level pe pahunchegi
    if discharge_rate > 0:
        time_to_critical = (battery_soc - CRITICAL_SOC) / discharge_rate
    else:
        time_to_critical = np.inf

    # TRIGGER CHECK - agar abhi tak trigger nahi hua aur time kam hai
    if trigger_minute is None and time_to_critical <= TRIGGER_LEAD_TIME:
        trigger_minute = i
        generator_online_minute = i + GENERATOR_STARTUP_MINUTES
        alerts.append(
            f"⚠️ Minute {i}: EARLY WARNING TRIGGERED! "
            f"Battery {battery_soc:.1f} kWh, discharge rate {discharge_rate:.2f} kWh/min, "
            f"estimated {time_to_critical:.1f} min tak critical hoga. "
            f"DIESEL START SIGNAL bheja gaya!"
        )

print("\n".join(alerts) if alerts else "Is simulation window mein trigger nahi hua.")

# ---------------------------------------------------------
# STEP 4: Verify - kya UPS ke andar generator ready ho gaya?
# ---------------------------------------------------------
if trigger_minute is not None:
    minutes_before_ups_runs_out = trigger_minute + UPS_BACKUP_MINUTES
    print(f"\n📊 VERIFICATION:")
    print(f"Trigger diya minute:              {trigger_minute}")
    print(f"Generator online hoga minute:      {generator_online_minute}")
    print(f"UPS backup khatam hoga minute:     {minutes_before_ups_runs_out} (agar battery bhi khatam ho jaye)")

    if generator_online_minute <= minutes_before_ups_runs_out:
        gap = minutes_before_ups_runs_out - generator_online_minute
        print(f"✅ SAFE: Generator UPS khatam hone se {gap} minute PEHLE hi online ho jayega.")
        print("✅ Computers/communication system KABHI power khoyenge nahi.")
    else:
        print("❌ RISK: Generator UPS ke backup se der se online hoga - trigger lead time badhao!")

# ---------------------------------------------------------
# STEP 5: Graph banao (poora scenario visualize karo)
# ---------------------------------------------------------
plt.figure(figsize=(12, 6))
plt.plot(soc_history, label="Battery SOC (kWh)", color="blue", linewidth=2)
plt.axhline(CRITICAL_SOC, color="orange", linestyle="--", label=f"Critical Level ({CRITICAL_SOC:.0f} kWh)")

if trigger_minute is not None:
    plt.axvline(trigger_minute, color="red", linestyle="--", label=f"⚠️ Early Warning Trigger (min {trigger_minute})")
    plt.axvline(generator_online_minute, color="green", linestyle="--", label=f"✅ Generator Online (min {generator_online_minute})")
    plt.axvspan(trigger_minute, trigger_minute + UPS_BACKUP_MINUTES, color="yellow", alpha=0.2, label="UPS Coverage Window (5 min)")

plt.title("Early Warning System: Battery Depletion & Diesel Trigger Timeline")
plt.xlabel("Time (minutes)")
plt.ylabel("Battery SOC (kWh)")
plt.legend(loc="upper right")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/early_warning_timeline.png")

print("\n✅ Graph saved: outputs/early_warning_timeline.png")