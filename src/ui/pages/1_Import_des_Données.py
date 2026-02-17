import streamlit as st
import pandas as pd
from pathlib import Path
import shutil
import sys
from pathlib import Path

def resolve_data_path():
    """Resolve data directory path for both normal and PyInstaller frozen mode"""
    if getattr(sys, 'frozen', False):
        # Mode compilé (PyInstaller) - data est à côté de l'exécutable
        base_dir = Path(sys.executable).parent
    else:
        # Mode script Python normal
        base_dir = Path(__file__).parent.parent.parent.parent
    return base_dir / "data"

st.set_page_config(
    page_title="Import des Données",
    page_icon=":material/download:",
    layout="wide"
)

st.title("Import des Données")

# Définir le dossier de sauvegarde des données
DATA_DIR = resolve_data_path()
DATA_DIR.mkdir(exist_ok=True)

# Section Calendrier
st.subheader("1. Calendrier Universitaire")

with st.expander("Format Excel attendu", expanded=False):
    st.info("""
    **Format requis :**
    - **11 colonnes** exactement
    
    **Structure :**
    - Colonne 1 : Numéro de semaine (34 à 52, puis 1 à 33)
    - Colonnes 2-11 : Demi-journées (1 à 10)
    
    **En-têtes :**
    - Ligne 1 : LUN, MAR, MER, JEU, VEN
    - Ligne 2 : 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    
    **Valeurs possibles dans les cellules :**
    - C : Cours
    - F : Fermé
    - A : Absence, etc...
    - (vide) : Disponible
    """)

    st.markdown("**Exemple de calendrier :**")

    # En-têtes sur 2 lignes
    colonnes = pd.MultiIndex.from_tuples([
        ("", "semaine"),
        ("LUN", "1"), ("LUN", "2"),
        ("MAR", "3"), ("MAR", "4"),
        ("MER", "5"), ("MER", "6"),
        ("JEU", "7"), ("JEU", "8"),
        ("VEN", "9"), ("VEN", "10"),
    ])

    exemple_calendrier = pd.DataFrame(
        [
            [36, "C", "C", "", "C", "", "C", "C", "", "C", ""],
            [37, "", "", "F", "", "F", "", "", "", "F", "F"],
            [38, "C", "", "C", "", "F", "C", "", "A", "", "F"],
        ],
        columns=colonnes
    )

    st.dataframe(
        exemple_calendrier,
        hide_index=True,
        use_container_width=True
    )

# Téléversement du fichier calendrier pour chaque niveau (DFASO1, DFASO2, DFTCC)
calendrier_file_DFASO1 = st.file_uploader(
    "Choisir le calendrier universitaire des DFASO1",
    type=["xlsx", "csv"],
    key="calendrier1"
)

calendrier_file_DFASO2 = st.file_uploader(
    "Choisir le calendrier universitaire des DFASO2",
    type=["xlsx", "csv"],
    key="calendrier2"
)

calendrier_file_DFTCC = st.file_uploader(
    "Choisir le calendrier universitaire des DFTCC",
    type=["xlsx", "csv"],
    key="calendrier3"
)

for niveau, calendrier_file in [("DFASO1", calendrier_file_DFASO1), ("DFASO2", calendrier_file_DFASO2), ("DFTCC", calendrier_file_DFTCC)]:
    if calendrier_file:
        df_cal = pd.read_excel(calendrier_file) if calendrier_file.name.endswith('xlsx') else pd.read_csv(calendrier_file)
        
        # Vérifications
        expected_nb_cols = 11
        
        errors = []
        warnings = []
        
        # Vérifier le nombre de colonnes
        if len(df_cal.columns) != expected_nb_cols:
            errors.append(f"Nombre de colonnes incorrect : {len(df_cal.columns)} au lieu de {expected_nb_cols}")

        # Affichage des erreurs/warnings
        if errors:
            for error in errors:
                st.error(error)
        elif warnings:
            for warning in warnings:
                st.warning(warning)
            st.success(f"Calendrier importé ({len(df_cal)} semaines)")
            st.dataframe(df_cal.head(10))
        else:
            st.success(f"Calendrier importé (validation OK - {len(df_cal)} semaines)")
            st.dataframe(df_cal.head(10))
