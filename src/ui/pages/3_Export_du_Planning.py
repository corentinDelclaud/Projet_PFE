from datetime import datetime, timedelta
import streamlit as st
from pathlib import Path
import sys
import pandas as pd
import zipfile
from io import BytesIO
import time
import os

def resolve_data_path():
    """Resolve data directory path for both normal and PyInstaller frozen mode"""
    if getattr(sys, 'frozen', False):
        # Mode compilé (PyInstaller) - data est à côté de l'exécutable
        base_dir = Path(sys.executable).parent
    else:
        # Mode script Python normal
        base_dir = Path(__file__).parent.parent.parent.parent
    return base_dir / "data"

def resolve_resultat_path():
    """Resolve resultat directory path for both normal and PyInstaller frozen mode"""
    if getattr(sys, 'frozen', False):
        # Mode compilé (PyInstaller) - resultat est à côté de l'exécutable
        base_dir = Path(sys.executable).parent
    else:
        # Mode script Python normal
        base_dir = Path(__file__).parent.parent.parent.parent
    return base_dir / "resultat"

# Add OR-TOOLS to path
if not getattr(sys, 'frozen', False):
    sys.path.append(str(Path(__file__).parent.parent.parent / "OR-TOOLS"))

st.set_page_config(
    page_title="Export du Planning",
    page_icon=":material/check_circle:",
    layout="wide"
)

st.title("Export du Planning")

DATA_DIR = resolve_data_path()
RESULTAT_DIR = resolve_resultat_path()

# Créer les dossiers s'ils n'existent pas
DATA_DIR.mkdir(exist_ok=True)
RESULTAT_DIR.mkdir(exist_ok=True)

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
        # Import the module (works in both normal and frozen mode)
        if getattr(sys, 'frozen', False):
            # En mode frozen, le module est dans le bundle
            from data.generate_student_code import generate_student_data
        else:
            # En mode normal, ajouter le chemin parent au sys.path
            data_dir_generation = Path(__file__).parent.parent.parent / "data"
            if str(data_dir_generation.parent) not in sys.path:
                sys.path.insert(0, str(data_dir_generation.parent))
            from data.generate_student_code import generate_student_data
                    
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
    
    # Import optimizer modules
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "OR-TOOLS"))
    
    try:
        # Import directly instead of using subprocess
        from config_manager import ModelConfig
        from optimizer import ScheduleOptimizer
        from exporter import export_planning, export_statistics
        import io
        import contextlib
        
        # Capture stdout to show logs
        logs = []
        
        # Helper to format time
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
        
        # Load configuration
        data_dir = resolve_data_path()
        output_dir = resolve_resultat_path()
        
        progress_bar.progress(0.1)
        status_text.text("Chargement de la configuration...")
        
        config = ModelConfig.from_csv_directory(data_dir)
        config.output_dir = output_dir
        
        # Validate configuration
        progress_bar.progress(0.15)
        status_text.text("Validation de la configuration...")
        log_container.text("✓ Configuration chargée")
        
        is_valid, errors = config.validate()
        if not is_valid:
            error_msg = "Configuration invalide:\n" + "\n".join([f"  - {e}" for e in errors])
            st.error(error_msg)
            st.session_state['model_status'] = 'error'
            st.session_state['model_running'] = False
            st.stop()
        
        log_container.text("✓ Configuration chargée\n✓ Configuration validée")
        
        # Save configuration
        config.save_to_json(config.output_dir / "config_used.json")
        
        # Create optimizer
        progress_bar.progress(0.2)
        status_text.text("Création de l'optimizer...")
        optimizer = ScheduleOptimizer(config)
        log_container.text("✓ Configuration chargée\n✓ Configuration validée\n✓ Optimizer créé")
        
        # Prepare data
        progress_bar.progress(0.25)
        status_text.text("Chargement des données...")
        optimizer.prepare_data()
        log_container.text("✓ Configuration chargée\n✓ Configuration validée\n✓ Optimizer créé\n✓ Données chargées")
        
        # Build model
        progress_bar.progress(0.5)
        status_text.text("Construction du modèle...")
        optimizer.build_model()
        log_container.text("✓ Configuration chargée\n✓ Configuration validée\n✓ Optimizer créé\n✓ Données chargées\n✓ Modèle construit")
        
        # Solve
        progress_bar.progress(0.75)
        status_text.text("Résolution en cours...")
        
        # Track progress with a custom approach
        import time as time_module
        start_time = time_module.time()
        max_time = config.solver_params.max_time_seconds
        
        # Show initial time
        remaining_display.metric("Temps restant", format_time(max_time))
        
        # Start solving (this will block)
        result = optimizer.solve()
        
        # Calculate elapsed time
        elapsed_time = int(time_module.time() - start_time)
        elapsed_display.metric("Temps écoulé", format_time(elapsed_time))
        remaining_display.metric("Temps restant", "0s")
        elapsed_display.metric("Temps écoulé", format_time(elapsed_time))
        remaining_display.metric("Temps restant", "0s")
        
        # Export results
        if result.is_success():
            progress_bar.progress(0.9)
            status_text.text("Export des résultats...")
            
            # Export planning
            export_planning(
                result,
                config.output_dir / "planning_solution.csv",
                config,
                optimizer
            )
            
            # Export statistics
            export_statistics(
                result,
                config.output_dir / "statistics.json"
            )
            
            progress_bar.progress(1.0)
            status_text.success("Génération terminée avec succès!")
            log_container.text("✓ Configuration chargée\n✓ Configuration validée\n✓ Optimizer créé\n✓ Données chargées\n✓ Modèle construit\n✓ Résolution terminée\n✓ Résultats exportés")
            
            st.session_state['model_status'] = 'success'
            st.session_state['model_running'] = False
            time.sleep(1)
            st.rerun()
        else:
            status_text.error(f"Erreur lors de la génération: {result.status}")
            if result.error_message:
                log_container.text(f"Erreur: {result.error_message}")
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