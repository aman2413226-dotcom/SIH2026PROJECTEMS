import pandas as pd
df = pd.read_csv("data/processed/decision_engine_output.csv")
print("Total load demand (5 years):", df["load_pred"].sum(), "kWh")