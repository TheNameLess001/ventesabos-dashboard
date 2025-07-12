import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from io import BytesIO
import base64

st.title("📊 SQLite Dashboard - Super Simple & Persistent")

# Path to your local SQLite file
DB_PATH = "mydata.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

# Table name
TABLE_NAME = "mydata"

# 1. Upload CSV file
file = st.file_uploader("Upload a CSV file to store in the database", type=["csv"])
if file:
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    # Save data to SQLite, replace table if exists
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
    st.success(f"File imported and saved to table '{TABLE_NAME}' in {DB_PATH}.")

# 2. Show data from database
if st.button("Show data in database"):
    try:
        df_db = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", engine)
        st.dataframe(df_db)
        # 3. Export as Excel
        towrite = BytesIO()
        df_db.to_excel(towrite, index=False, engine='xlsxwriter')
        towrite.seek(0)
        b64 = base64.b64encode(towrite.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="export.xlsx">⬇️ Download Excel export</a>'
        st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"No data found or error: {e}")

st.write("---")
st.info("• Upload a CSV to store it in a database (mydata.db). \
\n• Click 'Show data in database' to see and export everything stored so far.")
