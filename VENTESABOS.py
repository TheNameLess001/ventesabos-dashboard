# --- IMPORTS ---
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import datetime

# --- CONFIG ---
st.set_page_config(page_title="VENTESABOS - SBN", page_icon="📊", layout="wide")
st.markdown("""
    <style>
    body {background-color: #f7f9fa;}
    .stButton>button {background-color: #2ecc71; color: white; border-radius:10px;}
    .stTabs [data-baseweb="tab-list"] button {font-size: 1.1rem;}
    </style>
""", unsafe_allow_html=True)

# --- LOGO & HEADER ---
def show_header():
    st.image("fitnesspark.png", width=160)
    st.markdown("<h1 style='text-align:center; color:#222;'>VENTES ABONNEMENTS / RECOUVREMENT</h1>", unsafe_allow_html=True)
    st.markdown("---")

# --- LOGIN ---
def show_login():
    st.image("fitnesspark.png", width=120)
    st.markdown("<h2 style='text-align:center;'>Authentification</h2>", unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        user = st.text_input("Utilisateur", value="", key="login_user")
        pwd = st.text_input("Mot de passe", value="", type="password", key="login_pwd")
        submit = st.form_submit_button("Connexion")
        if submit:
            if user.lower() == "admin" and pwd == "Fpk@2025":
                st.session_state["logged"] = True
                st.experimental_rerun()
            else:
                st.error("Identifiants incorrects.")
        if st.button("Mot de passe oublié ?"):
            st.info("Contactez : [Manager.racine@fitnesspark.ma](mailto:Manager.racine@fitnesspark.ma)")

def show_logout():
    st.sidebar.button("Déconnexion", on_click=lambda: st.session_state.update({"logged": False}), key="logout_btn")

# --- UTILS ---
def to_excel(df_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet, index=True)
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    return b64

# ============================== VUES ABONNEMENTS ===========================
def vue_abos():
    st.header("Vue Abonnements (Club / Commerciaux)")
    file = st.file_uploader("Importer le fichier de ventes (CSV ou Excel)", type=["csv", "xlsx"], key="abos")
    if not file:
        st.info("Importez un fichier de ventes pour démarrer.")
        return

    # --- DATA ---
    ext = file.name.split('.')[-1]
    if ext == "csv":
        df = pd.read_csv(file, encoding='utf-8', sep=None, engine='python')
    else:
        df = pd.read_excel(file, engine="openpyxl")
    df.columns = df.columns.str.strip()

    # --- Colonnes dynamiques (détecte ou propose dropdown) ---
    offres_col = st.selectbox("Colonne des Offres", options=df.columns.tolist(), index=5)
    date_col = st.selectbox("Colonne Date de création", options=df.columns.tolist(), index=6)
    comm_col = st.selectbox("Colonne Commercial", options=df.columns.tolist(), index=11)

    # Filtres dynamiques
    offres_uniques = df[offres_col].dropna().unique().tolist()
    commerciaux_uniques = df[comm_col].dropna().unique().tolist()
    filtre_offre = st.multiselect("Filtrer par Offre", offres_uniques, offres_uniques)
    filtre_com = st.multiselect("Filtrer par Commercial", commerciaux_uniques, commerciaux_uniques)
    df = df[df[offres_col].isin(filtre_offre) & df[comm_col].isin(filtre_com)]

    tabs = st.tabs(["Vue Club", "Vue Commerciale"])

    # --- VUE CLUB ---
    with tabs[0]:
        st.subheader("Tableau Club (quantités)")
        table_club = df.groupby(offres_col).size().to_frame("Quantité").sort_values("Quantité", ascending=False)
        st.dataframe(table_club.style.highlight_max(axis=0, color='#e1ffe1'))
        st.subheader("Ventes par semaine (Club)")
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        table_week = df.groupby(df[date_col].dt.to_period('W'))[offres_col].value_counts().unstack().fillna(0)
        st.dataframe(table_week)
    
    # --- VUE COMMERCIALE ---
    with tabs[1]:
        st.subheader("Tableau Commercial (quantités)")
        table_com = df.groupby(comm_col)[offres_col].value_counts().unstack(fill_value=0)
        st.dataframe(table_com.style.highlight_max(axis=1, color='#d5e7ff'))
        st.subheader("Ventes par semaine (par Commercial)")
        week_com = df.groupby([df[date_col].dt.to_period('W'), comm_col]).size().unstack(fill_value=0)
        st.dataframe(week_com)
    
    # --- EXPORT
    st.markdown("#### 📥 Export (Excel)")
    excel_data = to_excel({"Tableau Club": table_club, "Tableau Commercial": table_com, "Par Semaine Club": table_week, "Par Semaine Com": week_com})
    st.download_button("Télécharger tout (Excel)", base64.b64decode(excel_data), file_name="analyse_abos.xlsx")
    
# ============================== VUES RECOUVREMENT ===========================
def vue_recouvrement():
    st.header("Vue Recouvrement")
    recouv_file = st.file_uploader(
        "Importer le fichier de recouvrement (CSV/Excel)", type=['csv', 'xlsx'], key="recouv"
    )
    if not recouv_file:
        st.info("Importe un fichier de recouvrement pour afficher les analyses.")
        return

    df_recouv = pd.read_csv(recouv_file) if recouv_file.name.endswith('csv') else pd.read_excel(recouv_file)
    df_recouv.columns = df_recouv.columns.str.strip()

    montant_col = "Montant de l'incident"         # Colonne M
    reglement_col = "Règlement de l'incident"     # Colonne R
    avoir_col = "Règlement avoir de l'incident"   # Colonne S
    commercial_col = "Prénom du commercial initial" # Colonne X

    # --- Nettoyage du montant (float ready) ---
    df_recouv[montant_col] = (
        df_recouv[montant_col]
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace("\u202f", "", regex=False)
    )
    df_recouv[montant_col] = pd.to_numeric(df_recouv[montant_col], errors="coerce").fillna(0)

    # Statut recouvert = au moins une des 2 colonnes remplie (R ou S)
    df_recouv["Recouvert"] = df_recouv[reglement_col].notna() | df_recouv[avoir_col].notna()

    # === GLOBAL CLUB ===
    total_rejets = len(df_recouv)
    total_montant = df_recouv[montant_col].sum()
    nb_recouvert = df_recouv["Recouvert"].sum()
    montant_recouvert = df_recouv.loc[df_recouv["Recouvert"], montant_col].sum()
    nb_impaye = total_rejets - nb_recouvert
    montant_impaye = total_montant - montant_recouvert

    st.markdown("## 📊 Résumé Global Recouvrement (Club)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total rejets (quantité)", total_rejets)
    col2.metric("Recouvert (quantité)", int(nb_recouvert))
    col3.metric("À recouvrir (quantité)", int(nb_impaye))
    col1.metric("Total rejets (valeur)", f"{total_montant:,.0f} MAD")
    col2.metric("Recouvert (valeur)", f"{montant_recouvert:,.0f} MAD")
    col3.metric("À recouvrir (valeur)", f"{montant_impaye:,.0f} MAD")

    # === TABLEAU CLUB ===
    table_club = pd.DataFrame({
        "Total rejets (quantité)": [total_rejets],
        "Recouvert (quantité)": [nb_recouvert],
        "À recouvrir (quantité)": [nb_impaye],
        "Total rejets (valeur)": [total_montant],
        "Recouvert (valeur)": [montant_recouvert],
        "À recouvrir (valeur)": [montant_impaye],
    })
    st.dataframe(table_club)

    # === TABLEAU PAR COMMERCIAL ===
    st.markdown("## 🧑‍💼 Vue par Commercial initial")
    table_com = df_recouv.groupby(commercial_col).agg(
        Total_Rejets = (montant_col, 'count'),
        Recouvert = ("Recouvert", 'sum'),
        À_Recouvrir = (montant_col, lambda x: x.isna().sum()),
        Montant_Total = (montant_col, 'sum'),
        Montant_Recouvert = (montant_col, lambda x: df_recouv.loc[x.index][df_recouv.loc[x.index,"Recouvert"]][montant_col].sum()),
        Montant_Impaye = (montant_col, lambda x: df_recouv.loc[x.index][~df_recouv.loc[x.index,"Recouvert"]][montant_col].sum()),
    )
    st.dataframe(table_com)

    # === GRAPHIQUE ===
    st.markdown("## 📈 Evolution du recouvrement (valeur recouvrée par mois)")
    df_recouv["Date_Regl"] = pd.to_datetime(df_recouv[reglement_col], errors='coerce')
    evolution = df_recouv[df_recouv["Recouvert"]].groupby(df_recouv["Date_Regl"].dt.to_period('M'))[montant_col].sum()
    evolution.plot(kind="bar", figsize=(10,4), color="#3498db")
    plt.ylabel("Montant recouvert (MAD)")
    plt.xlabel("Mois")
    plt.title("Evolution du recouvrement")
    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.clf()

    # === EXPORT
    export_dict_rcv = {
        "Tableau Club Recouvrement": table_club,
        "Tableau Commerciaux Recouvrement": table_com,
        "Evolution recouvrement": evolution.to_frame("Montant Recouvert")
    }
    excel_data = to_excel(export_dict_rcv)
    st.download_button(
        label="📥 Télécharger analyse Recouvrement (Excel)",
        data=base64.b64decode(excel_data),
        file_name="analyse_recouvrement.xlsx"
    )

# ============================== APP MAIN ===========================
def main():
    show_header()
    show_logout()
    onglets = st.tabs(["Ventes Abos", "Recouvrement"])
    with onglets[0]:
        vue_abos()
    with onglets[1]:
        vue_recouvrement()

# --- APP ENTRY ---
if "logged" not in st.session_state:
    st.session_state["logged"] = False

if not st.session_state["logged"]:
    show_login()
else:
    main()
