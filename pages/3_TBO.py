import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# Protection login
if "logged" not in st.session_state or not st.session_state["logged"]:
    st.warning("Vous devez vous connecter depuis la page d'accueil.")
    st.stop()

st.title("🏆 ANALYSEUR TBO - Fitness Park")

# Gold branding & style onglets
TBO_GOLD = "#FFD700"
st.markdown(f"""
    <style>
    .stApp {{ background-color: #fff; }}
    .block-container {{ padding-top: 2rem; }}
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        background-color: {TBO_GOLD};
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

def analyze_tbo(file):
    product_groups = {
        "ABONNEMENTS": [
            "CDD", "CDD1", "CDD12", "CDIAENG", "CDISENG",
            "SEANCEESSAI", "seancedessaie", "VIP", "OffreSummerBody25",
            "ULTIMATEEMPLOYE", "HOMEPARK", "1MOFFERT", "EMPLOYE",
            "OFFRERENTREE2025, "REGISTRATION-FEE"
        ],
        "ACCESS+": [
            "ALLACCESS+", "ALLACCESS+BF", "ALLACCESS+YS-cc"
        ],
        "COACHING": [
            "10PT", "15PT", "10PTPREMIUM", "1PT",
            "DUO15PT", "20PT", "DUO10PT", "SMALLGROUP", "15PTPREMIUM"
        ],
        "GOODIES": [
            "CADENAS", "CEINTUREMUSCU", "cordeasauterfpk",
            "gantmusculation", "GOURDEFP", "SAC",
            "SERVIETTEGRISE", "SERVIETTENOIRE", "SHAKER",
            "sanglecheville"
        ],
        "WATERSTATION": [
            "waterstation"
        ],
        "BOUTIQUE": []
    }
    try:
        xls = pd.ExcelFile(file)
        turnover_sheet = None
        for sheet in xls.sheet_names:
            sheet_lower = sheet.lower()
            if "chiffre" in sheet_lower or "affaires" in sheet_lower or "ca" in sheet_lower or "ventes" in sheet_lower:
                turnover_sheet = sheet
                break
        if not turnover_sheet:
            turnover_sheet = xls.sheet_names[-1]
        df = pd.read_excel(file, sheet_name=turnover_sheet)

        # Trouver la ligne produits/valeurs
        product_row, value_row = None, None
        for idx, row in df.iterrows():
            row_vals = [str(v) for v in row.values]
            if any("Fitness Park" in val or "Casablanca" in val for val in row_vals):
                value_row = idx
                product_row = idx - 1 if idx > 0 else 0
                break
        if product_row is None or value_row is None:
            return None, None, None, None, "Impossible de trouver les lignes de données dans le fichier Excel.", None
        products = df.iloc[product_row, 3:]
        values = df.iloc[value_row, 3:]
        turnover_data = {}
        for product, value in zip(products, values):
            if pd.notna(product) and pd.notna(value):
                product_name = str(product).strip()
                turnover_data[product_name] = value
        excel_total = list(turnover_data.values())[-1] if turnover_data else 0
        if "Total" in turnover_data:
            excel_total = turnover_data["Total"]
            del turnover_data["Total"]

        # Catégorisation et totaux
        group_totals = {g:0 for g in product_groups}
        group_details = {g:{} for g in product_groups}
        all_data = []
        for product, value in turnover_data.items():
            group = None
            if "Total" in product:
                continue
            for g, prod_list in product_groups.items():
                if g == "ABONNEMENTS":
                    if any(product.startswith(prefix) for prefix in ["CDD", "CDI", "SEANCE"]):
                        group = g
                        break
                    if any(prod.lower() in product.lower() for prod in prod_list):
                        group = g
                        break
                if product in prod_list:
                    group = g
                    break
            if not group:
                group = "BOUTIQUE"
            group_totals[group] += value
            group_details[group][product] = value
            all_data.append({"Groupe": group, "Produit": product, "Valeur": value})
        calculated_total = sum(group_totals.values())
        return group_totals, group_details, calculated_total, excel_total, None, all_data
    except Exception as e:
        return None, None, None, None, f"Erreur pendant l'analyse : {str(e)}", None

tbo_file = st.file_uploader("Importer un fichier TBO (Excel)", type=["xlsx", "xls"])
if not tbo_file:
    st.info("Importez un fichier TBO pour démarrer l'analyse.")
    st.stop()

group_totals, group_details, calculated_total, excel_total, error, all_data = analyze_tbo(tbo_file)
if error:
    st.error(error)
    st.stop()

tabs = st.tabs(["Résumé Global", "Détails par Groupe", "Export"])

# ===== TAB 1 : Résumé Global =====
with tabs[0]:
    st.subheader("🔎 Résumé du Chiffre d'Affaires TBO")
    total_warning = abs(calculated_total - excel_total) > 1

    st.markdown("**Total par groupe de produits**")
    df_totaux = pd.DataFrame([{"Groupe": g, "Total (DH)": total} for g, total in group_totals.items()])
    st.dataframe(df_totaux.sort_values("Total (DH)", ascending=False).style.format({"Total (DH)": "{:,.2f} DH"}))

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Somme des groupes", f"{calculated_total:,.2f} DH")
    col2.metric("Total Excel", f"{excel_total:,.2f} DH")
    diff = calculated_total - excel_total
    col3.metric("Différence", f"{diff:,.2f} DH", delta_color="inverse" if total_warning else "normal")

    if total_warning:
        st.error("⚠️ Attention : Écart significatif détecté entre la somme des groupes et le total Excel.")

    # Pie chart
    st.markdown("### 🥧 Répartition du CA par groupe")
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

    # Nouveau : Barplot par produit du groupe sélectionné
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
    df_all = pd.DataFrame(all_data)
    excel_data = to_excel({"Résumé Groupes": df_totaux, "Détail": df_all})
    st.download_button(
        label="📥 Télécharger toutes les données (Excel)",
        data=base64.b64decode(excel_data),
        file_name="TBO_analyse.xlsx"
    )
