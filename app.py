import json
import math
import os

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Road accidents", layout="wide")

LICENCE = " Open Licence (Etalab)"

INFO = {
    "logo": "assets/efrei_logo.jpg",                  
    "name": "Briand ASSIKIDANA",
    "email": "briandassikidana49@gmail.com",
    "year": "2026",
    "linkedin": "https://www.linkedin.com/in/briand-assikidana",
    "github": "https://github.com/askdbriand",
    "course": "Data Analysis & Visualization",
    "professor": "Mano Joseph Mathew",                 
    "professor_email": "mano.mathew@efrei.fr",
    "project": "Where is a road accident most likely to be fatal? (France, 2019-2024)",
}

JOURS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# comparable factors: file column + code labels (None = display the value)
FACTEURS = {
    "Lighting (day / night)": ("lum", {1: "Plein jour", 2: "Crépuscule ou aube", 3: "Nuit sans éclairage",
                                        4: "Nuit, éclairage éteint", 5: "Nuit éclairée"}),
    "Maximum permitted speed": ("vma", None),
    "Road type": ("catr", {1: "Autoroute", 2: "Route nationale", 3: "Route départementale",
                               4: "Voie communale", 5: "Hors réseau public", 6: "Parking",
                               7: "Métropole urbaine", 9: "Autre"}),
    "Weather report": ("atm", {1: "Normale", 2: "Pluie légère", 3: "Pluie forte", 4: "Neige ou grêle",
                      5: "Brouillard", 6: "Vent fort", 7: "Éblouissant", 8: "Couvert", 9: "Autre"}),
    "Weekday / weekend": ("weekend", {False: "Semaine", True: "Week-end"}),
}


def fmt(n):
    """Add spaces to large numbers: 327628 -> 327 628."""
    return f"{int(n):,}".replace(",", " ")


@st.cache_data(show_spinner=False)  # read only once
def charger():
    df = pd.read_csv("data/accidents_final.csv", dtype={"Num_Acc": str, "dep": str, "hrmn": str})
    qualite = pd.read_csv("data/qualite.csv")
    centres = pd.read_csv("data/centres_dep.csv", dtype={"dep": str})
    with open("data/departements.geojson", encoding="utf-8") as f:   # department boundaries
        contours = json.load(f)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")   # text -> actual date
    df["jour_sem"] = df["date"].dt.dayofweek                   # 0 = Monday, ... , 6 = Sunday
    df["tranche"] = df["heure"] // 3 * 3                       # 3-hour blocks 
    return df, qualite, centres, contours


try:
    df, qualite, centres, contours = charger()
except FileNotFoundError as e:
    st.error(f"File not found ({e.filename}). Launch first : python3 utils/prep.py, "
             "python3 utils/clean.py et python3 utils/geo.py")
    st.stop()

# name of each department: "75" -> "Paris"
noms = {f["properties"]["code"]: f["properties"]["nom"] for f in contours["features"]}

# reference values for all of France (used for KPIs and conclusions)
taux_global = df["mortel"].mean() * 100
tz = df.groupby("zone")["mortel"].mean() * 100
tm = df.groupby("moment")["mortel"].mean() * 100
tw = df.groupby("weekend")["mortel"].mean() * 100

# HOOK AND CONTEXT

# IDENTITY HEADER 
logo_col, info_col = st.columns([1, 4])
with logo_col:
    if os.path.exists(INFO["logo"]):                   # show the logo only if the file exists
        st.image(INFO["logo"], width=160, caption="EFREI Paris logo")
    else:
        st.markdown("**EFREI Paris**")                 # fallback when the logo file is missing
with info_col:
    st.markdown(
        f"**{INFO['name']}** · {INFO['year']}  \n"
        f"{INFO['course']} · Professor: {INFO['professor']}  \n"
        f"Project: {INFO['project']}  \n"
        f"[LinkedIn]({INFO['linkedin']}) · [GitHub]({INFO['github']}) · {INFO['email']}"
    )
st.divider()

st.title("Where is an accident most likely to be fatal?")

# DATASET, QUESTIONS AND DASHBOARD GUIDE 
tab_data, tab_questions, tab_guide = st.tabs(["Dataset", "Questions", "How to use the dashboard"])

with tab_data:
    st.markdown(
        f"**Source:** BAAC, the national database of road injury accidents (Ministère de l'intérieur), "
        f"published on data.gouv.fr under the {LICENCE}. Last update of the dataset: 29 December 2025.  \n"
        f"**Content used:** {fmt(len(df))} injury accidents recorded in France between {int(df['annee'].min())} "
        f"and {int(df['annee'].max())} ({fmt(df['metropole'].sum())} in mainland France).  \n"
        "**Structure:** one row per accident, built from three yearly files joined on the accident id: "
        "*characteristics* (date, time, department, lighting, weather), *places* (road type, speed limit) "
        "and *road users* (severity: killed, hospitalized...), summarised per accident.  \n"
        "**Main variable:** an accident is *fatal* when at least one person is killed. "
        "The share of fatal accidents is our measure of severity.  \n"
        "**Quality:** no duplicates; missing values and outliers are documented in the data quality section."
    )

with tab_questions:
    st.markdown(
        "**Main question:** where, and under which conditions, is an injury accident most likely to be fatal?\n\n"
        "1. Has severity changed between 2019 and 2024, and is the gap between areas stable? (section 1)\n"
        "2. Which conditions are associated with more severe accidents: lighting, speed limit, road type, weather, weekday? (section 2)\n"
        "3. On which days and at which hours are accidents the most severe? (section 3)\n"
        "4. Do night and location add up? (section 4)\n"
        "5. Which departments stand out, and where exactly do accidents happen? (sections 5 and 6)\n"
        "6. How strongly are these factors linked to fatal accidents and to each other? (section 7)"
    )

with tab_guide:
    st.markdown(
        "- **Sidebar:** choose the years, the area type and the departments, and the factor compared in section 2. "
        "The indicators and every chart follow these filters. The conclusions at the bottom always describe the whole of France.\n"
        "- **Indicators:** number of accidents, number of deaths, and share of fatal accidents compared with all of France "
        "(red = more severe than the national average).\n"
        "- **Charts:** hover to read exact values. Categories with fewer than 30 accidents are hidden.\n"
        "- **Map:** click a department, or choose it in the list. The map zooms in and shows one dot per accident "
        "(red = fatal, blue = non-fatal); hover a dot for its details."
    )


st.info(
    f"**Hook :** outside built-up areas, {tz['Hors agglomération']:.1f} %  accidents are fatal, "
    f"compared to {tz['En agglomération']:.1f} % in built-up areas. There are fewer accidents on these roads, "
    "but they are much more serious. This application identifies where and under what conditions the severity is greatest."
)
st.write("**Target audience :** citizens and local elected officials. **Context :** a personal-injury accident is a road accident that has resulted in at least one person being injured "
         ". In this context, a « fatal accident » means at least one person has been killed.")



# SIDEBAR
st.sidebar.header("Filters")
annees = st.sidebar.slider("Years", int(df["annee"].min()), int(df["annee"].max()),
                           (int(df["annee"].min()), int(df["annee"].max())))
zones = st.sidebar.multiselect("Area", sorted(df["zone"].unique()), default=sorted(df["zone"].unique()),
                               help="Within a built-up area = between the signs marking the entry to and exit from the municipality.")
deps = st.sidebar.multiselect("Departments (empty = all)", sorted(df["dep"].unique()))
choix = st.sidebar.selectbox("Factor to compare", list(FACTEURS), index=0,
                             help="Change the « Factors associated with severity » chart.")

d = df[df["annee"].between(annees[0], annees[1]) & df["zone"].isin(zones)]
if deps:
    d = d[d["dep"].isin(deps)]
if d.empty: # no results: notify instead of crashing
    st.warning(" No accidents with these filters.")
    st.stop()

# KPI 
taux = d["mortel"].mean() * 100
c1, c2, c3 = st.columns(3)
c1.metric("Accidents", fmt(len(d)))
c2.metric("People killed", fmt(d["nb_tues"].sum()))
c3.metric("Fatal accidents", f"{taux:.1f} %", f"{taux - taux_global:+.1f} pt vs all of France",
          delta_color="inverse", help="Red = more serious than the national average.")

# VISUAL 1: EVOLUTION 
st.subheader("1. The severity of accidents outside built-up areas remains higher every year")
g1 = d.groupby(["annee", "zone"])["mortel"].mean().mul(100).reset_index()
fig1 = px.line(g1, x="annee", y="mortel", color="zone", markers=True,
               labels={"annee": "Years", "mortel": "Fatal accidents (%)", "zone": "Area"})
fig1.update_xaxes(dtick=1)  # one graduation per year
if annees[0] <= 2020 <= annees[1]:
    fig1.add_vline(x=2020, line_dash="dot", annotation_text="Confinement")
st.plotly_chart(fig1)
st.caption("Description: Curves showing the proportion of fatal accidents by year, with one curve per zone. "
           "Each point = (accidents with at least one fatality) / (total accidents).")

# VISUAL 2: SELECTED FACTOR
col, labels = FACTEURS[choix]
d2 = d[d[col].notna()].copy()  # remove missing values
if labels:
    d2["cat"] = d2[col].map(labels)
else:
    d2["cat"] = d2[col].astype(int).astype(str) + " km/h"
g2 = d2.dropna(subset=["cat"]).groupby([col, "cat"])["mortel"].agg(["mean", "count"]).reset_index()
g2 = g2[g2["count"] >= 30]  # categories too small = unstable rates
g2["taux"] = g2["mean"] * 100
g2 = g2.rename(columns={"count": "accidents"}).sort_values(col)

st.subheader(f"2. Factors associated with severity: {choix}")
if g2.empty:
    st.warning("Not enough accidents for this factor with these filters.")
else:
    top = g2.loc[g2["taux"].idxmax()]
    st.markdown(f"**The highest rate : {top['cat']} ({top['taux']:.1f} %), "
                f"compared to an average of {taux:.1f} % across the selection.**")
    fig2 = px.bar(g2, x="cat", y="taux", hover_data={"accidents": True, "taux": ":.1f", "cat": False},
                  labels={"cat": choix, "taux": "Fatal accidents (%)", "accidents": "Accidents"})
    fig2.add_hline(y=taux, line_dash="dot", annotation_text="Average of the selection")
    st.plotly_chart(fig2)
    st.caption("Description: bars representing the share of fatal accidents for each category of the selected factor. "
               "Categories with fewer than 30 accidents are hidden. An association is observed, but it is not proof of causation.")

# VISUAL 3 : WHEN ?
st.subheader("3. When are accidents most serious?")
d3 = d.dropna(subset=["jour_sem", "tranche"])
g5 = d3.groupby(["jour_sem", "tranche"])["mortel"].agg(["mean", "count"]).reset_index()
g5 = g5[g5["count"] >= 30]  # time slots with too few hidden accidents
g5["taux"] = g5["mean"] * 100
tableau = g5.pivot(index="jour_sem", columns="tranche", values="taux")
tableau = tableau.reindex(index=range(7), columns=range(0, 24, 3))  # all rows and columns
tableau.index = JOURS                                               # 0 -> Monday, ...
tableau.columns = [f"{h}h-{h + 3}h" for h in range(0, 24, 3)]       # 0 -> 0h-3h,  ...

if tableau.stack().empty:
    st.warning("Not enough accidents for this chart with these filters.")
else:
    pire = tableau.stack().idxmax()  # (jour, tranche) du taux le plus élevé
    st.markdown(f"**The most critical time slot : {pire[0]} {pire[1]} ({tableau.stack().max():.1f} % of fatal accidents).**")
    fig5 = px.imshow(tableau, text_auto=".1f", aspect="auto", color_continuous_scale="YlOrRd",
                     labels={"x": "Time slot", "y": "Day of the week", "color": "Fatal accidents (%)"})
    st.plotly_chart(fig5)
    st.caption("Description: color-coded chart, where each cell represents the proportion of fatal accidents for a given day and a 3-hour time slot."
               "( more darker = more serious). Cells with fewer than 30 accidents are left blank.")

# VISUAL 4 : DO RISKS COMPOUND? (location x time of day)
st.subheader("4. Nighttime and the area: do the risks compound ?")
d4 = d.dropna(subset=["moment"])
g6 = d4.groupby(["zone", "moment"])["mortel"].agg(["mean", "count"]).reset_index()
g6 = g6[g6["count"] >= 30]
g6["taux"] = g6["mean"] * 100
g6 = g6.rename(columns={"count": "accidents"})

if g6.empty:
    st.warning("Not enough accidents for this chart with these filters.")
else:
    pire = g6.loc[g6["taux"].idxmax()]
    st.markdown(f"**The most serious case: : {pire['zone']}, {pire['moment'].lower()} ({pire['taux']:.1f} % of fatal accidents).**")
    fig6 = px.bar(g6, x="moment", y="taux", color="zone", barmode="group",
                  category_orders={"moment": ["Jour", "Crépuscule ou aube", "Nuit"]},
                  hover_data={"accidents": True, "taux": ":.1f"},
                  labels={"moment": "Time of day", "taux": "Fatal accidents (%)",
                          "zone": "Area", "accidents": "Accidents"})
    st.plotly_chart(fig6)
    st.caption("Description: grouped bar chart showing the share of fatal accidents, by time of day, "
               "one color per zone. This makes it possible to see whether the effect of nighttime is the same in urban areas as it is outside of them.")

# VISUAL 5 : SINGLE MAP (colored departments + incidents in the selected department)
st.subheader("5. The map: where are accidents the most serious?")
dm = d[d["metropole"]]
g3 = dm.groupby("dep").agg(accidents=("Num_Acc", "count"), tues=("nb_tues", "sum"),
                           taux=("mortel", "mean")).reset_index()
g3["taux"] = g3["taux"] * 100
g3["nom"] = g3["dep"].map(noms)       # nom du département pour la bulle d'information
# départements avec trop peu d'accidents masqués ; reset_index : le clic repère la zone par sa position
g3 = g3[g3["accidents"] >= 30].reset_index(drop=True)

dep_choisi = None
if g3.empty:
    st.warning("Not enough accidents for this chart with these filters.")
else:
    st.markdown(f"**Across departments, the share of fatal accidents ranges from {g3['taux'].min():.1f} % to {g3['taux'].max():.1f} %.**")
    options = ["None"] + sorted(g3["dep"])

    # 1) Clic sur la carte : Streamlit garde la sélection dans session_state (clé "carte_dep")
    clic = None
    try:
        etat = st.session_state.get("carte_dep")
        points = etat["selection"]["points"] if etat else []
        # curve_number 0 = la couche des départements (pas les points d'accidents)
        if points and points[0].get("curve_number", 0) == 0:
            p = points[0]
            if p.get("location"):
                clic = p["location"]
            elif p.get("point_index", 99999) < len(g3):
                clic = g3.loc[p["point_index"], "dep"]
    except (KeyError, TypeError, AttributeError):
        clic = None

    # 2) Un nouveau clic met à jour la liste ; la liste reste ensuite la référence
    if clic and clic != st.session_state.get("dernier_clic"):
        st.session_state["dep_sel"] = clic
    st.session_state["dernier_clic"] = clic
    if st.session_state.get("dep_sel") not in options:   # filtre changé : département plus disponible
        st.session_state["dep_sel"] = "None"

    st.write("Each department is colored according to its share of fatal accidents (the redder it is, the more serious the situation). "
             "Click on a department, or select it from the list (you can type its number): "
             "The map zooms in on it and displays each accident. Select « None » to return to the whole of France.")
    st.selectbox("Department to explore", options, key="dep_sel")
    if st.session_state["dep_sel"] != "None":
        dep_choisi = st.session_state["dep_sel"]

    # 3) La carte : départements colorés
    fig3 = px.choropleth_mapbox(
        g3, geojson=contours, locations="dep", featureidkey="properties.code",  # lien données <-> contours
        color="taux", color_continuous_scale="YlOrRd", hover_name="nom",
        hover_data={"dep": True, "accidents": True, "tues": True, "taux": ":.1f"},
        mapbox_style="open-street-map", zoom=4.5, center={"lat": 46.6, "lon": 2.5}, opacity=0.75,
        labels={"taux": "Fatal accidents(%)", "accidents": "Accidents", "tues": "Killed", "dep": "Department"})

    # 4) Si un département est choisi : on ajoute un point par accident sur la même carte
    if dep_choisi:
        dd = dm[dm["dep"] == dep_choisi]
        pts = dd.dropna(subset=["lat", "long"]).copy()
        if not pts.empty:
            mortels = pts[pts["mortel"]]                 # tous les accidents mortels sont affichés
            autres = pts[~pts["mortel"]]
            if len(autres) > 4000:                       # au-delà, échantillon pour garder une carte fluide
                autres = autres.sample(4000, random_state=42)  # graine fixe : même résultat à chaque fois
            pts = pd.concat([mortels, autres])

            # colonnes lisibles pour la bulle d'information
            pts["Gravity"] = pts["mortel"].map({True: "Mortel", False: "Non mortel"})
            pts["Date"] = pts["date"].dt.strftime("%d/%m/%Y")
            pts["Hour"] = pts["hrmn"]
            pts["Zone"] = pts["zone"]
            pts["Killed"] = pts["nb_tues"]
            pts["Seriously injured (hospitalized)"] = pts["nb_graves"]
            pts["Involved users"] = pts["nb_usagers"]
            pts["Road"] = pts["catr"].map(FACTEURS["Road type"][1])
            pts["Lighting"] = pts["lum"].map(FACTEURS["Lighting (day / night)"][1])
            pts["Speed max (km/h)"] = pts["vma"]

            fig7 = px.scatter_mapbox(
                pts, lat="lat", lon="long", color="Gravity",
                color_discrete_map={"Mortel": "#d7191c", "Non mortel": "#2c7bb6"},
                category_orders={"Gravity": ["Mortel", "Non mortel"]}, hover_name="Date",
                hover_data={"Hour": True, "Zone": True, "Killed": True, "Seriously injured (hospitalized)": True,
                            "Involved users": True, "Road": True, "Lighting": True,
                            "Speed max (km/h)": True, "Gravity": False, "lat": False, "long": False})
            fig7.update_traces(marker_size=8)
            for trace in fig7.data:                      # on ajoute les points sur la carte des départements
                fig3.add_trace(trace)

            # zoom automatique selon la taille du département
            etendue = max(pts["lat"].quantile(0.98) - pts["lat"].quantile(0.02),
                          pts["long"].quantile(0.98) - pts["long"].quantile(0.02))
            zoom = max(6, min(11, 8 - math.log2(max(etendue, 0.05))))
            centre = {"lat": pts["lat"].median(), "lon": pts["long"].median()}
        else:
            ligne = centres[centres["dep"] == dep_choisi]   # pas de GPS : on centre sur le département
            centre = {"lat": float(ligne["lat"].iloc[0]), "lon": float(ligne["long"].iloc[0])} if len(ligne) else {"lat": 46.6, "lon": 2.5}
            zoom = 8

        # fond des départements plus transparent pour bien voir les points
        fig3.update_traces(marker_opacity=0.35, selector=dict(type="choroplethmapbox"))
        fig3.update_layout(mapbox_center=centre, mapbox_zoom=zoom)

    fig3.update_layout(height=650, margin=dict(l=0, r=0, t=0, b=0),
                       legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.85)"))
    try:
        # on_select : permet de récupérer le département cliqué 
        st.plotly_chart(fig3, on_select="rerun", selection_mode="points", key="carte_dep")
    except TypeError:  # ancienne version de Streamlit : pas de clic possible
        st.plotly_chart(fig3)
    st.caption("Description: Map of metropolitan France. Each department is colored according to the proportion of accidents."
               "fatalities (yellow = lower, dark red = higher). Hover over a department to see its rate. "
               "Once a department is selected, each accident is displayed: red = at least one fatality, blue = no fatalities. "
               "Fatal accidents are all displayed; non-fatal accidents are limited to 4,000 sample. "
               "Overseas territories not represented.")

    # 5) Détails du département choisi
    if dep_choisi:
        st.markdown(f"#### Département {dep_choisi} : {noms.get(dep_choisi, '')}")
        dd = dm[dm["dep"] == dep_choisi]
        k1, k2, k3 = st.columns(3)
        k1.metric("Accidents", fmt(len(dd)))
        k2.metric("Personnes tuées", fmt(dd["nb_tues"].sum()))
        t_dep = dd["mortel"].mean() * 100
        k3.metric("Accidents mortels", f"{t_dep:.1f} %", f"{t_dep - taux:+.1f} pt vs la sélection", delta_color="inverse")

        # tableau : en agglomération vs hors agglomération
        par_zone = dd.groupby("zone").agg(Accidents=("Num_Acc", "count"), Tués=("nb_tues", "sum"),
                                          graves=("nb_graves", "sum"), taux=("mortel", "mean")).reset_index()
        par_zone["taux"] = (par_zone["taux"] * 100).round(1)
        par_zone = par_zone.rename(columns={"zone": "Zone", "graves": "Blessés graves (hospitalisés)",
                                            "taux": "Accidents mortels (%)"})
        st.dataframe(par_zone, hide_index=True)

# VISUAL 6 : CLASSEMENT 
if not g3.empty:
    st.subheader("6. The ranking of the departments")
    top10 = g3[g3["accidents"] >= 100].nlargest(10, "taux").sort_values("taux")
    top10["lib"] = top10["dep"] + " " + top10["nom"]
    if not top10.empty:
        best = top10.iloc[-1]                              # the list is sorted, the last row is the highest rate
        st.markdown(f"**Highest rate: {best['lib']} ({best['taux']:.1f} % of accidents are fatal, {fmt(best['accidents'])} accidents).**")
    fig4 = px.bar(top10, x="taux", y="lib", orientation="h", hover_data={"accidents": True, "tues": True},
                  labels={"taux": "Fatal accidents (%)", "lib": "Department", "accidents": "Accidents", "tues": "Killed"})
    fig4.update_yaxes(type="category")
    st.plotly_chart(fig4)
    st.caption("Description: The 10 metropolitan departments with the highest proportion of fatal accidents"
               "(at least 100 accidents within the selection).")

# VISUAL 7: CORRELATIONS 
st.subheader("7. How strongly are the factors linked to fatal accidents, and to each other?")
ind = pd.DataFrame({
    "Fatal accident": d["mortel"].astype(int),
    "Outside built-up area": (d["agg"] == 1).astype(int),   # agg = 1: outside built-up area
    "Night": (d["lum"] >= 3).astype(int),                    # lum 3 to 5: night
    "Weekend": d["weekend"].astype(int),
    "Max speed (km/h)": d["vma"],                            # empty values are ignored pair by pair
})
ind = ind.loc[:, ind.nunique() > 1]                          # a constant column has no correlation
if "Fatal accident" not in ind.columns or ind.shape[1] < 2:
    st.warning("Not enough variation to compute correlations with these filters.")
else:
    corr = ind.corr().round(2)                               # correlation between every pair of variables
    with_fatal = corr["Fatal accident"].drop("Fatal accident")
    best = with_fatal.abs().idxmax()                         # variable most linked to fatal accidents
    st.markdown(f"**Strongest link with fatal accidents: {best} (r = {with_fatal[best]:+.2f}).**")
    fig8 = px.imshow(corr, text_auto=True, zmin=-1, zmax=1, color_continuous_scale="RdBu_r",
                     aspect="auto", labels={"color": "Correlation (r)"})
    st.plotly_chart(fig8)
    st.caption("Description: correlation between each pair of variables (+1 = always together, 0 = no linear link, "
               "-1 = opposite). Coefficients with fatal accidents are small because fatal accidents are rare, "
               "so compare them with the rate charts above. A correlation is not a cause.")

# QUALITE DES DONNEES 
st.subheader("Data quality")
st.dataframe(qualite, hide_index=True)
st.caption("Report produced by utils/clean.py: duplicates, outliers, missing values, consistency.")


# KEY ELEMENTS, RECOMMENDATIONS AND LIMITS
st.subheader("Key elements")

# figures for the whole of France
open_road = df["agg"] == 1                                    # agg = 1: outside built-up areas
share_acc = open_road.mean() * 100                            # share of all accidents
share_fatal = open_road[df["mortel"]].mean() * 100            # share of fatal accidents
night_open = df.loc[open_road & (df["lum"] >= 3), "mortel"].mean() * 100
day_built = df.loc[~open_road & (df["lum"] == 1), "mortel"].mean() * 100

# most severe time slot (day x 3-hour slot) with at least 100 accidents
cren = df.dropna(subset=["jour_sem", "tranche"]).groupby(["jour_sem", "tranche"])["mortel"].agg(["mean", "count"]).reset_index()
cren = cren[cren["count"] >= 100]
pire = cren.loc[cren["mean"].idxmax()]
slot = f"{JOURS[int(pire['jour_sem'])]} {int(pire['tranche'])}h-{int(pire['tranche']) + 3}h"

# three departments with the highest share of fatal accidents (at least 100 accidents)
dep_stats = df[df["metropole"]].groupby("dep").agg(n=("Num_Acc", "count"), taux=("mortel", "mean")).reset_index()
dep_stats = dep_stats[dep_stats["n"] >= 100].nlargest(3, "taux")
top_deps = ", ".join(f"{r.dep} {noms.get(r.dep, '')} ({r.taux * 100:.1f} %)" for r in dep_stats.itertuples())

st.success(
    f"1. **Open roads concentrate the deadliest accidents.** Outside built-up areas there are {share_acc:.0f} % of accidents "
    f"but {share_fatal:.0f} % of fatal accidents ({tz['Hors agglomération']:.1f} % of accidents are fatal, "
    f"against {tz['En agglomération']:.1f} % in built-up areas).\n\n"
    f"2. **Night makes accidents more severe.** {tm['Nuit']:.1f} % of night accidents are fatal, against {tm['Jour']:.1f} % in daylight. "
    f"Outside built-up areas at night the figure is {night_open:.1f} %, against {day_built:.1f} % in built-up areas in daylight.\n\n"
    f"3. **Weekends are more severe than weekdays:** {tw[True]:.1f} % against {tw[False]:.1f} %.\n\n"
    f"4. **The most severe time slot** (at least 100 accidents) is {slot}: {pire['mean'] * 100:.1f} % of accidents are fatal.\n\n"
    f"5. **Departments that stand out** (at least 100 accidents): {top_deps}."
)

st.info(
    "**What could be done** \n\n"
    f"1. **Prioritise roads outside built-up areas.** They hold about {share_fatal:.0f} % of fatal accidents. "
    "Typical levers: speed management on the most dangerous stretches, safer road sides and junctions, clearer signage.\n\n"
    f"2. **Target nights and weekends.** Focus enforcement and awareness campaigns on the most severe time slots "
    "and check lighting and signage where accidents cluster.\n\n"
    f"3. **Start with the departments that stand out**. Local road-safety plans can use the accident map "
    "of this dashboard to find clusters of fatal accidents.\n\n"
    "4. **Measure what works.** Follow the same indicator every year and compare it with traffic data "
    "to know whether a measure reduces severity.\n\n"
    "**Next steps for the analysis:** this dataset cannot say why accidents are severe (speed actually driven, alcohol, fatigue, vehicle). "
    "Adding traffic volumes would give risk per kilometre driven, the vehicle and road user tables would show who is most exposed, "
    "and 2025 data can be added once published."
)

st.warning(
    "**Limits:** only injury accidents are recorded. Rates are not adjusted for traffic or population, "
    "and small departments have unstable rates. Factors are linked to each other (night and weekend go together). "
    "These results show associations, not causes. The data contains no personal information: only counts per accident are used."
)

st.divider()
st.caption(f"Course professor: {INFO['professor']} · {INFO['professor_email']}")