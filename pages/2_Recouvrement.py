import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

if "logged" not in st.session_state or not st.session_state["logged"]:
    st.warning("Vous devez vous connecter depuis la page d'accueil.")
    st.stop()

st.title("💰 Dashboard Recouvrement Fitness Park")

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
    def norm(x): return x.strip().lower().replace('é','e').replace('è','e').replace('ê','e').replace("’","'").replace("_", " ").replace("-", " ")
    normed = {norm(c):c for c in cols}
    for t in targets:
        t_norm = norm(t)
        if t_norm in normed:
            return normed[t_norm]
    return None

tabs = st.tabs(["📊 Dashboard Club Recouvrement", "🧑‍💼 Dashboard Commercial", "🚨 2 Rejets Successifs"])

# ===== TAB 1: Club Recouvrement =====
with tabs[0]:
    st.subheader("📊 Dashboard Club Recouvrement")
    file = st.file_uploader("Fichier Recouvrement (CSV ou Excel)", type=["csv", "xlsx"], key="recouv_club")
    if file:
        ext = file.name.split('.')[-1]
        df = safe_read_csv(file) if ext == "csv" else pd.read_excel(file, engine="openpyxl")
        df.columns = df.columns.str.strip()

        montant_col = match_col(df.columns, ["Montant de l'incident", "Montant", "M"])
        reglement_col = match_col(df.columns, ["Règlement de l'incident", "Reglement", "R"])
        avoir_col = match_col(df.columns, ["Règlement avoir de l'incident", "Avoir", "S"])

        for col in [montant_col]:
            df[col] = (
                df[col].astype(str)
                .str.replace(" ", "", regex=False)
                .str.replace(",", ".", regex=False)
                .str.replace("\u202f", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df["Recouvert"] = df[reglement_col].notna() | df[avoir_col].notna()
        total_rejets = len(df)
        nb_recouvert = df["Recouvert"].sum()
        nb_a_recouvrir = total_rejets - nb_recouvert
        total_montant = df[montant_col].sum()
        montant_recouvert = df[df["Recouvert"]][montant_col].sum()
        montant_a_recouvrir = total_montant - montant_recouvert
        taux_recouvrement = 100 * montant_recouvert / total_montant if total_montant > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔄 Total incidents", total_rejets)
        col2.metric("✅ Recouverts (Qté)", int(nb_recouvert))
        col3.metric("🕗 À Recouvrir (Qté)", int(nb_a_recouvrir))
        col4.metric("💰 Total incidents (MAD)", f"{total_montant:,.0f}")

        st.markdown("### KPIs Recouvrement")
        kpi_tab = pd.DataFrame({
            "Total recouvré (MAD)": [montant_recouvert],
            "Reste à recouvrir (MAD)": [montant_a_recouvrir],
            "Taux de recouvrement (%)": [taux_recouvrement],
            "Nb incidents": [total_rejets],
            "Nb recouverts": [nb_recouvert],
            "Nb à recouvrir": [nb_a_recouvrir]
        })

        # Affichage coloré du taux
        def color_kpi(val, seuil=60):
            if val < 50: return 'background-color:#ffdddd;color:#b30000;font-weight:bold;'
            elif val < seuil: return 'background-color:#fff7e6;color:#ff8800;font-weight:bold;'
            else: return 'background-color:#eaffea;color:#12621e;font-weight:bold;'
        st.dataframe(kpi_tab.style.applymap(lambda v: color_kpi(v) if isinstance(v, (float,int)) and v<=100 and v>=0 else ''))

        # Pie chart (Camembert)
        st.markdown("### 🥧 Camembert Recouvert / À recouvrir (quantité)")
        values = [nb_recouvert, nb_a_recouvrir]
        labels = ["Recouvert", "À Recouvrir"]
        colors = ["#37c759", "#ff0000"]
        fig1, ax1 = plt.subplots(figsize=(5, 5))
        ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90, textprops={'fontsize': 14})
        ax1.axis('equal')
        st.pyplot(fig1)

        # Pie chart Montant
        st.markdown("### 🥧 Camembert Recouvert / À recouvrir (valeur)")
        values_montant = [montant_recouvert, montant_a_recouvrir]
        labels_montant = ["Recouvert", "À Recouvrir"]
        fig2, ax2 = plt.subplots(figsize=(5, 5))
        ax2.pie(values_montant, labels=labels_montant, autopct='%1.1f%%', colors=colors, startangle=90, textprops={'fontsize': 14})
        ax2.axis('equal')
        st.pyplot(fig2)

        # Export Excel
        excel_data = to_excel({"KPIs Club": kpi_tab})
        st.download_button(
            label="📥 Télécharger Dashboard Club (Excel)",
            data=base64.b64decode(excel_data),
            file_name="recouvrement_club.xlsx"
        )

# ===== TAB 2: Dashboard Commercial =====
with tabs[1]:
    st.subheader("🧑‍💼 Dashboard Commercial Recouvrement")
    file2 = st.file_uploader("Fichier Recouvrement (CSV ou Excel)", type=["csv", "xlsx"], key="recouv_com")
    if file2:
        ext2 = file2.name.split('.')[-1]
        df2 = safe_read_csv(file2) if ext2 == "csv" else pd.read_excel(file2, engine="openpyxl")
        df2.columns = df2.columns.str.strip()

        montant_col = match_col(df2.columns, ["Montant de l'incident", "Montant", "M"])
        reglement_col = match_col(df2.columns, ["Règlement de l'incident", "Reglement", "R"])
        avoir_col = match_col(df2.columns, ["Règlement avoir de l'incident", "Avoir", "S"])
        commercial_col = match_col(df2.columns, ["Prénom du commercial initial", "Commercial", "X"])

        for col in [montant_col]:
            df2[col] = (
                df2[col].astype(str)
                .str.replace(" ", "", regex=False)
                .str.replace(",", ".", regex=False)
                .str.replace("\u202f", "", regex=False)
            )
            df2[col] = pd.to_numeric(df2[col], errors="coerce").fillna(0)

        df2["Recouvert"] = df2[reglement_col].notna() | df2[avoir_col].notna()
        total_montant = df2[montant_col].sum()

        # KPIs par commercial
        com_tab = df2.groupby(commercial_col).agg(
            Nb_Incidents = (montant_col, 'count'),
            Nb_Recouverts = ("Recouvert", 'sum'),
            Nb_a_Recouvrir = (montant_col, lambda x: x.isna().sum()),
            Montant_Total = (montant_col, 'sum'),
            Montant_Recouvert = (montant_col, lambda x: df2.loc[x.index][df2.loc[x.index,"Recouvert"]][montant_col].sum()),
            Montant_a_Recouvrir = (montant_col, lambda x: df2.loc[x.index][~df2.loc[x.index,"Recouvert"]][montant_col].sum()),
        )
        com_tab["Taux (%)"] = 100 * com_tab["Montant_Recouvert"] / com_tab["Montant_Total"].replace(0, np.nan)
        com_tab = com_tab.fillna(0)

        def color_taux(val):
            if val < 50: return 'background-color:#ffdddd;color:#b30000;font-weight:bold;'
            elif val < 60: return 'background-color:#fff7e6;color:#ff8800;font-weight:bold;'
            else: return 'background-color:#eaffea;color:#12621e;font-weight:bold;'
        st.dataframe(com_tab.style.applymap(lambda v: color_taux(v) if isinstance(v,(float,int)) and v<=100 and v>=0 else ''))

        # Barplot taux par commercial
        st.markdown("### 📊 Barplot du taux de recouvrement par commercial")
        plt.figure(figsize=(9,4))
        com_tab["Taux (%)"].plot(kind="bar", color=[("#ff0000" if v<50 else "#ff8800" if v<60 else "#37c759") for v in com_tab["Taux (%)"]])
        plt.title("Taux de recouvrement par commercial")
        plt.xlabel("Commercial")
        plt.ylabel("Taux de recouvrement (%)")
        plt.ylim(0, 100)
        plt.tight_layout()
        st.pyplot(plt.gcf())
        plt.clf()

        # Export Excel
        excel_data = to_excel({"KPIs Commerciaux": com_tab})
        st.download_button(
            label="📥 Télécharger Dashboard Commerciaux (Excel)",
            data=base64.b64decode(excel_data),
            file_name="recouvrement_commerciaux.xlsx"
        )

# ===== TAB 3: 2 Rejets Successifs (identique à version précédente) =====
with tabs[2]:
    st.subheader("🚨 Détection clients à 2 rejets successifs")
    st.markdown("Importer **deux fichiers exports mensuels consécutifs**. Les clients avec incidents impayés sur les deux mois seront listés.")
    file_a = st.file_uploader("Fichier Mois 1", type=["csv", "xlsx"], key="rej1")
    file_b = st.file_uploader("Fichier Mois 2", type=["csv", "xlsx"], key="rej2")

    if file_a and file_b:
        ext_a = file_a.name.split('.')[-1]
        ext_b = file_b.name.split('.')[-1]
        df_a = safe_read_csv(file_a) if ext_a == "csv" else pd.read_excel(file_a, engine="openpyxl")
        df_b = safe_read_csv(file_b) if ext_b == "csv" else pd.read_excel(file_b, engine="openpyxl")
        df_a.columns = df_a.columns.str.strip()
        df_b.columns = df_b.columns.str.strip()
        nom_col = match_col(df_a.columns, ["Nom", "Nom du client"])
        prenom_col = match_col(df_a.columns, ["Prénom", "Prenom"])
        reglement_col = match_col(df_a.columns, ["Règlement de l'incident", "Reglement", "R"])
        etat_col = match_col(df_a.columns, ["Etat de l'incident", "Etat", "P"])
        id_col = "___ClientID"
        df_a[id_col] = df_a[nom_col].astype(str).str.strip().str.upper() + " " + df_a[prenom_col].astype(str).str.strip().str.upper()
        df_b[id_col] = df_b[nom_col].astype(str).str.strip().str.upper() + " " + df_b[prenom_col].astype(str).str.strip().str.upper()
        impayes_a = df_a[(df_a[reglement_col].isna()) | (df_a[etat_col].astype(str).str.upper().str.strip() == "OUVERT")]
        impayes_b = df_b[(df_b[reglement_col].isna()) | (df_b[etat_col].astype(str).str.upper().str.strip() == "OUVERT")]
        deux_rejets = pd.merge(
            impayes_a[[id_col, nom_col, prenom_col]].drop_duplicates(),
            impayes_b[[id_col, nom_col, prenom_col]].drop_duplicates(),
            on=id_col, suffixes=('_mois1','_mois2')
        )
        deux_rejets["Nom complet"] = deux_rejets[nom_col + "_mois2"].astype(str).str.strip() + " " + deux_rejets[prenom_col + "_mois2"].astype(str).str.strip()
        st.markdown(f"**Nombre de clients avec 2 rejets successifs** : {len(deux_rejets)}")
        st.dataframe(deux_rejets[["Nom complet"]])
        output = BytesIO()
        deux_rejets[["Nom complet"]].to_excel(output, index=False)
        output.seek(0)
        st.download_button("📥 Télécharger liste clients à 2 rejets (Excel)", data=output.getvalue(), file_name="2_rejets_successifs.xlsx")
