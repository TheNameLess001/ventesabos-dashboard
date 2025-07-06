import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

if "logged" not in st.session_state or not st.session_state["logged"]:
    st.warning("Vous devez vous connecter depuis la page d'accueil.")
    st.stop()

st.title("🚰 VAD (Access+ & Waterstation) - Fitness Park")

file = st.file_uploader("Importer le fichier VAD (CSV ou Excel)", type=["csv", "xlsx"])
if not file:
    st.info("Importez un fichier VAD pour démarrer l'analyse.")
    st.stop()

ext = file.name.split('.')[-1]
for enc in ["utf-8", "cp1252", "latin-1"]:
    try:
        file.seek(0)
        if ext == "csv":
            df = pd.read_csv(file, encoding=enc, sep=None, engine="python")
        else:
            df = pd.read_excel(file)
        break
    except Exception:
        continue

df.columns = df.columns.str.strip()

# --- NOM EXACT DES COLONNES ---
def find_col(possibles):
    for col in df.columns:
        col_l = col.lower().replace("é", "e").replace("è", "e").replace("ê", "e")
        for p in possibles:
            if col_l == p.lower():
                return col
    return None

nom_col = find_col(["nom"])
prenom_col = find_col(["prénom", "prenom"])
montant_ttc_col = find_col(["montant ttc facture ou avoir"])
montant_ht_col = find_col(["montant ht de la ligne de facture / avoir"])
codeprod_col = find_col(["code du produit"])
com_col = find_col(["auteur"])
statut_col = None
for col in df.columns:
    if "statut" in col.lower() or col.lower() == "f":
        statut_col = col
        break

if not all([nom_col, prenom_col, montant_ttc_col, montant_ht_col, codeprod_col, com_col]):
    st.warning("Colonnes non détectées automatiquement. Merci de les sélectionner manuellement :")
    nom_col = st.selectbox("Colonne Nom", df.columns)
    prenom_col = st.selectbox("Colonne Prénom", df.columns)
    montant_ttc_col = st.selectbox("Colonne Montant TTC facture ou avoir", df.columns)
    montant_ht_col = st.selectbox("Colonne Montant HT de la ligne de facture / avoir", df.columns)
    codeprod_col = st.selectbox("Colonne Code du produit", df.columns)
    com_col = st.selectbox("Colonne Auteur (commercial)", df.columns)

# --- SUPPRIME LES "ANNULÉ" ---
if statut_col:
    df = df[~df[statut_col].astype(str).str.upper().str.contains("ANNULE")]

# Nettoyage HT (positif seulement)
df[montant_ht_col] = pd.to_numeric(df[montant_ht_col], errors="coerce").fillna(0)
df = df[df[montant_ht_col] > 0]

tabs = st.tabs(["Analyse Club ACCESS+", "Analyse Commerciale ACCESS+", "Analyse Waterstation"])

# ----------- TAB 1 : CLUB ACCESS+ -----------
with tabs[0]:
    st.header("💳 Analyse Club ACCESS+")
    chk_650 = st.checkbox("Supprimer les ventes ACCESS+ à 650 MAD (colonne M)", value=True)
    df_access = df[df[codeprod_col].astype(str).str.upper().str.startswith("ALLACCESS+")].copy()
    df_access[montant_ttc_col] = pd.to_numeric(df_access[montant_ttc_col], errors="coerce").fillna(0)
    if chk_650:
        df_access = df_access[df_access[montant_ttc_col].round(2) != 650.00]

    # Suppression des doublons (Nom+Prénom)
    df_access["client_id"] = df_access[nom_col].astype(str).str.strip().str.upper() + " " + df_access[prenom_col].astype(str).str.strip().str.upper()
    df_access = df_access.drop_duplicates("client_id")

    quantite_access = len(df_access)
    st.metric("Quantité Access+ vendue (unique)", quantite_access)

    # Tableau ventes club
    st.dataframe(df_access[[nom_col, prenom_col, montant_ttc_col, montant_ht_col, codeprod_col]].reset_index(drop=True))

# ----------- TAB 2 : COMMERCIAL ACCESS+ -----------
with tabs[1]:
    st.header("👔 Analyse ACCESS+ par commercial")
    df_access_com = df[df[codeprod_col].astype(str).str.upper().str.startswith("ALLACCESS+")].copy()
    # (Pas de filtre 650 ici !)
    df_access_com[montant_ttc_col] = pd.to_numeric(df_access_com[montant_ttc_col], errors="coerce").fillna(0)
    df_access_com["client_id"] = df_access_com[nom_col].astype(str).str.strip().str.upper() + " " + df_access_com[prenom_col].astype(str).str.strip().str.upper()
    df_access_com = df_access_com.drop_duplicates(["client_id", com_col])

    tab_acc = df_access_com.groupby(com_col).agg({"client_id":"count"}).rename(columns={"client_id":"Nb ventes unique"}).sort_values("Nb ventes unique", ascending=False)
    st.dataframe(tab_acc)

    st.markdown("### 📊 Ventes Access+ par commercial")
    if not tab_acc.empty:
        plt.figure(figsize=(10,4))
        tab_acc["Nb ventes unique"].plot(kind="bar", color="#409EFF")
        plt.ylabel("Quantité")
        plt.xlabel("Commercial")
        plt.title("Access+ vendus par commercial (unique clients)")
        plt.tight_layout()
        st.pyplot(plt.gcf())
        plt.clf()
    else:
        st.info("Aucune vente Access+ à afficher.")

# ----------- TAB 3 : WATERSTATION -----------
with tabs[2]:
    st.header("💧 Analyse WATERSTATION")
    df_ws = df[df[codeprod_col].astype(str).str.lower().str.startswith("waterstation")].copy()
    df_ws["client_id"] = df_ws[nom_col].astype(str).str.strip().str.upper() + " " + df_ws[prenom_col].astype(str).str.strip().str.upper()
    df_ws = df_ws.drop_duplicates("client_id")
    quantite_ws = len(df_ws)
    st.metric("Quantité Waterstation vendue (unique)", quantite_ws)

    tab_ws = df_ws.groupby(com_col).agg({"client_id":"count"}).rename(columns={"client_id":"Nb ventes unique"}).sort_values("Nb ventes unique", ascending=False)
    st.dataframe(tab_ws)

    st.markdown("### 📊 Ventes Waterstation par commercial")
    if not tab_ws.empty:
        plt.figure(figsize=(10,4))
        tab_ws["Nb ventes unique"].plot(kind="bar", color="#25B1E9")
        plt.ylabel("Quantité")
        plt.xlabel("Commercial")
        plt.title("Waterstation vendues par commercial (unique clients)")
        plt.tight_layout()
        st.pyplot(plt.gcf())
        plt.clf()
    else:
        st.info("Aucune vente Waterstation à afficher.")
