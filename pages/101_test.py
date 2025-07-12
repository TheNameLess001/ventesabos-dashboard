import streamlit as st
from sqlalchemy import create_engine

st.title("TEST CONNEXION POSTGRESQL")

# --- Chaine de connexion complète ---
PG_URL = "postgresql+psycopg2://postgres:Samoju123@@127.0.0.1:5432/postgres"

# --- Affichage de debug pour être sûr que tout s’exécute ---
st.write("🔄 Début du test de connexion...")

try:
    st.write("🔌 Création de l'engine SQLAlchemy...")
    engine = create_engine(PG_URL)
    st.write("🔍 Tentative de connexion à la base...")
    with engine.connect() as conn:
        st.success("✅ Connexion réussie à la base PostgreSQL !")
        result = conn.execute("SELECT 1").fetchone()
        st.write("Résultat du SELECT 1 :", result)
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")

st.write("🎯 Test terminé.")
