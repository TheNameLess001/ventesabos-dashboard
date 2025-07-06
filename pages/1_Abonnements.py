import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime

# ... autres imports ...

DF_KEY = "abos_df"      # Unique pour chaque page : "recouvrement_df", "vad_df", etc.
FILE_KEY = "abos_file"  # Pareil

if DF_KEY not in st.session_state:
    st.session_state[DF_KEY] = None
if FILE_KEY not in st.session_state:
    st.session_state[FILE_KEY] = None

use_previous = False

if st.session_state[DF_KEY] is not None:
    st.success("Un fichier est déjà chargé pour cette page.")
    use_previous = st.checkbox("Utiliser le fichier déjà importé ?", value=True)

if use_previous:
    df = st.session_state[DF_KEY]
else:
    uploaded_file = st.file_uploader("Importer un fichier Abonnements...", key="abos_upload")
    if uploaded_file:
        # Remplace cette partie par TON code de lecture habituel (csv/excel, cleaning etc.)
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, encoding="utf-8", sep=None, engine='python')
        else:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        # ... processing/cleaning ici ...
        st.session_state[DF_KEY] = df
        st.session_state[FILE_KEY] = uploaded_file
    else:
        st.info("Merci d'importer un fichier pour commencer.")
        st.stop()

# 👉 Ici tu peux continuer avec ton code analytique en utilisant df.
# ========== PROTECTION LOGIN ==========
if "logged" not in st.session_state or not st.session_state["logged"]:
    st.warning("Vous devez vous connecter depuis la page d'accueil.")
    st.stop()

st.title("📈 Analyse Ventes Abonnements Fitness Park")

def to_excel(df_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet, index=True)
    output.seek(0)
    return base64.b64encode(output.read()).decode()

def safe_read_csv(file):
    for enc in ["utf-8", "cp1252", "latin-1"]:
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=enc, sep=None, engine='python')
        except Exception:
            continue
    st.error("Impossible de lire le fichier CSV. Essayez de l'enregistrer à nouveau en UTF-8 ou Excel.")
    st.stop()

def match_col(cols, targets):
    """Matching exact sans accents ni case ni espaces."""
    def norm(x): return x.strip().lower().replace('é','e').replace('è','e').replace('ê','e').replace("’","'").replace("_", " ").replace("-", " ")
    normed = {norm(c):c for c in cols}
    for t in targets:
        t_norm = norm(t)
        if t_norm in normed:
            return normed[t_norm]
    return None

file = st.file_uploader("Fichier Ventes (CSV ou Excel)", type=["csv", "xlsx"])
if not file:
    st.info("Importez un fichier pour démarrer l'analyse.")
    st.stop()

ext = file.name.split('.')[-1]
df = safe_read_csv(file) if ext == "csv" else pd.read_excel(file, engine="openpyxl")
df.columns = df.columns.str.strip()

# -- Auto-matching exact --
col_candidats_offres = [
    "Nom de l’offre", "Nom de l'offre", "Offre", "Type d'abonnement", "Produit"
]
col_candidats_date = [
    "Date de création", "Date", "Date d'inscription"
]
col_candidats_com = [
    "Nom du commercial initial", "Commercial", "Prénom du commercial initial", "Vendeur"
]
col_candidats_nom = [
    "Nom", "Nom du client", "Nom complet"
]
col_candidats_prenom = [
    "Prénom", "Prenom", "Prenom du client"
]
col_candidats_lastpass = [
    "Dernier passage 6M", "Dernier passage", "Date dernier passage"
]

offres_col = match_col(df.columns, col_candidats_offres)
date_col = match_col(df.columns, col_candidats_date)
comm_col = match_col(df.columns, col_candidats_com)
nom_col = match_col(df.columns, col_candidats_nom)
prenom_col = match_col(df.columns, col_candidats_prenom)
lastpass_col = match_col(df.columns, col_candidats_lastpass)

st.subheader("🛠️ Vérification colonnes (modifiez si besoin)")
offres_col = st.selectbox("Colonne des Offres", options=df.columns.tolist(), index=df.columns.get_loc(offres_col) if offres_col in df.columns else 0)
date_col = st.selectbox("Colonne Date de création", options=df.columns.tolist(), index=df.columns.get_loc(date_col) if date_col in df.columns else 0)
comm_col = st.selectbox("Colonne Commercial", options=df.columns.tolist(), index=df.columns.get_loc(comm_col) if comm_col in df.columns else 0)
nom_col = st.selectbox("Colonne Nom", options=df.columns.tolist(), index=df.columns.get_loc(nom_col) if nom_col in df.columns else 0)
prenom_col = st.selectbox("Colonne Prénom", options=df.columns.tolist(), index=df.columns.get_loc(prenom_col) if prenom_col in df.columns else 0)
lastpass_col = st.selectbox("Colonne Dernier Passage", options=df.columns.tolist(), index=df.columns.get_loc(lastpass_col) if lastpass_col in df.columns else 0)

# --- Filtres dynamiques ---
st.subheader("🎛️ Filtres dynamiques")
offres_uniques = df[offres_col].dropna().unique().tolist()
commerciaux_uniques = df[comm_col].dropna().unique().tolist()
filtre_offre = st.multiselect("Filtrer par Offre", offres_uniques, offres_uniques)
filtre_com = st.multiselect("Filtrer par Commercial", commerciaux_uniques, commerciaux_uniques)
df = df[df[offres_col].isin(filtre_offre) & df[comm_col].isin(filtre_com)]

tabs = st.tabs(["📊 Dashboard Club Recouvrement", "🧑‍💼 Dashboard Commercial", "📊Graphiques", "🔴Inactifs"])

# ===== VUE CLUB =====
with tabs[0]:
    st.subheader("🔵 Tableau Club (quantités)")
    table_club = df.groupby(offres_col).size().to_frame("Quantité").sort_values("Quantité", ascending=False)
    st.dataframe(table_club)

    st.subheader("📅 Ventes par semaine (Club)")
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    table_week = df.groupby(df[date_col].dt.to_period('W'))[offres_col].value_counts().unstack().fillna(0)
    st.dataframe(table_week)

# ===== VUE COMMERCIALE =====
with tabs[1]:
    st.subheader("🟢 Tableau Commercial (quantités)")
    table_com = df.groupby([comm_col, offres_col]).size().unstack(fill_value=0)
    st.dataframe(table_com)

    st.subheader("📅 Ventes par semaine (par Commercial)")
    week_com = df.groupby([df[date_col].dt.to_period('W'), comm_col]).size().unstack(fill_value=0)
    st.dataframe(week_com)

    st.subheader("🗂️ Détail des ventes (Commercial x Offre)")
    table_com_offre = df.pivot_table(index=comm_col, columns=offres_col, values=date_col, aggfunc="count", fill_value=0)
    st.dataframe(table_com_offre)

# ===== GRAPHIQUES =====
with tabs[2]:
    st.subheader("📊 Graphique : Ventes Club par Offre")
    club_data = df.groupby(offres_col).size().sort_values(ascending=False)
    plt.figure(figsize=(9,4))
    club_data.plot(kind="bar", color="#3498db")
    plt.ylabel("Quantité vendue")
    plt.xlabel("Offre")
    plt.title("Ventes Club par Offre")
    st.pyplot(plt.gcf())
    plt.clf()

    st.subheader("📊 Graphique : Ventes par Commercial (stacked)")
    pivot = df.pivot_table(index=comm_col, columns=offres_col, values=date_col, aggfunc="count", fill_value=0)
    pivot.plot(kind="bar", stacked=True, figsize=(10,5))
    plt.ylabel("Quantité")
    plt.xlabel("Commercial")
    plt.title("Ventes par Commercial et Offre")
    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.clf()

    st.subheader("📈 Évolution des ventes (total par jour)")
    daily = df.groupby(df[date_col].dt.date).size()
    daily.plot(figsize=(10,4), color="#e67e22")
    plt.ylabel("Quantité totale")
    plt.xlabel("Date")
    plt.title("Ventes totales par jour")
    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.clf()

    st.subheader("📈 Ventes par commercial par semaine (stacked)")
    df['Semaine'] = df[date_col].dt.to_period('W')
    week_com_pivot = df.pivot_table(index='Semaine', columns=comm_col, values=offres_col, aggfunc="count", fill_value=0)
    week_com_pivot.plot(kind="bar", stacked=True, figsize=(10,5))
    plt.title("Ventes par commercial par semaine")
    plt.ylabel("Quantité")
    plt.xlabel("Semaine")
    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.clf()

# ===== INACTIFS =====
with tabs[3]:
    st.subheader("🙅‍♂️ Analyse des clients inactifs")
    if lastpass_col and nom_col and prenom_col:
        df['Nom complet'] = df[nom_col].astype(str).str.strip() + ' ' + df[prenom_col].astype(str).str.strip()
        df['Dernier passage dt'] = pd.to_datetime(df[lastpass_col], dayfirst=True, errors='coerce')
        now = pd.to_datetime(datetime.now().date())
        nb_jours = st.slider("Période d'inactivité (jours)", min_value=7, max_value=180, step=1, value=15)
        dernier_passage = df.groupby('Nom complet')['Dernier passage dt'].max().reset_index()
        dernier_passage = dernier_passage[dernier_passage['Dernier passage dt'].notna()]
        dernier_passage['Inactif'] = (now - dernier_passage['Dernier passage dt']).dt.days > nb_jours
        inactive = dernier_passage[dernier_passage['Inactif']]
        # Détail commercial
        last_trans = df.sort_values(['Nom complet','Dernier passage dt']).drop_duplicates('Nom complet', keep='last')
        inactive_com = inactive.merge(last_trans[['Nom complet',comm_col,'Dernier passage dt']], on=['Nom complet','Dernier passage dt'], how='left')
        res_inactif = inactive_com.groupby(comm_col)['Nom complet'].count().reset_index().rename(
            columns={'Nom complet':f'Nb clients inactifs (> {nb_jours}j)', comm_col:"Commercial"}
        ).sort_values(f'Nb clients inactifs (> {nb_jours}j)', ascending=False)
        st.markdown(f"**Inactifs par commercial (période > {nb_jours} jours)**")
        st.dataframe(res_inactif)
        st.markdown("**Détail inactifs (nom complet, dernier passage)**")
        st.dataframe(inactive_com[['Nom complet',comm_col,'Dernier passage dt']].sort_values(comm_col))
    else:
        st.warning("Impossible d'analyser les inactifs (colonnes manquantes). Vérifiez vos sélections.")

# ===== EXPORT =====
st.markdown("#### 📥 Export (Excel)")
export_dict = {
    "Tableau Club": table_club,
    "Tableau Commercial": table_com,
    "Détail Com x Offre": table_com_offre,
    "Par Semaine Club": table_week,
    "Par Semaine Com": week_com,
}
excel_data = to_excel(export_dict)
st.download_button(
    label="Télécharger tout (Excel)",
    data=base64.b64decode(excel_data),
    file_name="analyse_abos.xlsx"
)
