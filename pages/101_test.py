from sqlalchemy import create_engine

PG_USER = 'postgres'
PG_PASS = 'Samoju123@'
PG_HOST = 'localhost'
PG_DB   = 'fpk_dash'   # mets ici exactement ce qui est dans pgAdmin
PG_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}"
engine = create_engine(PG_URL)

with engine.connect() as conn:
    print(conn.execute("SELECT 1").fetchone())

