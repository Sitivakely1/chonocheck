import streamlit as st
import json
import os
import csv
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
import pytz

# Définir le fuseau horaire de l'Europe/Paris
tz_paris = pytz.timezone('Europe/Paris')

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="Commandant en Chef")

# --- USERS ---
USERS = {
    "Navalona": "1234",
    "Sandy": "1234",
    "Kanto": "1234",
    "Volana": "1234",
    "Steve": "1234",
    "admin": "adminpass"
}

DATA_FILE = 'shifts.json'

# --- COOKIES ---
cookies = EncryptedCookieManager(
    prefix="chrono_app/",
    password="une_chaine_secrete"
)

if not cookies.ready():
    st.stop()

# --- STYLE ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Wallpoet&display=swap');

    body, html, [class*="css"] {
        font-family: 'Wallpoet', monospace;
        background-color: #2c3e50; /* Couleur de secours si l'image ne charge pas */
    }

    .main {
        /* background-color: #2c3e50 !important; */
        color: #ecf0f1 !important;
        background-image: url('https://cherry.img.pmdstatic.net/fit/https.3A.2F.2Fimg.2Egamesider.2Ecom.2Fsto.2Fgallery.2Fcb80b3df22bc1703_6107f473e2fe3f137a6d4c1b.2Ejpg/640x360/quality/80/call-of-duty-world-at-war.jpg') !important;
        background-size: cover !important;
        background-repeat: no-repeat !important;
    }

    .stApp {
        /* background-color: #2c3e50; */
        color: #ecf0f1;
        background-image: url('https://cherry.img.pmdstatic.net/fit/https.3A.2F.2Fimg.2Egamesider.2Ecom.2Fsto.2Fgallery.2Fcb80b3df22bc1703_6107f473e2fe3f137a6d4c1b.2Ejpg/640x360/quality/80/call-of-duty-world-at-war.jpg');
        background-size: cover;
        background-repeat: no-repeat;
    }

    .st-emotion-cache-18ni7ap {
        font-family: 'Wallpoet', monospace;
    }

    .st-emotion-cache-1kyxpyv {
        background-color: #34495e;
        border: 2px solid #e74c3c;
        border-radius: 8px;
        color: #ecf0f1;
    }

    .stButton>button {
        background-color: #e74c3c;
        color: #000000;
        border: 2px solid #ecf0f1;
        border-radius: 8px;
        padding: 10px 24px;
        font-family: 'Wallpoet', monospace;
        font-size: 14px;
        box-shadow: 3px 3px 0px #c0392b;
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        background-color: #c0392b;
        box-shadow: 1px 1px 0px #922b21;
    }

    .stButton>button:active {
        background-color: #c0392b;
        box-shadow: none;
        transform: translateY(2px) translateX(2px);
    }

    .st-emotion-cache-v01q51 p {
        color: #ecf0f1 !important;
        font-weight: bold;
    }

    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
        color: #ecf0f1;
        font-family: 'Wallpoet', monospace;
    }
    .stTabs [data-baseweb="tab-list"] button.st-emotion-cache-1q58v9d {
        background-color: #34495e;
        border: 2px solid #ecf0f1;
    }
    .stTabs [data-baseweb="tab-list"] button.st-emotion-cache-1q58v9d:focus:not(:active) {
        box-shadow: 0 0 0 2px #e74c3c;
    }
    .st-emotion-cache-1b0ud4a p {
        font-size: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Fonctions d'aide ---
def format_time_h_m(seconds):
    if seconds is None: return "0h 0m"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

def format_time_m_s(seconds):
    if seconds is None: return "0m 0s"
    minutes = int(seconds // 60)
    seconds_remaining = int(seconds % 60)
    return f"{minutes}m {seconds_remaining}s"

def now_iso():
    return datetime.now(tz=tz_paris).isoformat(timespec='seconds')

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {'active_shifts': {}, 'completed_shifts': []}
    return {'active_shifts': {}, 'completed_shifts': []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def compute_pause_seconds(shift):
    total = 0
    for p in shift['pauses']:
        start = datetime.fromisoformat(p['start']).astimezone(tz_paris)
        end = datetime.fromisoformat(p['end']).astimezone(tz_paris) if p['end'] else datetime.now(tz=tz_paris)
        total += (end - start).total_seconds()
    return total

def compute_worked_seconds(shift):
    start = datetime.fromisoformat(shift['start']).astimezone(tz_paris)
    end = datetime.fromisoformat(shift['end']).astimezone(tz_paris)
    total = (end - start).total_seconds() - compute_pause_seconds(shift)
    return max(0, total)

def start_shift(data, name):
    if name not in data['active_shifts']:
        data['active_shifts'][name] = {'start': now_iso(), 'pauses': [], 'end': None}
        save_data(data)
        st.rerun()

def pause_shift(data, name):
    sh = data['active_shifts'].get(name)
    if sh and (not sh['pauses'] or sh['pauses'][-1].get('end') is not None):
        sh['pauses'].append({'start': now_iso(), 'end': None})
        save_data(data)
        st.rerun()

def resume_shift(data, name):
    sh = data['active_shifts'].get(name)
    if sh and sh['pauses'] and sh['pauses'][-1].get('end') is None:
        sh['pauses'][-1]['end'] = now_iso()
        save_data(data)
        st.rerun()

def end_shift(data, name):
    sh = data['active_shifts'].get(name)
    if sh:
        if sh['pauses'] and sh['pauses'][-1].get('end') is None:
            sh['pauses'][-1]['end'] = now_iso()
        sh['end'] = now_iso()
        sh['worked_seconds'] = compute_worked_seconds(sh)
        sh['pause_seconds'] = compute_pause_seconds(sh)
        sh['employee'] = name
        data['completed_shifts'].append(sh)
        del data['active_shifts'][name]
        save_data(data)
        st.toast(f"Mission terminée pour {name}. Rapport envoyé !", icon="✅")
        st.rerun()

def export_csv(data, all_users=False, current_user=''):
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nom', 'Début', 'Fin', 'Temps Travail', 'Temps Pause'])
    shifts = sorted(data['completed_shifts'], key=lambda x: x['start'], reverse=True)
    if not all_users:
        shifts = [sh for sh in shifts if sh.get('employee') == current_user]
    for sh in shifts:
        writer.writerow([
            sh.get('employee', 'inconnu'),
            sh.get('start', ''),
            sh.get('end', ''),
            format_time_h_m(sh.get('worked_seconds', 0)),
            format_time_m_s(sh.get('pause_seconds', 0))
        ])
    return output.getvalue()

# --- GESTION DE SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# Vérifier cookie
if cookies.get("user") and cookies.get("user") in USERS:
    st.session_state.logged_in = True
    st.session_state.current_user = cookies.get("user")

# Page login
if not st.session_state.logged_in:
    st.title("Système de Commandement")
    st.markdown("## Accès Opérations Militaires")
    col1, col2, col
