import streamlit as st
from datetime import datetime

# --- Simulation des fonctions et données (remplace par ton vrai code) ---
def start_shift(data, user):
    st.session_state["data"]["active_shifts"][user] = {
        "start": datetime.now().isoformat(),
        "pauses": []
    }
    st.rerun()

def pause_shift(data, user):
    st.session_state["data"]["active_shifts"][user]["pauses"].append({
        "start": datetime.now().isoformat(),
        "end": None
    })
    st.rerun()

def resume_shift(data, user):
    if st.session_state["data"]["active_shifts"][user]["pauses"]:
        st.session_state["data"]["active_shifts"][user]["pauses"][-1]["end"] = datetime.now().isoformat()
    st.rerun()

def end_shift(data, user):
    del st.session_state["data"]["active_shifts"][user]
    st.rerun()

# --- Données initiales ---
if "data" not in st.session_state:
    st.session_state["data"] = {"active_shifts": {}}

data = st.session_state["data"]
user = "Alice"  # Ex. utilisateur connecté

# --- Interface principale ---
tab1, tab2 = st.tabs(["⏱️ Chronométrage", "📊 Statistiques"])

with tab1:
    st.subheader(f"Actions pour {user}")
    if user in data['active_shifts']:
        sh = data['active_shifts'][user]
        start_time_obj = datetime.fromisoformat(sh['start'])
        st.success(f"Shift démarré le {start_time_obj.strftime('%d/%m/%Y')} à {start_time_obj.strftime('%H:%M:%S')}")

        # Détection du statut
        if sh['pauses'] and sh['pauses'][-1].get('end') is None:
            # --- PAUSE ---
            col_trex, col_status = st.columns([1, 5])
            with col_trex:
                st.image("https://media.tenor.com/NV5Z5J7Q9T4AAAAi/dino-slow.gif", width=80)  # GIF lent
            with col_status:
                st.info("Statut : En pause ⏸️")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Reprendre", use_container_width=True):
                    resume_shift(data, user)
            with col2:
                st.button("Terminer shift", disabled=True, use_container_width=True, help="Reprenez le travail avant de terminer.")

        else:
            # --- AU TRAVAIL ---
            col_trex, col_status = st.columns([1, 5])
            with col_trex:
                st.image("https://media.tenor.com/-_OjjLq7BRIAAAAi/dino-run.gif", width=80)  # GIF rapide
            with col_status:
                st.info("Statut : Au travail 👨‍💻")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Pause", use_container_width=True):
                    pause_shift(data, user)
            with col2:
                if st.button("Terminer shift", type="primary", use_container_width=True):
                    end_shift(data, user)

    else:
        st.info("Vous n'avez pas de shift en cours.")
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.image("https://media.tenor.com/-_OjjLq7BRIAAAAi/dino-run.gif", width=100)
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("🚀 Démarrer mon shift", use_container_width=True, type="primary"):
            start_shift(data, user)

with tab2:
    st.write("📊 Ici, tu pourrais afficher tes statistiques...")
