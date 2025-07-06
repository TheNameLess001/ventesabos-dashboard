import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# Protection login
if "logged" not in st.session_state or not st.session_state["logged"]:
    st.warning("Vous devez vous connecter depuis la page d'accueil.")
    st.stop()

st.title("🚀 ANALYSEUR VAD - Fitness Park")

# Gold branding & style onglets (identique Recouvrement/Facture)
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

vad_file = st.file_uploader("Importer un fichier VAD (Excel)", type=["xlsx", "xls"])
if not vad_file:
    st.info("Importez un fichier VAD pour démarrer l'analyse.")
    st.stop()

try:
    df = pd.read_excel(vad_file)
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error(f"Erreur de lecture : {e}")
    st.stop()

# === TABS ===
tabs = st.tabs(["Résumé Global", "Analyse par Club", "Analyse Commerciale", "Export"])

# ===== TAB 1 : Résumé Global =====
with tabs[0]:
    st.subheader("📊 Résumé Global VAD")
    st.dataframe(df.head(30))  # Juste un aperçu, à customiser selon ton fichier

    st.markdown("**À personnaliser : KPIs, camemberts, barplots... selon les colonnes du VAD**")

# ===== TAB 2 : Analyse par Club =====
with tabs[1]:
    st.subheader("🏟️ Analyse par Club")
    club_col = st.selectbox("Colonne Club", options=df.columns.tolist())
    df_club = df.groupby(club_col).size().reset_index(name="Quantité")
    st.dataframe(df_club.sort_values("Quantité", ascending=False))
    # Ex : camembert club
    fig, ax = plt.subplots()
    ax.pie(df_club["Quantité"], labels=df_club[club_col], autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

# ===== TAB 3 : Analyse Commerciale =====
with tabs[2]:
    st.subheader("🧑‍💼 Analyse Commerciale")
    com_col = st.selectbox("Colonne Commercial", options=df.columns.tolist())
    df_com = df.groupby(com_col).size().reset_index(name="Quantité")
    st.dataframe(df_com.sort_values("Quantité", ascending=False))
    fig, ax = plt.subplots()
    ax.bar(df_com[com_col], df_com["Quantité"], color="#FFD700")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# ===== TAB 4 : Export =====
with tabs[3]:
    st.subheader("⬇️ Exporter les analyses")
    excel_data = to_excel({
        "Résumé Global": df,
        "Clubs": df_club,
        "Commerciaux": df_com
    })
    st.download_button(
        label="📥 Télécharger toutes les données (Excel)",
        data=base64.b64decode(excel_data),
        file_name="VAD_analyse.xlsx"
    )
