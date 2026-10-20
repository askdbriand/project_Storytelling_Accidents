
# Download the department boundaries (base map) into data/departements.geojson
import os
import requests

URL = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
CHEMIN = "data/departements.geojson"

os.makedirs("data", exist_ok=True)
if os.path.exists(CHEMIN):  # cache: do not re-download
    print("Déjà présent :", CHEMIN)
else:
    reponse = requests.get(URL, timeout=60)
    reponse.raise_for_status()           # stop if the site returns an error
    with open(CHEMIN, "wb") as f:
        f.write(reponse.content)
    print("Téléchargé :", CHEMIN)