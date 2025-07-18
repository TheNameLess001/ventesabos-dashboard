import streamlit as st
import requests
import re

st.subheader("🛍️ Boutique Produits : Visualisez chaque produit avec sa photo")

# 1. On récupère la liste unique des produits dans la colonne sélectionnée
produit_col = col_produit  # <- adapte si ta variable de colonne produit a un autre nom !
produits = df[produit_col].dropna().unique()

@st.cache_data(show_spinner=False)
def get_image_url(product_name):
    """
    Va chercher la 1ère image trouvée sur DuckDuckGo Images (pas d'API Key requise).
    """
    try:
        search_url = "https://duckduckgo.com/"
        params = {"q": product_name}
        res = requests.post(search_url, data=params)
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

# 2. AFFICHAGE DES PRODUITS + PHOTOS SOUS FORME DE GRID
cols = st.columns(3)  # Affiche 3 produits par ligne

for idx, produit in enumerate(produits):
    col = cols[idx % 3]
    with col:
        st.markdown(f"**{produit}**")
        url_img = get_image_url(str(produit))
        if url_img:
            st.image(url_img, width=160, caption=produit)
        else:
            st.write(":x: Image non trouvée")
