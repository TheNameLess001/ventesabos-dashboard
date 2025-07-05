import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime

DEFAULT_LOGO = "fitnesspark.png"

def find_col(df, *alternatives):
    def clean(c): return c.strip().lower().replace("’","'").replace("é", "e").replace("è", "e").replace("ê", "e")
    colnames = [clean(c) for c in df.columns]
    for alt in alternatives:
        alt2 = clean(alt)
        for i, c in enumerate(colnames):
            if alt2 in c:
                return df.columns[i]
    return None

def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def set_css(dark):
    bg = "#181818" if dark else "#f7f9fa"
    txt = "#fafafa" if dark else "#2c3e50"
    accent = "#EAC601" if dark else "#3498db"
    st.markdown(
        f"""
        <style>
        body, .reportview-container {{background-color: {bg} !important; color: {txt} !important;}}
        .stButton>button, .stDownloadButton>button {{
            background-color: {accent} !important; color: white !important; 
            border:none; border-radius: 12px; font-weight:bold;
            padding: 8px 20px 8px 20px; margin: 5px 0 5px 0;
        }}
        .title-main {{
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: 2px;
            text-align:center;
            color: {txt};
        }}
        .subheader-main {{
            font-size: 1.3rem;
            font-weight: 700;
            letter-spacing: 1px;
            color: {accent};
            margin-top:10px;
        }}
        .subtitle {{
            font-size: 1.1rem;
            font-weight: 600;
            color: {txt};
        }}
        footer {{
            font-size:0.93rem;
            color: #B6B6B6;
            text-align:right;
        }}
        </style>
        """, unsafe_allow_html=True
    )

def show_logo_and_header(dark):
    txt = "#fafafa" if dark else "#2c3e50"
    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;align-items:center;">
            <img src="data:image/png;base64,{get_image_base64(DEFAULT_LOGO)}" width="150"/>
            <span class="title-main">VENTES ABONNEMENTS FITNESS PARK</span>
            <span style="color:{txt};font-size:16px;">Dashboard d'analyse • {datetime.now().strftime('%d/%m/%Y')}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def copyright():
    st.markdown("""
        <hr>
        <div style='text-align:right; color:#B6B6B6; font-size:0.93rem;'>
        © 2025 Fitness Park Analytics • by <b>GPT Partner</b> 🏆
        </div>
    """, unsafe_allow_html=True)

def to_excel(df_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=True)
    output.seek(0)
    return base64.b64encode(output.read()).decode()

def load_data(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, encoding='cp1252', sep=';')
    else:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
    df.columns = [c.strip() for c in df.columns]
    nom_col = find_col(df, "Nom", "nom")
    prenom_col = find_col(df, "Prénom", "prenom")
    if nom_col and prenom_col:
        df['Nom complet'] = df[nom_col].astype(str).str.strip() + ' ' + df[prenom_col].astype(str).str.strip()
    else:
        df['Nom complet'] = ""
    return df

def render_table_with_total(df, groupby_col, table_name=""):
    grouped = df.groupby(groupby_col).size().sort_values(ascending=False).to_frame("Quantité")
    total_row = pd.DataFrame({'Quantité': [grouped['Quantité'].sum()]}, index=["TOTAL"])
    table = pd.concat([total_row, grouped])
    st.markdown(f"<span class='subheader-main'>{table_name}</span>", unsafe_allow_html=True)
    st.dataframe(table)
    return table

def render_table_by_week(df, date_col, groupby_col, table_name=""):
    df_temp = df.copy()
    df_temp[date_col] = pd.to_datetime(df_temp[date_col], dayfirst=True, errors='coerce')
    df_temp['Semaine'] = df_temp[date_col].dt.strftime('%Y-%U')
    grouped = df_temp.groupby(['Semaine', groupby_col]).size().unstack(fill_value=0)
    grouped = grouped.loc[grouped.sum(axis=1).sort_index().index]
    st.markdown(f"<span class='subheader-main'>{table_name}</span>", unsafe_allow_html=True)
    st.dataframe(grouped)
    return grouped

def render_table_by_week_combined(df, date_col, groupby_col, table_name=""):
    df_temp = df.copy()
    df_temp[date_col] = pd.to_datetime(df_temp[date_col], dayfirst=True, errors='coerce')
    df_temp['Semaine'] = df_temp[date_col].dt.strftime('%Y-%U')
    pivot = pd.pivot_table(df_temp, index='Semaine', columns=groupby_col, values="Nom complet", aggfunc="count", fill_value=0)
    st.markdown(f"<span class='subheader-main'>{table_name}</span>", unsafe_allow_html=True)
    st.dataframe(pivot)
    return pivot

def render_commercial_detail(df, com_col, offre_col, table_name="Détail Commerciaux x Abos"):
    pivot = df.pivot_table(index=com_col, columns=offre_col, values="Nom complet", aggfunc="count", fill_value=0)
    total_row = pd.DataFrame(pivot.sum(axis=0)).T
    total_row.index = ["TOTAL"]
    pivot = pd.concat([total_row, pivot])
    st.markdown(f"<span class='subheader-main'>{table_name}</span>", unsafe_allow_html=True)
    st.dataframe(pivot)
    return pivot

def pretty_chart_palette():
    return [
        "#ffc300", "#2ecc71", "#3498db", "#e74c3c", "#6c3483",
        "#1abc9c", "#f39c12", "#d35400", "#34495e", "#A3CB38",
        "#8854d0", "#fdcb6e", "#00b894", "#636e72", "#00cec9"
    ]

def main():
    st.set_page_config(page_title="VENTES ABOS FITNESS PARK", page_icon="📊", layout="wide")
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        if st.button("🌓 Mode Sombre / Light", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
    set_css(st.session_state.dark_mode)
    show_logo_and_header(st.session_state.dark_mode)
    st.markdown("---")

    uploaded_file = st.file_uploader("**Importer le fichier de ventes (CSV ou Excel)**", type=['csv','xlsx'])
    if uploaded_file:
        df = load_data(uploaded_file)
        nom_offre_col = find_col(df, "Nom de l’offre", "Nom de l'offre", "offre")
        com_col = find_col(df, "Nom du commercial initial", "commercial")
        etat_col = find_col(df, "Etat", "etat")
        date_crea_col = find_col(df, "Date de création", "date création", "date")
        last_pass_col = "Dernier passage 6M"
        nom_col = find_col(df, "Nom", "nom")
        prenom_col = find_col(df, "Prénom", "prenom")
        export_dict = {}

        # --- GLOBAL FILTERS
        offres_all = sorted(df[nom_offre_col].dropna().unique()) if nom_offre_col else []
        commerciaux_all = sorted(df[com_col].dropna().unique()) if com_col else []
        filt_annule_global = st.sidebar.checkbox("Exclure les ventes annulées (colonne Etat)", value=False)
        selected_offres_global = st.sidebar.multiselect("Filtrer les offres (global)", offres_all, default=offres_all)
        selected_com_global = st.sidebar.multiselect("Filtrer les commerciaux (global)", commerciaux_all, default=commerciaux_all)
        # Filtering data
        df_filtered = df.copy()
        if filt_annule_global and etat_col:
            df_filtered = df_filtered[df_filtered[etat_col].astype(str).str.upper().str.strip() != "ANNULÉ"]
        if nom_offre_col:
            df_filtered = df_filtered[df_filtered[nom_offre_col].isin(selected_offres_global)]
        if com_col:
            df_filtered = df_filtered[df_filtered[com_col].isin(selected_com_global)]

        tabs = st.tabs([
            "🏢 Vue Club", 
            "🧑‍💼 Vue Commerciale", 
            "📊 Graphiques", 
            "🙅‍♂️ Clients Inactifs", 
            "🔄 Comparaison 2 fichiers"
        ])

        # --- VUE CLUB ---
        with tabs[0]:
            st.markdown("#### Analyse Club (quantités d'abos, filtrage live)")
            subtab_club = st.tabs(["Par offre", "Par semaine", "Offre × Semaine"])
            if not nom_offre_col or not date_crea_col:
                st.error("Colonne de l'offre ou de date absente.")
            else:
                # sous-vue 1
                with subtab_club[0]:
                    table = render_table_with_total(df_filtered, nom_offre_col, "Tableau Club (Total en haut)")
                    export_dict["Club"] = table
                # sous-vue 2
                with subtab_club[1]:
                    table_week = render_table_by_week(df_filtered, date_crea_col, nom_offre_col, "Ventes par semaine (offre)")
                    export_dict["Club_semaine"] = table_week
                # sous-vue 3
                with subtab_club[2]:
                    table_comb = render_table_by_week_combined(df_filtered, date_crea_col, nom_offre_col, "Ventes Offre × Semaine")
                    export_dict["Club_combine"] = table_comb

        # --- VUE COMMERCIALE ---
        with tabs[1]:
            st.markdown("#### Analyse Commerciale (quantités, filtrage live)")
            subtab_com = st.tabs(["Par commercial", "Par semaine", "Commercial × Semaine"])
            if not com_col or not nom_offre_col or not date_crea_col:
                st.error("Colonnes commercial, offre ou date absentes.")
            else:
                # sous-vue 1
                with subtab_com[0]:
                    table_com = render_table_with_total(df_filtered, com_col, "Tableau Commercial (Total en haut)")
                    st.markdown("---")
                    pivot_com = render_commercial_detail(df_filtered, com_col, nom_offre_col, "Détail des abos vendus (brut, Com x Offre)")
                    export_dict["Commercial"] = table_com
                    export_dict["Com_Detail"] = pivot_com
                # sous-vue 2
                with subtab_com[1]:
                    table_com_week = render_table_by_week(df_filtered, date_crea_col, com_col, "Ventes par semaine (commercial)")
                    export_dict["Com_semaine"] = table_com_week
                # sous-vue 3
                with subtab_com[2]:
                    table_combine = render_table_by_week_combined(df_filtered, date_crea_col, com_col, "Ventes Commercial × Semaine")
                    export_dict["Com_combine"] = table_combine

        # --- VUE GRAPHIQUES ---
        with tabs[2]:
            st.markdown("#### Visualisations graphiques filtrées (live)")
            if not (nom_offre_col and com_col and date_crea_col and "Nom complet" in df_filtered.columns):
                st.error("Colonnes manquantes dans le fichier.")
            else:
                pal = pretty_chart_palette()
                # Graph 1 : ventes par commercial x offre (stacked)
                st.markdown("<span class='subtitle'>Ventes par commercial (stacked par offre)</span>", unsafe_allow_html=True)
                if not df_filtered.empty:
                    pivot = df_filtered.pivot_table(index=com_col, columns=nom_offre_col, values="Nom complet", aggfunc="count", fill_value=0)
                    pivot = pivot.loc[(pivot.sum(axis=1)).sort_values(ascending=False).index]
                    pivot.plot(kind="bar", stacked=True, figsize=(10, 5), color=pal)
                    plt.title("Ventes par commercial et offre (quantités)")
                    plt.ylabel("Quantité")
                    plt.xlabel("Commercial")
                    plt.tight_layout()
                    st.pyplot(plt.gcf())
                    plt.clf()
                    export_dict["Graphique (pivot quantités)"] = pivot
                # Graph 2 : ventes club par offre
                st.markdown("<span class='subtitle'>Ventes club par offre</span>", unsafe_allow_html=True)
                club_tab = df_filtered.groupby(nom_offre_col).size().sort_values(ascending=False).to_frame("Quantité")
                club_tab.plot(kind="bar", figsize=(10,4), color=pal)
                plt.title("Quantité vendue par offre (Club)")
                plt.ylabel("Quantité")
                plt.xlabel("Offre")
                plt.tight_layout()
                st.pyplot(plt.gcf())
                plt.clf()
                export_dict["Graphique Club"] = club_tab
                # Graph 3 : evolution des ventes club par jour
                st.markdown("<span class='subtitle'>Évolution du total ventes par jour</span>", unsafe_allow_html=True)
                df_filtered[date_crea_col] = pd.to_datetime(df_filtered[date_crea_col], dayfirst=True, errors='coerce')
                daily = df_filtered.groupby(df_filtered[date_crea_col].dt.date).size()
                daily.plot(figsize=(10,4), color=pal[0])
                plt.title("Ventes totales par jour (club/commerciaux confondus)")
                plt.ylabel("Quantité")
                plt.xlabel("Date")
                plt.tight_layout()
                st.pyplot(plt.gcf())
                plt.clf()
                export_dict["Graphique Ventes Jour"] = daily.to_frame("Quantité")
                # Graph 4 : ventes par commercial par semaine (NOUVEAU)
                st.markdown("<span class='subtitle'>Ventes par commercial par semaine (stacked)</span>", unsafe_allow_html=True)
                df_filtered['Semaine'] = df_filtered[date_crea_col].dt.strftime('%Y-%U')
                week_com_pivot = df_filtered.pivot_table(index='Semaine', columns=com_col, values="Nom complet", aggfunc="count", fill_value=0)
                week_com_pivot.plot(kind="bar", stacked=True, figsize=(10,5), color=pal)
                plt.title("Ventes par commercial par semaine")
                plt.ylabel("Quantité")
                plt.xlabel("Semaine")
                plt.tight_layout()
                st.pyplot(plt.gcf())
                plt.clf()
                export_dict["Graphique Com Semaine"] = week_com_pivot

        # --- CLIENTS INACTIFS ---
        with tabs[3]:
            st.markdown("#### Liste des clients inactifs (période paramétrable)")
            if not (com_col and "Dernier passage 6M" in df_filtered.columns and "Nom complet" in df_filtered.columns):
                st.error("Colonnes manquantes dans le fichier. (dernier passage = Dernier passage 6M)")
            else:
                df_inac = df_filtered.copy()
                df_inac['Dernier passage'] = pd.to_datetime(df_inac["Dernier passage 6M"], dayfirst=True, errors='coerce')
                now = pd.to_datetime(datetime.now().date())
                nb_jours = st.slider(
                    "Sélectionne la période d'inactivité (en jours)", 
                    min_value=7, max_value=180, step=1, value=15, key="periode_inactif"
                )
                dernier_passage = df_inac.groupby('Nom complet')['Dernier passage'].max().reset_index()
                dernier_passage = dernier_passage[dernier_passage['Dernier passage'].notna()]
                dernier_passage['Inactif'] = (now - dernier_passage['Dernier passage']).dt.days > nb_jours
                inactive = dernier_passage[dernier_passage['Inactif']]
                last_trans = df_inac.sort_values(['Nom complet','Dernier passage']).drop_duplicates('Nom complet', keep='last')
                inactive_com = inactive.merge(last_trans[['Nom complet',com_col,'Dernier passage']], on=['Nom complet','Dernier passage'], how='left')
                res_inactif = inactive_com.groupby(com_col)['Nom complet'].count().reset_index().rename(
                    columns={'Nom complet':f'Nb clients inactifs (> {nb_jours}j)', com_col:"Commercial"}
                ).sort_values(f'Nb clients inactifs (> {nb_jours}j)', ascending=False)
                st.markdown(f"<span class='subtitle'>Inactifs par commercial (période &gt; {nb_jours} jours)</span>", unsafe_allow_html=True)
                st.dataframe(res_inactif)
                st.markdown("<span class='subtitle'>Détail inactifs (nom complet, dernier passage)</span>", unsafe_allow_html=True)
                st.dataframe(inactive_com[['Nom complet',com_col,'Dernier passage']].sort_values(com_col))
                export_dict["Clients inactifs"] = res_inactif
                export_dict["Inactifs détail"] = inactive_com[['Nom complet',com_col,'Dernier passage']]

        # --- EXPORT GLOBAL (SAUF COMPARAISON) ---
        st.sidebar.markdown("---")
        st.sidebar.header("Export Global")
        if export_dict:
            excel_data = to_excel(export_dict)
            st.sidebar.download_button(
                label="📥 Télécharger tout (Club, Com, Détail, Graph, Inactif)",
                data=base64.b64decode(excel_data),
                file_name="analyse_ventes_quantite.xlsx"
            )

        # --- COMPARAISON DEUX FICHIERS ---
        with tabs[4]:
            st.markdown("#### Comparaison entre deux fichiers (Club & Commercial)")
            file1 = st.file_uploader("Fichier période 1", type=['csv','xlsx'], key="cmp1")
            file2 = st.file_uploader("Fichier période 2", type=['csv','xlsx'], key="cmp2")
            if file1 and file2:
                df1 = load_data(file1)
                df2 = load_data(file2)
                nom_offre_col1 = find_col(df1, "Nom de l’offre", "Nom de l'offre", "offre")
                nom_offre_col2 = find_col(df2, "Nom de l’offre", "Nom de l'offre", "offre")
                com_col1 = find_col(df1, "Nom du commercial initial", "commercial")
                com_col2 = find_col(df2, "Nom du commercial initial", "commercial")
                # Vue Club
                if nom_offre_col1 and nom_offre_col2:
                    club1 = df1.groupby(nom_offre_col1).size().to_frame("Quantité_1")
                    club2 = df2.groupby(nom_offre_col2).size().to_frame("Quantité_2")
                    cmp_club = club1.join(club2, lsuffix='_1', rsuffix='_2', how='outer').fillna(0)
                    cmp_club['Diff Quantité'] = cmp_club['Quantité_2'] - cmp_club['Quantité_1']
                    st.markdown("##### 📊 Comparaison Club (quantités)")
                    st.dataframe(cmp_club)
                # Vue Com
                if com_col1 and com_col2:
                    com1 = df1.groupby(com_col1).size().to_frame("Quantité_1")
                    com2 = df2.groupby(com_col2).size().to_frame("Quantité_2")
                    cmp_com = com1.join(com2, lsuffix='_1', rsuffix='_2', how='outer').fillna(0)
                    cmp_com['Diff Quantité'] = cmp_com['Quantité_2'] - cmp_com['Quantité_1']
                    st.markdown("##### 📊 Comparaison Commerciaux (quantités)")
                    st.dataframe(cmp_com)

    copyright()

if __name__ == "__main__":
    main()
