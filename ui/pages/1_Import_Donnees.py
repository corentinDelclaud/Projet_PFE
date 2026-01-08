import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Import Données",
    page_icon="",
    layout="wide"
)

st.title("Import des Données")

# Section Étudiants
st.subheader("1. Fichier Étudiants")

with st.expander("Format Excel attendu", expanded=False):
    st.info("""
    **Format requis :**
    - **301 lignes** (étudiants avec en-tête inclus)
    - **6 colonnes** exactement
    
    **En-têtes de colonnes :**
    - num_etudiant
    - annee
    - num_etudiant_binome
    - jour_preference
    - periode_stage
    - periode_stage_externe
    """)
    
    st.markdown("**Exemple :**")
    exemple_df = pd.DataFrame({
        'num_etudiant': [1, 2, 3],
        'annee': ['DFASO1', 'DFASO2', 'DFTCC'],
        'num_etudiant_binome': [2, 3, 4],
        'jour_preference': ['Lundi', 'Mardi', 'Mercredi'],
        'periode_stage': [1, 2, 3],
        'periode_stage_externe': [3, 4, 1]
    })
    st.dataframe(exemple_df)

etudiants_file = st.file_uploader(
    "Choisir un fichier",
    type=["xlsx", "csv"],
    key="etudiants"
)

if etudiants_file:
    df = pd.read_excel(etudiants_file) if etudiants_file.name.endswith('xlsx') else pd.read_csv(etudiants_file)
    
    # Vérifications
    expected_cols = ['numero_etudiant', 'nom', 'numero_etudiant_binome', 'jour_preference', 'annee']
    expected_rows = 301
    expected_nb_cols = 5
    
    errors = []
    warnings = []
    
    # Vérifier le nombre de colonnes
    if len(df.columns) != expected_nb_cols:
        errors.append(f"Nombre de colonnes incorrect : {len(df.columns)} au lieu de {expected_nb_cols}")
    
    # Vérifier les noms de colonnes
    if list(df.columns) != expected_cols:
        errors.append(f"Colonnes attendues : {expected_cols}")
        errors.append(f"Colonnes trouvées : {list(df.columns)}")
    
    # Vérifier le nombre de lignes
    if len(df) != expected_rows:
        warnings.append(f"Nombre de lignes : {len(df)} (attendu : {expected_rows})")
    
    # Affichage des erreurs/warnings
    if errors:
        for error in errors:
            st.error(error)
    elif warnings:
        for warning in warnings:
            st.warning(warning)
        st.success(f"{len(df)} étudiants importés")
        st.dataframe(df.head(10))
    else:
        st.success(f"{len(df)} étudiants importés (validation OK)")
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

calendrier_file = st.file_uploader(
    "Choisir un fichier",
    type=["xlsx", "csv"],
    key="calendrier"
)

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
