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
st.set_page_config(layout="wide", page_title="Chronométrage Pro")

# --- AJOUT DE L'HORLOGE ÉLECTRONIQUE ---
# Cette section doit être placée tout en haut de l'application, après les configurations de page et les imports.
# HTML et CSS pour l'horloge
st.markdown(
    """
    <style>
    .digital-clock {
        text-align: center;
        padding: 20px;
        background-color: #1a1a2e;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        color: #00ff88;
        /* Utilisation d'une police standard pour éviter les problèmes de chargement */
        font-family: 'monospace', sans-serif;
        font-size: 80px;
        font-weight: bold;
        letter-spacing: 5px;
        margin-bottom: 30px;
        border: 2px solid #00ff88;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .digital-clock-small {
        font-size: 30px;
        font-weight: normal;
        margin-left: 10px;
        color: #ffffff;
    }
    </style>
    <div id="digital-clock" class="digital-clock"></div>
    <script>
        function updateTime() {
            const now = new Date();
            const options = { 
                timeZone: 'Europe/Paris', 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit',
                hour12: false
            };
            const timeString = now.toLocaleTimeString('fr-FR', options);
            document.getElementById('digital-clock').textContent = timeString;
        }
        setInterval(updateTime, 1000);
        updateTime(); // Appeler une fois immédiatement pour éviter le délai initial
    </script>
    """,
    unsafe_allow_html=True
)

# --- USERS ---
USERS = {
    "Navalona": "Andihoo2025",
    "Sandy": "Andihoo2025",
    "Kanto": "Andihoo2025",
    "Volana": "Andihoo2025",
    "Steve": "Andihoo2025",
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
    body, html, [class*="css"] {
        font-family: 'Ubuntu', sans-serif;
    }
    .main { background-color: #0f1116 !important; color: #e0e0e0 !important; }
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
    # Créer trois colonnes et placer le titre dans la colonne du milieu
    col1, col2, col3 = st.columns([1, 2, 1])  # La colonne du milieu est plus large
    with col2:
        st.title("Chronométrage Pro ⏱️")  # Titre centré

    # Formulaire de login
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur", key="login_user")
            password = st.text_input("Mot de passe", type="password", key="login_pass")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)
            if submitted:
                if USERS.get(username) == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    cookies["user"] = username
                    cookies.save()
                    st.toast(f"Bienvenue {username} !", icon="👋")
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect")
    st.stop()


# --- INTERFACE PRINCIPALE ---
user = st.session_state.current_user
data = load_data()

with st.sidebar:
    st.title("Menu")
    st.info(f"Salut **{user}** !")
    if st.button("Se déconnecter", use_container_width=True, type="primary"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        cookies["user"] = ""
        cookies.save()
        st.toast("Vous avez été déconnecté.", icon="👋")
        st.rerun()

st.header(f"🕐Chrono�")

if user == 'admin':
    tab1, tab2, tab3 = st.tabs(["📊 Reporting Global", "⚙️ Actions Administrateur", "📥 Exporter CSV"])
    with tab1:
        st.subheader("Reporting global - Tous les employés")
        if not data['completed_shifts']:
            st.info("Aucun shift terminé pour l'instant.")
        else:
            rows = []
            sorted_shifts = sorted(data['completed_shifts'], key=lambda x: x['start'], reverse=True)
            for sh in sorted_shifts:
                date = datetime.fromisoformat(sh['start']).strftime("%d/%m/%Y")
                rows.append({
                    "Nom": sh.get('employee', 'inconnu'),
                    "Date": date,
                    "Début": datetime.fromisoformat(sh['start']).strftime("%H:%M:%S"),
                    "Fin": datetime.fromisoformat(sh['end']).strftime("%H:%M:%S"),
                    "Temps de travail": format_time_h_m(sh.get('worked_seconds', 0)),
                    "Temps de pause": format_time_m_s(sh.get('pause_seconds', 0))
                })
            st.dataframe(rows, use_container_width=True)
    with tab2:
        st.subheader("Zone de danger")
        if st.button("🔴 Supprimer toutes les données enregistrées"):
            data['completed_shifts'] = []
            data['active_shifts'] = {}
            save_data(data)
            st.toast("Toutes les données ont été effacées.", icon="💥")
            st.rerun()
    with tab3:
        st.subheader("Exporter toutes les données")
        csv_data = export_csv(data, all_users=True)
        st.download_button(
            label="📥 Télécharger le fichier CSV Global",
            data=csv_data,
            file_name=f'shifts_tous_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )

else:
    tab1, tab2, tab3 = st.tabs(["⏱️ Chronométrage", "📈 Mon Reporting", "📥 Exporter Mes Données"])
    with tab1:
        st.subheader(f"Suivi des heures de {user}")
        if user in data['active_shifts']:
            sh = data['active_shifts'][user]
            start_time_obj = datetime.fromisoformat(sh['start'])

            # T-Rex + statut
            if sh['pauses'] and sh['pauses'][-1].get('end') is None:
                col_trex, col_status = st.columns([0.25, 0.75])
                with col_trex:
                    st.image("https://cdn.pixabay.com/animation/2022/07/29/17/29/17-29-15-99_512.gif", width=60, use_container_width=False)
                with col_status:
                    st.info("Reviens vite ! Tes missions t'attendent !")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Reprendre", use_container_width=True):
                        resume_shift(data, user)
                with col2:
                    st.button("Terminer shift", disabled=True, use_container_width=True, help="Reprenez le travail avant de terminer.")
            else:
                col_trex, col_status = st.columns([0.25, 0.75])
                with col_trex:
                    st.image("https://fabianlpineda.wordpress.com/wp-content/uploads/2016/11/walking_trex.gif", width=60, use_container_width=False)
                with col_status:
                    st.info("Statut : Occupé")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Pause", use_container_width=True):
                        pause_shift(data, user)
                with col2:
                    if st.button("Terminer shift", type="primary", use_container_width=True):
                        end_shift(data, user)

        else:
            st.info("Ton avenir t'attend ! Commence ton aventure !")
            if st.button("🚀 Démarrer mon shift", use_container_width=True, type="primary"):
                start_shift(data, user)

    with tab2:
        st.subheader(f"Historique de mes shifts")
        user_shifts = sorted([sh for sh in data['completed_shifts'] if sh.get('employee') == user], key=lambda x: x['start'], reverse=True)
        if not user_shifts:
            st.info("Vous n'avez pas encore de shift terminé.")
        else:
            rows = []
            for sh in user_shifts:
                date = datetime.fromisoformat(sh['start']).strftime("%d/%m/%Y")
                rows.append({
                    "Date": date,
                    "Début": datetime.fromisoformat(sh['start']).strftime("%H:%M"),
                    "Fin": datetime.fromisoformat(sh['end']).strftime("%H:%M"),
                    "Temps de travail": format_time_h_m(sh.get('worked_seconds', 0)),
                    "Temps de pause": format_time_m_s(sh.get('pause_seconds', 0))
                })
            st.dataframe(rows, use_container_width=True)

    with tab3:
        st.subheader("Exporter mes résultats personnels")
        csv_data = export_csv(data, all_users=False, current_user=user)
        st.download_button(
            label="📥 Télécharger mes données en CSV",
            data=csv_data,
            file_name=f'shifts_{user}_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            use_container_width=True
        )
