import streamlit as st
from sqlalchemy import create_engine

PG_USER = 'postgres'
PG_PASS = 'Samoju123@'
PG_HOST = '127.0.0.1'  # ou 'localhost' si ça fonctionne
PG_DB   = 'postgres'
PG_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}"

st.title("TEST CONNEXION POSTGRESQL")

try:
    engine = create_engine(PG_URL)
    with engine.connect() as conn:
        st.success("✅ Connexion réussie à la base PostgreSQL !")
        st.write("Résultat du SELECT 1 :", conn.execute("SELECT 1").fetchone())
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")
