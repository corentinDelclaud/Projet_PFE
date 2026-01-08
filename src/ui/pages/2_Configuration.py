import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Configuration",
    page_icon="",
    layout="wide"
)

st.title("Configuration du Planning")

# Initialisation du state pour stocker les disciplines et les stages
if "disciplines" not in st.session_state:
    st.session_state.disciplines = []
if "stages" not in st.session_state:
    st.session_state.stages = []

st.subheader("1. Gestion des disciplines")
st.info("Ajoutez ou supprimez les disciplines")

# Formulaire d'ajout
with st.form("ajout_discipline", clear_on_submit=True):
    st.markdown("##### Ajouter une nouvelle discipline")

    # Informations générales
    nom_discipline = st.text_input("Nom de la discipline", placeholder="Ex: Prothèse, Parodontologie...")
    en_binome = st.checkbox("Travail en binôme")
    quota_par_etudiant = st.number_input("Quota par étudiant", min_value=1, step=1, value=1)

    st.markdown("---")
    st.markdown("**Configuration par vacation** (demi-journées 1 à 10)")
    st.caption("Pour chaque vacation, indiquez si l'UIC est présent, le nom de la salle et le nombre de fauteuils disponibles.")

    # Configuration par vacation
    vacations_data = []
    
    # Créer 5 lignes de 2 vacations chacune (Lun-Ven, matin-après-midi)
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    periodes = ["Matin", "Après-midi"]
    
    for idx_jour, jour in enumerate(jours):
        st.markdown(f"**{jour}**")
        col1, col2 = st.columns(2)
        
        for idx_periode, periode in enumerate(periodes):
            vacation_num = idx_jour * 2 + idx_periode + 1
            col = col1 if idx_periode == 0 else col2
            
            with col:
                st.markdown(f"*Vacation {vacation_num} ({periode})*")
                presence = st.checkbox(
                    f"UIC présent",
                    value=False,
                    key=f"presence_{vacation_num}"
                )
                
                salle = st.text_input(
                    f"Nom de la salle",
                    key=f"salle_{vacation_num}",
                    placeholder=f"Ex: Salle {vacation_num}"
                )
                fauteuils = st.number_input(
                    f"Nombre de fauteuils",
                    min_value=1,
                    step=1,
                    value=1,
                    key=f"fauteuils_{vacation_num}"
                )
                
                # On enregistre seulement si présence cochée
                vacations_data.append({
                    "vacation": vacation_num,
                    "presence": presence,
                    "salle": salle if presence else "",
                    "fauteuils": fauteuils if presence else 0
                })

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
            "quota_par_etudiant": quota_par_etudiant,
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
                st.write(f"2. Quota par étudiant : {d['quota_par_etudiant']}")
            
            with col_vacations:
                st.markdown("**Configuration des vacations**")
                
                # Créer un DataFrame pour afficher les vacations
                vacations_actives = [v for v in d['vacations'] if v['presence']]
                
                if vacations_actives:
                    df_vac = pd.DataFrame(vacations_actives)
                    df_vac = df_vac.rename(columns={
                        'vacation': 'Vacation',
                        'salle': 'Salle',
                        'fauteuils': 'Fauteuils'
                    })
                    df_vac = df_vac[['Vacation', 'Salle', 'Fauteuils']]
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


st.markdown("---")

st.subheader("2. Gestion des stages")
st.info("Configurez les périodes de stage")

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
    
    submitted_stage = st.form_submit_button("Ajouter le stage")

# Gestion de l'ajout de stage
if submitted_stage:
    if not nom_stage.strip():
        st.error("Veuillez renseigner le nom du stage.")
    elif date_fin < date_debut:
        st.error("La date de fin doit être postérieure à la date de début.")
    else:
        # Ajout dans le state
        st.session_state.stages.append({
            "numero_periode": numero_periode,
            "nom_stage": nom_stage,
            "date_debut": date_debut,
            "date_fin": date_fin
        })
        st.success(f"Stage '{nom_stage}' ajouté avec succès !")

# Affichage des stages enregistrés
if st.session_state.stages:
    st.subheader("Stages enregistrés")

    # Ajoute de titre de colonnes
    col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1.5, 1.5, 0.8])
    with col1:
        st.markdown("**Période**")
    with col2:
        st.markdown("**Nom du stage**")
    with col3:
        st.markdown("**Date de début**")
    with col4:
        st.markdown("**Date de fin**")
    with col5:
        st.markdown("**Actions**")

    # Trier par numéro de période
    stages_tries = sorted(st.session_state.stages, key=lambda x: x['numero_periode'])
    
    for idx, stage in enumerate(stages_tries):
        col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1.5, 1.5, 0.8])
        with col1:
            st.markdown(f"**{stage['numero_periode']}**")
        with col2:
            st.write(stage['nom_stage'])
        with col3:
            st.write(f"{stage['date_debut'].strftime('%d/%m/%Y')}")
        with col4:
            st.write(f"{stage['date_fin'].strftime('%d/%m/%Y')}")
        with col5:
            if st.button("Supprimer", key=f"delete_stage_{idx}", type="primary"):
                # Retrouver l'index réel dans la liste non triée
                real_idx = st.session_state.stages.index(stage)
                st.session_state.stages.pop(real_idx)
                st.rerun()
else:
    st.warning("Aucun stage enregistré. Ajoutez-en un ci-dessus.")

