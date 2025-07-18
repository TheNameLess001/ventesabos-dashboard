import streamlit as st
import pandas as pd
import requests
import re

st.title("🛍️ Catalogue Produits avec Photos Automatiques")

# -------- UPLOAD ----------
uploaded_file = st.file_uploader("Importer votre fichier produits (Excel ou CSV)", type=["csv", "xlsx", "xls"])
if not uploaded_file:
    st.info("Veuillez importer un fichier pour continuer.")
    st.stop()

# -------- READ DATA ---------
@st.cache_data(show_spinner=False)
def safe_read_any(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        for enc in ["utf-8", "cp1252", "latin-1"]:
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=enc, sep=None, engine='python')
            except Exception:
                continue
    else:
        return pd.read_excel(file, engine="openpyxl")
    st.error("Impossible de lire le fichier. Essayez un autre format ou encoding.")
    st.stop()

df = safe_read_any(uploaded_file)
df.columns = df.columns.str.strip()

# -------- CHOOSE PRODUCT COLUMN ----------
cols = list(df.columns)
col_produit = st.selectbox("Sélectionnez la colonne contenant le nom ou code produit :", cols)

produits = df[col_produit].dropna().unique()

# -------- FONCTION IMAGE WEB -----------
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

# -------- AFFICHAGE GRID BOUTIQUE -------
st.subheader("🖼️ Boutique produits avec photo")
if len(produits) == 0:
    st.warning("Aucun produit trouvé dans cette colonne.")
else:
    cols = st.columns(3)  # 3 produits par ligne
    for idx, produit in enumerate(produits):
        col = cols[idx % 3]
        with col:
            st.markdown(f"**{produit}**")
            url_img = get_image_url(str(produit))
            if url_img:
                st.image(url_img, width=160, caption=produit)
            else:
                st.write(":x: Image non trouvée")
