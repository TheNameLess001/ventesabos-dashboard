import streamlit as st
import streamlit_authenticator as stauth

# Authentification Google (remplace par tes valeurs)
client_id = "652000245286-ao2ner99ebmk8u4kjr3rnh1mv8mluuhq.apps.googleusercontent.com"
client_secret = "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"

# Crée l'authenticator avec Google comme provider
authenticator = stauth.Authenticate(
    credentials={
        "oauth": {
            "client_id": client_id,
            "client_secret": client_secret,
            "provider": "google"
        }
    },
    cookie_name="streamlit_auth",
    key="some_random_key",
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login('Connexion Google', 'main')

if authentication_status:
    st.success(f"Bienvenue {name or username} !")
    st.write("🎉 Dashboard sécurisé par Google.")
elif authentication_status is False:
    st.error("Accès refusé.")
elif authentication_status is None:
    st.info("Connectez-vous avec Google ci-dessus.")
