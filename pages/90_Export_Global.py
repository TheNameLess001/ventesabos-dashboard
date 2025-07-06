import streamlit as st
import pandas as pd
import base64
from io import BytesIO

st.title("📦 Export Global Analyses")

def to_excel(df_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for name, df in df_dict.items():
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=name[:28], index=False)
    output.seek(0)
    return base64.b64encode(output.read()).decode()

export_dict = {}
if "abos_df" in st.session_state and st.session_state["abos_df"] is not None:
    export_dict["Abonnements"] = st.session_state["abos_df"]
if "recouvrement_df" in st.session_state and st.session_state["recouvrement_df"] is not None:
    export_dict["Recouvrement"] = st.session_state["recouvrement_df"]
if "vad_df" in st.session_state and st.session_state["vad_df"] is not None:
    export_dict["VAD"] = st.session_state["vad_df"]
if "facture_df" in st.session_state and st.session_state["facture_df"] is not None:
    export_dict["Facture"] = st.session_state["facture_df"]

if export_dict:
    excel_data = to_excel(export_dict)
    st.success(f"{len(export_dict)} analyses prêtes à exporter.")
    st.download_button(
        label="📥 Télécharger toutes les analyses (Excel)",
        data=base64.b64decode(excel_data),
        file_name="Export_Analyses_FitnessPark.xlsx"
    )
else:
    st.warning("Aucune analyse n'a encore été importée sur les autres pages.")
