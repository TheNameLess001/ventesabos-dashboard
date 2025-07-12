from sqlalchemy import create_engine

PG_USER = 'postgres'
PG_PASS = 'Samoju123@'
PG_HOST = '127.0.0.1'
PG_DB   = 'postgres'
PG_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}"

try:
    engine = create_engine(PG_URL)
    with engine.connect() as conn:
        print("Connexion OK !")
        print(conn.execute("SELECT 1").fetchone())
except Exception as e:
    print("Erreur de connexion :", e)
