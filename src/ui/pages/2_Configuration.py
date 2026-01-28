from operator import attrgetter
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Configuration",
    page_icon=":material/settings:",
    layout="wide"
)

st.title("Configuration du Planning")

# Définir le dossier pour stocker les données de configuration
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
STAGES_CSV = DATA_DIR / "stages.csv"
PERIODES_CSV = DATA_DIR / "periodes.csv"

# Initialisation du state pour stocker les disciplines et les stages
if "disciplines" not in st.session_state:
    st.session_state.disciplines = []
if "stages" not in st.session_state:
    # Charger les stages existants depuis le CSV s'il existe
    if STAGES_CSV.exists():
        df_stages = pd.read_csv(STAGES_CSV)
        st.session_state.stages = df_stages.to_dict('records')
    else:
        st.session_state.stages = []
if "periodes" not in st.session_state:
    # Charger les périodes existantes depuis le CSV s'il existe
    if PERIODES_CSV.exists():
        df_periodes = pd.read_csv(PERIODES_CSV)
        st.session_state.periodes = df_periodes.to_dict('records')
    else:
        st.session_state.periodes = []

st.subheader("1. Gestion des disciplines")
st.caption("Ajoutez ou supprimez les disciplines")

# Formulaire d'ajout
with st.form("ajout_discipline", clear_on_submit=True):
    st.markdown("##### Ajouter une nouvelle discipline")

    # Informations générales
    nom_discipline = st.text_input("Nom de la discipline", placeholder="Ex: Prothèse, Parodontologie...")
    en_binome = st.checkbox("Travail en binôme")
    jour_pref = st.checkbox("Considérer le jour préféré")
    remplissage_salle = st.checkbox("Remplir complètement les salles")
    st.markdown("**Configuration des vacations** (demi-journées 1 à 10)")
    st.caption("Pour chaque vacation, indiquez si l'UIC est présent, le nom de la salle et le nombre d'élèves nécessaires.")

    # Configuration par vacation
    vacations_data = []
    
    # Créer 2 lignes (matin/après-midi) pour chaque jour (lundi à vendredi en colon)
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    periodes = ["Matin", "Après-midi"]

    cols = st.columns(5)
    for jours in enumerate(jours):
        with cols[jours[0]]:
            st.markdown(f"**{jours[1]}**")

    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"] 

    for idx_periode, periode in enumerate(periodes):
        st.caption(f"**{periode}*")
        cols = st.columns(5)
        
        for idx_jour, jour in enumerate(jours):
            vacation_num = idx_jour * 2 + idx_periode + 1
            
            with cols[idx_jour]:
                presence = st.checkbox(
                    f"UIC présent",
                    value=False,
                    key=f"presence_{vacation_num}"
                )
            
                eleves = st.number_input(
                    f"Nombre de disponibilités",
                    min_value=1,
                    step=1,
                    value=1,
                    key=f"eleves_{vacation_num}"
                )
                
                # On enregistre seulement si présence cochée
                vacations_data.append({
                    "vacation": vacation_num,
                    "presence": presence,
                    "eleves": eleves if presence else 0
                })

    st.markdown("---")
    st.markdown("**Configurations optionnelles**")
    st.caption("Cochez les options que vous souhaitez activer pour cette discipline")

    # Sélection des niveaux en cochant les cases sur la même ligne
    niveaux_possibles = ["DFAS01", "DFAS02", "DFTCC"]
    
    # Organisation en 2 colonnes principales
    col_gauche, col_droite = st.columns(2)
    
    # COLONNE GAUCHE
    with col_gauche:
        # 1. Niveaux concernés et quotas
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 1. Niveaux et quotas")
        with col_check:
            use_quotas = st.checkbox("Activer", key="use_quotas")
        
        st.caption("Sélectionnez les niveaux concernés par cette discipline et indiquez le quota minimum pour l'année pour chaque niveau")
        niveaux_selectionnes = []
        quota_par_niveau = {}
        
        for niveau in niveaux_possibles:
            col_check, col_quota = st.columns([0.4, 0.6])
            with col_check:
                if st.checkbox(niveau, key=f"niveau_{niveau}"):
                    niveaux_selectionnes.append(niveau)
            with col_quota:
                quota = st.number_input(
                    f"Quota minimum pour {niveau}",
                    min_value=0,
                    step=1,
                    value=0,
                    key=f"quota_{niveau}",
                    label_visibility="collapsed"
                )
                quota_par_niveau[niveau] = quota

        st.markdown("---")
        
        # 2. Fréquence des vacations
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 2. Fréquence des vacations")
        with col_check:
            use_freq_vacations = st.checkbox("Activer", key="use_freq_vacations")
        
        # fréquence de semaines pour les vacations
        freq_vacations = st.number_input(
            "Fréquence de semaines des vacations pour l'élève ( 1 = chaque semaine, 2 = une semaine sur deux, ... )",
            min_value=0,
            step=1,
            value=0,
            key="frequence_semaines"
        )

        st.markdown("---")

        # 3. Nombre de vacations par semaine
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 3. Vacations par semaine")
        with col_check:
            use_nb_vacations_semaine = st.checkbox("Activer", key="use_nb_vacations_semaine")
        
        # nombre de vacations par semaine 
        nb_vacations_par_semaine = st.number_input(
            "Nombre de vacations à faire par semaine pour l'élève",
            min_value=0,
            step=1,
            value=0,
            key="nb_vacations_semaine"
        )

        st.markdown("---")

        # 4. Vacations par semestre
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 4. Vacations par semestre")
        with col_check:
            use_nb_semestre = st.checkbox("Activer", key="use_nb_semestre")
        
        # nombre de vacations nécessaires pour chaque semestre (il y en a 2 par an) sur la meme ligne
        nb_semestres = 2
        semestre_cols = st.columns(nb_semestres)
        for semestre in range(1, nb_semestres + 1):
            with semestre_cols[semestre - 1]:
                nb_vacations_semestre = st.number_input(
                    f"Nombre de vacations nécessaires pour le semestre {semestre}",
                    min_value=0,
                    step=1,
                    value=0,
                    key=f"nb_vacations_semestre_{semestre}"
                )

    # COLONNE DROITE
    with col_droite:
        # 5. Jours consécutifs
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 5. Jours consécutifs")
        with col_check:
            use_jours_consecutifs = st.checkbox("Activer", key="use_jours_consecutifs")
        
        # Paires de jours consécutifs autorisés (ex: Lundi-Mardi, Mercredi-Jeudi)
        jours_consecutifs = st.multiselect(
            "Paires de jours consécutifs autorisés",
            options=[
                "Lundi-Mardi",
                "Mardi-Mercredi",
                "Mercredi-Jeudi",
                "Jeudi-Vendredi",
                "Vendredi-Lundi"
            ],
            key="jours_consecutifs"
        )

        st.markdown("---")

        # 6. Mixité des niveaux
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 6. Mixité des niveaux")
        with col_check:
            use_mixite = st.checkbox("Activer", key="use_mixite")
        st.caption("La mixité des niveaux permet de définir des contraintes sur la composition des groupes d'élèves lors des vacations.")
        
        # Mixité des niveaux dans une même vacation (0: pas de contraintes, 1: exactement 1 élève de chaque niveau, 2: au moins 2 niveaux différents, 3: tous du meme niveau)
        mixite_options = {
            1: "Exactement 1 élève de chaque niveau",
            2: "Au moins 2 niveaux différents",
            3: "Tous du même niveau"
        }
        mixite_selection = st.selectbox(
            "Mixité des niveaux dans une même vacation",
            options=list(mixite_options.keys()),
            format_func=lambda x: mixite_options[x],
            key="mixite_niveaux"
        )

        st.markdown("---")

        # 7. Évitement des répétitions
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 7. Évitement répétitions")
        with col_check:
            use_evitement = st.checkbox("Activer", key="use_evitement")
        # Donner une explication simple et claire
        st.caption("L'évitement des répétitions permet de limiter le nombre de fois qu'un élève peut avoir la même vacation consécutivement.")
        
        # éviter les répétitions (pas X fois de suite la même vacation pour un élève (X = 2 à 5)) 
        evitement_repetitions = st.number_input(
            "Éviter les répétitions (pas X fois de suite la même vacation pour un élève)",
            min_value=0,
            max_value=5,
            step=1,
            value=0,
            key="evitement_repetitions"
        )

        st.markdown("---")

        # 8. Ordre de priorité
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 8. Ordre de priorité")
        with col_check:
            use_ordre_priorite = st.checkbox("Activer", key="use_ordre_priorite")
        
        # Ordre de priorité des niveaux (ex: DFAS01 > DFAS02 > DFTCC) un dropdown avec les niveaux dans l'ordre
        st.caption("Ordre de priorité des niveaux")
        ordre_niveaux = []
        ordre_cols = st.columns(len(niveaux_possibles))
        for i in range(len(niveaux_possibles)):
            with ordre_cols[i]:
                niveau_choisi = st.selectbox(
                    f"Niveau {i + 1}",
                    options=niveaux_possibles,
                    key=f"ordre_niveau_{i}"
                )
                ordre_niveaux.append(niveau_choisi)

        st.markdown("---")

        # 9. Règles de remplacement
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 9. Règles de remplacement")
        with col_check:
            use_remplacement = st.checkbox("Activer", key="use_remplacement")
        
        # Règles de remplacement (ex: si un élève DFAS01 est indisponible, il peut être remplacé par un DFAS02, puis DFTCC il faut indiquer aussi le nombre d'élèves maximum par niveau qui peuvent remplacer)
        st.caption("Règles de remplacement")

        col_niveau_absent, col_niveau_remplacant, col_quota = st.columns(3)
        with col_niveau_absent:
            st.write("**Niveau absent**")
        with col_niveau_remplacant:
            st.write("**Remplacer par**")
        with col_quota:
            st.write("**Quota**")

        regles_remplacement = {}

        for i in range(len(niveaux_possibles)):
            col_niveau_absent, col_niveau_remplacant, col_quota = st.columns([0.2, 0.4, 0.4])
            
            with col_niveau_absent:
                st.caption(f"**{niveaux_possibles[i]}** :")
            
            with col_niveau_remplacant:
                niveau_remplacant = st.selectbox(
                    "Remplacer par",
                    options=[n for n in niveaux_possibles if n != niveaux_possibles[i]],
                    key=f"niveau_remplacant_{i}",
                    label_visibility="collapsed" 
                )
            
            with col_quota:
                quota_remplacement = st.number_input(
                    "Quota de remplacement",
                    min_value=1,
                    step=1,
                    value=1,
                    key=f"quota_remplacement_{i}",
                    label_visibility="collapsed" 
                )
            
            regles_remplacement[niveaux_possibles[i]] = {
                'niveau_remplacant': niveau_remplacant,
                'quota': quota_remplacement
            }

     # Soumission du formulaire
    submitted = st.form_submit_button("Ajouter la discipline")

# Gestion de l'ajout
if submitted:
    # Vérification que le nom de la discipline est renseigné
    if not nom_discipline.strip():
        st.error("Veuillez renseigner le nom de la discipline.")
    else:
        # Génération automatique du code discipline
        code_discipline = f"{len(st.session_state.disciplines) + 1}"

        # Ajout dans le state
        st.session_state.disciplines.append({
            "code_discipline": code_discipline,
            "nom_discipline": nom_discipline,
            "en_binome": en_binome,
            "quota_par_niveau": quota_par_niveau,
            "vacations": vacations_data
        })

        st.success(f"Discipline '{nom_discipline}' ajoutée avec succès !")

# Affichage tableau récapitulatif
if st.session_state.disciplines:
    st.subheader("Disciplines enregistrées")

    for idx, d in enumerate(st.session_state.disciplines):
        with st.expander(f"**{d['code_discipline']}. {d['nom_discipline']}**"):
            col_info, col_vacations, col_actions = st.columns([1, 2, 0.5])
            
            with col_info:
                st.markdown("**Informations générales**")
                st.write(f"1. Travail en binôme : {'Oui' if d['en_binome'] else 'Non'}")
                st.write(f"2. Quota par étudiant : {d['quota_par_niveau']}")
            
            with col_vacations:
                st.markdown("**Configuration des vacations**")
                
                # Créer un DataFrame pour afficher les vacations
                vacations_actives = [v for v in d['vacations'] if v['presence']]
                
                if vacations_actives:
                    df_vac = pd.DataFrame(vacations_actives)
                    df_vac = df_vac.rename(columns={
                        'vacation': 'Vacation',
                        'salle': 'Salle',
                        'eleves': 'Élèves'
                    })
                    df_vac = df_vac[['Vacation', 'Salle', 'Élèves']]
                    st.dataframe(df_vac, hide_index=True, use_container_width=True)
                else:
                    st.warning("Aucune vacation configurée pour cette discipline.")
            
            with col_actions:
                st.markdown("**Actions**")
                if st.button("Supprimer", key=f"delete_{idx}", type="primary"):
                    st.session_state.disciplines.pop(idx)
                    st.rerun()
else:
    st.warning("Aucune discipline enregistrée. Ajoutez-en une ci-dessus.")

# Fonction pour sauvegarder les périodes dans le CSV
def save_periodes_to_csv():
    if st.session_state.periodes:
        df = pd.DataFrame(st.session_state.periodes)
        # Réorganiser les colonnes selon le format attendu
        df = df[['id_periode', 'deb_semaine', 'fin_semaine', 'periode']]
        df.to_csv(PERIODES_CSV, index=False)
    else:
        # Si plus de périodes, créer un CSV vide avec les headers
        df = pd.DataFrame(columns=['id_periode', 'deb_semaine', 'fin_semaine', 'periode'])
        df.to_csv(PERIODES_CSV, index=False)

# Fonction pour sauvegarder les stages dans le CSV
def save_stages_to_csv():
    if st.session_state.stages:
        df = pd.DataFrame(st.session_state.stages)
        # Réorganiser les colonnes selon le format attendu
        df = df[['id_stage', 'nom_stage', 'deb_semaine', 'fin_semaine', 'pour_niveau', 'periode']]
        df.to_csv(STAGES_CSV, index=False)
    else:
        # Si plus de stages, créer un CSV vide avec les headers
        df = pd.DataFrame(columns=['id_stage', 'nom_stage', 'deb_semaine', 'fin_semaine', 'pour_niveau', 'periode'])
        df.to_csv(STAGES_CSV, index=False)

# Fonction pour convertir une date en numéro de semaine
def date_to_week_number(date):
    return date.isocalendar()[1]

st.markdown("---")
st.subheader("2. Gestion des périodes")
st.caption("Définissez les périodes de stage pour l'année universitaire")
with st.form("gestion_periodes", clear_on_submit=True):
    st.markdown("##### Ajouter une nouvelle période de stage")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        numero_periode = st.number_input("Numéro de la période", min_value=0, max_value=6, step=1, value=1)

    with col2:
        date_debut = st.date_input("Date de début")
    with col3:
        date_fin = st.date_input("Date de fin") 
    submitted_periode = st.form_submit_button("Ajouter la période")

# Gestion de l'ajout de période
if submitted_periode:
    if date_fin < date_debut:
        st.error("La date de fin doit être postérieure à la date de début.")
    if any(p['periode'] == numero_periode for p in st.session_state.periodes):
        st.error(f"La période {numero_periode} existe déjà.")
    else:
        # Générer un nouvel ID (max ID existant + 1)
        max_id = max([s['id_periode'] for s in st.session_state.periodes], default=0)
        max_id += 1
        
        st.session_state.periodes.append({
            'id_periode': max_id,
            'deb_semaine': date_debut,
            'fin_semaine': date_fin,
            'periode': numero_periode
        })
        
        # Sauvegarder dans le CSV
        save_periodes_to_csv()
        
        st.success(f"Période {numero_periode} ajoutée avec succès !")

# Affichage des périodes enregistrées
if st.session_state.periodes:
    st.subheader("Périodes enregistrées")
    periodes_tries = sorted(st.session_state.periodes, key=lambda x: x['periode'])

    # Ajoute de titre de colonnes
    col1, col2, col3, col4, col5 = st.columns([0.5, 1.5, 1.5, 1.5, 0.8])
    with col1:
        st.markdown("**Période**")
    with col2:
        st.markdown("**Date de début**")
    with col3:
        st.markdown("**Date de fin**")
    with col4:
        st.markdown("")
    with col5:
        st.markdown("**Actions**")

    for idx, periode in enumerate(periodes_tries):
        col1, col2, col3, col4, col5 = st.columns([0.5, 1.5, 1.5, 1.5, 0.8])
        with col1:
            st.markdown(f"**{periode['periode']}**")
        with col2:
            st.write(f"{periode['deb_semaine']}")
        with col3:
            st.write(f"{periode['fin_semaine']}")
        with col4:
            st.write("")
        with col5:
            if st.button("Supprimer", key=f"delete_periode_{periode['id_periode']}", type="primary"):
                # Retrouver l'index réel dans la liste non triée
                real_idx = st.session_state.periodes.index(periode)
                st.session_state.periodes.pop(real_idx)
                save_periodes_to_csv()
                st.rerun()
else:
    st.warning("Aucune période enregistrée. Ajoutez-en une ci-dessus.")

st.markdown("---")
st.subheader("3. Gestion des stages")
st.caption("Configurez les périodes de stage")

# Formulaire d'ajout de stage
with st.form("ajout_stage", clear_on_submit=True):
    st.markdown("##### Ajouter une nouvelle période de stage")
    
    col1, col2 = st.columns(2)
    
    with col1:
        numero_periode = st.number_input("Numéro de la période", min_value=1, max_value=4, step=1, value=1)
        nom_stage = st.text_input("Nom du stage", placeholder="Ex: Stage clinique P1, Stage hospitalier...")
    
    with col2:
        date_debut = st.date_input("Date de début")
        date_fin = st.date_input("Date de fin")

    annee_universitaire = st.multiselect("Année universitaire", ["DFAS01", "DFAS02", "DFTCC"])
    
    submitted_stage = st.form_submit_button("Ajouter le stage")

# Gestion de l'ajout de stage, add multiselect year one for each year
if submitted_stage:
    if not nom_stage.strip():
        st.error("Veuillez renseigner le nom du stage.")
    elif date_fin < date_debut:
        st.error("La date de fin doit être postérieure à la date de début.")
    elif not annee_universitaire:
        st.error("Veuillez sélectionner au moins une année universitaire.")
    else:
        # Générer un nouvel ID (max ID existant + 1)
        max_id = max([s['id_stage'] for s in st.session_state.stages], default=0)
        
        # Convertir les dates en numéros de semaine
        semaine_debut = date_to_week_number(date_debut)
        semaine_fin = date_to_week_number(date_fin)
        
        # Ajouter pour chaque année sélectionnée
        for annee in annee_universitaire:
            max_id += 1
            st.session_state.stages.append({
                'id_stage': max_id,
                'nom_stage': nom_stage,
                'deb_semaine': semaine_debut,
                'fin_semaine': semaine_fin,
                'pour_niveau': annee,
                'periode': numero_periode
            })
        
        # Sauvegarder dans le CSV
        save_stages_to_csv()
        
        st.success(f"Stage '{nom_stage}' ajouté avec succès pour {', '.join(annee_universitaire)} !")


# Affichage des stages enregistrés
if st.session_state.stages:
    st.subheader("Stages enregistrés")

    # Ajoute de titre de colonnes
    col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 1.5, 1.5, 1.5, 0.8])
    with col1:
        st.markdown("**Période**")
    with col2:
        st.markdown("**Nom du stage**")
    with col3:
        st.markdown("**Date de début**")
    with col4:
        st.markdown("**Date de fin**")
    with col5:
        st.markdown("**Année universitaire**")
    with col6:
        st.markdown("**Actions**")

    # Trier par annee universitaire
    stages_tries = sorted(st.session_state.stages, key=lambda x: (x['pour_niveau'],x['periode']))
    
    for idx, stage in enumerate(stages_tries):
        col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 1.5, 1.5, 1.5, 0.8])
        with col1:
            st.markdown(f"**{stage['periode']}**")
        with col2:
            st.write(stage['nom_stage'])
        with col3:
            st.write(f"{stage['deb_semaine']}")
        with col4:
            st.write(f"{stage['fin_semaine']}")
        with col5:
            st.write(stage['pour_niveau'])
        with col6:
            if st.button("Supprimer", key=f"delete_stage_{stage['id_stage']}", type="primary"):
                # Retrouver l'index réel dans la liste non triée
                real_idx = st.session_state.stages.index(stage)
                st.session_state.stages.pop(real_idx)
                save_stages_to_csv()
                st.rerun()
else:
    st.warning("Aucun stage enregistré. Ajoutez-en un ci-dessus.")
