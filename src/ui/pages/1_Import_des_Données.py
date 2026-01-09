import streamlit as st
import pandas as pd
from pathlib import Path
import shutil

st.set_page_config(
    page_title="Import des Données",
    page_icon=":material/download:",
    layout="wide"
)

st.title("Import des Données")

# Définir le dossier de sauvegarde des données
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Section Étudiants
st.subheader("1. Fichier Étudiants")

with st.expander("Format Excel attendu", expanded=False):
    st.info("""
    **Format requis :**
    - **7 colonnes** exactement
    
    **En-têtes de colonnes :**
    - id_eleve
    - nom
    - annee
    - id_binome
    - jour_preference
    - periode_stage
    - periode_stage_ext
    """)
    
    st.markdown("**Exemple :**")
    exemple_df = pd.DataFrame({
        'id_eleve': [1, 2, 3],
        'nom': ['Dupont Joe', 'Martin Paul', 'Durand Lucie'],
        'annee': ['DFASO1', 'DFASO2', 'DFTCC'],
        'id_binome': [2, 3, 4],
        'jour_preference': ['Lundi', 'Mardi', 'Mercredi'],
        'periode_stage': [1, 2, 3],
        'periode_stage_ext': [3, 4, 1]
    })
    st.dataframe(exemple_df)

etudiants_file = st.file_uploader(
    "Choisir un fichier",
    type=["xlsx", "csv"],
    key="etudiants"
)

existing_eleves = DATA_DIR / "eleves.csv"
if existing_eleves.exists():
    df = pd.read_csv(existing_eleves)
    st.success(f"Liste des étudiants importée avec succès : {len(df)} étudiants \n\n Vous trouverez les 10 premiers enregistrements ci-dessous.")
    st.dataframe(df.head(10))


if etudiants_file:
    df = pd.read_excel(etudiants_file) if etudiants_file.name.endswith('xlsx') else pd.read_csv(etudiants_file)
    
    # Vérifications
    expected_cols = ['id_eleve', 'nom', 'id_binome', 'jour_preference', 'annee', 'periode_stage', 'periode_stage_ext']
    expected_nb_cols = 7
    
    errors = []
    warnings = []
    
    # Vérifier le nombre de colonnes
    if len(df.columns) != expected_nb_cols:
        errors.append(f"Nombre de colonnes incorrect : {len(df.columns)} au lieu de {expected_nb_cols}")
    
    # Vérifier les noms de colonnes
    if list(df.columns) != expected_cols:
        errors.append(f"Colonnes attendues : {expected_cols}")
        errors.append(f"Colonnes trouvées : {list(df.columns)}")
    
    # Affichage des erreurs/warnings
    if errors:
        for error in errors:
            st.error(error)
    elif warnings:
        for warning in warnings:
            st.warning(warning)
    else:
        output_path = DATA_DIR / "eleves.csv"

        if output_path.exists():
            output_path.unlink()  # Supprimer l'ancien fichier s'il existe
        
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        st.success(f"Liste des étudiants importée avec succès : {len(df)} étudiants \n\n Vous trouverez les 10 premiers enregistrements ci-dessous.")
        st.dataframe(df.head(10))

st.markdown("---")

# Section Calendrier
st.subheader("2. Calendrier Universitaire")

with st.expander("Format Excel attendu", expanded=False):
    st.info("""
    **Format requis :**
    - **53 lignes** (semaines de l'année universitaire avec en-tête inclus)
    - **11 colonnes** exactement
    
    **Structure :**
    - Colonne 1 : Numéro de semaine (36 à 52, puis 1 à 35)
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
        expected_rows = 53
        expected_nb_cols = 11
        
        errors = []
        warnings = []
        
        # Vérifier le nombre de colonnes
        if len(df_cal.columns) != expected_nb_cols:
            errors.append(f"Nombre de colonnes incorrect : {len(df_cal.columns)} au lieu de {expected_nb_cols}")
        
        # Vérifier le nombre de lignes
        if len(df_cal) != expected_rows:
            errors.append(f"Nombre de lignes incorrect : {len(df_cal)} au lieu de {expected_rows}")
        
        # Vérifier la séquence des semaines (36-52, 1-35)
        if len(df_cal) == expected_rows:
            first_col = df_cal.iloc[:, 0]
            semaines_attendues = list(range(36, 53)) + list(range(1, 36))
            semaines_trouvees = first_col.tolist()
            if semaines_trouvees != semaines_attendues:
                warnings.append("L'ordre des semaines ne correspond pas à l'année universitaire (36-52, 1-35)")
        
        # Vérifier les valeurs dans les cellules
        valid_values = ['C', 'F', 'A', '', ' ', None]
        for col in df_cal.columns[1:]:  # Ignorer la colonne Semaine
            invalid = df_cal[col][~df_cal[col].isin(valid_values) & df_cal[col].notna()]
            if len(invalid) > 0:
                warnings.append(f"Colonne {col} contient des valeurs invalides : {invalid.unique().tolist()}")
        
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
