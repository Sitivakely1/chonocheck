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
    }

    .main {
        background-color: #330107 !important;
        color: #330107 !important;
        background-image: url('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQghqRKyKBo-CfZhlSYYG3MKfQ36R1_Wp78Vg&s');
    }

    .stApp {
        background-color: #330107;
        color: #330107;
        background-image: url('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQghqRKyKBo-CfZhlSYYG3MKfQ36R1_Wp78Vg&s');
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
        color: #000000; /* Correction ici: le texte du bouton est maintenant noir */
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

    .st-emotion-cache-v01q51 {
        background-color: #3b1f4b;
        border-radius: 8px;
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
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Nom de code", key="login_user")
            password = st.text_input("Mot de passe sécurisé", type="password", key="login_pass")
            submitted = st.form_submit_button("Entrer dans le QG", use_container_width=True)
            if submitted:
                if USERS.get(username) == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    cookies["user"] = username
                    cookies.save()
                    st.toast(f"Bienvenue, Commandant {username} !", icon="🫡")
                    st.rerun()
                else:
                    st.error("Accès refusé. Nom de code ou mot de passe incorrect.")
    st.stop()

# --- INTERFACE PRINCIPALE ---
user = st.session_state.current_user
data = load_data()

with st.sidebar:
    st.title("Tableau des Opérations")
    st.info(f"Commandant en service : **{user}**")
    if st.button("Déconnexion du système", use_container_width=True, type="primary"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        cookies["user"] = ""
        cookies.save()
        st.toast("Système déconnecté. À bientôt, Commandant.", icon="🚨")
        st.rerun()

st.header(f"Centre de Commandement")

if user == 'admin':
    tab1, tab2, tab3 = st.tabs(["📊 Rapport de Mission", "⚙️ Panneau de Sécurité", "📥 Archives de Guerre"])
    with tab1:
        st.subheader("Rapport global des Opérations")
        if not data['completed_shifts']:
            st.info("Aucune opération terminée pour l'instant.")
        else:
            rows = []
            sorted_shifts = sorted(data['completed_shifts'], key=lambda x: x['start'], reverse=True)
            for sh in sorted_shifts:
                date = datetime.fromisoformat(sh['start']).strftime("%d/%m/%Y")
                rows.append({
                    "Commandant": sh.get('employee', 'inconnu'),
                    "Date de mission": date,
                    "Début mission": datetime.fromisoformat(sh['start']).strftime("%H:%M:%S"),
                    "Fin mission": datetime.fromisoformat(sh['end']).strftime("%H:%M:%S"),
                    "Durée d'opération": format_time_h_m(sh.get('worked_seconds', 0)),
                    "Temps de ravitaillement": format_time_m_s(sh.get('pause_seconds', 0))
                })
            st.dataframe(rows, use_container_width=True)
    with tab2:
        st.subheader("Zone de danger")
        if st.button("🔴 Effacer toutes les données de mission"):
            data['completed_shifts'] = []
            data['active_shifts'] = {}
            save_data(data)
            st.toast("Toutes les archives ont été effacées. Confidentialité totale.", icon="💥")
            st.rerun()
    with tab3:
        st.subheader("Exporter les rapports d'opération")
        csv_data = export_csv(data, all_users=True)
        st.download_button(
            label="📥 Télécharger le rapport global des missions",
            data=csv_data,
            file_name=f'rapport_global_missions_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )

else:
    tab1, tab2, tab3 = st.tabs(["⚔️ Ma Mission", "📈 Mon Bilan", "📥 Mes Archives"])
    with tab1:
        st.subheader(f"Statut d'opération pour {user}")
        st.markdown("*Que votre détermination soit votre blindage.*")
        if user in data['active_shifts']:
            sh = data['active_shifts'][user]
            start_time_obj = datetime.fromisoformat(sh['start'])

            # T-Rex + statut
            if sh['pauses'] and sh['pauses'][-1].get('end') is None:
                col_trex, col_status = st.columns([0.25, 0.75])
                with col_trex:
                    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHZ5dTBwbzZsbWl5aTgxMHQwbW1zcmIzZXBwcHh3cHN5M2V4cmU5bCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/YqZzVw3d6uJ5l7b19R/giphy.gif", width=60, use_container_width=False)
                with col_status:
                    st.info("Statut : En ravitaillement ☕")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Retourner au combat", use_container_width=True):
                        resume_shift(data, user)
                with col2:
                    st.button("Mettre fin à la mission", disabled=True, use_container_width=True, help="Reprenez l'opération avant d'y mettre fin.")
            else:
                col_trex, col_status = st.columns([0.25, 0.75])
                with col_trex:
                    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaG1oejgzMHY2Z2k4eXp0NXZjZzIzZXc5Z2R2a3FmODJ5ajZ0NnA4NiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPm2Vq6VdF9jGco/giphy.gif", width=60, use_container_width=False)
                with col_status:
                    st.info("Statut : Sur le terrain ! 🪖")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Départ en ravitaillement", use_container_width=True):
                        pause_shift(data, user)
                with col2:
                    if st.button("Mettre fin à la mission", type="primary", use_container_width=True):
                        end_shift(data, user)

        else:
            st.info("Aucune mission en cours. Prêt à vous déployer ?")
            if st.button("🚀 Démarrer la mission", use_container_width=True, type="primary"):
                start_shift(data, user)

    with tab2:
        st.subheader(f"Journal de combat de {user}")
        user_shifts = sorted([sh for sh in data['completed_shifts'] if sh.get('employee') == user], key=lambda x: x['start'], reverse=True)
        if not user_shifts:
            st.info("Vous n'avez pas encore de mission terminée.")
        else:
            rows = []
            for sh in user_shifts:
                date = datetime.fromisoformat(sh['start']).strftime("%d/%m/%Y")
                rows.append({
                    "Date de mission": date,
                    "Début de mission": datetime.fromisoformat(sh['start']).strftime("%H:%M"),
                    "Fin de mission": datetime.fromisoformat(sh['end']).strftime("%H:%M"),
                    "Durée d'opération": format_time_h_m(sh.get('worked_seconds', 0)),
                    "Temps de ravitaillement": format_time_m_s(sh.get('pause_seconds', 0))
                })
            st.dataframe(rows, use_container_width=True)

    with tab3:
        st.subheader("Exporter mes données de mission")
        csv_data = export_csv(data, all_users=False, current_user=user)
        st.download_button(
            label="📥 Télécharger le rapport de mes missions",
            data=csv_data,
            file_name=f'rapport_missions_{user}_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )



