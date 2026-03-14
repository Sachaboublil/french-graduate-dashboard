import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="French Graduate Salary Dashboard", layout="wide")

st.markdown("""
    <style>
        [data-testid="collapsedControl"] {display: none}
        section[data-testid="stSidebar"] {display: none}
    </style>
""", unsafe_allow_html=True)

st.title("French Graduate Salary Dashboard")

data = pd.read_csv("/Users/sachaboublil/Desktop/Travail 2/DSBA/T2/Data visualization/Dataset_cleaned.csv", sep=";")
data["Salaire brut annuel estimé"] = pd.to_numeric(data["Salaire brut annuel estimé"], errors="coerce")
data["Nombre de réponses"] = pd.to_numeric(data["Nombre de réponses"], errors="coerce")
data["Part des femmes"] = pd.to_numeric(data["Part des femmes"], errors="coerce")
data["Part des hommes"] = 100 - data["Part des femmes"]

col_insertion = [c for c in data.columns if "insertion" in c.lower()][0]
data[col_insertion] = pd.to_numeric(data[col_insertion], errors="coerce")
insertion_rate = data[col_insertion].mean()

domain_mapping = {
    "Droit, économie et gestion": "Law, Economics and Management",
    "Ensemble Masters LMD (hors Masters enseignement)": "Ensemble Masters LMD (hors Masters)",
    "Lettres, langues, arts": "Arts and Languages",
    "Masters enseignement": "Teaching Masters",
    "Sciences humaines et sociales": "Humanities and Social Sciences",
    "Sciences, technologies et santé": "Science, Technology and Health"
}

# KPI metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Number of French Graduates Surveyed", f"{int(data['Nombre de réponses'].sum()):,}")
with col2:
    st.metric("Average Gross Annual Salary", f"€{int(data['Salaire brut annuel estimé'].mean()):,}")
with col3:
    st.metric("Insertion Rate", f"{insertion_rate:.1f}%")

st.divider()

# Graph 1 - Bar chart avec sélection multiple
df_plot = data.groupby("Domaine")["Salaire brut annuel estimé"].mean().reset_index()
df_plot["Domaine"] = df_plot["Domaine"].replace(domain_mapping)
df_plot = df_plot.sort_values("Salaire brut annuel estimé")

fig2 = px.bar(
    df_plot,
    x="Salaire brut annuel estimé", y="Domaine",
    orientation="h",
    title="French graduate average annual salary across domains (click to filter)",
    labels={"Domaine": "Domain", "Salaire brut annuel estimé": "Gross Annual Salary (€)"}
)
fig2.update_layout(xaxis_range=[0, 40000], height=700, clickmode="event+select")
fig2.update_traces(unselected=dict(marker=dict(opacity=0.3)))

selected = st.plotly_chart(fig2, use_container_width=True, on_select="rerun", key="bar_chart")

# Récupérer les domaines cliqués
all_domains = df_plot["Domaine"].tolist()

if selected and selected.get("selection") and selected["selection"].get("points"):
    selected_domains = list(set([p["label"] for p in selected["selection"]["points"]]))
else:
    selected_domains = all_domains  # Par défaut : tous sélectionnés

# Inverser le mapping pour filtrer sur les données originales
reverse_mapping = {v: k for k, v in domain_mapping.items()}
selected_domains_fr = [reverse_mapping.get(d, d) for d in selected_domains]

# Graph 2 - Line chart filtré
filtered = data[data["Domaine"].isin(selected_domains_fr)]

if set(selected_domains) == set(all_domains):
    title_line = "French graduate average annual salary variation over years"
else:
    title_line = f"Average annual salary over years — {', '.join(selected_domains)}"

fig1 = px.line(
    filtered.groupby("Année")["Salaire brut annuel estimé"].mean().reset_index(),
    x="Année", y="Salaire brut annuel estimé",
    title=title_line,
    labels={"Année": "Year", "Salaire brut annuel estimé": "Average Annual Salary (€)"}
)
st.plotly_chart(fig1, use_container_width=True)

# Graph 3 (left) + Graph 4 (right)
col_left, col_right = st.columns(2)

with col_left:
    df_femmes = data.groupby("Domaine")[["Part des femmes", "Part des hommes"]].mean().dropna().reset_index()
    df_femmes["Domaine"] = df_femmes["Domaine"].replace(domain_mapping)
    df_melted = df_femmes.melt(id_vars="Domaine", value_vars=["Part des femmes", "Part des hommes"],
                                var_name="Gender", value_name="Share")
    df_melted["Gender"] = df_melted["Gender"].replace({"Part des femmes": "Women", "Part des hommes": "Men"})

    fig3 = px.bar(df_melted,
                  x="Domaine", y="Share", color="Gender",
                  barmode="stack",
                  color_discrete_map={"Women": "#C0392B", "Men": "#2980B9"},
                  title="Share of women and men graduates by domain",
                  labels={"Domaine": "Domain", "Share": "Share (%)", "Gender": "Gender"})
    fig3.update_layout(yaxis_range=[0, 100], height=700)
    st.plotly_chart(fig3, use_container_width=True)

with col_right:
    df_bours = pd.read_excel('/Users/sachaboublil/Desktop/Travail 2/DSBA/T2/Data visualization/Boursiers France.xlsx')
    df_bours.columns = ['Academie', 'Proportion']

    academie_to_region = {
        'AIX-MARSEILLE': "Provence-Alpes-Côte d'Azur",
        'AMIENS': 'Hauts-de-France',
        'BESANCON': 'Bourgogne-Franche-Comté',
        'BORDEAUX': 'Nouvelle-Aquitaine',
        'CLERMONT-FERRAND': 'Auvergne-Rhône-Alpes',
        'CORSE': 'Corse',
        'CRETEIL': 'Île-de-France',
        'DIJON': 'Bourgogne-Franche-Comté',
        'GRENOBLE': 'Auvergne-Rhône-Alpes',
        'GUADELOUPE': 'Guadeloupe',
        'GUYANE': 'Guyane',
        'LA REUNION': 'La Réunion',
        'LILLE': 'Hauts-de-France',
        'LIMOGES': 'Nouvelle-Aquitaine',
        'LYON': 'Auvergne-Rhône-Alpes',
        'MARTINIQUE': 'Martinique',
        'MAYOTTE': 'Mayotte',
        'MONTPELLIER': 'Occitanie',
        'NANCY-METZ': 'Grand Est',
        'NANTES': 'Pays de la Loire',
        'NICE': "Provence-Alpes-Côte d'Azur",
        'NORMANDIE': 'Normandie',
        'ORLEANS-TOURS': 'Centre-Val de Loire',
        'PARIS': 'Île-de-France',
        'POITIERS': 'Nouvelle-Aquitaine',
        'REIMS': 'Grand Est',
        'RENNES': 'Bretagne',
        'STRASBOURG': 'Grand Est',
        'TOULOUSE': 'Occitanie',
        'VERSAILLES': 'Yvelines'
    }

    df_bours['Region'] = df_bours['Academie'].map(academie_to_region)
    df_region = df_bours.groupby('Region')['Proportion'].mean().reset_index()

    geojson = requests.get("https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson").json()

    bins = [0, 35, 40, 45, 50, 100]
    labels = ['Less than 35%', '35% to 40%', '40% to 45%', '45% to 50%', 'More than 50%']
    df_region['Category'] = pd.cut(df_region['Proportion'], bins=bins, labels=labels)

    color_map = {
        'Less than 35%': '#d6eaf8',
        '35% to 40%': '#85c1e9',
        '40% to 45%': '#2e86c1',
        '45% to 50%': '#1a5276',
        'More than 50%': '#0a1f44'
    }

    fig4 = px.choropleth(
        df_region,
        geojson=geojson,
        locations='Region',
        featureidkey='properties.nom',
        color='Category',
        color_discrete_map=color_map,
        category_orders={'Category': labels[::-1]},
        title='Share of scholarship students by region (%)',
        labels={'Category': 'Scholarship students (%)'}
    )



    fig4.update_geos(
    fitbounds="locations",
    visible=False,
    projection_type="mercator"
)
    fig4.update_layout(
    height=700,
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
    geo=dict(
        projection_scale=6,
        center=dict(lat=46.5, lon=2.5)
    )
)


    st.plotly_chart(fig4, use_container_width=True)
