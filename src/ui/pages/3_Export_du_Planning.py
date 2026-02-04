from datetime import datetime, timedelta
import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import zipfile
from io import BytesIO
import subprocess
import time
import re

# Add OR-TOOLS to path
sys.path.append(str(Path(__file__).parent.parent.parent / "OR-TOOLS"))

st.set_page_config(
    page_title="Export du Planning",
    page_icon=":material/check_circle:",
    layout="wide"
)

st.title("Export du Planning")

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
RESULTAT_DIR = Path(__file__).parent.parent.parent.parent / "resultat"

st.subheader("Vérification des prérequis")

def check_csv_valid(filepath):
    """Check if CSV exists and has at least 2 rows (header + 1 data)"""
    if not filepath.exists():
        return False, "Fichier manquant"
    
    try:
        df = pd.read_csv(filepath)
        if len(df) < 1:
            return False, "Fichier vide"
        return True, f"{len(df)} entrée(s)"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

# Check all required files
checks = {
    "Import des calendriers universitaires de la première année": DATA_DIR / "calendrier_DFAS01.csv",
    "Import des calendriers universitaires de la deuxième année": DATA_DIR / "calendrier_DFAS02.csv",
    "Import des calendriers universitaires de la troisième année": DATA_DIR / "calendrier_DFTCC.csv",
    "Configuration des disciplines": DATA_DIR / "disciplines.csv",
    "Configuration des périodes": DATA_DIR / "periodes.csv",
    "Configuration des stages": DATA_DIR / "stages.csv",
    "Nombre d'élèves": DATA_DIR / "eleves.csv"
}

all_valid = True
results = {}

for name, filepath in checks.items():
    is_valid, message = check_csv_valid(filepath)
    results[name] = (is_valid, message)
    all_valid = all_valid and is_valid

# Display results
for name, (is_valid, message) in results.items():
    if is_valid:
        st.success(f"{name}: {message}")
    else:
        st.error(f"{name}: {message}")

# Show missing steps
if not all_valid:
    missing_items = [name for name, (valid, _) in results.items() if not valid]
    st.info("Complétez le(s) étape(s) suivante(s):\n\n" + "\n".join([f"- {item}" for item in missing_items]))

st.markdown("---")
st.subheader("Génération des liste d'éleves")
# Button to generate student lists with codes generate_student_code.py
if st.button("Générer les listes d'élèves avec codes", use_container_width=True):
    try:

        data_dir_generation = Path(__file__).parent.parent.parent / "data"
        sys.path.insert(0, str(data_dir_generation))
                    
        from generate_student_code import generate_student_data
                    
        eleves_csv = DATA_DIR / "eleves.csv"
        eleves_df = pd.read_csv(eleves_csv)
        nombre_eleves_DFAS01 = eleves_df['DFAS01'].sum()
        nombre_eleves_DFAS02 = eleves_df['DFAS02'].sum()
        nombre_eleves_DFTCC = eleves_df['DFTCC'].sum()

        # verifie si colonne meme_jour_semaine est vrai pour une discipline prendre la liste des presence uic si vrai
        discipline_csv = DATA_DIR / "disciplines.csv"
        disciplines_df = pd.read_csv(discipline_csv)
        zlist = [] # liste des presences uic si meme_jour_semaine est vrai
        for index, row in disciplines_df.iterrows():
            if 'meme_jour_semaine' in row and row['meme_jour_semaine'] == True:
                try:
                    import ast
                    presence_dict = ast.literal_eval(row['presence'])
                    presence_list = [i-1 for i, val in presence_dict.items() if val]
                    liste_presence_uic = {}
                    liste_presence_uic[row['nom_discipline']] = presence_list
                except (ValueError, SyntaxError, AttributeError):
                    # Skip if parsing fails
                    continue
        zlist = sorted(set(val for plist in liste_presence_uic.values() for val in plist))
        generate_student_data(nombre_eleves_DFAS01, nombre_eleves_DFAS02, nombre_eleves_DFTCC, zlist)
        
        st.success("Listes d'élèves générées avec succès!")
    except Exception as e:
        st.error(f"Erreur lors de la génération des listes d'élèves: {str(e)}")

st.markdown("---")

st.subheader("Génération du planning")

if not all_valid:
    st.warning("Vous devez d'abord compléter tous les prérequis ci-dessus.")
    st.stop()

# Initialize session state
if 'model_status' not in st.session_state:
    st.session_state['model_status'] = None
if 'model_running' not in st.session_state:
    st.session_state['model_running'] = False
if 'optimization_result' not in st.session_state:
    st.session_state['optimization_result'] = None


# Button to launch optimization
col1, col2 = st.columns([3, 1])

with col1:
    if st.button(
        "Lancer la génération du planning",
        type="primary",
        disabled=st.session_state['model_running'],
        use_container_width=False
    ):
        st.session_state['model_running'] = True
        st.session_state['model_status'] = 'running'
        st.rerun()

with col2:
    if st.session_state.get('model_status') == 'success':
        if st.button("Régénérer", use_container_width=True):
            st.session_state['model_running'] = True
            st.session_state['model_status'] = 'running'
            st.rerun()

# If model is running
if st.session_state.get('model_running', False):
    st.info("Génération du planning en cours... Cela peut prendre plusieurs minutes.")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Time display
    col1, col2 = st.columns(2)
    with col1:
        elapsed_display = st.empty()
        elapsed_display.metric("Temps écoulé", "0s")
    with col2:
        remaining_display = st.empty()
        remaining_display.metric("Temps restant", "Calcul...")
    
    log_expander = st.expander("Logs détaillés", expanded=False)
    log_container = log_expander.empty()
    
    # Path to optimizer script
    app_script = Path(__file__).parent.parent.parent / "OR-TOOLS" / "app.py"
    env_python = sys.executable
    
    try:
        # Launch subprocess
        process = subprocess.Popen(
            [env_python, str(app_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Read output
        logs = []
        solution_count = 0
        elapsed_time = 0
        remaining_time = None
        max_time = 10800  # Default 3 hours
        objective = 0
        
        # Force immediate display
        placeholder = st.empty()
        
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
                
            line = line.strip()
            if line:
                logs.append(line)
                log_container.text("\n".join(logs[-50:]))  # Show last 50 lines
                
                # Parse max time from solver start
                solver_start_match = re.search(r'SOLVER_START\|MaxTime: (\d+)s', line)
                if solver_start_match:
                    max_time = int(solver_start_match.group(1))
                    remaining_display.metric("Temps restant", f"{max_time}s")
                
                # Parse solution progress (EXACT FORMAT)
                # Format: PROGRESS|Solution #X|Elapsed: Ys|Remaining: Zs|Objective: V
                progress_match = re.search(
                    r'PROGRESS\|Solution #(\d+)\|Elapsed: (\d+)s\|Remaining: (\d+)s\|Objective: ([\d.]+)',
                    line
                )
                
                if progress_match:
                    solution_count = int(progress_match.group(1))
                    elapsed_time = int(progress_match.group(2))
                    remaining_time = int(progress_match.group(3))
                    objective = float(progress_match.group(4))
                    
                    # Format time as HH:MM:SS
                    def format_time(seconds):
                        hours = seconds // 3600
                        minutes = (seconds % 3600) // 60
                        secs = seconds % 60
                        if hours > 0:
                            return f"{hours}h {minutes}m {secs}s"
                        elif minutes > 0:
                            return f"{minutes}m {secs}s"
                        else:
                            return f"{secs}s"
                    
                    # Update displays
                    elapsed_display.metric(
                        "Temps écoulé",
                        format_time(elapsed_time)
                    )
                    remaining_display.metric(
                        "Temps restant",
                        format_time(remaining_time)
                    )
                
                # Check for other progress keywords
                progress_keywords = {
                    'Chargement des données': 10,
                    'Variables créées': 20,
                    'Index construits': 25,
                    'Contraintes de capacité': 35,
                    'Contraintes d\'unicité': 40,
                    'Contraintes max vacations': 45,
                    'Contraintes de remplissage': 50,
                    'Contraintes de binômes': 55,
                    'Contraintes avancées': 65,
                    'Objectif configuré': 70,
                    'RÉSOLUTION': 75,
                }
                
                for keyword, percent in progress_keywords.items():
                    if keyword in line:
                        if percent < 75:  # Don't override solving progress
                            progress_bar.progress(percent / 100)
                            status_text.text(line)
                        break
        
        # Wait for completion
        return_code = process.wait()
        
        if return_code == 0:
            progress_bar.progress(1.0)
            status_text.success("Génération terminée avec succès!")
            
            # Final time display
            if elapsed_time > 0:
                elapsed_display.metric(
                    "Temps total",
                    format_time(elapsed_time)
                )
            remaining_display.metric(
                "Temps restant",
                "0s"
            )
            
            st.session_state['model_status'] = 'success'
            st.session_state['model_running'] = False
            time.sleep(1)
            st.rerun()
        else:
            status_text.error(f"Erreur lors de la génération (code: {return_code})")
            st.session_state['model_status'] = 'error'
            st.session_state['model_running'] = False
    
    except Exception as e:
        st.error(f"Erreur: {str(e)}")
        st.session_state['model_status'] = 'error'
        st.session_state['model_running'] = False
st.markdown("---")

if st.session_state.get('model_status') == 'success':
    st.subheader("Export du planning")
    
    # Check if planning solution exists
    planning_solution_path = RESULTAT_DIR / "planning_solution.csv"
    
    if not planning_solution_path.exists():
        st.error("Le fichier planning_solution.csv n'a pas été généré.")
        st.stop()
    
    # Show statistics if available
    stats_path = RESULTAT_DIR / "statistics.json"
    if stats_path.exists():
        import json
        with open(stats_path, 'r') as f:
            stats = json.load(f)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total affectations", stats.get('total_assignments', 0))
        with col2:
            st.metric("Disciplines", len(stats.get('assignments_by_discipline', {})))
        with col3:
            fulfilled = sum(1 for v in stats.get('quota_fulfillment', {}).values() if v.get('fulfilled'))
            total = len(stats.get('quota_fulfillment', {}))
            st.metric("Quotas remplis", f"{fulfilled}/{total}")
    
    col1, col2 = st.columns(2)

    # L'emplois du temps complet
    with col1:
        st.markdown("#### Emplois du temps individuels")
        if st.button("Générer et télécharger", key="edt", use_container_width=True):
            with st.spinner("Génération en cours..."):
                try:
                    formatters_dir = Path(__file__).parent.parent.parent / "formatters"
                    sys.path.insert(0, str(formatters_dir))
                    
                    from generate_formatted_student_TT import generate_individual_plannings, create_timetable_excel
                    
                    output_folder = RESULTAT_DIR / "planning_personnel"
                    generate_individual_plannings(str(planning_solution_path), str(output_folder))
                    
                    excel_output = RESULTAT_DIR / "emplois_du_temps.xlsx"
                    create_timetable_excel(str(output_folder), str(excel_output), datetime(2025, 9, 1))
                    
                    with open(excel_output, 'rb') as f:
                        st.download_button(
                            label="Télécharger emplois_du_temps.xlsx",
                            data=f,
                            file_name="emplois_du_temps.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    st.success("Généré avec succès!")
                    
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")

    with col2:
        st.markdown("#### Fiches d'appel")
        if st.button("Générer et télécharger", key="appel", use_container_width=True):
            with st.spinner("Génération en cours..."):
                try:
                    formatters_dir = Path(__file__).parent.parent.parent / "formatters"
                    sys.path.insert(0, str(formatters_dir))
                    
                    from generate_formatted_fiche_appel import generate_discipline_year_excel
                    
                    output_folder = RESULTAT_DIR / "fiche_appel_par_discipline"
                    generate_discipline_year_excel(str(planning_solution_path), str(output_folder))
                    
                    # Créer un ZIP
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for excel_file in output_folder.glob("*.xlsx"):
                            zip_file.write(excel_file, excel_file.name)
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label="Télécharger fiches_appel.zip",
                        data=zip_buffer,
                        file_name="fiches_appel_disciplines.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    st.success("Généré avec succès!")
                    
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")

else:
    st.info("ℹLancez d'abord la génération du planning pour accéder aux options d'export.")