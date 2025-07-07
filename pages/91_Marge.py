import streamlit as st
import pandas as pd
import numpy as np

st.title("🛍️ Marge Goodies & Boutique")

st.markdown("**Importer la page 1 du TBO (quantités vendues)**")
file_qte = st.file_uploader("Page 1 - Quantités", type=["csv", "xlsx"], key="qte")
st.markdown("**Importer la page 6 du TBO (CA)**")
file_ca = st.file_uploader("Page 6 - CA", type=["csv", "xlsx"], key="ca")

st.markdown("**Importer le fichier Goodies.csv (prix achat)**")
file_goodies = st.file_uploader("Goodies.csv", type=["csv", "xlsx"], key="goodies")
st.markdown("**Importer le fichier Boutique.csv (prix achat)**")
file_boutique = st.file_uploader("Boutique.csv", type=["csv", "xlsx"], key="boutique")

if file_qte and file_ca and file_goodies and file_boutique:
    # Chargement robuste
    def read_any(file):
        for enc in ["utf-8", "cp1252", "latin-1"]:
            try:
                file.seek(0)
                if file.name.endswith(".csv"):
                    return pd.read_csv(file, encoding=enc, sep=None, engine="python")
                else:
                    return pd.read_excel(file)
            except Exception:
                continue
        st.error("Impossible de lire le fichier.")
        return None

    df_qte = read_any(file_qte)
    df_ca = read_any(file_ca)
    goodies = read_any(file_goodies)
    boutique = read_any(file_boutique)

    if any(d is None for d in [df_qte, df_ca, goodies, boutique]):
        st.stop()

    st.write("#### Colonnes page 1 (quantités) :", df_qte.columns)
    st.write("#### Colonnes page 6 (CA) :", df_ca.columns)
    st.write("#### Colonnes goodies :", goodies.columns)
    st.write("#### Colonnes boutique :", boutique.columns)

    # Sélection des colonnes
    col_prod_qte = st.selectbox("Colonne produit (Quantités)", df_qte.columns)
    col_qte = st.selectbox("Colonne quantité", df_qte.columns)
    col_prod_ca = st.selectbox("Colonne produit (CA)", df_ca.columns)
    col_ca = st.selectbox("Colonne chiffre d'affaires", df_ca.columns)
    col_prod_goodies = st.selectbox("Colonne produit (Goodies)", goodies.columns)
    col_prix_goodies = st.selectbox("Colonne prix achat (Goodies)", goodies.columns)
    col_prod_boutique = st.selectbox("Colonne produit (Boutique)", boutique.columns)
    col_prix_boutique = st.selectbox("Colonne prix achat (Boutique)", boutique.columns)

    # Agréger tous les produits
    prix_achat = pd.concat([
        goodies[[col_prod_goodies, col_prix_goodies]].rename(columns={col_prod_goodies: "Produit", col_prix_goodies: "PrixAchat"}),
        boutique[[col_prod_boutique, col_prix_boutique]].rename(columns={col_prod_boutique: "Produit", col_prix_boutique: "PrixAchat"})
    ], ignore_index=True)
    prix_achat["Produit"] = prix_achat["Produit"].astype(str).str.upper()
    prix_achat["PrixAchat"] = pd.to_numeric(prix_achat["PrixAchat"], errors="coerce")

    # Fusion Quantité & CA
    df_qte_ = df_qte[[col_prod_qte, col_qte]].copy().rename(columns={col_prod_qte: "Produit", col_qte: "Quantité"})
    df_ca_ = df_ca[[col_prod_ca, col_ca]].copy().rename(columns={col_prod_ca: "Produit", col_ca: "CA"})
    for df_ in [df_qte_, df_ca_]:
        df_["Produit"] = df_["Produit"].astype(str).str.upper()
    df_qte_["Quantité"] = pd.to_numeric(df_qte_["Quantité"], errors="coerce")
    df_ca_["CA"] = pd.to_numeric(df_ca_["CA"], errors="coerce")
    df_ventes = pd.merge(df_qte_, df_ca_, on="Produit", how="inner")

    # Merge avec prix d'achat
    df_marge = pd.merge(df_ventes, prix_achat, on="Produit", how="left")
    df_marge = df_marge.dropna(subset=["Quantité", "CA", "PrixAchat"])
    df_marge = df_marge[df_marge["Quantité"] > 0]

    # Calcul prix vente moyen, marge unitaire, marge totale
    df_marge["PrixVenteMoyen"] = df_marge["CA"] / df_marge["Quantité"]
    df_marge["MargeUnitaire"] = df_marge["PrixVenteMoyen"] - df_marge["PrixAchat"]
    df_marge["MargeTotale"] = df_marge["MargeUnitaire"] * df_marge["Quantité"]

    st.markdown("### 🧾 Marge réelle par produit (Goodies & Boutique)")
    st.dataframe(df_marge[["Produit", "Quantité", "CA", "PrixAchat", "PrixVenteMoyen", "MargeUnitaire", "MargeTotale"]])

    st.markdown("### 💰 Marge totale Goodies & Boutique")
    st.write(f"**Marge totale globale** : {df_marge['MargeTotale'].sum():,.0f} MAD")

    # Export Excel
    import base64
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_marge.to_excel(writer, sheet_name="Marge_Produits", index=False)
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    st.download_button(
        "📥 Exporter l'analyse (Excel)",
        base64.b64decode(b64),
        file_name="marge_goodies_boutique.xlsx"
    )
else:
    st.info("Merci d'importer les 4 fichiers demandés.")
