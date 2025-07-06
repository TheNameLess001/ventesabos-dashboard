import streamlit as st
import pandas as pd
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

def read_vad_file(file):
    # Auto Excel/CSV import (sans crash)
    try:
        ext = file.name.split('.')[-1].lower()
        if ext in ["xlsx", "xls"]:
            df = pd.read_excel(file)
        elif ext == "csv":
            # Essaye plusieurs encodages pour CSV
            for enc in ["utf-8", "cp1252", "latin-1"]:
                try:
                    file.seek(0)
                    df = pd.read_csv(file, encoding=enc, sep=None, engine='python')
                    break
                except Exception:
                    continue
            else:
                return None, "Erreur de lecture du fichier CSV."
        else:
            return None, "Format non supporté."
        return df, None
    except Exception as e:
        return None, f"Erreur : {e}"

def analyze_vad(df):
    # À adapter selon ta logique métier VAD (remplace/complète à ta sauce)
    # Suppose ici qu’on a des colonnes ‘Groupe’, ‘Produit’, ‘Valeur’ 
    # Si ce n’est pas le cas, adapte l’analyse !
    if not {'Groupe','Produit','Valeur'}.issubset(df.columns):
        return None, None, None, "Fichier non conforme (attendu : colonnes 'Groupe','Produit','Valeur')"
    group_totals = df.groupby('Groupe')['Valeur'].sum().to_dict()
    group_details = {g:df[df['Groupe']==g][['Produit','Valeur']].set_index('Produit')['Valeur'].to_dict() for g in group_totals}
    all_data = df.to_dict('records')
    total = df['Valeur'].sum()
    return group_totals, group_details, total, None

vad_file = st.file_uploader("Importer un fichier VAD (Excel ou CSV)", type=["xlsx", "xls", "csv"])
if not vad_file:
    st.info("Importez un fichier VAD pour démarrer l'analyse.")
    st.stop()

df_vad, vad_err = read_vad_file(vad_file)
if vad_err:
    st.error(vad_err)
    st.stop()

group_totals, group_details, total_vad, vad_analyse_err = analyze_vad(df_vad)
if vad_analyse_err:
    st.error(vad_analyse_err)
    st.dataframe(df_vad)
    st.stop()

tabs = st.tabs(["Résumé Global", "Détails par Groupe", "Export"])

# ===== TAB 1 : Résumé Global =====
with tabs[0]:
    st.subheader("🔎 Résumé Global VAD")
    df_totaux = pd.DataFrame([{"Groupe": g, "Total (DH)": t} for g, t in group_totals.items()])
    st.dataframe(df_totaux.sort_values("Total (DH)", ascending=False).style.format({"Total (DH)": "{:,.2f} DH"}))
    st.markdown(f"**Total global : {total_vad:,.2f} DH**")

    # Pie chart
    st.markdown("### 🥧 Répartition par groupe")
    fig, ax = plt.subplots(figsize=(7, 5))
    labels = [g for g, t in group_totals.items() if t > 0]
    sizes = [t for g, t in group_totals.items() if t > 0]
    colors = plt.get_cmap("tab20c").colors
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90, textprops={'fontsize': 13})
    ax.axis('equal')
    st.pyplot(fig)

# ===== TAB 2 : Détail par Groupe =====
with tabs[1]:
    st.subheader("📑 Détail des ventes par groupe")
    group_names = [g for g in group_details if group_details[g]]
    group_sel = st.selectbox("Choisir un groupe", group_names)
    df_detail = pd.DataFrame([
        {"Produit": p, "Valeur (DH)": v}
        for p, v in group_details[group_sel].items()
    ]).sort_values("Valeur (DH)", ascending=False)
    st.dataframe(df_detail.style.format({"Valeur (DH)": "{:,.2f} DH"}))
    st.success(f"Total {group_sel}: {group_totals[group_sel]:,.2f} DH")

    # Barplot par produit du groupe sélectionné
    st.markdown("### 📊 Barplot - Répartition des ventes par produit")
    plt.figure(figsize=(8, 4))
    plt.bar(df_detail["Produit"], df_detail["Valeur (DH)"], color="#FFD700")
    plt.ylabel("Valeur (DH)")
    plt.xlabel("Produit")
    plt.title(f"Ventes du groupe {group_sel}")
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.tight_layout()
    for idx, row in df_detail.iterrows():
        plt.text(idx, row["Valeur (DH)"], f"{row['Valeur (DH)']:,.0f}", ha='center', va='bottom', fontsize=9)
    st.pyplot(plt.gcf())
    plt.clf()

# ===== TAB 3 : Export =====
with tabs[2]:
    st.subheader("⬇️ Exporter toutes les données")
    excel_data = to_excel({"Résumé Groupes": df_totaux, "Détail": df_vad})
    st.download_button(
        label="📥 Télécharger toutes les données (Excel)",
        data=base64.b64decode(excel_data),
        file_name="VAD_analyse.xlsx"
    )
