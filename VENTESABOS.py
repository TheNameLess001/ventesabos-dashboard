import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import datetime

# ========== CONFIG ==========
st.set_page_config(page_title="VENTESABOS BI SUITE", page_icon="📊", layout="wide")
LOGO_PATH = "logo_fitnesspark.png"

# ========== UTILS ==========
def to_excel(df_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet, index=True)
    output.seek(0)
    return base64.b64encode(output.read()).decode()

def safe_read_csv(file):
    # Essaye plusieurs encodages
    for enc in ["utf-8", "cp1252", "latin-1"]:
        try:
            file.seek(0)
            return pd.read_csv(file, encoding=enc, sep=None, engine='python')
        except Exception:
            continue
    st.error("Impossible de lire le fichier CSV. Essayez de l'enregistrer à nouveau en UTF-8 ou Excel.")
    st.stop()

# ========== LOGIN ==========
def show_login():
    col1, col2, col3 = st.columns([2,4,2])
    with col2:
        try:
            st.image(LOGO_PATH, width=210)
        except Exception:
            st.markdown("<h2 style='text-align:center;'>Fitness Park</h2>", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;font-size:2em;font-weight:bold;color:#262730;margin-bottom:0.5em;">Bienvenue sur le Dashboard Ventes & Recouvrement</div>', unsafe_allow_html=True)
    with st.form(key="login_form"):
        username = st.text_input("Utilisateur", placeholder="Admin")
        password = st.text_input("Mot de passe", type="password", placeholder="********")
        submit = st.form_submit_button("Se connecter")
    if st.button("Mot de passe oublié ?"):
        st.info("Contactez : [Manager.racine@fitnesspark.ma](mailto:Manager.racine@fitnesspark.ma)")
    if submit:
        if username == "Admin" and password == "Fpk@2025":
            st.session_state["logged"] = True
            st.experimental_rerun()
        else:
            st.error("Identifiants incorrects.")

def show_logout():
    st.sidebar.markdown("---")
    if st.sidebar.button("Déconnexion"):
        st.session_state["logged"] = False
        st.experimental_rerun()

def show_header():
    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;align-items:center;">
            <img src="{LOGO_PATH}" width="150"/>
            <span style="font-size:2.4rem;font-weight:800;letter-spacing:2px;color:#2c3e50;">DASHBOARD ANALYTIQUE FITNESS PARK</span>
            <span style="color:#2c3e50;font-size:16px;">Ventes Abos & Recouvrement • {datetime.datetime.now().strftime('%d/%m/%Y')}</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")

# ========== VUE ABONNEMENTS ==========
def vue_abos():
    st.header("Vue Abonnements (Club / Commerciaux)")
    file = st.file_uploader("Importer le fichier de ventes (CSV ou Excel)", type=["csv", "xlsx"], key="abos")
    if not file:
        st.info("Importez un fichier de ventes pour démarrer.")
        return
    ext = file.name.split('.')[-1]
    df = safe_read_csv(file) if ext == "csv" else pd.read_excel(file, engine="openpyxl")
    df.columns = df.columns.str.strip()
    offres_col = st.selectbox("Colonne des Offres", options=df.columns.tolist(), index=min(5, len(df.columns)-1))
    date_col = st.selectbox("Colonne Date de création", options=df.columns.tolist(), index=min(6, len(df.columns)-1))
    comm_col = st.selectbox("Colonne Commercial", options=df.columns.tolist(), index=min(11, len(df.columns)-1))
    offres_uniques = df[offres_col].dropna().unique().tolist()
    commerciaux_uniques = df[comm_col].dropna().unique().tolist()
    filtre_offre = st.multiselect("Filtrer par Offre", offres_uniques, offres_uniques)
    filtre_com = st.multiselect("Filtrer par Commercial", commerciaux_uniques, commerciaux_uniques)
    df = df[df[offres_col].isin(filtre_offre) & df[comm_col].isin(filtre_com)]
    tabs = st.tabs(["Vue Club", "Vue Commerciale"])
    with tabs[0]:
        st.subheader("Tableau Club (quantités)")
        table_club = df.groupby(offres_col).size().to_frame("Quantité").sort_values("Quantité", ascending=False)
        st.dataframe(table_club)
        st.subheader("Ventes par semaine (Club)")
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        table_week = df.groupby(df[date_col].dt.to_period('W'))[offres_col].value_counts().unstack().fillna(0)
        st.dataframe(table_week)
    with tabs[1]:
        st.subheader("Tableau Commercial (quantités)")
        table_com = df.groupby(comm_col)[offres_col].value_counts().unstack(fill_value=0)
        st.dataframe(table_com)
        st.subheader("Ventes par semaine (par Commercial)")
        week_com = df.groupby([df[date_col].dt.to_period('W'), comm_col]).size().unstack(fill_value=0)
        st.dataframe(week_com)
    st.markdown("#### 📥 Export (Excel)")
    excel_data = to_excel({"Tableau Club": table_club, "Tableau Commercial": table_com, "Par Semaine Club": table_week, "Par Semaine Com": week_com})
    st.download_button("Télécharger tout (Excel)", base64.b64decode(excel_data), file_name="analyse_abos.xlsx")

# ========== VUE RECOUVREMENT ==========
def vue_recouvrement():
    st.header("Vue Recouvrement")
    recouv_file = st.file_uploader(
        "Importer le fichier de recouvrement (CSV/Excel)", type=['csv', 'xlsx'], key="recouv"
    )
    if not recouv_file:
        st.info("Importe un fichier de recouvrement pour afficher les analyses.")
        return
    ext = recouv_file.name.split('.')[-1]
    df_recouv = safe_read_csv(recouv_file) if ext == "csv" else pd.read_excel(recouv_file)
    df_recouv.columns = df_recouv.columns.str.strip()
    montant_col = "Montant de l'incident"
    reglement_col = "Règlement de l'incident"
    avoir_col = "Règlement avoir de l'incident"
    commercial_col = "Prénom du commercial initial"
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
    table_club = pd.DataFrame({
        "Total rejets (quantité)": [total_rejets],
        "Recouvert (quantité)": [nb_recouvert],
        "À recouvrir (quantité)": [nb_impaye],
        "Total rejets (valeur)": [total_montant],
        "Recouvert (valeur)": [montant_recouvert],
        "À recouvrir (valeur)": [montant_impaye],
    })
    st.dataframe(table_club)
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

# ========== APP PRINCIPALE ==========
def main():
    show_header()
    show_logout()
    onglets = st.tabs(["Ventes Abos", "Recouvrement"])
    with onglets[0]:
        vue_abos()
    with onglets[1]:
        vue_recouvrement()

if "logged" not in st.session_state:
    st.session_state["logged"] = False
if not st.session_state["logged"]:
    show_login()
    st.stop()
else:
    main()
