import streamlit as st
from streamlit_lottie import st_lottie
import requests
import random
import time

st.set_page_config(page_title="Introduction", page_icon="🏠")

# --- GOLD STYLE ---
st.markdown("""
    <style>
    .small-logo { animation: fadeIn 2.1s; display: block; margin-left:auto; margin-right:auto; margin-bottom: 10px;}
    @keyframes fadeIn {
        0% {opacity: 0;}
        100% {opacity: 1;}
    }
    .motivation {color: #FFD700;font-size:1.1em; font-style:italic;}
    .quick-stat {background:#fffbe6;border-radius:8px;padding:12px 18px;margin:8px 0;color:#222;box-shadow:0 2px 6px #ffc60022;}
    .blinking {animation: blink 1.2s linear infinite;}
    @keyframes blink {
      50% {opacity: 0.7;}
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGO BLOCK ---
def logo_block():
    try:
        st.image("logo_fitnesspark.png", width=110)
    except Exception:
        st.markdown("<h2 style='text-align:center;'>Fitness Park</h2>", unsafe_allow_html=True)

# --- LOTTIE ---
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

lottie_url = "https://assets10.lottiefiles.com/packages/lf20_kxsd2ytq.json"  # Change to your favorite

# --- FAKE DASHBOARD STATS ROTATOR (for demo, link to real stats if you want) ---
fake_stats = [
    {"Abonnements vendus": 21, "Taux Recouvrement": "85.2%", "Inactifs": 12, "Top Commercial": "K. LENOIRE"},
    {"Abonnements vendus": 8, "Taux Recouvrement": "92.5%", "Inactifs": 7, "Top Commercial": "M. OULAD"},
    {"Abonnements vendus": 16, "Taux Recouvrement": "78.9%", "Inactifs": 18, "Top Commercial": "K. LENOIRE"},
    {"Abonnements vendus": 34, "Taux Recouvrement": "88.0%", "Inactifs": 2, "Top Commercial": "B. OUNOUAR"}
]
stat_txts = [
    lambda s: f"📈 <b>{s['Abonnements vendus']} abonnements</b> vendus hier | Recouvrement <b>{s['Taux Recouvrement']}</b>",
    lambda s: f"🧑‍💼 Top commercial : <b>{s['Top Commercial']}</b> | Inactifs détectés : <b>{s['Inactifs']}</b>",
]

# --- MOTIVATIONAL QUOTES ---
quotes = [
    "« Success is the sum of small efforts, repeated day in and day out. » – Robert Collier",
    "« La victoire aime l’effort. »",
    "« Don’t watch the clock; do what it does. Keep going. » – Sam Levenson",
    "« Transformez vos données en actions. »",
    "« You are the dashboard designer of your own destiny. »",
    "« Every stat tells a story. Make yours legendary. »"
]

# === LAYOUT ===
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
logo_block()

lottie_json = load_lottieurl(lottie_url)
if lottie_json:
    st_lottie(lottie_json, height=120, key="fitness-lottie")
else:
    st.info("⏳ Animation non disponible. (Problème réseau ou lien Lottie)")

st.markdown("""
    <div style='text-align:center;font-size:2.15em;font-weight:bold;color:#1d2b49;margin-top:5px;margin-bottom:0;'>Bienvenue sur la BI Suite Fitness Park</div>
    <div style="text-align:center;font-size:1.17em;margin:10px auto 18px auto;color:#222;">
        Analyse. Décision. Performance.<br>🚀
    </div>
""", unsafe_allow_html=True)

# --- ROTATING INFO CAROUSEL (simulate)
with st.container():
    stat_idx = int((time.time()//2) % len(fake_stats))
    stat_row = fake_stats[stat_idx]
    stat_txt = stat_txts[stat_idx % len(stat_txts)](stat_row)
    st.markdown(f'<div class="quick-stat blinking" style="text-align:center;">{stat_txt}</div>', unsafe_allow_html=True)

# --- RANDOM MOTIVATIONAL QUOTE ---
quote = random.choice(quotes)
st.markdown(f'<div class="motivation" style="text-align:center;margin:12px 0 15px 0;">{quote}</div>', unsafe_allow_html=True)

# --- Quick nav buttons (like a menu) ---
col_a, col_b, col_c, col_d = st.columns([1,1,1,1])
with col_a:
    if st.button("🏆 Abonnements"):
        st.switch_page("pages/1_Abonnements.py")
with col_b:
    if st.button("💶 Recouvrement"):
        st.switch_page("pages/2_Recouvrement.py")
with col_c:
    if st.button("🛒 VAD"):
        st.switch_page("pages/4_VAD.py")
with col_d:
    if st.button("📑 Facture"):
        st.switch_page("pages/3_tbo.py")

st.markdown("""
<div style='text-align:center;margin-top:36px;'>
    <hr style='border:0.5px solid #eee'>
    <span style="color:#888;font-family:monospace;font-size:1em;">
        <b>SBN PY</b> • BI Suite Fitness Park
    </span>
</div>
""", unsafe_allow_html=True)
