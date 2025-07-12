from sqlalchemy import create_engine

PG_USER = 'postgres'
PG_PASS = 'Samoju123@'
PG_HOST = '127.0.0.1'  # ← FORCE TCP/IP
PG_DB   = 'postgres'
PG_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}"

import streamlit as st
st.title("TEST CONNEXION POSTGRESQL (TCP/IP)")

try:
    engine = create_engine(PG_URL)
    with engine.connect() as conn:
        st.success("Connexion réussie à la base PostgreSQL (TCP/IP) !")
        st.write(conn.execute("SELECT 1").fetchone())
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
