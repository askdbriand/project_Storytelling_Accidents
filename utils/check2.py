# utils/check2.py : où sont les GPS manquants ?
import pandas as pd

df = pd.read_csv("data/accidents_final.csv", dtype={"dep": str})
df["gps_vide"] = df["lat"].isna()
print(df.groupby("metropole")["gps_vide"].mean().mul(100).round(2))  # % de GPS vides
print(df["metropole"].value_counts())