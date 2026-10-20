# utils check.py : taux de gravité par zone et valeurs "non renseigné"
import pandas as pd

df = pd.read_csv("data/accidents_clean.csv", dtype=str)  # tout en texte
df["mortel"] = df["mortel"] == "True"                    # on remet le booléen

# part d'accidents mortels selon la zone (ça confirme aussi le code de la colonne agg)
print((df.groupby("zone")["mortel"].agg(["count", "mean"])).round(4))

# part de valeurs -1 (non renseigné) dans les colonnes clés
for col in ["lum", "atm", "catr", "vma", "surf"]:
    print(col, round((df[col].str.strip() == "-1").mean() * 100, 2), "% non renseigné")