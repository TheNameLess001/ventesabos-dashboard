import streamlit as st
from sqlalchemy import create_engine

st.title("🔌 Test connexion à la base FPK_DASH")

PG_USER = 'postgres'
PG_PASS = 'Samoju123@'
PG_HOST = '127.0.0.1'
PG_DB   = 'FPK_DASH'
PG_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}"

st.write("Tentative de connexion à la base de données...")

try:
    engine = create_engine(PG_URL)
    with engine.connect() as conn:
        st.success("✅ Connexion réussie à la base FPK_DASH !")
        res = conn.execute("SELECT 1").fetchone()
        st.write("Résultat du SELECT 1 :", res)
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")

st.write("Fin du test.")
