import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Introduction", page_icon="🏠")

LOGO_PATH = "logo_fitnesspark.png"
USERS_DB = "users_db.csv"

# --- STYLE GOLD ---
st.markdown("""
    <style>
    .small-logo { animation: fadeIn 2.1s; display: block; margin-left:auto; margin-right:auto; margin-bottom: 10px;}
    @keyframes fadeIn {
        0% {opacity: 0;}
        100% {opacity: 1;}
    }
    </style>
""", unsafe_allow_html=True)

def check_login(username, pwd):
    try:
        users = pd.read_csv(USERS_DB, dtype=str)
        users["user"] = users["user"].str.strip()
        users["password"] = users["password"].astype(str).str.strip()
        return ((users["user"] == username) & (users["password"] == pwd)).any()
    except Exception as e:
        st.error(f"Erreur chargement BDD utilisateurs : {e}")
        return False

def change_password(user, db_path=USERS_DB):
    st.subheader("🔒 Changer mon mot de passe")
    with st.form("change_pwd_form", clear_on_submit=True):
        old_pwd = st.text_input("Ancien mot de passe", type="password")
        new_pwd1 = st.text_input("Nouveau mot de passe", type="password")
        new_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password")
        submit = st.form_submit_button("Valider")
    if submit:
        df = pd.read_csv(db_path, dtype=str)
        user_row = (df["user"] == user)
        if not user_row.any():
            st.error("Utilisateur introuvable.")
            return
        old_ok = (df.loc[user_row, "password"].iloc[0] == old_pwd)
        if not old_ok:
            st.error("Ancien mot de passe incorrect.")
        elif not new_pwd1 or not new_pwd2:
            st.error("Le nouveau mot de passe ne peut pas être vide.")
        elif new_pwd1 != new_pwd2:
            st.error("Les nouveaux mots de passe ne correspondent pas.")
        elif new_pwd1 == old_pwd:
            st.warning("Le nouveau mot de passe doit être différent de l'ancien.")
        else:
            df.loc[user_row, "password"] = new_pwd1
            df.to_csv(db_path, index=False)
            st.success("Votre mot de passe a été changé avec succès !")
            st.session_state["logged"] = False
            st.session_state.pop("user", None)
            st.info("Veuillez vous reconnecter avec votre nouveau mot de passe.")
            st.rerun()

def show_login():
    col1, col2, col3 = st.columns([2,4,2])
    with col2:
        try:
            st.image(LOGO_PATH, width=110)
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
            st.experimental_rerun()  # Rerun direct, pas de spinner Streamlit!
        else:
            st.error("Identifiants incorrects.")

if "logged" not in st.session_state:
    st.session_state["logged"] = False

if not st.session_state["logged"]:
    show_login()
    st.stop()
else:
    # Page d'accueil "welcome" une fois connecté
    col1, col2, col3 = st.columns([2, 5, 2])
    with col2:
        try:
            st.image(LOGO_PATH, width=110)
        except Exception:
            st.markdown("<h2 style='text-align:center;'>Fitness Park</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align:center;font-size:2.1em;font-weight:bold;color:#1d2b49;margin-top:5px;'>
        Bienvenue, {st.session_state.get("user", "Utilisateur")}
    </div>
    <div style='margin:10px auto 30px auto;text-align:center;max-width:600px;'>
    <h4>📄 <b>Description des pages :</b></h4>
    <ul style="text-align:left;">
        <li><b>Abonnements</b> : Analyse ventes abos, parts, comparatifs clubs & commerciaux, podium vendeurs.</li>
        <li><b>Recouvrement</b> : Analyse impayés/réglés, taux de recouvrement club & commercial, graphes de suivi, détection double-rejet.</li>
        <li><b>VAD</b> : Analyse des ventes à distance (VAD), Access+, Waterstation, analyse club/commercial, filtrage multi-critères.</li>
        <li><b>Facture</b> : Analyse TBO/factures globales, répartition CA, barplots par familles produits.</li>
        <li><b>Exporter</b> : Télécharge tous les tableaux analysés de chaque vue en Excel (.xlsx).</li>
        <li><b>Contact</b> : Vos contacts SBN PY.</li>
    </ul>
    <h4>🖥️ <b>Utilisation :</b></h4>
    <ul style="text-align:left;">
        <li>Uploade un fichier Excel ou CSV sur chaque page pour voir l'analyse correspondante.</li>
        <li>Utilise les filtres et graphiques pour explorer la data club, commercial, type d'abonnement, etc.</li>
        <li>Tu peux toujours changer de page via le menu à gauche.</li>
    </ul>
    <p style="margin-top:18px;font-size:1.1em;"><b>Besoin d'aide ?</b> <a href='mailto:Manager.racine@fitnesspark.ma'>Manager.racine@fitnesspark.ma</a></p>
    </div>
    """, unsafe_allow_html=True)

    # --- Changement de mot de passe ---
    change_password(st.session_state.get("user", ""))

    # Signature
    st.markdown("""
    <div style='text-align:center;margin-top:60px;'>
        <hr style='border:0.5px solid #eee'>
        <span style="color:#888;font-family:monospace;font-size:1em;">
            <b>SBN PY</b> • BI Suite Fitness Park
        </span>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.get("logged", False):
    if st.sidebar.button("Déconnexion"):
        st.session_state["logged"] = False
        st.session_state.pop("user", None)
        st.rerun()
