import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import re
import calendar
from collections import Counter
import numpy as np

# ----- MAPPING -----
# ... [Garde ici ton mapping et fonctions utilitaires comme avant] ...
# (Je les laisse inchangées pour alléger ce message)

# ... (Garde ici les fonctions get_segment, make_unique, mad_format, extract_month_name) ...

def highlight_annual(row):
    styles = ['']  # Première colonne = segment
    values = row[1:-1].values  # Tous les mois sauf segment & total
    for i, val in enumerate(values):
        if i == 0 or pd.isna(val):
            styles.append('')
        else:
            prev = values[i-1]
            if pd.isna(prev) or prev == 0:
                styles.append('')
            else:
                delta = (val - prev) / abs(prev)
                if delta > 0.10:
                    styles.append('background-color: #FFB3B3')  # Rouge
                elif delta < -0.10:
                    styles.append('background-color: #B3FFB3')  # Vert
                else:
                    styles.append('')
    styles.append('')  # Total Année
    return styles

def highlight_monthly(val, prev):
    try:
        if pd.isna(prev) or prev == 0 or pd.isna(val):
            return ''
        delta = (val - prev) / abs(prev)
        if delta > 0.10:
            return 'background-color: #FFB3B3'
        elif delta < -0.10:
            return 'background-color: #B3FFB3'
        else:
            return ''
    except:
        return ''

st.set_page_config(layout="wide")
st.title("💼 Analyse des Charges & Segments")

st.info(
    "Sur tous les tableaux, les charges qui ont **augmenté de plus de 10%** sont surlignées en **rouge**, "
    "celles qui ont **diminué de plus de 10%** en **vert** (comparé au mois précédent)."
)

uploaded_file = st.file_uploader("🗂️ Importer le fichier Balance", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # ... [Bloc lecture/import CSV ou Excel comme dans ton code d'origine] ...
        if uploaded_file.name.endswith('.csv'):
            content = uploaded_file.read()
            encodings = ['utf-8', 'ISO-8859-1', 'latin1']
            for enc in encodings:
                try:
                    s = content.decode(enc)
                    break
                except:
                    continue
            lines = s.splitlines()
            sep_candidates = [';', ',', '\t', '|']
            sep = max(sep_candidates, key=lambda c: lines[3].count(c))
            header4 = lines[3].split(sep)
            header4 = [str(x).strip() for x in header4]
            header4 = make_unique(header4)
            header5 = lines[4].split(sep)
            header5 = [str(x).strip() for x in header5]
            data_lines = lines[5:]
            s_data = "\n".join(data_lines)
            file_buffer = io.StringIO(s_data)
            df = pd.read_csv(file_buffer, sep=sep, header=None)
            df.columns = header4
        else:
            xls = pd.ExcelFile(uploaded_file)
            header4 = pd.read_excel(xls, header=None, nrows=4).iloc[3].astype(str).str.strip().tolist()
            header4 = make_unique(header4)
            header5 = pd.read_excel(xls, header=None, nrows=5).iloc[4].astype(str).str.strip().tolist()
            df = pd.read_excel(xls, header=None, skiprows=5)
            df.columns = header4

        # -- SEGMENTS DETECTION --
        mapping_vals = set()
        for lignes in mapping.values():
            mapping_vals.update([x.strip().upper() for x in lignes])
        detected_intitule_col = None
        for col in df.columns:
            sample = df[col].astype(str).str.strip().str.upper()
            if sample.isin(mapping_vals).any():
                detected_intitule_col = col
                break
        if detected_intitule_col is None:
            st.error("Colonne des intitulés non détectée. Vérifie la structure du fichier !")
            st.stop()

        # -- MOIS COLUMNS DETECTION --
        mois_cols = []
        mois_headers = []
        for idx, (h4, h5) in enumerate(zip(header4, header5)):
            if h4.startswith("Solde au") and h5 == "Débit":
                mois_cols.append(str(df.columns[idx]).strip().replace('\n','').replace('\r',''))
                mois_headers.append(h4)
        mois_names = [extract_month_name(h) for h in mois_headers]
        mois_names = [str(m).strip().replace('\n','').replace('\r','') for m in mois_names]
        mois_cols = [str(m).strip().replace('\n','').replace('\r','') for m in mois_cols]

        # -- FORMAT MONTANTS ULTIME --
        for col in mois_cols:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[\s\u202f\t\r\n]", "", regex=True)
                .str.replace(",", ".", regex=False)
                .replace({"None": np.nan, "nan": np.nan, "": np.nan})
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # -- AFFECTATION DES SEGMENTS --
        df["SEGMENT"] = df[detected_intitule_col].apply(get_segment)
        df["SEGMENT"] = pd.Categorical(df["SEGMENT"], categories=list(mapping.keys()), ordered=True)
        df = df[df["SEGMENT"].notnull()]

        # -- TABLEAU GLOBAL ANNUEL AVEC HIGHLIGHT --
        st.markdown("### 📊 Tableau annuel (surlignage automatique des hausses/baisse par mois)")
        agg_annee = df.groupby("SEGMENT", observed=False)[mois_cols].sum(numeric_only=True)
        agg_annee = agg_annee.reindex(list(mapping.keys())).fillna(0)
        agg_annee.columns = [str(c).strip().replace('\n','').replace('\r','') for c in agg_annee.columns]
        agg_annee["Total Année"] = agg_annee[mois_cols].sum(axis=1)
        display_agg_annee = agg_annee.copy()
        display_agg_annee.columns = [*mois_names, "Total Année"]

        styled_annual = display_agg_annee.style.apply(highlight_annual, axis=1).format(mad_format)
        st.dataframe(styled_annual, use_container_width=True)
        st.caption("⬆️ Rouge : hausse >10% | ⬇️ Vert : baisse >10% par rapport au mois précédent (ligne par ligne).")

        # -- TABLEAU PAR MOIS (AVEC HIGHLIGHT COLONNE EN COURS VS PRECEDENTE) --
        st.markdown("### 📅 Tableaux par mois (scroll horizontal & alertes évolutions)")
        tabs = st.tabs(mois_names)
        for i, col in enumerate(mois_cols):
            with tabs[i]:
                agg_mois = df.groupby("SEGMENT", observed=False)[[col]].sum(numeric_only=True)
                agg_mois = agg_mois.reindex(list(mapping.keys())).fillna(0)
                agg_mois.columns = [mois_names[i]]
                # Highlight par rapport au mois précédent
                if i > 0:
                    prev_col = mois_cols[i-1]
                    prev_data = df.groupby("SEGMENT", observed=False)[[prev_col]].sum(numeric_only=True).reindex(list(mapping.keys())).fillna(0)
                    styled = agg_mois.copy()
                    # Construction du df stylé par ligne
                    def row_highlight(s):
                        styles = []
                        for val, prev in zip(s, prev_data[prev_col].values):
                            styles.append(highlight_monthly(val, prev))
                        return styles
                    st.dataframe(
                        agg_mois.style.apply(row_highlight, axis=0).format(mad_format),
                        use_container_width=True
                    )
                else:
                    st.dataframe(agg_mois.applymap(mad_format), use_container_width=True)

        st.caption("⬆️ Rouge : hausse >10% | ⬇️ Vert : baisse >10% par rapport au mois précédent.")

        # ... (la suite de ton code : pop-up détail segment, graphiques, etc. peuvent rester inchangés)

    except Exception as e:
        st.error(f"{e}")
