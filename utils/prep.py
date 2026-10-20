
# Reads the 24 files, computes severity per accident, joins the tables and saves the result
import pandas as pd

YEARS = range(2019, 2025)
RAW = "data/raw"


def read(table, year):
    """Lit un fichier CSV BAAC  et ajoute la colonne annee."""
    path = f"{RAW}/{table}-{year}.csv"
    try:
        df = pd.read_csv(path, sep=None, engine="python", dtype=str, encoding="utf-8-sig")
    except UnicodeDecodeError: # some files are not in utf-8
        df = pd.read_csv(path, sep=None, engine="python", dtype=str, encoding="latin-1")
    df = df.rename(columns={"Accident_Id": "Num_Acc"})  # 2022: different column name
    df["annee"] = year  # our own year column (same format for every file)
    return df


def load_all():
    tables = []
    for year in YEARS:
        # we only keep the columns useful for the story
        carac = read("caracteristiques", year)[["Num_Acc", "annee", "jour", "mois", "hrmn", "lum", "dep", "agg", "atm", "lat", "long"]].copy()
        lieux = read("lieux", year)[["Num_Acc", "annee", "catr", "vma", "surf"]].copy()
        usagers = read("usagers", year)[["Num_Acc", "annee", "grav"]].copy()

        # severity per accident: an accident has several road users, so we summarize BEFORE joining
        usagers["grav"] = pd.to_numeric(usagers["grav"], errors="coerce")
        par_acc = usagers.groupby(["Num_Acc", "annee"]).agg(
            nb_usagers=("grav", "size"),
            nb_tues=("grav", lambda g: (g == 2).sum()),    # grav = 2: killed
            nb_graves=("grav", lambda g: (g == 3).sum()),  # grav = 3: injured and hospitalized
        ).reset_index()

        # remove possible duplicates, then join on Num_Acc + year
        carac = carac.drop_duplicates(["Num_Acc", "annee"])
        lieux = lieux.drop_duplicates(["Num_Acc", "annee"])
        df = carac.merge(lieux, on=["Num_Acc", "annee"], how="left")
        df = df.merge(par_acc, on=["Num_Acc", "annee"], how="left")
        tables.append(df)

    df = pd.concat(tables, ignore_index=True)

    # cleaning and created variables
    df["dep"] = df["dep"].str.strip().str.zfill(2)  # "1" -> "01" ("2A" and "971" are unchanged)
    df["mortel"] = df["nb_tues"] > 0               # accident with at least one person killed
    df["zone"] = df["agg"].map({"1": "Hors agglomération", "2": "En agglomération"})
    return df


if __name__ == "__main__":
    df = load_all()
    df.to_csv("data/accidents_clean.csv", index=False)  # partially clean version

    # checks 
    print("Lignes, colonnes :", df.shape)
    print("\nAccidents / tués par année :")
    print(df.groupby("annee").agg(accidents=("Num_Acc", "size"), tues=("nb_tues", "sum")))
    print("\nPart d'accidents mortels (%) :", round(df["mortel"].mean() * 100, 2))
    print("\nValeurs manquantes (%) :")
    print((df.isna().mean() * 100).round(2))
    print("\nDoublons :", df.duplicated(["Num_Acc", "annee"]).sum())
    print("\nNombre de départements :", df["dep"].nunique())
    print(sorted(df["dep"].dropna().unique()))
    print("\nValeurs de zone :", df["zone"].value_counts(dropna=False).to_dict())