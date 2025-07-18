import streamlit as st
import pandas as pd
import requests
import re

st.title("📦 Boutique Produits & Podium des ventes")

# --- UPLOAD FICHIER ---
uploaded_file = st.file_uploader("Importer votre fichier (Excel ou CSV)", type=["csv", "xlsx", "xls"])
if not uploaded_file:
    st.info("Merci d'importer un fichier pour continuer.")
    st.stop()

# --- LECTURE FICHIER ---
@st.cache_data(show_spinner=False)
def safe_read_any(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        for enc in ["utf-8", "cp1252", "latin-1"]:
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=enc)
            except Exception:
                continue
    else:
        return pd.read_excel(file, engine="openpyxl")
    st.error("Impossible de lire le fichier.")
    st.stop()

df = safe_read_any(uploaded_file)

# --- NORMALISATION COLONNES ---
df.columns = [c.strip() for c in df.columns]
code_col = df.columns[15]  # P = index 15
montant_col = df.columns[16]  # Q = index 16
etat_col = df.columns[5]  # F = index 5

# --- FILTRAGE : PAS 'annulé' ni 'incident' ---
df = df[
    (~df[etat_col].astype(str).str.lower().str.contains("annul"))
    & (~df[etat_col].astype(str).str.lower().str.contains("incident"))
]

# --- NETTOYAGE ---
df = df[[code_col, montant_col]]
df = df.dropna(subset=[code_col, montant_col])
df[code_col] = df[code_col].astype(str).str.strip()
df[montant_col] = pd.to_numeric(df[montant_col], errors='coerce')
df = df[df[montant_col] > 0]

# --- AGREGATS VENTES ---
ca_par_produit = df.groupby(code_col)[montant_col].sum().sort_values(ascending=False)
qte_par_produit = df.groupby(code_col)[montant_col].count().sort_values(ascending=False)

# --- FONCTION IMAGE ---
@st.cache_data(show_spinner=False)
def get_image_url(product_name):
    try:
        search_url = "https://duckduckgo.com/"
        params = {"q": product_name}
        res = requests.post(search_url, data=params, timeout=10)
        searchObj = re.search(r'vqd=([\d-]+)\&', res.text, re.M|re.I)
        if not searchObj:
            return None
        vqd = searchObj.group(1)
        headers = {'User-Agent': 'Mozilla/5.0'}
        params = (
            ('l', 'fr-fr'),
            ('o', 'json'),
            ('q', product_name),
            ('vqd', vqd),
            ('f', ',,,'),
            ('p', '1'),
            ('v7exp', 'a')
        )
        resp = requests.get("https://duckduckgo.com/i.js", headers=headers, params=params, timeout=10)
        data = resp.json()
        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]["image"]
        else:
            return None
    except Exception:
        return None

# --- ONGLET INTERFACE ---
tabs = st.tabs(["Boutique", "Podium des ventes"])

# --- 1. BOUTIQUE (avec photos) ---
with tabs[0]:
    st.subheader("🛒 Tous les produits")
    produits = ca_par_produit.index.tolist()
    cols = st.columns(3)
    for idx, produit in enumerate(produits):
        col = cols[idx % 3]
        with col:
            st.markdown(f"**{produit}**")
            url_img = get_image_url(str(produit))
            if url_img:
                st.image(url_img, width=150, caption=f"{produit}")
            else:
                st.write(":x: Image non trouvée")
            st.caption(f"Quantité vendue : {qte_par_produit[produit]}")
            st.caption(f"Chiffre d'affaires : {ca_par_produit[produit]:,.0f} MAD")

# --- 2. PODIUM ---
with tabs[1]:
    st.subheader("🏆 Podium des meilleures ventes")
    st.write("**Par chiffre d'affaires (CA) :**")
    podium_ca = ca_par_produit.head(3)
    st.table(pd.DataFrame({
        "Produit": podium_ca.index,
        "CA (MAD)": podium_ca.values,
        "Quantité": [qte_par_produit.get(p, 0) for p in podium_ca.index]
    }).set_index("Produit"))

    st.write("**Par quantité vendue :**")
    podium_qte = qte_par_produit.head(3)
    st.table(pd.DataFrame({
        "Produit": podium_qte.index,
        "Quantité": podium_qte.values,
        "CA (MAD)": [ca_par_produit.get(p, 0) for p in podium_qte.index]
    }).set_index("Produit"))

    st.write("**Les moins vendus (par quantité) :**")
    moins_vendus = qte_par_produit.tail(3)
    st.table(pd.DataFrame({
        "Produit": moins_vendus.index,
        "Quantité": moins_vendus.values,
        "CA (MAD)": [ca_par_produit.get(p, 0) for p in moins_vendus.index]
    }).set_index("Produit"))
