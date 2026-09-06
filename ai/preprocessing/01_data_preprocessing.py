"""
BHARATI ENERGY MANAGEMENT AI - DATA PREPROCESSING (FRESH START)
====================================================================
Ye script 2 REAL datasets ko combine karta hai:
1. IIG Bharati data (2012-2016) - temperature, air pressure, wind, humidity
   (real Bharati station se, IIG/NCPOR se mila hua)
2. Open-Meteo solar radiation data (same date range, Bharati coordinates)

Output: data/processed/processed_data.csv - ek clean, merged file
jisme sab weather parameters ek jagah honge.
"""

import pandas as pd
import numpy as np

# ---------------------------------------------------------
# STEP 1: IIG weather data load karo (real Bharati data)
# ---------------------------------------------------------
iig_df = pd.read_csv("data/raw/iig_bharati.csv")
iig_df["obstime"] = pd.to_datetime(iig_df["obstime"], errors="coerce")
iig_df.dropna(subset=["obstime"], inplace=True)
iig_df.rename(columns={"obstime": "datetime"}, inplace=True)

print(f"IIG data loaded: {len(iig_df)} rows")
print(f"Date range: {iig_df['datetime'].min()} to {iig_df['datetime'].max()}")
print(f"Columns: {iig_df.columns.tolist()}")
print("\n" + "="*60 + "\n")

# ---------------------------------------------------------
# STEP 2: Solar radiation data load karo (Open-Meteo se)
# ---------------------------------------------------------
solar_df = pd.read_csv("data/raw/solar_radiation.csv", skiprows=2)
solar_df.rename(columns={"time": "datetime"}, inplace=True)
solar_df["datetime"] = pd.to_datetime(solar_df["datetime"], errors="coerce")
solar_df.dropna(subset=["datetime"], inplace=True)

print(f"Solar radiation data loaded: {len(solar_df)} rows")
print(f"Date range: {solar_df['datetime'].min()} to {solar_df['datetime'].max()}")
print("\n" + "="*60 + "\n")

# ---------------------------------------------------------
# STEP 3: Duplicate timestamps hatao (agar koi ho)
# ---------------------------------------------------------
iig_df.drop_duplicates(subset=["datetime"], inplace=True)
solar_df.drop_duplicates(subset=["datetime"], inplace=True)

# ---------------------------------------------------------
# STEP 4: Dono ko merge karo (datetime ke basis pe)
# ---------------------------------------------------------
merged_df = pd.merge(iig_df, solar_df, on="datetime", how="inner")
merged_df.sort_values("datetime", inplace=True)
merged_df.reset_index(drop=True, inplace=True)

print(f"Merged data: {len(merged_df)} rows")
print(f"Date range: {merged_df['datetime'].min()} to {merged_df['datetime'].max()}")

# ---------------------------------------------------------
# STEP 5: Missing values handle karo (gaps ko fill karo)
# ---------------------------------------------------------
merged_df.ffill(inplace=True)
merged_df.bfill(inplace=True)  # agar shuru mein hi koi missing ho

# ---------------------------------------------------------
# STEP 6: Time-based features banao
# ---------------------------------------------------------
merged_df["hour"] = merged_df["datetime"].dt.hour
merged_df["hour_sin"] = np.sin(2 * np.pi * merged_df["hour"] / 24)
merged_df["hour_cos"] = np.cos(2 * np.pi * merged_df["hour"] / 24)
merged_df["day_of_week"] = merged_df["datetime"].dt.dayofweek
merged_df["month"] = merged_df["datetime"].dt.month
merged_df["is_day"] = merged_df["hour"].apply(lambda h: 1 if 6 <= h < 18 else 0)

# ---------------------------------------------------------
# STEP 7: Save final processed file
# ---------------------------------------------------------
merged_df.to_csv("data/processed/processed_data.csv", index=False)

print("\n" + "="*60)
print("✅ DONE! processed_data.csv ban gayi hai data/processed/ folder mein")
print(f"✅ Total rows: {len(merged_df)}")
print(f"✅ Columns: {merged_df.columns.tolist()}")
print("="*60)
print("\nPreview:")
print(merged_df.head())