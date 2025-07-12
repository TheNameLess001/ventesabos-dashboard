import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import re
import calendar
from collections import Counter
import numpy as np

# --- Mapping segments/charges ---
mapping = {
    # ... (le même mapping que précédemment, inchangé)
    "Nettoyage": [...],
    "Des employés": [...],
    "Leasing": [...],
    "Réparations et entretien": [...],
    "Publicité et relations publiques": [...],
    "Services professionnels": [...],
    "Achats et fournitures": [...],
    "Fournitures": [...],
    "Téléphones/ Communication": [...],
    "Entraînement": [...],
    "Autres": [...]
}
SEGMENTS_ORDER = list(mapping.keys())
mapping = {str(k).strip(): [str(x).strip() for x in v] for k, v in mapping.items()}

# --- Fonctions utilitaires ---
def make_unique(seq):
    counter = Counter()
    res = []
    for s in seq:
        if s in counter:
            counter[s] += 1
            res.append(f"{s}_{counter[s]}")
        else:
            counter[s] = 0
            res.append(s)
    return res

def get_segment(nom):
    for seg, lignes in mapping.items():
        if isinstance(nom, str) and nom.strip().upper() in [x.strip().upper() for x in lignes]:
            return seg
    if isinstance(nom, str) and nom.strip().upper() == "INTERETS DES EMPRUNTS ET DETTES":
        return "INTERETS / FINANCE"
    return None

def mad_format(x):
    try:
        x = float(x)
        if pd.isna(x):
            return ""
        return "{:,.0f} MAD".replace(",", " ").format(x)
    except:
        return ""

def extract_month_name(header):
    m = re.search(r'Solde au (\d{2})[/-](\d{2})[/-](\d{4})', header)
    if m:
        month = int(m.group(2))
        year = m.group(3)
        return f"{calendar.month_name[month]} {year}"
    return header

def highlight_annual(row):
    styles = ['']
    values = row[1:-1].values
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
                    styles.append('background-color: #FFB3B3')
                elif delta < -0.10:
                    styles.append('background-color: #B3FFB3')
                else:
                    styles.append('')
    styles.append('')
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

def heatmap_style(val, vmin, vmax):
    # Color scale from green (low) to red (high)
    if pd.isna(val):
        return ''
    norm = (val - vmin) / (vmax - vmin) if vmax != vmin else 0
    r = int(255 * norm)
    g = int(255 * (1-norm))
    b = 200
    return f'background-color: rgb({r},{g},{b}, 0.5)'

st.set_page_config(layout="wide")
st.title("💼 Analyse Visuelle et Interactive des Charges & Segments")

st.info(
    "🔴 **Rouge** : hausse >10% | 🟢 **Vert** : baisse >10% (mois précédent).<br>"
    "📊 Comparez segments, explorez graphiques dynamiques et exportez le tout !",
    icon="💡"
)

uploaded_file = st.file_uploader("🗂️ Importer le fichier Balance", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # --- Import CSV/XLSX (inchangé) ---
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

        # --- Segment Detection ---
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

        # --- Mois Columns ---
        mois_cols = []
        mois_headers = []
        for idx, (h4, h5) in enumerate(zip(header4, header5)):
            if h4.startswith("Solde au") and h5 == "Débit":
                mois_cols.append(str(df.columns[idx]).strip().replace('\n','').replace('\r',''))
                mois_headers.append(h4)
        mois_names = [extract_month_name(h) for h in mois_headers]
        mois_names = [str(m).strip().replace('\n','').replace('\r','') for m in mois_names]
        mois_cols = [str(m).strip().replace('\n','').replace('\r','') for m in mois_cols]

        # --- Clean montants ---
        for col in mois_cols:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[\s\u202f\t\r\n]", "", regex=True)
                .str.replace(",", ".", regex=False)
                .replace({"None": np.nan, "nan": np.nan, "": np.nan})
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # --- Affectation des segments ---
        df["SEGMENT"] = df[detected_intitule_col].apply(get_segment)
        df["SEGMENT"] = pd.Categorical(df["SEGMENT"], categories=SEGMENTS_ORDER, ordered=True)
        df = df[df["SEGMENT"].notnull()]

        # --- TABLEAU GLOBAL ANNUEL AVEC HIGHLIGHT + HEATMAP ---
        st.markdown("### 📊 Tableau annuel : toutes les évolutions en un coup d'œil")
        agg_annee = df.groupby("SEGMENT", observed=False)[mois_cols].sum(numeric_only=True)
        agg_annee = agg_annee.reindex(SEGMENTS_ORDER).fillna(0)
        agg_annee.columns = [str(c).strip().replace('\n','').replace('\r','') for c in agg_annee.columns]
        agg_annee["Total Année"] = agg_annee[mois_cols].sum(axis=1)
        display_agg_annee = agg_annee.copy()
        display_agg_annee.columns = [*mois_names, "Total Année"]
        # --- Highlight alertes ---
        styled_annual = display_agg_annee.style.apply(highlight_annual, axis=1).format(mad_format)
        # --- Heatmap continue (optionnel, décommenter pour tester) ---
        heatmap_df = agg_annee[mois_cols]
        vmin, vmax = np.nanmin(heatmap_df.values), np.nanmax(heatmap_df.values)
        styled_annual = styled_annual.background_gradient(
            cmap='YlOrRd', axis=None, subset=mois_names
        )
        st.dataframe(styled_annual, use_container_width=True)
        st.caption("⬆️ Rouge : hausse >10% | ⬇️ Vert : baisse >10% vs mois précédent. Fond jaune/rouge = heatmap progression.")

        # --- Export Excel avec couleurs ---
        import xlsxwriter
        from io import BytesIO
        if st.button("⬇️ Exporter ce tableau (annuel) en Excel stylé"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                export_df = agg_annee.copy()
                export_df.columns = mois_names + ["Total Année"]
                export_df.to_excel(writer, sheet_name='Charges', index=True)
                workbook  = writer.book
                worksheet = writer.sheets['Charges']
                # Format de base
                fmt_mad = workbook.add_format({'num_format': '#,##0" MAD"', "align": "right"})
                for col_num in range(1, 1+len(mois_names)):
                    worksheet.set_column(col_num, col_num, 18, fmt_mad)
                # Highlight colors
                for row_num in range(1, 1+len(export_df)):
                    for col_num in range(1, 1+len(mois_names)):
                        curr = export_df.iloc[row_num-1, col_num-1]
                        prev = export_df.iloc[row_num-1, col_num-2] if col_num > 1 else None
                        if col_num > 1 and pd.notna(prev) and prev != 0 and pd.notna(curr):
                            delta = (curr - prev) / abs(prev)
                            if delta > 0.10:
                                worksheet.write(row_num, col_num, curr, workbook.add_format({'bg_color': '#FFB3B3', 'num_format': '#,##0" MAD"'}))
                            elif delta < -0.10:
                                worksheet.write(row_num, col_num, curr, workbook.add_format({'bg_color': '#B3FFB3', 'num_format': '#,##0" MAD"'}))
                writer.save()
                b64 = base64.b64encode(output.getvalue()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="charges_annee.xlsx">Télécharger le tableau Excel avec couleurs</a>'
                st.markdown(href, unsafe_allow_html=True)

        # --- Détail segment interactif ---
        st.markdown("### 🔍 Détail interactif par segment")
        segment_selected = st.selectbox(
            "Clique sur un segment pour voir le détail des lignes sources :",
            [s for s in SEGMENTS_ORDER if s in df['SEGMENT'].unique()]
        )
        if segment_selected:
            with st.expander(f"Détails pour le segment : {segment_selected}", expanded=True):
                lignes_segment = df[df['SEGMENT'] == segment_selected]
                display_cols = [detected_intitule_col] + mois_cols
                display_lignes = lignes_segment[display_cols].copy()
                for col in mois_cols:
                    display_lignes[col] = display_lignes[col].apply(mad_format)
                st.dataframe(display_lignes, use_container_width=True)

        # --- TABLEAU PAR MOIS (AVEC HIGHLIGHT COLONNE EN COURS VS PRECEDENTE) ---
        st.markdown("### 📅 Tableaux par mois (scroll & alertes évolutions)")
        tabs = st.tabs(mois_names)
        for i, col in enumerate(mois_cols):
            with tabs[i]:
                agg_mois = df.groupby("SEGMENT", observed=False)[[col]].sum(numeric_only=True)
                agg_mois = agg_mois.reindex(SEGMENTS_ORDER).fillna(0)
                agg_mois.columns = [mois_names[i]]
                # Highlight par rapport au mois précédent
                if i > 0:
                    prev_col = mois_cols[i-1]
                    prev_data = df.groupby("SEGMENT", observed=False)[[prev_col]].sum(numeric_only=True).reindex(SEGMENTS_ORDER).fillna(0)
                    styled = agg_mois.copy()
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

        # --- MULTIGRAPH INTERACTIF ---
        st.markdown("### 🎛️ Compare plusieurs segments (période commune)")

        segments_available = [str(seg).replace("’", "").replace("'", "").replace('"', "").strip() for seg in SEGMENTS_ORDER]
        cols_mois_vraies = [c for c in agg_annee.columns if c != "Total Année"]

        # 1 seul slider période (commune à tous)
        if len(cols_mois_vraies) > 1:
            from_month, to_month = st.select_slider(
                "Sélectionne la période à afficher pour TOUS les graphiques (de ... à ...)",
                options=cols_mois_vraies,
                value=(cols_mois_vraies[0], cols_mois_vraies[-1]),
                key="slider_global"
            )
            idx_start = cols_mois_vraies.index(from_month)
            idx_end = cols_mois_vraies.index(to_month)
            if idx_start > idx_end:
                idx_start, idx_end = idx_end, idx_start
            selected_months = cols_mois_vraies[idx_start:idx_end+1]
        else:
            selected_months = cols_mois_vraies

        segments_selected = st.multiselect(
            "Sélectionne les segments à afficher",
            options=segments_available,
            default=[segments_available[0]],
            help="Ajoute un ou plusieurs segments. Chacun aura son propre graphique sur la période choisie !"
        )

        if segments_selected and selected_months:
            for seg in segments_selected:
                st.markdown(f"#### 📊 Segment : **{seg}** ({from_month} → {to_month})")
                bar_vals = agg_annee.loc[seg, selected_months].values
                fig, ax = plt.subplots(figsize=(min(8, 1 + 0.5*len(selected_months)), 4))
                ax.bar(selected_months, bar_vals, color="#4682b4")
                ax.set_ylabel("Montant (MAD)")
                ax.set_xlabel("Mois")
                ax.set_title(f"Variation de {seg}")
                for i, v in enumerate(bar_vals):
                    if not pd.isna(v) and v != 0:
                        ax.text(i, v, f"{int(v):,}", ha='center', va='bottom', fontsize=10)
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                st.pyplot(fig)
        else:
            st.info("Sélectionne au moins un segment ET une période pour voir les graphiques !")

        # --- TABLEAU CUMUL PÉRIODE SÉLECTIONNÉE (SLIDER) ---
        st.markdown("### 🧮 Cumul des segments sur la période sélectionnée")
        if len(cols_mois_vraies) > 1:
            from_month, to_month = st.select_slider(
                "Sélectionne la période à cumuler (de ... à ...)",
                options=cols_mois_vraies,
                value=(cols_mois_vraies[0], cols_mois_vraies[-1]),
                key="slider_cumul"
            )
            idx_start = cols_mois_vraies.index(from_month)
            idx_end = cols_mois_vraies.index(to_month)
            if idx_start > idx_end:
                idx_start, idx_end = idx_end, idx_start
            selected_months = cols_mois_vraies[idx_start:idx_end+1]
        else:
            selected_months = cols_mois_vraies

        cumul_df = agg_annee[selected_months].sum(axis=1)
        cumul_table = pd.DataFrame({"CUMUL SELECTIONNÉ": cumul_df})
        cumul_table = cumul_table.applymap(mad_format)
        st.dataframe(cumul_table, use_container_width=True)

    except Exception as e:
        st.error(f"{e}")
