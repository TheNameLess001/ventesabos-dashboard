import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

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

file = st.file_uploader("Fichier Ventes (CSV ou Excel)", type=["csv", "xlsx"])
if not file:
    st.info("Importez un fichier pour démarrer l'analyse.")
    st.stop()

ext = file.name.split('.')[-1]
df = safe_read_csv(file) if ext == "csv" else pd.read_excel(file, engine="openpyxl")
df.columns = df.columns.str.strip()

# --- Sélection des colonnes dynamiquement ---
st.subheader("🛠️ Sélection des colonnes d'analyse")
col_names = df.columns.tolist()
offres_col = st.selectbox("Colonne des Offres", options=col_names)
date_col = st.selectbox("Colonne Date de création", options=col_names)
comm_col = st.selectbox("Colonne Commercial", options=col_names)

# --- Filtres dynamiques ---
st.subheader("🎛️ Filtres dynamiques")
offres_uniques = df[offres_col].dropna().unique().tolist()
commerciaux_uniques = df[comm_col].dropna().unique().tolist()
filtre_offre = st.multiselect("Filtrer par Offre", offres_uniques, offres_uniques)
filtre_com = st.multiselect("Filtrer par Commercial", commerciaux_uniques, commerciaux_uniques)
df = df[df[offres_col].isin(filtre_offre) & df[comm_col].isin(filtre_com)]

tabs = st.tabs(["Vue Club", "Vue Commerciale", "Graphiques"])

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
