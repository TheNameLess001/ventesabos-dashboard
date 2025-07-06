import streamlit as st
import pandas as pd

st.set_page_config(page_title="Introduction", page_icon="🏠")

LOGO_PATH = "logo_fitnesspark.png"
USERS_DB = "users_db.csv"

st.markdown("""
    <style>
    .center-logo-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 16px;
        margin-bottom: 8px;
        width: 100%;
    }
    .scroll-instructions {
        max-height: 520px;
        overflow-y: auto;
        padding: 16px 22px;
        background: #fffbe6;
        border-radius: 12px;
        box-shadow: 0 2px 16px #ffdc8022;
        margin-bottom: 24px;
    }
    /* Modal (popup) CSS */
    .modal-bg {
        position: fixed;
        top:0; left:0; width:100vw; height:100vh;
        background: rgba(35,35,35,0.40);
        z-index: 9999;
        display: flex; justify-content: center; align-items: center;
    }
    .modal-content {
        background: #fff;
        padding: 32px 24px 24px 24px;
        border-radius: 15px;
        min-width: 320px;
        box-shadow: 0 6px 42px #4443;
        max-width:90vw;
    }
    .modal-content h2 {margin-top:0;color:#1d2b49;}
    .modal-close {
        color:#fff; background:#ffbf00;
        border:none; border-radius:8px;
        padding:6px 16px; margin-top:16px;
        font-weight:bold; font-size:1em;
        cursor:pointer;
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

def show_logo_centered():
    st.markdown("<div class='center-logo-wrap'>", unsafe_allow_html=True)
    try:
        st.image(LOGO_PATH, width=110)
    except Exception:
        st.markdown("<h2 style='text-align:center;'>Fitness Park</h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def pwd_change_modal(user, db_path=USERS_DB):
    with st.form("change_pwd_form_popup", clear_on_submit=True):
        st.markdown("<h2>🔒 Changer mon mot de passe</h2>", unsafe_allow_html=True)
        old_pwd = st.text_input("Ancien mot de passe", type="password")
        new_pwd1 = st.text_input("Nouveau mot de passe", type="password")
        new_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password")
        submit = st.form_submit_button("Valider")
    close_modal = st.button("Fermer", key="close_modal", help="Fermer la fenêtre")
    msg = ""
    if submit:
        df = pd.read_csv(db_path, dtype=str)
        user_row = (df["user"] == user)
        if not user_row.any():
            msg = "Utilisateur introuvable."
        elif (df.loc[user_row, "password"].iloc[0] != old_pwd):
            msg = "Ancien mot de passe incorrect."
        elif not new_pwd1 or not new_pwd2:
            msg = "Le nouveau mot de passe ne peut pas être vide."
        elif new_pwd1 != new_pwd2:
            msg = "Les nouveaux mots de passe ne correspondent pas."
        elif new_pwd1 == old_pwd:
            msg = "Le nouveau mot de passe doit être différent de l'ancien."
        else:
            df.loc[user_row, "password"] = new_pwd1
            df.to_csv(db_path, index=False)
            st.success("Votre mot de passe a été changé avec succès !")
            st.session_state["logged"] = False
            st.session_state.pop("user", None)
            st.session_state["show_pwd_popup"] = False
            st.info("Veuillez vous reconnecter avec votre nouveau mot de passe.")
            st.stop()
        if msg:
            st.error(msg)
    if close_modal:
        st.session_state["show_pwd_popup"] = False

def show_login():
    col1, col2, col3 = st.columns([2,4,2])
    with col2:
        show_logo_centered()
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
            st.rerun()
        else:
            st.error("Identifiants incorrects.")

if "logged" not in st.session_state:
    st.session_state["logged"] = False
if "show_pwd_popup" not in st.session_state:
    st.session_state["show_pwd_popup"] = False

if not st.session_state["logged"]:
    show_login()
    st.stop()
else:
    col1, col2, col3 = st.columns([2, 5, 2])
    with col2:
        show_logo_centered()
    st.markdown(f"""
    <div style='text-align:center;font-size:2.1em;font-weight:bold;color:#1d2b49;margin-top:5px;'>
        Bienvenue, {st.session_state.get("user", "Utilisateur")}
    </div>
    """, unsafe_allow_html=True)

    # --- BOUTONS EN HAUT ---
    nav_col1, nav_col2, nav_col3 = st.columns([1,1,2])
    with nav_col1:
        if st.button("🔒 Changer mon mot de passe"):
            st.session_state["show_pwd_popup"] = True
    with nav_col2:
        if st.button("Déconnexion"):
            st.session_state["logged"] = False
            st.session_state.pop("user", None)
            st.session_state["show_pwd_popup"] = False
            st.rerun()
    with nav_col3:
        st.markdown(
            "<a href='mailto:Manager.racine@fitnesspark.ma' style='text-decoration:none;font-weight:bold;color:#555;'>📧 Support technique</a>",
            unsafe_allow_html=True
        )

    st.markdown("""
    <div class="scroll-instructions">
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

    # --- POPUP MODAL POUR CHANGEMENT MOT DE PASSE ---
    if st.session_state.get("show_pwd_popup", False):
        st.markdown(
            "<div class='modal-bg'><div class='modal-content'>", unsafe_allow_html=True)
        pwd_change_modal(st.session_state.get("user", ""))
        st.markdown("</div></div>", unsafe_allow_html=True)

    # Signature
    st.markdown("""
    <div style='text-align:center;margin-top:60px;'>
        <hr style='border:0.5px solid #eee'>
        <span style="color:#888;font-family:monospace;font-size:1em;">
            <b>SBN PY</b> • BI Suite Fitness Park
        </span>
    </div>
    """, unsafe_allow_html=True)
