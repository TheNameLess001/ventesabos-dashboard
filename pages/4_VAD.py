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

# Auto encodage
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

nom_col = [c for c in df.columns if c.lower().startswith("nom")][0]
prenom_col = [c for c in df.columns if c.lower().startswith("prénom") or c.lower().startswith("prenom")][0]
montant_ttc_col = [c for c in df.columns if "ttc" in c.lower() or "montant" in c.lower() and "ttc" in c.lower() or c.lower() == "m"][0]
montant_ht_col = [c for c in df.columns if ("montant ht" in c.lower() or c.lower() == "r")][0]
codeprod_col = [c for c in df.columns if "code produit" in c.lower() or c.lower() == "p"][0]
com_col = [c for c in df.columns if "commercial" in c.lower() or c.lower().startswith("prénom") and "initial" in c.lower() or c.lower() == "w"][-1]

# Nettoyage des montants (pas de négatif ni zéro, HT)
df[montant_ht_col] = pd.to_numeric(df[montant_ht_col], errors="coerce").fillna(0)
df = df[df[montant_ht_col] > 0]

# Section ACCESS+
st.header("💳 Analyse ACCESS+")
chk_650 = st.checkbox("Supprimer les ventes ACCESS+ à 650 MAD (colonne M)", value=True)
df_access = df[df[codeprod_col].astype(str).str.upper().str.startswith("ALLACCESS+")]
if chk_650:
    df_access = df_access[df_access[montant_ttc_col] != 650]

# Suppression des doublons (Nom+Prénom)
df_access["client_id"] = df_access[nom_col].astype(str).str.strip().str.upper() + " " + df_access[prenom_col].astype(str).str.strip().str.upper()
df_access = df_access.drop_duplicates("client_id")

quantite_access = len(df_access)
st.metric("Quantité Access+ vendue (unique)", quantite_access)

# Tableau ventes par commercial
tab_acc = df_access.groupby(com_col).agg({"client_id":"count"}).rename(columns={"client_id":"Nb ventes unique"}).sort_values("Nb ventes unique", ascending=False)
st.dataframe(tab_acc)

# Barplot
st.markdown("### 📊 Ventes Access+ par commercial")
plt.figure(figsize=(10,4))
tab_acc["Nb ventes unique"].plot(kind="bar", color="#409EFF")
plt.ylabel("Quantité")
plt.xlabel("Commercial")
plt.title("Access+ vendus par commercial (unique clients)")
plt.tight_layout()
st.pyplot(plt.gcf())
plt.clf()

# Section WATERSTATION
st.header("💧 Analyse WATERSTATION")
df_ws = df[df[codeprod_col].astype(str).str.lower().str.startswith("waterstation")]
# Un seul accès par client (Nom+Prénom)
df_ws["client_id"] = df_ws[nom_col].astype(str).str.strip().str.upper() + " " + df_ws[prenom_col].astype(str).str.strip().str.upper()
df_ws = df_ws.drop_duplicates("client_id")

quantite_ws = len(df_ws)
st.metric("Quantité Waterstation vendue (unique)", quantite_ws)

tab_ws = df_ws.groupby(com_col).agg({"client_id":"count"}).rename(columns={"client_id":"Nb ventes unique"}).sort_values("Nb ventes unique", ascending=False)
st.dataframe(tab_ws)

st.markdown("### 📊 Ventes Waterstation par commercial")
plt.figure(figsize=(10,4))
tab_ws["Nb ventes unique"].plot(kind="bar", color="#25B1E9")
plt.ylabel("Quantité")
plt.xlabel("Commercial")
plt.title("Waterstation vendues par commercial (unique clients)")
plt.tight_layout()
st.pyplot(plt.gcf())
plt.clf()
