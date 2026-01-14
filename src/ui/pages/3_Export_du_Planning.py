import streamlit as st
import pandas as pd
import subprocess
import os
import sys
from pathlib import Path
import time
import threading
import zipfile
from io import BytesIO

def create_zip_from_folder(folder_path):
    """Crée un fichier ZIP contenant tous les CSV d'un dossier"""
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for csv_file in Path(folder_path).glob("*.csv"):
            zip_file.write(csv_file, csv_file.name)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def create_zip_from_folder_recursive(folder_path):
    """Crée un fichier ZIP contenant tous les fichiers d'un dossier (récursif)"""
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        folder_path = Path(folder_path)
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(folder_path)
                zip_file.write(file_path, arcname)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

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
if st.session_state.get('model_status') == 'success':
    # Vérifier que planning_solution.csv existe
    planning_solution_path = RESULTAT_DIR / "planning_solution.csv"
    
    if not planning_solution_path.exists():
        st.error("Le fichier planning_solution.csv n'a pas été généré.")
        st.stop()
    
    tab1, tab2 = st.tabs(["Vue Calendrier", "Vue Étudiants"])
    
    with tab1:
        st.subheader("Fiches d'appel par cours")
        st.info("Génère une fiche d'appel par cours (Semaine, Jour, Période, Discipline)")
        
        # Étape 1: Générer les CSV
        if st.button("Générer les fiches d'appel CSV", type="primary"):
            with st.spinner("Génération des CSV en cours..."):
                try:
                    output_csv_path = Path(__file__).parent.parent.parent / "output_csv"
                    if str(output_csv_path) not in sys.path:
                        sys.path.insert(0, str(output_csv_path))
                    from generate_attendance_list import generate_call_sheets
                    
                    output_dir = RESULTAT_DIR / "fiche_appel"
                    generate_call_sheets(str(planning_solution_path), str(output_dir))
                    
                    st.success(f"Fiches d'appel CSV générées dans : {output_dir}")
                    nb_files = len(list(output_dir.glob("*.csv")))
                    st.metric("Nombre de fiches CSV générées", nb_files)
                    
                except Exception as e:
                    st.error(f"Erreur lors de la génération CSV : {str(e)}")
        
        fiche_appel_dir = RESULTAT_DIR / "fiche_appel"
        
        # Afficher les options d'export si les CSV existent
        if fiche_appel_dir.exists() and any(fiche_appel_dir.glob("*.csv")):
            st.markdown("---")
            st.subheader("Export des fiches d'appel")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Format PDF**")
                if st.button("Générer les PDF", key="gen_pdf"):
                    with st.spinner("Génération des PDF en cours..."):
                        try:
                            result_path = Path(__file__).parent.parent.parent / "result"
                            if str(result_path) not in sys.path:
                                sys.path.insert(0, str(result_path))
                            from generate_appel_pdf import generate_all_discipline_appel_pdfs_for_one_day
                            
                            # Lire les semaines/jours disponibles depuis les CSV
                            csv_files = list(fiche_appel_dir.glob("*.csv"))
                            semaines_jours = set()
                            for csv_file in csv_files:
                                parts = csv_file.stem.split("_")
                                if len(parts) >= 3:
                                    semaine = parts[0].replace("Semaine", "")
                                    jour = parts[1]
                                    semaines_jours.add((int(semaine), jour))
                            
                            # Générer PDF pour chaque combinaison
                            for semaine, jour in semaines_jours:
                                output_pdf_dir = RESULTAT_DIR / "feuilles_appel_pdf" / f"S{semaine}_{jour}"
                                generate_all_discipline_appel_pdfs_for_one_day(
                                    str(fiche_appel_dir),
                                    str(output_pdf_dir),
                                    semaine,
                                    jour
                                )
                            
                            st.success("PDFs générés avec succès!")
                            
                        except Exception as e:
                            st.error(f"Erreur lors de la génération PDF : {str(e)}")
            
            with col2:
                st.write("**Format Excel**")
                if st.button("Générer les Excel", key="gen_excel"):
                    with st.spinner("Génération des Excel en cours..."):
                        try:
                            result_path = Path(__file__).parent.parent.parent / "result"
                            if str(result_path) not in sys.path:
                                sys.path.insert(0, str(result_path))
                            from generate_appel_excel import generate_all_discipline_appel_excels_for_one_day
                            
                            # Lire les semaines/jours disponibles
                            csv_files = list(fiche_appel_dir.glob("*.csv"))
                            semaines_jours = set()
                            for csv_file in csv_files:
                                parts = csv_file.stem.split("_")
                                if len(parts) >= 3:
                                    semaine = parts[0].replace("Semaine", "")
                                    jour = parts[1]
                                    semaines_jours.add((int(semaine), jour))
                            
                            # Générer Excel pour chaque combinaison
                            for semaine, jour in semaines_jours:
                                output_excel_dir = RESULTAT_DIR / "feuilles_appel_excel" / f"S{semaine}_{jour}"
                                generate_all_discipline_appel_excels_for_one_day(
                                    str(fiche_appel_dir),
                                    str(output_excel_dir),
                                    semaine,
                                    jour
                                )
                            
                            st.success("Fichiers Excel générés avec succès!")
                            
                        except Exception as e:
                            st.error(f"Erreur lors de la génération Excel : {str(e)}")
            
            # Boutons de téléchargement
            st.markdown("---")
            st.subheader("Téléchargements")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    label="⬇ Fiches CSV (ZIP)",
                    data=create_zip_from_folder(fiche_appel_dir),
                    file_name="fiches_appel_csv.zip",
                    mime="application/zip"
                )
            
            with col2:
                pdf_dir = RESULTAT_DIR / "feuilles_appel_pdf"
                if pdf_dir.exists() and any(pdf_dir.rglob("*.pdf")):
                    st.download_button(
                        label="⬇ Fiches PDF (ZIP)",
                        data=create_zip_from_folder_recursive(pdf_dir),
                        file_name="fiches_appel_pdf.zip",
                        mime="application/zip"
                    )
            
            with col3:
                excel_dir = RESULTAT_DIR / "feuilles_appel_excel"
                if excel_dir.exists() and any(excel_dir.rglob("*.xlsx")):
                    st.download_button(
                        label="⬇ Fiches Excel (ZIP)",
                        data=create_zip_from_folder_recursive(excel_dir),
                        file_name="fiches_appel_excel.zip",
                        mime="application/zip"
                    )
    
    with tab2:
        st.subheader("Planning par Étudiant")
        
        # Charger la liste des étudiants
        eleves_df = pd.read_csv(DATA_DIR / "eleves.csv")
        student_options = [f"{row['id_eleve']} - {row['nom']}" for _, row in eleves_df.iterrows()]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_student = st.selectbox(
                "Sélectionnez un étudiant",
                options=[""] + student_options,
                help="Choisissez un étudiant pour générer son planning individuel"
            )
        
        with col2:
            export_all = st.checkbox("Tous les étudiants", value=False)
        
        # Étape 1: Générer les CSV
        if st.button("Générer les plannings CSV", type="primary"):
            with st.spinner("Génération des CSV en cours..."):
                try:
                    output_csv_path = Path(__file__).parent.parent / "output_csv"
                    if str(output_csv_path) not in sys.path:
                        sys.path.insert(0, str(output_csv_path))
                    from generate_student_TT import generate_individual_plannings
                    
                    output_dir = RESULTAT_DIR / "planning_personnel"
                    generate_individual_plannings(str(planning_solution_path), str(output_dir))
                    
                    st.success(f"Plannings CSV générés dans : {output_dir}")
                    nb_files = len(list(output_dir.glob("*.csv")))
                    st.metric("Nombre de plannings CSV générés", nb_files)
                    
                except Exception as e:
                    st.error(f"Erreur lors de la génération CSV : {str(e)}")
        
        planning_personnel_dir = RESULTAT_DIR / "planning_personnel"
        
        # Afficher les options d'export si les CSV existent
        if planning_personnel_dir.exists() and any(planning_personnel_dir.glob("*.csv")):
            st.markdown("---")
            st.subheader("Export format Excel")
            
            if st.button("Générer les emplois du temps Excel", key="gen_student_excel"):
                with st.spinner("Génération des emplois du temps Excel en cours..."):
                    try:
                        result_path = Path(__file__).parent.parent.parent / "result"
                        if str(result_path) not in sys.path:
                            sys.path.insert(0, str(result_path))
                        from generate_formatted_student_TT import create_timetable_excel
                        
                        excel_output = "emplois_du_temps.xlsx"
                        create_timetable_excel(str(planning_personnel_dir), excel_output)
                        
                        st.success("Emplois du temps Excel générés avec succès!")
                        
                    except Exception as e:
                        st.error(f"Erreur lors de la génération Excel : {str(e)}")
            
            # Boutons de téléchargement
            st.markdown("---")
            st.subheader("Téléchargements")
            
            if not export_all and selected_student:
                # Téléchargement d'un seul étudiant
                student_id = selected_student.split(" - ")[0]
                student_files = list(planning_personnel_dir.glob(f"{student_id}_*.csv"))
                
                if student_files:
                    with open(student_files[0], 'rb') as f:
                        st.download_button(
                            label=f"⬇ Planning CSV de {selected_student}",
                            data=f,
                            file_name=student_files[0].name,
                            mime="text/csv"
                        )
                else:
                    st.warning(f"Aucun planning trouvé pour l'étudiant {selected_student}")
            
            else:
                # Téléchargement de tous les plannings
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="⬇ Tous les plannings CSV (ZIP)",
                        data=create_zip_from_folder(planning_personnel_dir),
                        file_name="plannings_etudiants_csv.zip",
                        mime="application/zip"
                    )
                
                with col2:
                    excel_dir = RESULTAT_DIR / "emplois_du_temps_excel"
                    if excel_dir.exists() and any(excel_dir.glob("*.xlsx")):
                        excel_file = list(excel_dir.glob("*.xlsx"))[0]
                        with open(excel_file, 'rb') as f:
                            st.download_button(
                                label="⬇ Emplois du temps Excel",
                                data=f,
                                file_name=excel_file.name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

else:
    st.info("Lancez d'abord la génération du planning pour accéder aux options d'export.")