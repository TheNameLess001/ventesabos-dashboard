import streamlit as st

LOGO_PATH = "logo_fitnesspark.png"

def show_login():
    col1, col2, col3 = st.columns([2,4,2])
    with col2:
        try:
            st.image(LOGO_PATH, width=200)
        except:
            st.markdown("<h2 style='text-align:center;'>Fitness Park</h2>", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;font-size:2em;font-weight:bold;color:#262730;">Bienvenue sur la BI Suite Fitness Park</div>', unsafe_allow_html=True)
    with st.form("login_form"):
        user = st.text_input("Utilisateur", placeholder="Admin")
        pwd = st.text_input("Mot de passe", type="password")
        ok = st.form_submit_button("Connexion")
    if st.button("Mot de passe oublié ?"):
        st.info("Contactez : [Manager.racine@fitnesspark.ma](mailto:Manager.racine@fitnesspark.ma)")
    if ok:
        if user == "Admin" and pwd == "Fpk@2025":
            st.session_state["logged"] = True
            st.success("Connexion réussie ! Sélectionnez une page dans le menu à gauche.")
            st.stop()
        else:
            st.error("Identifiants incorrects.")

if "logged" not in st.session_state:
    st.session_state["logged"] = False

if not st.session_state["logged"]:
    show_login()
    st.stop()
else:
    st.markdown("<h2 style='text-align:center;'>Sélectionnez une page dans le menu à gauche</h2>", unsafe_allow_html=True)
    st.success("Accès accordé. Utilisez le menu de gauche.")

# Option de déconnexion partout
if st.session_state["logged"]:
    if st.sidebar.button("Déconnexion"):
        st.session_state["logged"] = False
        st.experimental_rerun()
