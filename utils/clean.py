
# Cleans data/accidents_clean.csv -> accidents_final.csv + quality report + department centers
import numpy as np
import pandas as pd

# 1) Reading, with clear messages if something is missing
try:
    df = pd.read_csv("data/accidents_clean.csv",
                     dtype={"Num_Acc": str, "dep": str, "hrmn": str, "lat": str, "long": str})
except FileNotFoundError:
    print("data/accidents_clean.csv not found -> run python3 utils/prep.py first")
    raise SystemExit

attendues = ["jour", "lat", "long", "hrmn", "lum", "vma", "nb_tues", "nb_usagers"]
absentes = [c for c in attendues if c not in df.columns]
if absentes:
    print("Missing columns: ", absentes, "-> Modify the line in prep.py (jour, lat, long) then run it again.")
    raise SystemExit

rapport = {"Departing lines": len(df)}  

# 2) Duplicates
rapport["Duplicates removed (Num_Acc + année)"] = int(df.duplicated(["Num_Acc", "annee"]).sum())
df = df.drop_duplicates(["Num_Acc", "annee"])

# 3) -1 = "not specified" -> empty value
for col in ["lum", "atm", "catr", "vma", "surf"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").replace(-1, np.nan)

# 4) Speeds: keep only the possible values
vitesses_ok = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130]
aberrante = df["vma"].notna() & ~df["vma"].isin(vitesses_ok)
rapport["Excessive speeds (no-load conditions)"] = int(aberrante.sum())
df.loc[aberrante, "vma"] = np.nan

# 5) Date, day of the week, time, and time of day
dates = pd.DataFrame({"year": df["annee"],
                      "month": pd.to_numeric(df["mois"], errors="coerce"),
                      "day": pd.to_numeric(df["jour"], errors="coerce")})
df["date"] = pd.to_datetime(dates, errors="coerce")  # invalid date -> empty
rapport["Invalid dates"] = int(df["date"].isna().sum())
df["weekend"] = df["date"].dt.dayofweek >= 5          # Saturday or Sunday

# hrmn can be "17:30" or "1730": remove the ":" and keep the first 2 digits
df["heure"] = pd.to_numeric(df["hrmn"].str.replace(":", "").str.zfill(4).str[:2], errors="coerce")
rapport["Invalid hours"] = int((~df["heure"].between(0, 23)).sum())

# light: 1 full daylight, 2 twilight or dawn, 3 to 5 night
df["moment"] = df["lum"].map({1: "Jour", 2: "Crépuscule ou aube", 3: "Nuit", 4: "Nuit", 5: "Nuit"})

# 6) Metropolitan France or overseas territories (overseas: departments 97x and 98x)
df["metropole"] = ~df["dep"].str.startswith(("97", "98"))

# 7) GPS coordinates: replace commas with periods, then keep only those that fall within Metropolitan France
df["lat"] = pd.to_numeric(df["lat"].str.replace(",", "."), errors="coerce")
df["long"] = pd.to_numeric(df["long"].str.replace(",", "."), errors="coerce")
gps_ok = df["lat"].between(41, 52) & df["long"].between(-5.5, 10)
rapport["GPS invalid in metropolitan France (%)"] = round((~gps_ok[df["metropole"]]).mean() * 100, 2)
df.loc[~gps_ok, ["lat", "long"]] = np.nan

# center of each department (median of GPS coordinates): will be used to position the bubbles on the map
centres = df[df["metropole"]].groupby("dep")[["lat", "long"]].median().dropna().reset_index()
centres.to_csv("data/centres_dep.csv", index=False)

# 8) Consistency checks
rapport["Accidents involving no other road user"] = int((df["nb_usagers"].fillna(0) == 0).sum())
rapport["Inconsistencies (fatalities > road users)"] = int((df["nb_tues"] > df["nb_usagers"]).sum())
for col in ["lum", "atm", "catr", "vma", "surf", "heure", "lat", "long"]:
    rapport[f"Missing : {col} (%)"] = round(df[col].isna().mean() * 100, 2)
rapport["Lines at the end"] = len(df)

# 9) Backups
pd.DataFrame(list(rapport.items()), columns=["Contrôle", "Valeur"]).to_csv("data/qualite.csv", index=False)
df.to_csv("data/accidents_final.csv", index=False)

# 10) Display for verification
for nom, valeur in rapport.items():
    print(nom, ":", valeur)
print("\nCodes lum présents :", df["lum"].value_counts().sort_index().to_dict())
print("Accidents mortels (%) par moment :")
print((df.groupby("moment")["mortel"].mean() * 100).round(2))
print("Accidents mortels (%) semaine / week-end :")
print((df.groupby("weekend")["mortel"].mean() * 100).round(2))
print("Départements avec un centre GPS :", len(centres))