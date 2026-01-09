import streamlit as st
import pandas as pd
import subprocess
import os
from pathlib import Path
import time
import threading

st.set_page_config(
    page_title="Export du Planning",
    page_icon=":material/check_circle:",
    layout="wide"
)

st.title("Export du Planning")

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
RESULTAT_DIR = Path(__file__).parent.parent.parent.parent / "resultat"

st.subheader("Vérification des prérequis")
# Fonction pour vérifier si un CSV a au moins 2 lignes (header + 1 data)
def check_csv_valid(filepath):
    if not filepath.exists():
        return False, "Fichier non trouvé"
    
    try:
        df = pd.read_csv(filepath)
        if len(df) < 2:
            return False, f"Au moins 2 lignes de données requises (trouvé: {len(df)})"
        return True, f" {len(df)} lignes trouvées"
    except Exception as e:
        return False, f"Erreur de lecture: {str(e)}"

# Partie 1: Vérifications
checks = {
    "Liste des étudiants": DATA_DIR / "eleves.csv",
    "Configuration des stages": DATA_DIR / "mock_stages.csv"
}

all_valid = True
results = {}

for name, filepath in checks.items():
    is_valid, message = check_csv_valid(filepath)
    results[name] = (is_valid, message)
    all_valid = all_valid and is_valid

for name, (is_valid, message) in results.items():
    if is_valid:
        st.success(f" {name}: {message}")
    else:
        st.error(f" {name}: {message}")

# Liens rapides vers les pages nécessaires
if not all_valid:
    eleves_valid, _ = results["Liste des étudiants"]
    stages_valid, _ = results["Configuration des stages"]
    
    missing_items = []
    if not eleves_valid:
        missing_items.append("Importer la liste des étudiants")
    if not stages_valid:
        missing_items.append("Configurer les stages")
    
    st.info("Complétez le(s) étape(s) suivante(s) :\n\n" + "\n\n".join([f"- {item}" for item in missing_items]))

st.markdown("---")

# Partie 2: Génération du planning
st.subheader("Génération du planning")

if not all_valid:
    st.warning("Vous devez d'abord compléter tous les prérequis ci-dessus.")
    st.stop()

# Initialiser le session state
if 'model_status' not in st.session_state:
    st.session_state['model_status'] = None
if 'model_running' not in st.session_state:
    st.session_state['model_running'] = False

# Bouton de lancement
if st.button("Lancer la génération du planning", type="primary", disabled=st.session_state['model_running']):
    st.session_state['model_running'] = True
    st.session_state['model_status'] = 'running'
    st.session_state['model_output'] = []
    st.rerun()

# Si le modèle est en cours d'exécution
if st.session_state.get('model_running', False):
    
    st.info("Génération du planning en cours... Cela peut prendre plusieurs minutes.")
    
    # Conteneurs pour la barre de progression et les logs
    progress_container = st.empty()
    status_container = st.empty()
    log_container = st.expander("Logs en temps réel", expanded=False)
    
    # Chemin vers le script model.py
    model_script = Path(__file__).parent.parent.parent / "OR-TOOLS" / "model.py"
    env_python = "/Users/poomedy/.pyenv/versions/3.13.7/envs/pfe_ortools/bin/python3"
    
    # Exécuter le processus
    try:
        process = subprocess.Popen(
            [env_python, str(model_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Rediriger stderr vers stdout
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Lire la sortie ligne par ligne
        progress_value = 0
        for line in process.stdout:
            line = line.strip()
            if line:
                st.session_state['model_output'].append(line)
                
                # Mettre à jour la barre de progression basée sur les logs
                if "Chargement" in line or "Loading" in line:
                    progress_value = 20
                elif "Construction" in line or "Building" in line:
                    progress_value = 40
                elif "Contraintes" in line or "Constraints" in line:
                    progress_value = 60
                elif "Résolution" in line or "Solving" in line:
                    progress_value = 80
                elif "Solution trouvée" in line or "Solution found" in line:
                    progress_value = 95
                elif "Écriture" in line or "Writing" in line:
                    progress_value = 98
                
                # Afficher la progression
                progress_container.progress(progress_value / 100)
                status_container.text(f"Progression: {progress_value}% - {line[:60]}...")
                
                # Afficher dans les logs
                with log_container:
                    st.text(line)
        
        # Attendre la fin du processus
        return_code = process.wait()
        
        if return_code == 0:
            progress_container.progress(100)
            status_container.success("Génération terminée avec succès !")
            st.session_state['model_status'] = 'success'
            st.session_state['model_running'] = False
            st.balloons()
            time.sleep(2)
            st.rerun()
        else:
            status_container.error("Erreur lors de la génération")
            st.session_state['model_status'] = 'error'
            st.session_state['model_running'] = False
            with st.expander("Détails de l'erreur", expanded=True):
                for line in st.session_state.get('model_output', []):
                    st.code(line)
    
    except Exception as e:
        status_container.error(f"Erreur: {str(e)}")
        st.session_state['model_status'] = 'error'
        st.session_state['model_running'] = False


st.markdown("---")

# Partie 3 : Export du planning
tab1, tab2 = st.tabs(["Vue Calendrier", "Vue Étudiants"])

with tab1:
    st.subheader("Planning Calendrier")

with tab2:
    st.subheader("Planning par Étudiant")
    etudiant = st.selectbox("Exporter un étudiant (Sélectionnez un étudiant dans la liste)", ["1", "2", "..."])
    # Sélectionner tous les étudiants
    tous_les_etudiants = st.checkbox("Exporter tous les étudiants")

# Section Export
st.subheader("Export")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="⬇ Télécharger Planning Excel",
        data="",  # Votre DataFrame converti en Excel
        file_name="planning_hospitalier.xlsx",
        mime="application/vnd.ms-excel",
        help="Exporter le planning au format Excel"
    )

with col2:
    st.download_button(
        label="⬇ Télécharger Planning PDF",
        data="",
        file_name="planning_hospitalier.pdf",
        mime="application/pdf",
        help="Exporter le planning au format PDF"
    )
