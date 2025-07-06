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

# --- Upload ---
vad_file = st.file_uploader("Importer un fichier VAD (Excel ou CSV)", type=["xlsx", "xls", "csv"])
if not vad_file:
    st.info("Importez un fichier VAD pour démarrer l'analyse.")
    st.stop()

df = safe_read_any(vad_file)
df.columns = df.columns.str.strip()

# --- Auto-match de colonnes (avec fallback pour user selection) ---
def auto_select(candidates, dfcols, contains_any=None):
    for c in candidates:
        if c in dfcols:
            return c
    if contains_any:
        for c in dfcols:
            if any(word in c.lower() for word in contains_any):
                return c
    return dfcols[0]

with st.expander("🛠️ Vérifiez/sélectionnez les colonnes à utiliser", expanded=False):
    cols = list(df.columns)
    col_date = st.selectbox("Colonne date de création", options=cols,
                            index=cols.index(auto_select(
                                ["Date de création de la facture", "Date"], cols, ["date"])))
    col_auteur = st.selectbox("Colonne Auteur", options=cols,
                              index=cols.index(auto_select(
                                ["Auteur"], cols, ["auteur"])))
    col_etat = st.selectbox("Colonne Etat de la facture ou de l'avoir", options=cols,
                            index=cols.index(auto_select(
                                ["Etat de la facture ou de l'avoir", "Etat"], cols, ["etat"])))
    col_mttc = st.selectbox("Colonne Montant TTC", options=cols,
                            index=cols.index(auto_select(
                                ["Montant TTC facture ou avoir", "Montant TTC"], cols, ["ttc"])))
    col_mtht = st.selectbox("Colonne Montant HT", options=cols,
                            index=cols.index(auto_select(
                                ["Montant HT facture ou avoir", "Montant HT de la ligne de facture / avoir", "Montant HT"], cols, ["ht"])))
    col_nom = st.selectbox("Colonne Nom (hors prénom)", options=cols,
                           index=cols.index(auto_select(
                                ["Nom"], cols, ["nom"])))
    col_prenom = st.selectbox("Colonne Prénom", options=cols,
                              index=cols.index(auto_select(
                                ["Prénom"], cols, ["prenom"])))
    col_produit = st.selectbox("Colonne Code du produit", options=cols,
                               index=cols.index(auto_select(
                                ["Code du produit"], cols, ["code du produit", "code"])))
    # Club & Commercial
    club_col = st.selectbox("Colonne Club", options=cols,
                            index=cols.index(auto_select(["Club"], cols, ["club"])))
    commercial_col = st.selectbox("Colonne Commercial", options=cols,
                                  index=cols.index(auto_select(
                                      ["Auteur", "Nom du commercial actuel", "Nom du commercial initial"], cols, ["auteur", "commercial"])))

# Cleaning rules
df = df[df[col_auteur].astype(str).str.lower() != "automatisme"]
df = df[df[col_etat].astype(str).str.lower() != "annulé"]

# Conversion ultra-robuste des montants
def clean_money(s):
    return (
        s.astype(str)
        .str.replace("\u202f", "", regex=True)
        .str.replace(" ", "", regex=True)
        .str.replace(",", ".", regex=False)
        .str.replace("MAD", "", regex=False)
        .str.replace("dh", "", regex=False)
        .str.replace("-", "", regex=False)
        .str.extract(r'([-+]?\d*\.?\d+)', expand=False)
    )

df[col_mtht] = pd.to_numeric(clean_money(df[col_mtht]), errors="coerce")
df[col_mttc] = pd.to_numeric(clean_money(df[col_mttc]), errors="coerce")

df = df[df[col_mtht].notnull() & df[col_mttc].notnull()]

# **SUPPRESSION des lignes TTC <= 0**
df = df[df[col_mttc] > 0]
df = df[df[col_mtht] > 0]

# Client unique par Nom+Prénom
df['Client_Unique'] = (df[col_nom].astype(str).str.strip() + " " + df[col_prenom].astype(str).str.strip()).str.upper()
df['Date'] = pd.to_datetime(df[col_date], dayfirst=True, errors='coerce')

# ---- Filtres auteur ----
all_auteurs = sorted(df[col_auteur].dropna().unique().tolist())
selected_auteurs = st.sidebar.multiselect("Filtrer par Auteur", all_auteurs, default=all_auteurs)

df = df[df[col_auteur].isin(selected_auteurs)]

# Filtres interactifs
filtre_650 = st.sidebar.checkbox("⚡ Filtrer sur Montant TTC = 650", value=False)
if filtre_650:
    df = df[df[col_mttc] = 650]

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
    st.markdown("### Pie Chart - Répartition des produits (TT)")
    top_prod = df.groupby(col_produit)[col_mttc].sum().sort_values(ascending=False).head(8)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(top_prod.values, labels=top_prod.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)
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
    auteurs_club = st.multiselect("Filtrer par Auteur (Club)", all_auteurs, default=all_auteurs, key="auteurs_club")
    club_df = df[df[col_auteur].isin(auteurs_club)]
    access_df = club_df[club_df[col_produit].astype(str).str.upper() == "ALLACCESS+"]
    water_df = club_df[club_df[col_produit].astype(str).str.lower() == "waterstation"]
    st.markdown("### Access+ par club")
    acc_club = access_df.groupby(club_col)['Client_Unique'].nunique().sort_values(ascending=False)
    st.dataframe(acc_club.to_frame("Clients Access+ uniques"))
    st.markdown("### Waterstation par club")
    water_club = water_df.groupby(club_col)['Client_Unique'].nunique().sort_values(ascending=False)
    st.dataframe(water_club.to_frame("Clients Waterstation uniques"))

    # === BARPLOT COMPARATIF CLUB Access+ / Waterstation ===
    st.markdown("### Comparatif Access+ / Waterstation par club")
    access_counts = acc_club
    water_counts = water_club
    clubs = sorted(list(set(access_counts.index) | set(water_counts.index)))
    bar_width = 0.35
    idx = np.arange(len(clubs))
    a = [access_counts.get(club, 0) for club in clubs]
    w = [water_counts.get(club, 0) for club in clubs]
    if any(a) or any(w):
        fig, ax = plt.subplots(figsize=(max(7,len(clubs)*0.6), 4))
        ax.bar(idx - bar_width/2, a, bar_width, label="Access+", color="#5B7DFF")
        ax.bar(idx + bar_width/2, w, bar_width, label="Waterstation", color="#60C878")
        ax.set_xticks(idx)
        ax.set_xticklabels(clubs, rotation=45, ha="right")
        ax.set_ylabel("Clients uniques")
        ax.set_title("Comparatif Access+ / Waterstation par club")
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
        plt.clf()
    else:
        st.info("Aucun résultat pour Access+ ou Waterstation sur cette sélection.")

# ==== Par Commercial ====
with tabs[2]:
    st.subheader("🧑‍💼 Analyse Commerciale VAD")
    auteurs_com = st.multiselect("Filtrer par Auteur (Commerciaux)", all_auteurs, default=all_auteurs, key="auteurs_com")
    commercial_df = df[df[col_auteur].isin(auteurs_com)]

    # Table globale clients uniques par commercial
    vad_com = commercial_df.groupby(commercial_col)['Client_Unique'].nunique().sort_values(ascending=False)
    st.dataframe(vad_com.to_frame("Clients uniques"))
    if not vad_com.empty:
        fig, ax = plt.subplots()
        vad_com.plot(kind="bar", color="#FFD700", ax=ax)
        plt.ylabel("Clients uniques")
        plt.title("VAD - Clients uniques par commercial")
        plt.tight_layout()
        st.pyplot(fig)
        plt.clf()
    else:
        st.info("Aucun résultat commercial sur cette sélection.")

    # === Détail Access+ / Waterstation par commercial ===
    st.markdown("### Détail Access+ et Waterstation par commercial")
    access_com = commercial_df[commercial_df[col_produit].astype(str).str.upper() == "ALLACCESS+"]
    water_com = commercial_df[commercial_df[col_produit].astype(str).str.lower() == "waterstation"]

    # Table Access+ par commercial
    access_detail = access_com.groupby(commercial_col)['Client_Unique'].nunique().sort_values(ascending=False).rename("Clients Access+ uniques")
    st.write("#### Access+ par commercial")
    st.dataframe(access_detail.to_frame())

    # Table Waterstation par commercial
    water_detail = water_com.groupby(commercial_col)['Client_Unique'].nunique().sort_values(ascending=False).rename("Clients Waterstation uniques")
    st.write("#### Waterstation par commercial")
    st.dataframe(water_detail.to_frame())

    # === BARPLOT ACCESS+ PAR COMMERCIAL ===
    st.markdown("### Barplot Access+ par commercial")
    if not access_detail.empty:
        fig, ax = plt.subplots(figsize=(max(7,len(access_detail)*0.6), 4))
        access_detail.plot(kind="bar", color="#FFD700", ax=ax)
        ax.set_ylabel("Clients Access+ uniques")
        ax.set_title("Access+ par commercial")
        plt.tight_layout()
        st.pyplot(fig)
        plt.clf()
    else:
        st.info("Aucun commercial n'a vendu Access+ sur cette sélection.")

    # === BARPLOT WATERSTATION PAR COMMERCIAL ===
    st.markdown("### Barplot Waterstation par commercial")
    if not water_detail.empty:
        fig, ax = plt.subplots(figsize=(max(7,len(water_detail)*0.6), 4))
        water_detail.plot(kind="bar", color="#60C878", ax=ax)
        ax.set_ylabel("Clients Waterstation uniques")
        ax.set_title("Waterstation par commercial")
        plt.tight_layout()
        st.pyplot(fig)
        plt.clf()
    else:
        st.info("Aucun commercial n'a vendu Waterstation sur cette sélection.")

# ==== Export ====
with tabs[3]:
    st.subheader("⬇️ Exporter les analyses")
    excel_data = to_excel({
        "VAD_Global": df,
        "Access+_par_club": acc_club.to_frame("Clients Access+ uniques"),
        "Waterstation_par_club": water_club.to_frame("Clients Waterstation uniques"),
        "Par_Commercial": vad_com.to_frame("Clients uniques"),
        "Access+_par_commercial": access_detail.to_frame(),
        "Waterstation_par_commercial": water_detail.to_frame()
    })
    st.download_button(
        label="📥 Télécharger toutes les données (Excel)",
        data=base64.b64decode(excel_data),
        file_name="VAD_analyse.xlsx"
    )
