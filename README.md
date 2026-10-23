# Road accidents in France: where is an accident most likely to be fatal?

Individual Streamlit project (Data Storytelling), EFREI Paris, group Ing2_DAI.  
**Author:** ASSIKIDANA Briand (20251450)  
**Course:** Data Analysis & Visualization | **Professor:** Mano Joseph Mathew  

**Deployed app:** https://road-accidents-france.streamlit.app/  
**Demo video:** [assets/demo.mov](assets/demo.mov)

## 1. Question and audience
- **Question**: where, and under which conditions, is an injury accident most likely to be fatal?
- **Audience**: citizens and local elected officials.
- **Story arc**: hook (outside built-up areas, 10.4 % of accidents are fatal against 3.0 % in built-up areas), context, analysis (trend, factors, time, combination of risks, map, correlations), key elements, recommendations and limits.
- **Key results (2019-2024, France)**: 5.7 % of injury accidents are fatal; 10.4 % outside built-up areas against 3.0 % inside; 7.5 % at night against 4.9 % in daylight; 7.1 % at weekends against 5.2 % on weekdays. Outside built-up areas there are about 36 % of accidents but about two thirds of fatal accidents (computed in the app).
- These are **observed associations**, not cause-and-effect relationships.

## 2. Data
| Item | Detail |
|---|---|
| Dataset | Bases de données annuelles des accidents corporels de la circulation routière (BAAC), annual databases of road injury accidents, years 2005 to 2024 |
| Portal | data.gouv.fr: https://www.data.gouv.fr/datasets/53698f4ca3a729239d2036df/ |
| Producer | Ministère de l'intérieur (data.gouv.fr organization) |
| Licence | Licence Ouverte / Open Licence (Etalab): https://www.etalab.gouv.fr/wp-content/uploads/2014/05/Licence_Ouverte.pdf |
| Created / last updated | 8 July 2013 / 29 December 2025 (annual frequency) |
| Period used | 2019 to 2024 (6 years) |
| Volume | 327,628 injury accidents (309,756 in mainland France) |

**Files used** (4 per year, 24 CSV files in total): characteristics, places, road users, vehicles (the vehicles file is downloaded but not used in the application). The "registered vehicles" files are not used.
**Why 2019 and not earlier**: the structure of the database changed in 2019. The most recent data available stops in 2024.

**Base map**: simplified boundaries of the mainland departments, file `departements-version-simplifiee.geojson` from the GitHub repository `gregoiredavid/france-geojson` (Licence Ouverte 2.0). Names and codes come from INSEE (2018 vintage) and the boundaries from IGN Admin Express COG (2018 edition). This is a second source, used only as a base map (no accident data).

## 3. Cleaning, validation and created variables
- **File and column names that differ between years**: files are recognised by keyword and renamed `table-year.csv`; the column `Accident_Id` (2022) is renamed `Num_Acc`.
- **Join**: characteristics + places + road user severity, on `Num_Acc` + year. Severity is computed per accident before the join (an accident has several road users).
- **"Not provided" values (-1)** converted to empty values.
- **Outlier maximum speeds**: 966 values set to empty (the accident is kept).
- **Departments** formatted on 2 characters ("1" becomes "01").
- **GPS coordinates**: comma replaced by a point; plausibility check for mainland France.

| Check | Result |
|---|---|
| Rows at start / at end | 327,628 / 327,628 (no row removed) |
| Duplicates (Num_Acc + year) | 0 |
| Invalid dates / invalid hours | 0 / 0 |
| Accidents with no road user / inconsistencies (deaths > road users) | 0 / 0 |
| Missing values | vma 2.45 %; surf 0.04 %; atm 0.01 %; lum and catr 0 % |
| Missing GPS | 5.45 %, all in overseas territories (not shown on the map) |

The full report is displayed in the application ("Data quality" section).

**Created variables**: `mortel` (at least one person killed), `zone` (inside or outside a built-up area), `moment` (daytime, twilight or dawn, night), `heure` (hour), `tranche` (3-hour slot), `date`, `jour_sem` (day of the week), `weekend`, `metropole` (mainland France).

## 4. Application content
- **Header**: EFREI logo, author, year, course, professor, project title, LinkedIn and GitHub links, and the data source and licence line.
- **Introduction**: hook, audience and context, and three tabs: *Dataset* (source, content, structure, main variable), *Questions* (the questions answered by each section) and *How to use the dashboard*.
- **Sidebar**: years, area type, departments, factor to compare.
- **KPIs** linked to the filters: accidents, people killed, share of fatal accidents (difference with France).
- **7 interactive visuals**:
  1. trend by year and by area type;
  2. severity by a chosen factor (lighting, speed limit, road type, weather, weekday/weekend);
  3. heatmap of day of the week × 3-hour slot;
  4. area type × time of day;
  5. single map: departments coloured by share of fatal accidents (rate shown on hover); selecting a department (click or list) zooms in and shows one dot per accident, with date, time, area, deaths, seriously injured, road users, road type, lighting and speed limit on hover;
  6. ranking of departments;
  7. correlation matrix between fatal accident, outside built-up area, night, weekend and maximum speed.
- **Data quality** section.
- **Key elements** (computed for the whole of France, independent of the filters), **recommendations** ("What could be done": levers to test, not proven by the dataset), next steps for the analysis and limits.
- **Footer** with the course professor's contact.
- **Accessibility**: labelled axes and units, a text description under every visual, readable palettes (red/blue for the accident dots).

## 5. Technical choices
- `st.cache_data` for loading the files; aggregations computed from already cleaned files.
- Accident map: all fatal accidents are displayed, non-fatal ones are limited to 4,000 per department (sample with a fixed seed `random_state=42`, so it is reproducible).
- Minimum of 30 accidents per category, slot or department in the charts (100 for rankings and key elements) to limit unstable rates.
- A department can be selected by clicking the map or from a list (the list is the fallback if clicking is not available).

## 6. Ethics, privacy and limits
- No personal data: only counts per accident are used (no age, sex or address).
- Only **injury accidents** are recorded.
- Rates are not adjusted for traffic or population.
- Small departments have unstable rates.
- Factors are linked to each other (for example night and weekend). Correlation coefficients with fatal accidents are small because fatal accidents are rare.
- Only the severity of accidents is studied, not their causes.
- The recommendations are hypotheses to test: the dataset has no information on traffic, speeds actually driven, or road-safety measures.

## 7. Reproduce the project
```bash
pip install -r requirements.txt
python utils/io.py       # downloads the 24 BAAC files (data/raw)
python utils/prep.py     # reading, join -> data/accidents_clean.csv
python utils/clean.py    # cleaning -> data/accidents_final.csv, qualite.csv, centres_dep.csv
python utils/geo.py      # department boundaries -> data/departements.geojson
streamlit run app.py
```
The processed files used by the app (`data/accidents_final.csv`, about 41 MB, `qualite.csv`, `centres_dep.csv` and `departements.geojson`) are included in the repository so the app starts immediately. The raw BAAC files are not included: `utils/io.py` downloads them and the scripts above regenerate everything.
Tested with Python 3.13. 

## 8. Structure
```
app.py                  Streamlit application
utils/io.py             data download
utils/prep.py           reading, join
utils/clean.py          cleaning, validation, variables
utils/geo.py            department boundaries
utils/inspect_cols.py   column comparison between years
utils/check1.py         spot checks
utils/check2.py         GPS coordinates check
assets/efrei_logo.jpg   EFREI Paris logo
assets/demo.mov.        
data/                   data/ processed data used by the app (raw files downloaded by utils/io.py, not versioned).
requirements.txt
```

## 9. Credits and licences
- Accident data: Ministère de l'intérieur, BAAC, data.gouv.fr, Licence Ouverte / Open Licence, dataset last updated on 29 December 2025.
- Department boundaries: IGN Admin Express COG (2018 edition) and INSEE, via the GitHub repository gregoiredavid/france-geojson, Licence Ouverte 2.0.
- Base maps: OpenStreetMap contributors.
- Libraries: Streamlit, pandas, NumPy, Plotly, Requests.
- EFREI Paris logo: property of EFREI Paris, used for identification only.
- This project is student work: it has no official status and is neither endorsed nor approved by the data producers.