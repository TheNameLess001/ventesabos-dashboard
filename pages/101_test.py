from sqlalchemy import create_engine

PG_URL = "postgresql+psycopg2://postgres:Samoju123@@127.0.0.1:5432/postgres"

try:
    engine = create_engine(PG_URL)
    with engine.connect() as conn:
        print("Connexion OK !")
        print(conn.execute("SELECT 1").fetchone())
except Exception as e:
    print("Erreur de connexion :", e)
