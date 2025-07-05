import streamlit as st
import pandas as pd
import base64
from io import BytesIO

if "logged" not in st.session_state or not st.session_state["logged"]:
    st.warning("Vous devez vous connecter depuis la page d'accueil.")
    st.stop()

st.title("📈 Analyse Ventes Abonnements")
file = st.file_uploader("Fichier Ventes (CSV ou Excel)", type=["csv", "xlsx"])
if file:
    ext = file.name.split('.')[-1]
    for enc in ["utf-8", "cp1252", "latin-1"]:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding=enc, sep=None, engine='python') if ext == "csv" else pd.read_excel(file)
            break
        except Exception:
            continue
    else:
        st.error("Erreur lecture fichier.")
        st.stop()
    df.columns = df.columns.str.strip()
    offres_col = st.selectbox("Colonne des Offres", options=df.columns.tolist())
    date_col = st.selectbox("Colonne Date de création", options=df.columns.tolist())
    comm_col = st.selectbox("Colonne Commercial", options=df.columns.tolist())
    offres_uniques = df[offres_col].dropna().unique().tolist()
    commerciaux_uniques = df[comm_col].dropna().unique().tolist()
    filtre_offre = st.multiselect("Filtrer par Offre", offres_uniques, offres_uniques)
    filtre_com = st.multiselect("Filtrer par Commercial", commerciaux_uniques, commerciaux_uniques)
    df = df[df[offres_col].isin(filtre_offre) & df[comm_col].isin(filtre_com)]
    st.dataframe(df)
    # ... (mets ici tous tes tableaux/exports/graph comme avant)
