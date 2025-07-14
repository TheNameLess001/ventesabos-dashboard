import streamlit as st
import pandas as pd
import datetime
import io
import base64

st.set_page_config(layout="wide")
st.title("🔍 Extraction clients sans Access+ et/ou Waterstation")

def read_csv_any_encoding_any_sep(file):
    """Lit un CSV même si le séparateur ou l'encodage sont exotiques."""
    encodings = ["utf-8", "utf-16", "ISO-8859-1", "latin1"]
    seps = [",", ";", "\t", "|"]
    last_error = None
    for enc in encodings:
        for sep in seps:
            try:
                file.seek(0)
                df = pd.read_csv(file, encoding=enc, sep=sep)
                # Vérifie qu'il y a au moins 2 colonnes pour valider
                if len(df.columns) > 1:
                    return df
            except Exception as e:
                last_error = e
                continue
    # Si rien ne marche, on lit tout et on affiche les premières lignes brutes
    file.seek(0)
    preview = file.read(1024)
    st.error("Impossible de lire le fichier CSV avec les encodages et séparateurs courants.")
    st.write("Aperçu brut du fichier :", preview)
    if last_error:
        st.write(f"Dernière erreur rencontrée : {last_error}")
    raise ValueError("Lecture du fichier impossible.")

def calcul_age(date_naissance):
    try:
        if pd.isnull(date_naissance): return None
        if isinstance(date_naissance, str):
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    date = datetime.datetime.strptime(date_naissance, fmt)
                    break
                except: continue
            else:
                return None
        else:
            date = pd.to_datetime(date_naissance, errors='coerce')
        today = pd.Timestamp("today")
        age = (today - pd.to_datetime(date)).days // 365
        return age
    except: return None

uploaded_file = st.file_uploader("Importer la liste des clients", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Lecture du fichier, compatible tous encodages ET tous séparateurs
    if uploaded_file.name.endswith(".csv"):
        df = read_csv_any_encoding_any_sep(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("Aperçu fichier :", df.head(10))
    colonnes = df.columns.tolist()

    # Sélection manuelle si besoin
    col_type = st.selectbox("Colonne TYPE (ex: 'Type')", colonnes, index=0)
    col_nom = st.selectbox("Colonne NOM DU CLIENT", colonnes, index=1)
    col_abonnement = st.selectbox("Colonne ABONNEMENT (Access+/Waterstation) (U)", colonnes, index=20 if len(colonnes)>20 else -1)
    col_naissance = st.selectbox("Colonne DATE DE NAISSANCE (F)", colonnes, index=5 if len(colonnes)>5 else -1)

    # Masques pour options
    mask_access = ~df[col_abonnement].astype(str).str.upper().str.contains("ACCESS\+", regex=True, na=False)
    mask_water = ~df[col_abonnement].astype(str).str.upper().str.contains("WATERSTATION", regex=True, na=False)

    # Vue 1 : Sans Access+
    st.header("🛑 Clients sans Access+ (uniques)")
    vue1 = df[mask_access].drop_duplicates(subset=[col_nom])
    st.dataframe(vue1, use_container_width=True)
    st.info(f"Nombre de clients sans Access+ : **{len(vue1)}**")

    # Vue 2 : Sans Access+ ni Waterstation
    st.header("🚱 Clients sans Access+ ni Waterstation")
    vue2 = df[mask_access & mask_water].drop_duplicates(subset=[col_nom])
    st.dataframe(vue2, use_container_width=True)
    st.info(f"Nombre de clients sans Access+ ni Waterstation : **{len(vue2)}**")

    # Vue 3 : Sans Waterstation et < 25 ans
    st.header("🎯 Clients sans Waterstation et < 25 ans")
    df["AGE"] = df[col_naissance].apply(calcul_age)
    mask_age = df["AGE"].notnull() & (df["AGE"] < 25)
    vue3 = df[mask_water & mask_age].drop_duplicates(subset=[col_nom])
    st.dataframe(vue3, use_container_width=True)
    st.info(f"Nombre de clients sans Waterstation et < 25 ans : **{len(vue3)}**")

    # Export Excel combiné
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        vue1.to_excel(writer, sheet_name="Sans_Access+", index=False)
        vue2.to_excel(writer, sheet_name="Sans_Access+_ni_Waterstation", index=False)
        vue3.to_excel(writer, sheet_name="Sans_Waterstation_<25ans", index=False)
        writer.save()
    st.download_button(
        "⬇️ Télécharger l'export Excel combiné",
        data=output.getvalue(),
        file_name="clients_sans_options.xlsx"
    )
else:
    st.warning("Importe un fichier pour démarrer l'analyse.")
