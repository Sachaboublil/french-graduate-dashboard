import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- 1. Page Configuration ---

st.set_page_config(page_title="French Graduate Salary Dashboard", layout="wide")
col_title, col_sign = st.columns([4, 1])

with col_title:
    st.title("French Graduate Salary Dashboard")

with col_sign:
    st.markdown("""
        <p style="font-family: 'Georgia', serif; font-style: italic; font-weight: normal; 
                  font-size: 0.85em; color: #7F8C8D; text-align: right; margin-top: 10px;">
            Les rois de la Galette
        </p>
    """, unsafe_allow_html=True)
    st.image('Rois de la galette.jpg', width=80)





# --- 2. Data Loading & Cleaning ---
@st.cache_data
def load_data():
    df = pd.read_csv('Dataset_cleaned.csv', sep=";")

    
    # Détecter automatiquement la colonne salaire
    salary_col = [c for c in df.columns if "salaire" in c.lower() and "annuel" in c.lower() and "estim" in c.lower()][0]
    df = df.rename(columns={salary_col: "Salaire brut annuel estimé"})
    
    # Détecter automatiquement la colonne réponses
    reponses_col = [c for c in df.columns if "r" in c.lower() and "ponses" in c.lower()][0]
    df = df.rename(columns={reponses_col: "Nombre de réponses"})
    
    # Détecter automatiquement la colonne femmes
    femmes_col = [c for c in df.columns if "femmes" in c.lower()][0]
    df = df.rename(columns={femmes_col: "Part des femmes"})

    df["Salaire brut annuel estimé"] = pd.to_numeric(df["Salaire brut annuel estimé"], errors="coerce")
    df["Nombre de réponses"] = pd.to_numeric(df["Nombre de réponses"], errors="coerce")
    df["Part des femmes"] = pd.to_numeric(df["Part des femmes"], errors="coerce")
    df["Part des hommes"] = 100 - df["Part des femmes"]

    col_ins = [c for c in df.columns if "insertion" in c.lower()][0]
    df[col_ins] = pd.to_numeric(df[col_ins], errors="coerce")
    return df, col_ins

data, col_insertion_name = load_data()

domain_mapping = {
    "Droit, économie et gestion": "Law, Economics and Management",
    "Ensemble Masters LMD (hors Masters enseignement)": "Ensemble Masters LMD (Excl. Teaching)",
    "Lettres, langues, arts": "Arts and Languages",
    "Masters enseignement": "Teaching Masters",
    "Sciences humaines et sociales": "Humanities and Social Sciences",
    "Sciences, technologies et santé": "Science, Technology and Health"
}
reverse_mapping = {v: k for k, v in domain_mapping.items()}
all_domains = list(domain_mapping.values())

if "selected_domains" not in st.session_state:
    st.session_state.selected_domains = all_domains.copy()

# --- 3. Filter data based on selection ---
selected_fr = [reverse_mapping.get(d, d) for d in st.session_state.selected_domains]
filtered = data[data["Domaine"].isin(selected_fr)]

# --- 4. KPI Metrics ---
kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("Total Graduates Surveyed", f"{int(filtered['Nombre de réponses'].sum()):,}")
with kpi2:
    st.metric("Avg Gross Annual Salary", f"€{int(filtered['Salaire brut annuel estimé'].mean()):,}")
with kpi3:
    st.metric("Avg Insertion Rate", f"{filtered[col_insertion_name].mean():.1f}%")

st.divider()

# --- 5. Domain Filter Buttons + Bar Chart ---
st.markdown("**Filter by domain:**")
btn_cols = st.columns(len(all_domains) + 1)

with btn_cols[0]:
    if st.button("All", use_container_width=True):
        st.session_state.selected_domains = all_domains.copy()
        st.rerun()

for i, domain in enumerate(all_domains):
    with btn_cols[i + 1]:
        is_selected = domain in st.session_state.selected_domains
        label = f"✓ {domain}" if is_selected else domain
        if st.button(label, use_container_width=True, key=f"btn_{i}"):
            if is_selected and len(st.session_state.selected_domains) > 1:
                st.session_state.selected_domains.remove(domain)
            elif not is_selected:
                st.session_state.selected_domains.append(domain)
            st.rerun()

# Bar chart
df_plot = data.groupby("Domaine")["Salaire brut annuel estimé"].mean().reset_index()
df_plot["Domaine_EN"] = df_plot["Domaine"].replace(domain_mapping)
df_plot = df_plot.sort_values("Salaire brut annuel estimé")
df_plot["selected"] = df_plot["Domaine_EN"].isin(st.session_state.selected_domains)

fig_bar = px.bar(
    df_plot, x="Salaire brut annuel estimé", y="Domaine_EN",
    orientation="h",
    title="Average Salary by Domain",
    labels={"Domaine_EN": "Domain", "Salaire brut annuel estimé": "Gross Salary (€)"},
    color="selected",
    color_discrete_map={True: "#3498DB", False: "#D5D8DC"}
)
fig_bar.update_layout(xaxis_range=[0, 45000], height=400, showlegend=False)
st.plotly_chart(fig_bar, use_container_width=True)

# --- 6. Line Chart ---
title_line = "Salary Trend (All Domains)" if len(st.session_state.selected_domains) == len(all_domains) \
             else f"Salary Trend: {', '.join(st.session_state.selected_domains)}"

fig_line = px.line(
    filtered.groupby("Année")["Salaire brut annuel estimé"].mean().reset_index(),
    x="Année", y="Salaire brut annuel estimé",
    title=title_line,
    labels={"Année": "Year", "Salaire brut annuel estimé": "Salary (€)"},
    markers=True
)
st.plotly_chart(fig_line, use_container_width=True)

# --- 7. Gender Distribution & Regional Map ---
col_left, col_right = st.columns(2)

with col_left:
    df_gender = filtered.groupby("Domaine")[["Part des femmes", "Part des hommes"]].mean().dropna().reset_index()
    df_gender["Domaine_EN"] = df_gender["Domaine"].replace(domain_mapping)
    df_melted = df_gender.melt(id_vars="Domaine_EN", value_vars=["Part des femmes", "Part des hommes"],
                                var_name="Gender", value_name="Share")
    df_melted["Gender"] = df_melted["Gender"].replace({"Part des femmes": "Women", "Part des hommes": "Men"})

    fig_sex = px.bar(df_melted, x="Domaine_EN", y="Share", color="Gender", barmode="stack",
                  color_discrete_map={"Women": "#C0392B", "Men": "#2980B9"},
                  title="Gender Balance (Filtered)",
                  labels={"Domaine_EN": "Domain", "Share": "Share (%)"})
    fig_sex.update_layout(yaxis_range=[0, 100], height=500)
    st.plotly_chart(fig_sex, use_container_width=True)

with col_right:
    try:
        df_bours = pd.read_excel('Boursiers France.xlsx')
        df_bours.columns = ['Academie', 'Proportion']

        academie_to_region = {
            'AIX-MARSEILLE': "Provence-Alpes-Côte d'Azur", 'AMIENS': 'Hauts-de-France',
            'BESANCON': 'Bourgogne-Franche-Comté', 'BORDEAUX': 'Nouvelle-Aquitaine',
            'CLERMONT-FERRAND': 'Auvergne-Rhône-Alpes', 'CORSE': 'Corse',
            'CRETEIL': 'Île-de-France', 'DIJON': 'Bourgogne-Franche-Comté',
            'GRENOBLE': 'Auvergne-Rhône-Alpes', 'GUADELOUPE': 'Guadeloupe',
            'GUYANE': 'Guyane', 'LA REUNION': 'La Réunion', 'LILLE': 'Hauts-de-France',
            'LIMOGES': 'Nouvelle-Aquitaine', 'LYON': 'Auvergne-Rhône-Alpes',
            'MARTINIQUE': 'Martinique', 'MAYOTTE': 'Mayotte', 'MONTPELLIER': 'Occitanie',
            'NANCY-METZ': 'Grand Est', 'NANTES': 'Pays de la Loire',
            'NICE': "Provence-Alpes-Côte d'Azur", 'NORMANDIE': 'Normandie',
            'ORLEANS-TOURS': 'Centre-Val de Loire', 'PARIS': 'Île-de-France',
            'POITIERS': 'Nouvelle-Aquitaine', 'REIMS': 'Grand Est',
            'RENNES': 'Bretagne', 'STRASBOURG': 'Grand Est',
            'TOULOUSE': 'Occitanie', 'VERSAILLES': 'Île-de-France'
        }

        df_bours['Region'] = df_bours['Academie'].str.upper().map(academie_to_region)
        df_reg = df_bours.groupby('Region')['Proportion'].mean().reset_index()

        geojson = requests.get("https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson").json()

        bins = [0, 35, 40, 45, 50, 100]
        labels = ['Less than 35%', '35% to 40%', '40% to 45%', '45% to 50%', 'More than 50%']
        df_reg['Category'] = pd.cut(df_reg['Proportion'], bins=bins, labels=labels)
        color_map = {
            'Less than 35%': '#d6eaf8', '35% to 40%': '#85c1e9',
            '40% to 45%': '#2e86c1', '45% to 50%': '#1a5276', 'More than 50%': '#0a1f44'
        }

        fig_map = px.choropleth(
            df_reg, geojson=geojson, locations='Region', featureidkey='properties.nom',
            color='Category', color_discrete_map=color_map,
            category_orders={'Category': labels[::-1]},
            title='Scholarship Student Share by Region (%)'
        )
        fig_map.update_geos(fitbounds="locations", visible=False, projection_type="mercator")
        fig_map.update_layout(
            height=500, margin={"r": 0, "t": 50, "l": 0, "b": 0},
            geo=dict(projection_scale=6, center=dict(lat=46.5, lon=2.5))
        )
        st.plotly_chart(fig_map, use_container_width=True)

    except Exception as e:
        st.error(f"Regional Map Load Error: {e}")
