import streamlit as st
import pandas as pd
import os

st.title("🛍️ Marge Goodies & Boutique")

# Charger automatiquement goodies.csv et boutique.csv du dossier principal
try:
    goodies = pd.read_csv("Goodies.csv")
    boutique = pd.read_csv("Boutique.csv")
except Exception as e:
    st.error(f"Impossible de charger Goodies.csv ou Boutique.csv dans le dossier principal : {e}")
    st.stop()

st.success("Fichiers Goodies.csv et Boutique.csv bien trouvés dans le dossier principal.")

# Import du TBO (avec page 1 et page 6 dans le même fichier)
st.markdown("**Importer le fichier TBO (contenant quantités ET CA)**")
file_tbo = st.file_uploader("Fichier TBO", type=["csv", "xlsx"], key="tbo")

if file_tbo:
    # Chargement robuste du TBO
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

    tbo = read_any(file_tbo)
    if tbo is None:
        st.stop()

    st.write("#### Colonnes TBO :", tbo.columns)
    # Sélection de colonnes
    col_prod = st.selectbox("Colonne produit", tbo.columns)
    col_qte = st.selectbox("Colonne quantité vendue", tbo.columns)
    col_ca = st.selectbox("Colonne chiffre d'affaires", tbo.columns)
    # Colonnes dans goodies et boutique
    col_prod_goodies = goodies.columns[0]
    col_prix_goodies = goodies.columns[1]
    col_prod_boutique = boutique.columns[0]
    col_prix_boutique = boutique.columns[1]

    # Agréger tous les produits (goodies + boutique)
    prix_achat = pd.concat([
        goodies[[col_prod_goodies, col_prix_goodies]].rename(columns={col_prod_goodies: "Produit", col_prix_goodies: "PrixAchat"}),
        boutique[[col_prod_boutique, col_prix_boutique]].rename(columns={col_prod_boutique: "Produit", col_prix_boutique: "PrixAchat"})
    ], ignore_index=True)
    prix_achat["Produit"] = prix_achat["Produit"].astype(str).str.upper()
    prix_achat["PrixAchat"] = pd.to_numeric(prix_achat["PrixAchat"], errors="coerce")

    # Filtre uniquement sur produits présents dans goodies/boutique
    tbo["Produit"] = tbo[col_prod].astype(str).str.upper()
    tbo["Quantité"] = pd.to_numeric(tbo[col_qte], errors="coerce")
    tbo["CA"] = pd.to_numeric(tbo[col_ca], errors="coerce")

    # Match uniquement les produits présents dans goodies/boutique
    tbo_goodies_boutique = tbo[tbo["Produit"].isin(prix_achat["Produit"])].copy()
    df_marge = pd.merge(tbo_goodies_boutique, prix_achat, on="Produit", how="left")
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
    st.info("Merci d'importer le fichier TBO (page 1 et 6 ensemble).")

