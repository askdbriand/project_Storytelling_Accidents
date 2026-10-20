
# Compare les colonnes de chaque année avec celles de 2024
import pandas as pd

YEARS = range(2019, 2025)

for table in ["caracteristiques", "lieux", "usagers", "vehicules"]:
    print("\n=== TABLE :", table)
    ref = None
    for year in reversed(YEARS):  # on commence par 2024 (référence)
        # sep=None : pandas devine le séparateur ; nrows=0 : on lit seulement les noms de colonnes
        cols = list(pd.read_csv(f"data/raw/{table}-{year}.csv", sep=None,
                                engine="python", nrows=0, encoding="utf-8-sig").columns)
        if ref is None:
            ref = cols
            print(year, "(référence) :", cols)
        else:
            print(year, "| manquantes :", set(ref) - set(cols), "| en plus :", set(cols) - set(ref))