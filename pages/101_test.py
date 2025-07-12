import streamlit as st
from sqlalchemy import create_engine

st.title("TEST CONNEXION POSTGRESQL")

PG_URL = "postgresql+psycopg2://postgres:Samoju123@@127.0.0.1:5432/FPK_DASH"

try:
    engine = create_engine(PG_URL)
    with engine.connect() as conn:
        st.success("✅ Connexion réussie à la base PostgreSQL !")
        st.write("Résultat du SELECT 1 :", conn.execute("SELECT 1").fetchone())
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")
