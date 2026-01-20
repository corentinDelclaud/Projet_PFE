"""
parameter.py - Initialisation et chargement des données avant la création du modèle
"""
import sys
import os
import csv

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.discipline import discipline
from classes.eleve import eleve
from classes.vacation import vacation
from classes.cours import cours
from classes.stage import stage
from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau
from Projet_PFE.src.classes.enum.demijournee import Periode


def initialize_disciplines():
    """Initialise les disciplines avec leurs paramètres"""
    poly = discipline(1, "Polyclinique", ["A101"] * 10, [20,20,20,20,20,20,20,20,20,20], True, [52,52,52], [True]*10,[4,5,6])
    paro = discipline(2, "Parodontologie", ["A102"] * 10, [0,4,4,4,4,4,4,4,4,4], False, [6,6,6], [False, True, True, True, True, True, True, True, True, True],[4,5,6])
    como = discipline(3, "Comodulation", ["A103"] * 10, [3,3,3,3,3,3,0,0,3,3], False, [6,6,6] , [True, True, True, True, True, True, False, False, True, True],[4,5,6])
    pedo_soins = discipline(4, "Pédodontie Soins", ["A104"] * 10, [10,0,0,0,20,20,20,0,20,0], True, [12,12,12], [True]*10,[4,5,6])
    odf = discipline(5, "Orthodontie", ["A105"] * 10, [3] * 10, False, [4,4,4], [True]*10,[5])
    occl = discipline(6, "Occlusodontie", ["A106"] * 10, [4,0,4,0,0,0,4,0,4,0], False, [3,0,0], [True, False, True, False, False, False, True, False, True, False],[4])
    ra = discipline(7, "Radiologie", ["A107"] * 10, [4] * 10, False, [9,8,0], [True]*10,[4,5])
    ste = discipline(8, "Stérilisation", ["A108"] * 10, [1] * 10, False, [3,2,0], [True]*10,[4,5,6])
    pano = discipline(9, "Panoramique", ["A109"] * 10, [0,1,0,1,0,1,0,1,0,1,0,1] * 10, False, [0,3,3], [True]*10,[5,6])
    urg = discipline(10, "Urgence", ["A110"] * 10, [12] * 10, False, [20,20,20], [True]*10,[4,5,6])
    pedo_urg = discipline(11, "Pédodontie Urgences", ["A111"] * 10, [2] * 10, False, [0,1,1], [True]*10,[5,6])
    bloc = discipline(12, "BLOC", ["A112"] * 10, [0,0,2,0,0,0,2,0,0,0], False, [0,1,1], [False,False,True,False,False,False,True,False,False,False],[5,6])
    sp = discipline(13, "Soins spécifiques", ["A113"] * 10, [1,0,0,0,0,0,0,0,0,0], False, [0,0,0], [True,False,False,False,False,False,False,False,False,False],[5,6])   

    poly.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
    paro.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, True, True, True, True, True, True, True, True])
    como.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, False, False, True, True])
    pedo_soins.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, False, False, False, True, True, True, False, True, False])
    odf.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, True, True, True, False, False, False, True])
    occl.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, False, True, False, False, False, True, False, True, False])
    ra.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
    ste.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
    pano.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, True, False, True, False, True, False, True])
    urg.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True, True, True, True, True, True, True, True, True, True])
    pedo_urg.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [False, True, False, False, False, False, False, True, False, True])
    bloc.multiple_modif_presence([0,1,2,3,4,5,6,7,8,9], [True,False,True,False,False,False,True,False,False,False])

    print("Discipline reels charges avec succes.")
    
    return [poly, paro, como, pedo_soins, odf, occl, ra, ste, pano, urg, pedo_urg, bloc, sp]


def load_students(eleves_csv='eleves_with_code.csv'):
    """Charge les élèves depuis le fichier CSV"""
    eleves = []
    eleves_by_niveau = {
        niveau.DFAS01: [],
        niveau.DFAS02: [],
        niveau.DFTCC: []
    }

    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', eleves_csv)
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pref = jour_pref[row["jour_preference"]] 
                niv = niveau[row["annee"]]
                
                new_eleve = eleve(
                    id_eleve=int(row["id_eleve"]),
                    nom=row["code"],
                    id_binome=int(row["id_binome"]),
                    jour_preference=pref,
                    annee=niv
                )
                new_eleve.periode_stage = int(row.get("periode_stage", 0))
                new_eleve.periode_stage_ext = int(row.get("periode_stage_ext", 0))
                
                eleves.append(new_eleve)
                eleves_by_niveau[niv].append(new_eleve)
                
        print(f"Chargement réussi : {len(eleves)} élèves chargés depuis {csv_path}")
        return eleves, eleves_by_niveau
        
    except FileNotFoundError:
        print(f"Erreur : Le fichier {csv_path} est introuvable.")
        sys.exit(1)
    except KeyError as e:
        print(f"Erreur de format dans le CSV (Enum inconnu) : {e}")
        sys.exit(1)


def load_stages(stages_csv='mock_stages.csv'):
    """Charge les stages depuis le fichier CSV"""
    stages_lookup = {}
    stages_csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', stages_csv)
    
    try:
        with open(stages_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row["pour_niveau"], int(row["periode"]))
                if key not in stages_lookup:
                    stages_lookup[key] = []
                stages_lookup[key].append({
                    "nom": row["nom_stage"],
                    "debut": int(row["deb_semaine"]),
                    "fin": int(row["fin_semaine"]),
                    "niveau_obj": niveau[row["pour_niveau"]]
                })
        print("Configuration des stages chargée avec succès.")
        return stages_lookup
        
    except FileNotFoundError:
        print(f"Attention: Fichier stages.csv introuvable ({stages_csv_path}).")
        return {}


def assign_stages_to_students(eleves, stages_lookup):
    """Assigne les stages aux élèves en fonction de leur période"""
    stages_eleves = {}
    
    for el in eleves:
        p_id = getattr(el, 'periode_stage', 0)
        if p_id > 0:
            key = (el.annee.name, p_id)
            if key in stages_lookup:
                stage_data_list = stages_lookup[key]
                user_stages = []
                for sd in stage_data_list:
                    new_st = stage(sd["nom"], sd["debut"], sd["fin"], sd["niveau_obj"], p_id)
                    user_stages.append(new_st)
                
                stages_eleves[el.id_eleve] = user_stages
    
    return stages_eleves


def generate_vacations():
    """Génère les créneaux horaires (vacations) pour l'année universitaire"""
    vacations = []
    weeks_range = list(range(34, 53)) + list(range(1, 34))

    for semaine in weeks_range: 
        for jour in range(0, 5):  # Lundi (0) à Vendredi (4)
            for p in Periode:
                vacations.append(vacation(semaine, jour, p))
    
    return vacations


def load_calendars(calendrier_DFAS01_csv='mock_calendrier_DFAS01.csv',
                   calendrier_DFAS02_csv='mock_calendrier_DFASS02.csv',
                   calendrier_DFTCC_csv='mock_calendrier_DFTCC.csv'):
    """Charge les calendriers d'indisponibilités pour chaque niveau"""
    calendar_unavailability = {
        niveau.DFAS01: set(),
        niveau.DFAS02: set(),
        niveau.DFTCC: set()
    }

    calendar_files = {
        niveau.DFAS01: calendrier_DFAS01_csv,
        niveau.DFAS02: calendrier_DFAS02_csv,
        niveau.DFTCC: calendrier_DFTCC_csv
    }

    print("Chargement des calendriers...")
    for niv, filename in calendar_files.items():
        cal_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', filename)
        try:
            with open(cal_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        s_val = row.get("Semaine")
                        if not s_val:
                            continue
                        if s_val.upper().startswith("S"):
                            s_val = s_val[1:]
                        
                        semaine = int(s_val)
                        
                        for i in range(1, 11):
                            col_k = str(i)
                            val = (row.get(col_k) or "").strip()
                            if val:
                                calendar_unavailability[niv].add((semaine, i - 1))
                    except ValueError:
                        continue
            print(f"  - Calendrier {niv.name} chargé ({len(calendar_unavailability[niv])} indisponibilités).")

        except FileNotFoundError:
            print(f"Attention: Calendrier introuvable {cal_path}")
    
    return calendar_unavailability
