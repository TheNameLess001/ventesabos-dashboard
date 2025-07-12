from sqlalchemy import create_engine

PG_USER = 'postgres'
PG_PASS = 'Samoju123@'
PG_HOST = 'localhost'
PG_DB   = 'postgres'
PG_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}"

print("Début script")  # ← Ici
try:
    print("Avant create_engine")  # ← Ici
    engine = create_engine(PG_URL)
    print("Après create_engine")   # ← Ici
    with engine.connect() as conn:
        print("Connexion établie")  # ← Ici
        print(conn.execute("SELECT 1").fetchone())
    print("Connexion OK !")
except Exception as e:
    print("Erreur de connexion:", e)
