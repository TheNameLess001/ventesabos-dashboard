import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

if "logged" not in st.session_state or not st.session_state["logged"]:
    st.warning("Vous devez vous connecter depuis la page d'accueil.")
    st.stop()

st.title("💰 Analyse Recouvrement")
recouv_file = st.file_uploader("Fichier Recouvrement (CSV ou Excel)", type=["csv", "xlsx"])
if recouv_file:
    ext = recouv_file.name.split('.')[-1]
    for enc in ["utf-8", "cp1252", "latin-1"]:
        try:
            recouv_file.seek(0)
            df_recouv = pd.read_csv(recouv_file, encoding=enc, sep=None, engine='python') if ext == "csv" else pd.read_excel(recouv_file)
            break
        except Exception:
            continue
    else:
        st.error("Erreur lecture fichier.")
        st.stop()
    df_recouv.columns = df_recouv.columns.str.strip()
    montant_col = "Montant de l'incident"
    reglement_col = "Règlement de l'incident"
    avoir_col = "Règlement avoir de l'incident"
    commercial_col = "Prénom du commercial initial"
    df_recouv[montant_col] = (
        df_recouv[montant_col].astype(str)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace("\u202f", "", regex=False)
    )
    df_recouv[montant_col] = pd.to_numeric(df_recouv[montant_col], errors="coerce").fillna(0)
    df_recouv["Recouvert"] = df_recouv[reglement_col].notna() | df_recouv[avoir_col].notna()
    total_rejets = len(df_recouv)
    total_montant = df_recouv[montant_col].sum()
    nb_recouvert = df_recouv["Recouvert"].sum()
    montant_recouvert = df_recouv.loc[df_recouv["Recouvert"], montant_col].sum()
    nb_impaye = total_rejets - nb_recouvert
    montant_impaye = total_montant - montant_recouvert
    st.metric("Total rejets", total_rejets)
    st.metric("Total recouvert", int(nb_recouvert))
    st.metric("À recouvrir", int(nb_impaye))
    st.metric("Total rejets (valeur)", f"{total_montant:,.0f} MAD")
    st.metric("Recouvert (valeur)", f"{montant_recouvert:,.0f} MAD")
    st.metric("À recouvrir (valeur)", f"{montant_impaye:,.0f} MAD")
    # ... Ajoute ici tes tableaux, exports, graphes comme avant ...
