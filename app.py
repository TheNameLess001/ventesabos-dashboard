import streamlit as st
import pandas as pd

LOGO_PATH = "logo_fitnesspark.png"
USERS_DB = "users_db.csv"  # Ton fichier des comptes utilisateurs

def check_login(username, pwd):
    try:
        users = pd.read_csv(USERS_DB, dtype=str)
        # Nettoyage sécurité
        users["user"] = users["user"].str.strip()
        users["password"] = users["password"].astype(str).str.strip()
        return ((users["user"] == username) & (users["password"] == pwd)).any()
    except Exception as e:
        st.error(f"Erreur chargement BDD utilisateurs : {e}")
        return False

def show_login():
    col1, col2, col3 = st.columns([2,4,2])
    with col2:
        try:
            st.image(LOGO_PATH, width=200)
        except Exception:
            st.markdown("<h2 style='text-align:center;'>Fitness Park</h2>", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;font-size:2em;font-weight:bold;color:#262730;">Bienvenue sur la BI Suite Fitness Park</div>', unsafe_allow_html=True)
    with st.form("login_form"):
        user = st.text_input("Utilisateur", placeholder="Admin")
        pwd = st.text_input("Mot de passe", type="password")
        ok = st.form_submit_button("Connexion")
    if st.button("Mot de passe oublié ?"):
        st.info("Contactez : [Manager.racine@fitnesspark.ma](mailto:Manager.racine@fitnesspark.ma)")
    if ok:
        if check_login(user, pwd):
            st.session_state["logged"] = True
            st.session_state["user"] = user
            st.success("Connexion réussie ! Accueil en cours...")
            st.rerun()
        else:
            st.error("Identifiants incorrects.")

if "logged" not in st.session_state:
    st.session_state["logged"] = False

if not st.session_state["logged"]:
    show_login()
    st.stop()
else:
    # Page d'accueil une fois connecté
    col1, col2, col3 = st.columns([2, 5, 2])
    with col2:
        try:
            st.image(LOGO_PATH, width=220)
        except Exception:
            st.markdown("<h2 style='text-align:center;'>Fitness Park</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;font-size:2em;font-weight:bold;color:#1d2b49;margin-top:10px;'>Bienvenue, {}</div>
    <div style='margin:15px auto 30px auto;text-align:center;max-width:600px;'>
    <h4>📄 <b>Description des pages :</b></h4>
    <ul style="text-align:left;">
        <li><b>Abonnements</b> : Analyse ventes abos, parts, comparatifs clubs & commerciaux, podium vendeurs.</li>
        <li><b>Recouvrement</b> : Analyse impayés/réglés, taux de recouvrement club & commercial, graphes de suivi, détection double-rejet.</li>
        <li><b>VAD</b> : Analyse des ventes à distance (VAD), Access+, Waterstation, analyse club/commercial, filtrage multi-critères.</li>
        <li><b>Facture</b> : Analyse TBO/factures globales, répartition CA, barplots par familles produits.</li>
        <li><b>Exporter</b> : Télécharge tous les tableaux analysés de chaque vue en Excel (.xlsx).</li>
    </ul>
    <h4>🖥️ <b>Comment utiliser :</b></h4>
    <ul style="text-align:left;">
        <li>Uploade un fichier Excel ou CSV sur chaque page pour voir l'analyse correspondante.</li>
        <li>Utilise les filtres et les graphiques pour explorer la data club, commercial, type d'abonnement, etc.</li>
        <li>Tu peux toujours changer de page via le menu à gauche.</li>
    </ul>
    <p style="margin-top:18px;font-size:1.1em;"><b>Pour toute question :</b> <a href='mailto:Manager.racine@fitnesspark.ma'>Manager.racine@fitnesspark.ma</a></p>
    </div>
    """.format(st.session_state.get("user", "Utilisateur")), unsafe_allow_html=True)

    # Signature
    st.markdown("""
    <div style='text-align:center;margin-top:80px;'>
        <hr style='border:0.5px solid #eee'>
        <span style="color:#888;font-family:monospace;font-size:1em;">
            <b>SBN PY</b> • BI Suite Fitness Park
        </span>
    </div>
    """, unsafe_allow_html=True)

# Bouton de déconnexion
if st.session_state.get("logged", False):
    if st.sidebar.button("Déconnexion"):
        st.session_state["logged"] = False
        st.session_state.pop("user", None)
        st.rerun()
