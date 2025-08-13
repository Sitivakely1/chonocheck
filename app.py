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
st.set_page_config(layout="wide", page_title="ChronoQuest")

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
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    
    body, html, [class*="css"] {
        font-family: 'Press Start 2P', monospace;
    }
    
    .st-emotion-cache-18ni7ap {
        font-family: 'Press Start 2P', monospace;
    }

    .main { 
        background-color: #1a1a2e !important; 
        color: #e0e0e0 !important;
        background-image: url('https://www.transparenttextures.com/patterns/epoxy-resin.png');
    }
    
    .stApp {
        background-color: #1a1a2e;
        color: #e0e0e0;
        background-image: url('https://www.transparenttextures.com/patterns/epoxy-resin.png');
    }
    
    .st-emotion-cache-1c7y2ex {
        background-color: #2e1a3b;
        border: 2px solid #6a0572;
        border-radius: 8px;
        color: #e0e0e0;
    }

    .stButton>button {
        background-color: #6a0572;
        color: #f7b731;
        border: 2px solid #f7b731;
        border-radius: 12px;
        padding: 10px 24px;
        font-family: 'Press Start 2P', monospace;
        font-size: 14px;
        box-shadow: 4px 4px 0px #f7b731;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background-color: #8b0a99;
        box-shadow: 2px 2px 0px #f7b731;
    }

    .stButton>button:active {
        background-color: #4b0351;
        box-shadow: none;
        transform: translateY(2px) translateX(2px);
    }
    
    .st-emotion-cache-1kyxpyv {
        background-color: #2e1a3b;
        color: #f7b731;
    }
    
    .st-emotion-cache-163w6y5 {
        color: #f7b731;
        font-family: 'Press Start 2P', monospace;
    }
    
    .st-emotion-cache-1c7y2ex {
        background-color: #2e1a3b !important;
        color: #f7b731 !important;
        border: 2px solid #f7b731 !important;
    }
    
    .st-emotion-cache-1kyxpyv {
        background-color: #2e1a3b !important;
    }

    .st-emotion-cache-v01q51 {
        background-color: #3b1f4b;
        border-radius: 8px;
    }

    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
        color: #e0e0e0;
        font-family: 'Press Start 2P', monospace;
    }
    .stTabs [data-baseweb="tab-list"] button.st-emotion-cache-1q58v9d {
        background-color: #4b0351;
        border: 2px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab-list"] button.st-emotion-cache-1q58v9d:focus:not(:active) {
        box-shadow: 0 0 0 2px #f7b731;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# --- Fonctions d'aide (pas de changement) ---
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
        st.toast(f"Shift terminé pour {name}. Bon repos !", icon="🎉")
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
    st.title("ChronoQuest")
    st.markdown("## L'aventure commence ici")
    st.image("https://i.imgur.com/2uR2Y7j.gif", use_column_width=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Nom de héros", key="login_user")
            password = st.text_input("Mot de passe secret", type="password", key="login_pass")
            submitted = st.form_submit_button("Entrer dans le donjon", use_container_width=True)
            if submitted:
                if USERS.get(username) == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    cookies["user"] = username
                    cookies.save()
                    st.toast(f"Bienvenue, {username}, aventurier !", icon="⚔️")
                    st.rerun()
                else:
                    st.error("Nom de héros ou mot de passe incorrect... l'aventure n'est pas pour vous.")
    st.stop()

# --- INTERFACE PRINCIPALE ---
user = st.session_state.current_user
data = load_data()

with st.sidebar:
    st.title("Journal de quête")
    st.info(f"Héros en action : **{user}**")
    if st.button("Quitter la quête", use_container_width=True, type="primary"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        cookies["user"] = ""
        cookies.save()
        st.toast("Vous avez quitté la partie.", icon="🚪")
        st.rerun()

st.header(f"Tableau de Bord")

if user == 'admin':
    tab1, tab2, tab3 = st.tabs(["📊 Donjon", "⚙️ Panneau de Maître", "📥 Trésor de guerre"])
    with tab1:
        st.subheader("Bilan des quêtes")
        if not data['completed_shifts']:
            st.info("Aucune quête terminée pour l'instant.")
        else:
            rows = []
            sorted_shifts = sorted(data['completed_shifts'], key=lambda x: x['start'], reverse=True)
            for sh in sorted_shifts:
                date = datetime.fromisoformat(sh['start']).strftime("%d/%m/%Y")
                rows.append({
                    "Nom du Héros": sh.get('employee', 'inconnu'),
                    "Date de quête": date,
                    "Début de quête": datetime.fromisoformat(sh['start']).strftime("%H:%M:%S"),
                    "Fin de quête": datetime.fromisoformat(sh['end']).strftime("%H:%M:%S"),
                    "Temps d'action": format_time_h_m(sh.get('worked_seconds', 0)),
                    "Temps de repos": format_time_m_s(sh.get('pause_seconds', 0))
                })
            st.dataframe(rows, use_container_width=True)
    with tab2:
        st.subheader("Zone de danger")
        if st.button("🔴 Effacer l'histoire du monde"):
            data['completed_shifts'] = []
            data['active_shifts'] = {}
            save_data(data)
            st.toast("Toutes les données ont été effacées, l'univers a été réinitialisé.", icon="💥")
            st.rerun()
    with tab3:
        st.subheader("Télécharger le grand livre d'histoire")
        csv_data = export_csv(data, all_users=True)
        st.download_button(
            label="📥 Télécharger le fichier d'histoire global",
            data=csv_data,
            file_name=f'shifts_tous_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )

else:
    tab1, tab2, tab3 = st.tabs(["⚔️ Ma Quête", "📈 Mon Bilan", "📥 Mon Trésor"])
    with tab1:
        st.subheader(f"Statut de quête pour {user}")
        if user in data['active_shifts']:
            sh = data['active_shifts'][user]
            start_time_obj = datetime.fromisoformat(sh['start'])

            # T-Rex + statut
            if sh['pauses'] and sh['pauses'][-1].get('end') is None:
                col_trex, col_status = st.columns([0.25, 0.75])
                with col_trex:
                    st.image("https://media.tenor.com/7123dIeQ-8MAAAAC/mario-peach.gif", width=60, use_container_width=False)
                with col_status:
                    st.info("Statut : En pause... 🍄")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Reprendre l'aventure", use_container_width=True):
                        resume_shift(data, user)
                with col2:
                    st.button("Terminer la quête", disabled=True, use_container_width=True, help="Reprenez l'aventure avant de la terminer.")
            else:
                col_trex, col_status = st.columns([0.25, 0.75])
                with col_trex:
                    st.image("https://media.tenor.com/7123dIeQ-8MAAAAC/mario-peach.gif", width=60, use_container_width=False)
                with col_status:
                    st.info("Statut : En mission ! ⚔️")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Faire une pause", use_container_width=True):
                        pause_shift(data, user)
                with col2:
                    if st.button("Terminer la quête", type="primary", use_container_width=True):
                        end_shift(data, user)

        else:
            st.info("Aucune quête en cours. Prêt à commencer ?")
            if st.button("🚀 Démarrer mon aventure", use_container_width=True, type="primary"):
                start_shift(data, user)

    with tab2:
        st.subheader(f"Journal de quêtes de {user}")
        user_shifts = sorted([sh for sh in data['completed_shifts'] if sh.get('employee') == user], key=lambda x: x['start'], reverse=True)
        if not user_shifts:
            st.info("Vous n'avez pas encore de quête terminée.")
        else:
            rows = []
            for sh in user_shifts:
                date = datetime.fromisoformat(sh['start']).strftime("%d/%m/%Y")
                rows.append({
                    "Date de quête": date,
                    "Début de quête": datetime.fromisoformat(sh['start']).strftime("%H:%M"),
                    "Fin de quête": datetime.fromisoformat(sh['end']).strftime("%H:%M"),
                    "Temps d'action": format_time_h_m(sh.get('worked_seconds', 0)),
                    "Temps de repos": format_time_m_s(sh.get('pause_seconds', 0))
                })
            st.dataframe(rows, use_container_width=True)

    with tab3:
        st.subheader("Exporter mon butin")
        csv_data = export_csv(data, all_users=False, current_user=user)
        st.download_button(
            label="📥 Télécharger le journal de mes exploits",
            data=csv_data,
            file_name=f'shifts_{user}_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )
