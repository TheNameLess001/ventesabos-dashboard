import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

if "logged" not in st.session_state or not st.session_state["logged"]:
    st.warning("Vous devez vous connecter depuis la page d'accueil.")
    st.stop()

st.title("💎 ANALYSEUR VAD - Fitness Park")

VAD_GOLD = "#FFD700"
st.markdown(f"""
    <style>
    .stApp {{ background-color: #fff; }}
    .block-container {{ padding-top: 2rem; }}
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        background-color: {VAD_GOLD};
        color: #222;
        font-weight:bold;
        border-radius: 10px 10px 0 0;
        border-bottom: 3px solid #FFBF00;
    }}
    .stTabs [data-baseweb="tab-list"] button {{
        background-color: #f4f4f4;
        color: #222;
        border-radius: 10px 10px 0 0;
        margin-right: 2px;
    }}
    </style>
""", unsafe_allow_html=True)

def to_excel(df_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    output.seek(0)
    return base64.b64encode(output.read()).decode()

def safe_read_any(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        for enc in ["utf-8", "cp1252", "latin-1"]:
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=enc, sep=None, engine='python')
            except Exception:
                continue
    else:
        return pd.read_excel(file, engine="openpyxl")
    st.error("Impossible de lire le fichier. Essayez un autre format ou encoding.")
    st.stop()

vad_file = st.file_uploader("Importer un fichier VAD (Excel ou CSV)", type=["xlsx", "xls", "csv"])
if not vad_file:
    st.info("Importez un fichier VAD pour démarrer l'analyse.")
    st.stop()

df = safe_read_any(vad_file)
df.columns = df.columns.str.strip()

st.info("Colonnes disponibles : " + ", ".join(df.columns))

# Sélection manuelle par l'utilisateur
with st.expander("🛠️ Sélectionner les colonnes à utiliser", expanded=True):
    col_date = st.selectbox("Colonne date de création", options=df.columns)
    col_auteur = st.selectbox("Colonne Auteur", options=df.columns)
    col_etat = st.selectbox("Colonne Etat de la facture ou de l'avoir", options=df.columns)
    col_mttc = st.selectbox("Colonne Montant TTC", options=df.columns)
    col_mtht = st.selectbox("Colonne Montant HT", options=df.columns)
    col_nom = st.selectbox("Colonne Nom (hors prénom)", options=df.columns)
    col_prenom = st.selectbox("Colonne Prénom", options=df.columns)
    col_produit = st.selectbox("Colonne Code du produit", options=df.columns)

# Cleaning rules
df = df[df[col_auteur].astype(str).str.lower() != "automatisme"]
df = df[df[col_etat].astype(str).str.lower() != "annulé"]

# 🚨 Conversion ultra-robuste des montants
def clean_money(s):
    return (
        s.astype(str)
        .str.replace("\u202f", "", regex=True)    # Espace insécable
        .str.replace(" ", "", regex=True)         # Espaces classiques
        .str.replace(",", ".", regex=False)       # Virgules --> points
        .str.replace("MAD", "", regex=False)
        .str.replace("dh", "", regex=False)
        .str.extract(r'([-+]?\d*\.?\d+)', expand=False)   # Garde chiffres/point/signes
    )

df[col_mtht] = pd.to_numeric(clean_money(df[col_mtht]), errors="coerce")
df[col_mttc] = pd.to_numeric(clean_money(df[col_mttc]), errors="coerce")

df = df[df[col_mtht] > 0]

# Client unique par Nom+Prénom
df['Client_Unique'] = (df[col_nom].astype(str).str.strip() + " " + df[col_prenom].astype(str).str.strip()).str.upper()
df['Date'] = pd.to_datetime(df[col_date], dayfirst=True, errors='coerce')

# Filtres interactifs
filtre_650 = st.sidebar.checkbox("⚡ Filtrer sur Montant TTC >= 650", value=False)
if filtre_650:
    df = df[df[col_mttc] >= 650]

# Onglets BI
tabs = st.tabs([
    "Résumé Global",
    "Par Club (Access+, Waterstation)",
    "Par Commercial",
    "Export"
])

# ==== Résumé Global ====
with tabs[0]:
    st.subheader("📊 Résumé Global VAD")
    st.write("Nombre de factures/avoirs :", len(df))
    st.write("Nombre de clients uniques :", df['Client_Unique'].nunique())
    st.write("Montant TTC total :", f"{df[col_mttc].sum():,.0f} MAD")
    st.write("Montant HT total :", f"{df[col_mtht].sum():,.0f} MAD")
    st.write("Nombre de lignes Access+ :", (df[col_produit].astype(str).str.upper() == "ALLACCESS+").sum())
    st.write("Nombre de lignes Waterstation :", (df[col_produit].astype(str).str.lower() == "waterstation").sum())
    # Graph TTC
    st.markdown("### Pie Chart - Répartition des produits (TT)")
    top_prod = df.groupby(col_produit)[col_mttc].sum().sort_values(ascending=False).head(8)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(top_prod.values, labels=top_prod.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)
    # Barplot MTT HT
    st.markdown("### Barplot - Montant HT par produit (Top 10)")
    ht_by_prod = df.groupby(col_produit)[col_mtht].sum().sort_values(ascending=False).head(10)
    plt.figure(figsize=(8,4))
    plt.bar(ht_by_prod.index, ht_by_prod.values, color=VAD_GOLD)
    plt.ylabel("Montant HT (MAD)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.clf()

# ==== Par Club (Access+, Waterstation) ====
with tabs[1]:
    st.subheader("🏟️ Analyse Club (Access+, Waterstation)")
    # Sélection club
    club_col_candidates = [c for c in df.columns if "club" in c.lower()]
    if not club_col_candidates:
        club_col_candidates = df.columns
    club_col = st.selectbox("Sélectionner la colonne club", options=club_col_candidates)
    access_df = df[df[col_produit].astype(str).str.upper() == "ALLACCESS+"]
    water_df = df[df[col_produit].astype(str).str.lower() == "waterstation"]
    st.markdown("### Access+ par club")
    acc_club = access_df.groupby(club_col)['Client_Unique'].nunique().sort_values(ascending=False)
    st.dataframe(acc_club.to_frame("Clients Access+ uniques"))
    fig, ax = plt.subplots()
    acc_club.plot(kind="bar", color="#5B7DFF", ax=ax)
    plt.ylabel("Clients Access+")
    plt.title("Access+ (clients uniques) par club")
    plt.tight_layout()
    st.pyplot(fig)
    plt.clf()

    st.markdown("### Waterstation par club")
    water_club = water_df.groupby(club_col)['Client_Unique'].nunique().sort_values(ascending=False)
    st.dataframe(water_club.to_frame("Clients Waterstation uniques"))
    fig, ax = plt.subplots()
    water_club.plot(kind="bar", color="#60C878", ax=ax)
    plt.ylabel("Clients Waterstation")
    plt.title("Waterstation (clients uniques) par club")
    plt.tight_layout()
    st.pyplot(fig)
    plt.clf()

# ==== Par Commercial ====
with tabs[2]:
    st.subheader("🧑‍💼 Analyse Commerciale VAD")
    # Sélection commerciale
    commercial_col_candidates = [c for c in df.columns if "commercial" in c.lower()]
    if not commercial_col_candidates:
        commercial_col_candidates = df.columns
    commercial_col = st.selectbox("Sélectionner la colonne commercial", options=commercial_col_candidates)
    vad_com = df.groupby(commercial_col)['Client_Unique'].nunique().sort_values(ascending=False)
    st.dataframe(vad_com.to_frame("Clients uniques"))
    fig, ax = plt.subplots()
    vad_com.plot(kind="bar", color="#FFD700", ax=ax)
    plt.ylabel("Clients uniques")
    plt.title("VAD - Clients uniques par commercial")
    plt.tight_layout()
    st.pyplot(fig)
    plt.clf()

# ==== Export ====
with tabs[3]:
    st.subheader("⬇️ Exporter les analyses")
    excel_data = to_excel({
        "VAD_Global": df,
        "Access+_par_club": acc_club.to_frame("Clients Access+ uniques"),
        "Waterstation_par_club": water_club.to_frame("Clients Waterstation uniques"),
        "Par_Commercial": vad_com.to_frame("Clients uniques")
    })
    st.download_button(
        label="📥 Télécharger toutes les données (Excel)",
        data=base64.b64decode(excel_data),
        file_name="VAD_analyse.xlsx"
    )
