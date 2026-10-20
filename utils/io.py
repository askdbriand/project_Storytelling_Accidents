
# Download the 2019–2024 BAAC files from data.gouv.fr
import os
import requests

URL = "https://www.data.gouv.fr/api/1/datasets/53698f4ca3a729239d2036df/"
YEARS = range(2019, 2025)  # 2019 à 2024

# Identifying the names of the CSV files to facilitate downloading, as some files are named differently (e.g :  Caract_2024, carcteristiques-2021)
TABLES = {"caracteristiques": "car", "lieux": "lieux", "usagers": "usagers", "vehicules": "vehicules"}

os.makedirs("data/raw", exist_ok=True)
resp = requests.get(URL, timeout=30)
resp.raise_for_status()                      # stop if the site returns an error
resources = resp.json()["resources"]         # list of 106 files

for r in resources:
    title = r["title"].lower()
    for name, start in TABLES.items():
        for year in YEARS:
            # correct format, correct filename prefix, correct year, and excluding "immatricule" files
            if r["format"] == "csv" and title.startswith(start) and str(year) in title and "immatricul" not in title:
                path = f"data/raw/{name}-{year}.csv"
                if not os.path.exists(path):  # do not re-download
                    print("Téléchargement :", path)
                    file_resp = requests.get(r["url"], timeout=120)
                    file_resp.raise_for_status()   #  error if the download fails
                    with open(path, "wb") as f:    # we write only after success
                        f.write(file_resp.content)

# counts only the expected files
found = sum(os.path.exists(f"data/raw/{n}-{y}.csv") for n in TABLES for y in YEARS)
print("Fichiers présents :", found, "/ 24")