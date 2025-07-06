import streamlit as st

st.set_page_config(page_title="Contact - SBN PY", page_icon="💼")

# Gold branding
st.markdown("""
    <style>
    .contact-card {
        background: linear-gradient(110deg, #FFD700 0%, #fff 100%);
        border-radius: 16px;
        padding: 40px 30px 32px 30px;
        box-shadow: 0 2px 16px #ccc4;
        max-width: 470px;
        margin: 40px auto 0 auto;
        color: #232323;
        text-align: center;
    }
    .contact-card h1 {font-size:2.3em;margin-bottom:10px;color:#1d2b49;}
    .contact-card h2 {font-size:1.5em;margin-top:5px;margin-bottom:16px;color:#222;}
    .contact-label {color: #555;font-weight:bold;}
    .contact-value {font-family:monospace;font-size:1.18em;}
    a.contact-link {color:#0059b2;font-weight:600;text-decoration:underline;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="contact-card">
    <h1>💼 Contact</h1>
    <h2>BOUNOIR SAIF EDDINE</h2>
    <div>
        <span class="contact-label">Email : </span>
        <a class="contact-value" href="mailto:bounoirsaifeddine1@gmail.com">bounoirsaifeddine1@gmail.com</a>
    </div>
    <div style="margin-top:12px;">
        <span class="contact-label">Téléphone : </span>
        <span class="contact-value">+212 638831099</span>
    </div>
    <div style="margin-top:12px;">
        <span class="contact-label">LinkedIn : </span>
        <a class="contact-link" href="https://www.linkedin.com/in/bounoir-saif-eddine/" target="_blank">
            BOUNOIR SAIF EDDINE
        </a>
    </div>
    <div style="margin-top:22px;font-size:1.05em;">
        <span class="contact-label">Projet : </span>
        <span class="contact-value">SBN PY • BI Suite Fitness Park</span>
    </div>
    <div style="margin-top:22px;font-size:1.13em;color:#444;">Merci pour votre confiance !</div>
</div>
""", unsafe_allow_html=True)
