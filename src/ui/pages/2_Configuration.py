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
DISCIPLINES_CSV = DATA_DIR / "disciplines.csv"

# Initialisation du state pour stocker les disciplines et les stages
if "disciplines" not in st.session_state:
    # Charger les disciplines existantes depuis le CSV s'il existe
    if DISCIPLINES_CSV.exists():
        df_disciplines = pd.read_csv(DISCIPLINES_CSV)
        st.session_state.disciplines = df_disciplines.to_dict('records')
    else:
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

def save_disciplines_to_csv():
    if st.session_state.disciplines:
        df = pd.DataFrame(st.session_state.disciplines)
        # Réorganiser les colonnes selon le format attendu
        df = df[['id_discipline', 'nom_discipline', 'nb_eleve', 'en_binome', 'quota', 'presence', 'annee', 'frequence_vacations', 'nb_vacations_par_semaine', 'repartition_semestrielle', 'paire_jours', 'mixite_groupes', 'repartition_continuite', 'priorite_niveau', 'remplacement_niveau', 'take_jour_pref', 'be_filled']]
        df.to_csv(DISCIPLINES_CSV, index=False)
    else:
        # Si plus de disciplines, créer un CSV vide avec les headers
        df = pd.DataFrame(columns=['id_discipline', 'nom_discipline', 'nb_eleve', 'en_binome', 'quota', 'presence', 'annee', 'frequence_vacations', 'nb_vacations_par_semaine', 'repartition_semestrielle', 'paire_jours', 'mixite_groupes', 'repartition_continuite', 'priorite_niveau', 'remplacement_niveau',  'take_jour_pref', 'be_filled'])
        df.to_csv(DISCIPLINES_CSV, index=False)

st.subheader("1. Gestion des disciplines")
st.caption("Ajoutez ou supprimez les disciplines")
with st.form("ajout_discipline", clear_on_submit=True):
    st.markdown("##### Ajouter une nouvelle discipline")

    # Informations générales
    nom_discipline = st.text_input("Nom de la discipline", placeholder="Ex: Prothèse, Parodontologie...")
    en_binome = st.checkbox("Être en binôme")
    jour_pref = st.checkbox("Considérer le jour préféré")
    remplissage_salle = st.checkbox("Remplir complètement les salles")
    st.markdown("**Configuration des vacations** (demi-journées 1 à 10)")
    st.caption("Pour chaque vacation, indiquez si l'UIC est présent, le nom de la salle et le nombre d'élèves nécessaires.")
    
    # Créer 2 lignes (matin/après-midi) pour chaque jour (lundi à vendredi en colon)
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    periodes = ["Matin", "Après-midi"]

    cols = st.columns(5)
    for jours in enumerate(jours):
        with cols[jours[0]]:
            st.markdown(f"**{jours[1]}**")

    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"] 
    presence_uic = {}
    nb_dispo = {}

    for idx_periode, periode in enumerate(periodes):
        st.caption(f"**{periode}*")
        cols = st.columns(5)
        
        for idx_jour, jour in enumerate(jours):
            vacation_num = idx_jour * 2 + idx_periode + 1
            
            with cols[idx_jour]:
                presence_uic[vacation_num] = st.checkbox(
                    f"Présent UIC",
                    key=f"presence_{vacation_num}"
                )
                
                nb_dispo[vacation_num] = st.number_input(
                    f"Nombre de disponibilités",
                    min_value=0,
                    step=1,
                    value=0,
                    key=f"nb_dispo_{vacation_num}"
                )

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
        
        # 2. Fréquence des semaines
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 2. Fréquence des semaines")
        with col_check:
            use_freq_semaine = st.checkbox("Activer", key="use_freq_semaine")
        
        # fréquence de semaines pour les vacations
        freq_semaine = st.number_input(
            "Fréquence de semaines pour l'élève ( 1 = chaque semaine, 2 = une semaine sur deux, 3 = une semaine sur trois ... )",
            min_value=0,
            max_value=4,
            step=1,
            value=0,
            key="frequence_semaines"
        )

        st.markdown("---")

        # 3. Nombre de vacations par semaine
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 3. Nombre de vacations par semaine")
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

        # 4. Nombre de vacations par semestre
        col_title, col_check = st.columns([0.7, 0.3])
        with col_title:
            st.markdown("##### 4. Nombre de vacations par semestre")
        with col_check:
            use_nb_semestre = st.checkbox("Activer", key="use_nb_semestre")
        
        # nombre de vacations nécessaires pour chaque semestre (il y en a 2 par an) sur la meme ligne
        nb_vacations_par_semestre = {}
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
                nb_vacations_par_semestre[semestre] = nb_vacations_semestre

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
            "Paires de jours consécutifs autorisés (ex: Lundi-Mardi, Mercredi-Jeudi)",
            options=[
                "Lundi-Mardi",
                "Mardi-Mercredi",
                "Mercredi-Jeudi",
                "Jeudi-Vendredi",
                "Vendredi-Lundi"
            ],
            key="jours_consecutifs"
        )

        # Map les paires en tuples d'indices
        jours_consecutifs_indices = {
            "Lundi-Mardi": (0, 1),
            "Mardi-Mercredi": (1, 2),
            "Mercredi-Jeudi": (2, 3),
            "Jeudi-Vendredi": (3, 4),
            "Vendredi-Lundi": (4, 0)
        }

        jours_consecutifs = [jours_consecutifs_indices[jour] for jour in jours_consecutifs]

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
            st.markdown("##### 7. Évitement des répétitions")
        with col_check:
            use_evitement = st.checkbox("Activer", key="use_evitement")
        # Donner une explication simple et claire
        st.caption("L'évitement des répétitions permet de limiter le nombre de fois qu'un élève peut avoir la même vacation consécutivement.")
        
        # Contrainte de continuité (X,Y)  X : Éviter répétitions : 0 = Pas de contrainte 1 = Pas 2 fois de suite 2 = Pas 3 fois de suite 3 = Jamais plus de X fois (préciser X)  Y : distance en semaines pour la contrainte de continuité (ex: 12 semaines = 3 mois)
        evitement_repetitions_x = st.number_input(
            "Éviter les répétitions (pas X fois de suite la même vacation pour un élève)",
            min_value=0,
            max_value=4,
            step=1,
            value=0,
            key="evitement_repetitions_x"
        )

        evitement_repetitions_y = st.number_input(
            "Distance en semaines pour la contrainte de continuité (ex: 12 semaines = 3 mois)",
            min_value=0,
            step=1,
            value=0,
            key="evitement_repetitions_y"
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
    submitted_discipline = st.form_submit_button("Ajouter la discipline")

# Gestion de l'ajout d'une discipline
if submitted_discipline:
    # Vérification que le nom de la discipline est renseigné
    if not nom_discipline.strip():
        st.error("Veuillez renseigner le nom de la discipline.")
    else:
        # Génération automatique du code discipline
        code_discipline = f"{len(st.session_state.disciplines) + 1}"

        # Ajout dans le state
        st.session_state.disciplines.append({
            "id_discipline": code_discipline,
            "nom_discipline": nom_discipline,
            "nb_eleve": nb_dispo,
            "en_binome": en_binome,
            "quota": quota_par_niveau,
            "presence": presence_uic,
            "annee": niveaux_selectionnes,
            "frequence_vacations": freq_semaine,
            "nb_vacations_par_semaine": nb_vacations_par_semaine,
            "repartition_semestrielle": nb_vacations_par_semestre,
            "paire_jours": jours_consecutifs,
            "mixite_groupes": mixite_selection,
            "repartition_continuite": (evitement_repetitions_x, evitement_repetitions_y),
            "priorite_niveau": ordre_niveaux,
            "remplacement_niveau": regles_remplacement,
            "take_jour_pref": jour_pref,
            "be_filled": remplissage_salle
        })

        # Sauvegarde dans le CSV
        save_disciplines_to_csv()

        st.success(f"Discipline '{nom_discipline}' ajoutée avec succès !")

# Affichage tableau récapitulatif
if st.session_state.disciplines:
    st.subheader("Disciplines enregistrées")

    for idx, d in enumerate(st.session_state.disciplines):
        with st.expander(f"**{d['id_discipline']}. {d['nom_discipline']}**"):
            # Informations générales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"**Travail en binôme:** {'Oui' if d['en_binome'] else 'Non'}")
            with col2:
                st.write(f"**Jour préféré:** {'Oui' if d['take_jour_pref'] else 'Non'}")
            with col3:
                st.write(f"**Remplir salles:** {'Oui' if d['be_filled'] else 'Non'}")

            # Configuration des vacations
            vacation_data = []
            jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
            periodes = ["Matin", "Après-midi"]
            
            # Gérer le cas où presence et nb_eleve sont des chaînes
            presence = d.get('presence', {})
            nb_eleve = d.get('nb_eleve', {})
            
            # Convertir si c'est une chaîne (depuis CSV)
            if isinstance(presence, str):
                import ast
                try:
                    presence = ast.literal_eval(presence)
                except:
                    presence = {}
            
            if isinstance(nb_eleve, str):
                import ast
                try:
                    nb_eleve = ast.literal_eval(nb_eleve)
                except:
                    nb_eleve = {}
            
            for vacation_num in range(1, 11):
                jour_idx = (vacation_num - 1) // 2
                periode_idx = (vacation_num - 1) % 2
                
                vacation_data.append({
                    "Vacation": vacation_num,
                    "Jour": jours[jour_idx],
                    "Période": periodes[periode_idx],
                    "Présent UIC": presence[vacation_num],
                    "Nb disponibilités": nb_eleve.get(vacation_num, 0)
                })
            
            df_vacations = pd.DataFrame(vacation_data)
            st.dataframe(df_vacations, hide_index=True, use_container_width=True)   

            # Niveaux et quotas
            quota = d.get('quota', {})
            annee = d.get('annee', [])
            
            # Convertir si c'est une chaîne
            if isinstance(quota, str):
                import ast
                try:
                    quota = ast.literal_eval(quota)
                except:
                    quota = {}
            
            if isinstance(annee, str):
                import ast
                try:
                    annee = ast.literal_eval(annee)
                except:
                    annee = []
            
            if annee:
                quota_data = []
                for niveau in annee:
                    quota_data.append({
                        "Niveau": niveau,
                        "Quota": quota.get(niveau, 0)
                    })
                df_quota = pd.DataFrame(quota_data)
                st.dataframe(df_quota, hide_index=True, use_container_width=True)
            else:
                st.info("Aucun niveau sélectionné")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Fréquence des vacations
                freq = d.get('frequence_vacations', 0)
                if freq > 0:
                    st.write(f"**Fréquence des semaines:** {freq} semaine(s)")
                
                # Nombre de vacations par semaine
                nb_vac_semaine = d.get('nb_vacations_par_semaine', 0)
                if nb_vac_semaine > 0:
                    st.write(f"**Vacations par semaine:** {nb_vac_semaine}")
                
                # Répartition semestrielle
                repartition_sem = d.get('repartition_semestrielle', {})
                if isinstance(repartition_sem, str):
                    import ast
                    try:
                        repartition_sem = ast.literal_eval(repartition_sem)
                    except:
                        repartition_sem = {}
                
                if repartition_sem and any(v > 0 for v in repartition_sem.values()):
                    st.write("**Répartition semestrielle:**")
                    for sem, nb in repartition_sem.items():
                        if nb > 0:
                            st.write(f"  - Semestre {sem}: {nb} vacations")
                
                # Jours consécutifs
                paire_jours = d.get('paire_jours', [])
                if isinstance(paire_jours, str):
                    import ast
                    try:
                        paire_jours = ast.literal_eval(paire_jours)
                    except:
                        paire_jours = []
                
                if paire_jours:
                    jours_map = {
                        (0, 1): "Lundi-Mardi",
                        (1, 2): "Mardi-Mercredi",
                        (2, 3): "Mercredi-Jeudi",
                        (3, 4): "Jeudi-Vendredi",
                        (0, 4): "Vendredi-Lundi"
                    }
                    st.write("**Jours consécutifs autorisés:**")
                    for paire in paire_jours:
                        if isinstance(paire, tuple):
                            st.write(f"  - {jours_map.get(paire, str(paire))}")
            
            with col2:
                # Mixité des groupes
                mixite = d.get('mixite_groupes', 0)
                if mixite > 0:
                    mixite_options = {
                        1: "Exactement 1 élève de chaque niveau",
                        2: "Au moins 2 niveaux différents",
                        3: "Tous du même niveau"
                    }
                    st.write(f"**Mixité des groupes:** {mixite_options.get(mixite, 'Non défini')}")
                
                # Évitement des répétitions
                continuite = d.get('repartition_continuite', (0, 0))
                if isinstance(continuite, str):
                    import ast
                    try:
                        continuite = ast.literal_eval(continuite)
                    except:
                        continuite = (0, 0)
                
                if continuite[0] > 0:
                    st.write(f"**Évitement répétitions:** Pas {continuite[0]} fois de suite")
                    st.write(f"**Distance:** {continuite[1]} semaines")
                
                # Ordre de priorité
                priorite = d.get('priorite_niveau', [])
                if isinstance(priorite, str):
                    import ast
                    try:
                        priorite = ast.literal_eval(priorite)
                    except:
                        priorite = []
                
                if priorite:
                    st.write(f"**Ordre de priorité:** {' > '.join(priorite)}")
                
                # Règles de remplacement
                remplacement = d.get('remplacement_niveau', {})
                if isinstance(remplacement, str):
                    import ast
                    try:
                        remplacement = ast.literal_eval(remplacement)
                    except:
                        remplacement = {}
                
                if remplacement:
                    st.write("**Règles de remplacement:**")
                    for niveau, regle in remplacement.items():
                        if isinstance(regle, dict):
                            st.write(f"  - {niveau} → {regle.get('niveau_remplacant', 'N/A')} (quota: {regle.get('quota', 0)})")
            with col4:
                if st.button("Supprimer", key=f"delete_{idx}", type="primary"):
                    st.session_state.disciplines.pop(idx)
                    save_disciplines_to_csv()
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

        # Convert dates to week numbers
        semaine_debut = date_to_week_number(date_debut)
        semaine_fin = date_to_week_number(date_fin)
        
        st.session_state.periodes.append({
            'id_periode': max_id,
            'deb_semaine': semaine_debut,
            'fin_semaine': semaine_fin,
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
    col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1.5, 1.5, 0.8])
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
        col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1.5, 1.5, 0.8])
        with col1:
            st.markdown(f"**{periode['periode']}**")
        with col2:
            st.write(f"Semaine {periode['deb_semaine']}")
        with col3:
            st.write(f"Semaine {periode['fin_semaine']}")
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
