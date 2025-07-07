import streamlit as st
import pandas as pd
import numpy as np
import os

st.title("🛍️ Marge Goodies & Boutique (analyse avancée)")

# Charger goodies.csv et boutique.csv du dossier principal
try:
    goodies = pd.read_csv("Goodies.csv")
    boutique = pd.read_csv("Boutique.csv")
except Exception as e:
    st.error(f"Impossible de charger Goodies.csv ou Boutique.csv : {e}")
    st.stop()

st.success("Fichiers Goodies.csv et Boutique.csv bien trouvés dans le dossier principal.")

st.markdown("**Importer la page 1 du TBO (quantités)**")
file_tbo1 = st.file_uploader("Page 1 TBO", type=["csv", "xlsx"], key="tbo1")
st.markdown("**Importer la page 6 du TBO (CA)**")
file_tbo6 = st.file_uploader("Page 6 TBO", type=["csv", "xlsx"], key="tbo6")

def read_any(file, header=None):
    for enc in ["utf-8", "cp1252", "latin-1"]:
        try:
            file.seek(0)
            if file.name.endswith(".csv"):
                return pd.read_csv(file, encoding=enc, header=header)
            else:
                return pd.read_excel(file, header=header)
        except Exception:
            continue
    st.error("Impossible de lire le fichier.")
    return None

if file_tbo1 and file_tbo6:
    # Lecture brute des deux fichiers (on lit TOUT pour pouvoir naviguer dans les lignes)
    tbo1_full = read_any(file_tbo1, header=None)
    tbo6_full = read_any(file_tbo6, header=None)
    if tbo1_full is None or tbo6_full is None:
        st.stop()

    st.write("Page 1 (quantité) :")
    st.dataframe(tbo1_full.head(8))
    st.write("Page 6 (CA) :")
    st.dataframe(tbo6_full.head(8))

    # Lecture des produits (ligne 4), quantités (ligne 6), CA (ligne 5)
    produits = tbo1_full.iloc[3].values
    quantites = tbo1_full.iloc[5].values
    ca = tbo6_full.iloc[4].values

    # Construction DataFrame ventes
    df = pd.DataFrame({
        "Produit": produits,
        "Quantité": quantites,
        "CA": ca
    })
    df = df.dropna()
    # Nettoyage
    df["Produit"] = df["Produit"].astype(str).str.upper().str.strip()
    df["Quantité"] = pd.to_numeric(df["Quantité"], errors="coerce")
    df["CA"] = pd.to_numeric(df["CA"], errors="coerce")
    df = df[df["Quantité"] > 0]
    df = df[df["CA"] > 0]

    # Concat base prix d'achat
    goodies.columns = ["Produit", "PrixAchat"]
    boutique.columns = ["Produit", "PrixAchat"]
    prix_achat = pd.concat([goodies, boutique], ignore_index=True)
    prix_achat["Produit"] = prix_achat["Produit"].astype(str).str.upper().str.strip()
    prix_achat["PrixAchat"] = pd.to_numeric(prix_achat["PrixAchat"], errors="coerce")

    # Merge
    df_marge = pd.merge(df, prix_achat, on="Produit", how="inner")
    df_marge = df_marge.dropna(subset=["Quantité", "CA", "PrixAchat"])
    df_marge = df_marge[df_marge["Quantité"] > 0]

    # Calculs marge
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
    st.info("Merci d'importer la page 1 ET la page 6 du TBO.")

