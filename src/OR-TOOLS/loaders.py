''' 
LOADERS - Adapté pour Model V5_03_C

Ce module de chargement reproduit exactement la logique de model_V5_03_C:
 - Disciplines hardcodées avec toutes les configurations
 - Chargement élèves depuis eleves_with_code.csv
 - Chargement stages avec stages_lookup (dict de listes de dicts)
 - Chargement calendriers avec (semaine, slot_idx) comme clé
 - Périodes hardcodées
 
'''
import sys
import os
import logging
import csv
import collections
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.discipline import discipline
from classes.eleve import eleve
from classes.stage import stage
from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau
from classes.enum.demijournee import DemiJournee
from classes.periode import Periode

logger = logging.getLogger(__name__)

class DataLoadError(Exception):
    """Exception personnalisée pour les erreurs de chargement"""
    pass

# =============================================================================
# DISCIPLINES HARDCODÉES (Configuration exacte du model_V5_03_C)
# =============================================================================

def load_disciplines() -> List[discipline]:
    """
    Charge les disciplines avec configuration hardcodée (identique à model_V5_03_C)
    
    Returns:
        List[discipline]: Liste des 13 disciplines configurées
    """
    logger.info("Chargement des disciplines (configuration hardcodée)...")
    
    # Instanciation des disciplines (Configuration issue de model_V5_03_C)
    poly = discipline(1, "Polyclinique", [20,20,20,20,20,20,20,20,20,20], True, [50,50,50], [True]*10,[4,5,6])
    paro = discipline(2, "Parodontologie", [0,4,4,4,4,4,4,4,4,4], False, [6,6,6], [False, True, True, True, True, True, True, True, True, True],[4,5,6])
    como = discipline(3, "Comodulation", [3,3,3,3,3,3,0,0,3,3], False, [6,6,6] , [True, True, True, True, True, True, False, False, True, True],[4,5,6])
    pedo_soins = discipline(4, "Pédodontie Soins", [10,0,0,0,20,20,20,0,20,0], True, [12,12,12], [True]*10,[4,5,6])
    odf = discipline(5, "Orthodontie", [3] * 10, False, [4,4,4], [True]*10,[5])
    occl = discipline(6, "Occlusodontie", [4,0,4,0,0,0,4,0,4,0], False, [3,0,0], [True, False, True, False, False, False, True, False, True, False],[4])
    ra = discipline(7, "Radiologie", [4] * 10, False, [9,8,0], [True]*10,[4,5])
    ste = discipline(8, "Stérilisation", [1] * 10, False, [3,2,0], [True]*10,[4,5,6])
    pano = discipline(9, "Panoramique", [0,1,0,1,1,1,0,1,0,1,0,1] * 10, False, [0,3,3], [True]*10,[5,6])
    urg = discipline(10, "Urgence", [8] * 10, False, [20,20,20], [True]*10,[4,5,6])
    pedo_urg = discipline(11, "Pédodontie Urgences", [2] * 10, False, [0,1,1], [True]*10,[5,6])
    bloc = discipline(12, "BLOC", [0,0,2,0,0,0,2,0,0,0], False, [0,1,1], [False,False,True,False,False,False,True,False,False,False],[5,6])
    sp = discipline(13, "Soins spécifiques", [1,0,0,0,0,0,0,0,0,0], False, [0,0,0], [True,False,False,False,False,False,False,False,False,False],[5,6])
    
    # Configuration des présences (Ouvertures/Fermetures créneaux types)
    # Format: [LunMatin, LunAprem, MarMatin, MarAprem, MerMatin, MerAprem, JeuMatin, JeuAprem, VenMatin, VenAprem]
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
    
    # Modifications spécifiques (Contraintes avancées)
    poly.modif_nb_vacations_par_semaine(2)
    poly.modif_paire_jours([ (0,1), (2,3), (0,4) ]) # Paires requises: (Lun,Mar), (Mer,Jeu), (Lun,Ven)
    poly.modif_take_jour_pref(True)
    
    bloc.modif_fill_requirement(True)
    
    occl.modif_repetition_continuite(1, 12)  # Pas 2 fois de suite dans 12 semaines
    
    sp.modif_fill_requirement(True)
    
    ste.modif_fill_requirement(True)
    
    ra.modif_priorite_niveau([4,5,6])  # Priorité: 4A > 5A > 6A
    
    odf.modif_repartition_semestrielle([2,2])  # 4 total, 2 par semestre
    
    pedo_soins.modif_frequence_vacations(1)  # Une semaine sur deux
    pedo_soins.modif_priorite_niveau([5,6,4])  # Priorité: 5A > 6A > 4A
    pedo_soins.modif_meme_jour(True)
    
    paro.modif_mixite_groupes(2) # Au moins 2 niveaux différents par vacation
    
    como.modif_mixite_groupes(3) # Un élève de chaque niveau
    
    pano.modif_priorite_niveau([6,5])  # Priorité: 6A > 5A
    
    urg.modif_remplacement_niveau([(5,6,7),(5,4,5)])  # 5A→6A (7 élèves), 5A→4A (5 élèves)
    
    pedo_urg.modif_priorite_niveau([6,5])  # Priorité: 6A > 5A
    
    disciplines = [poly, paro, como, pedo_soins, odf, occl, ra, ste, pano, urg, pedo_urg, bloc, sp]
    
    logger.info(f"✓ {len(disciplines)} disciplines chargées avec configuration hardcodée")
    return disciplines

# =============================================================================
# ÉLÈVES (Chargement depuis CSV - identique à model_V5_03_C)
# =============================================================================

def load_eleves(eleves_path: Path) -> List[eleve]:
    """
    Charge les élèves depuis eleves_with_code.csv (logique model_V5_03_C)
    
    Args:
        eleves_path: Chemin vers eleves_with_code.csv
    
    Returns:
        List[eleve]: Liste des élèves
    
    Raises:
        DataLoadError: Si le fichier est manquant ou invalide
    """
    if not eleves_path.exists():
        raise DataLoadError(f"Fichier élèves introuvable: {eleves_path}")
    
    logger.info("Chargement des élèves...")
    
    try:
        eleves = []
        with open(eleves_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Parse jour preference
                    jour_pref_str = row.get("jour_preference", "lundi").strip().lower()
                    jour_pref_map = {
                        "lundi": (0, DemiJournee.matin),
                        "mardi": (1, DemiJournee.matin),
                        "mercredi": (2, DemiJournee.matin),
                        "jeudi": (3, DemiJournee.matin),
                        "vendredi": (4, DemiJournee.matin)
                    }
                    
                    if jour_pref_str in jour_pref_map:
                        jour, period = jour_pref_map[jour_pref_str]
                        jour_preference = jour_pref(jour, period)
                    else:
                        jour_preference = jour_pref(0, DemiJournee.matin)  # Default: Lundi matin
                    
                    # Parse niveau
                    annee_str = row.get("annee", "DFAS01").strip()
                    try:
                        annee_niveau = niveau[annee_str]
                    except KeyError:
                        logger.warning(f"Niveau inconnu '{annee_str}' pour élève {row.get('id_eleve')}, utilisation DFAS01 par défaut")
                        annee_niveau = niveau.DFAS01
                    
                    # Créer élève
                    el = eleve(
                        id_eleve=int(row["id_eleve"]),
                        nom=row["nom"].strip(),
                        prenom=row["prenom"].strip(),
                        annee=annee_niveau,
                        jour_preference=jour_preference,
                        periode_stage=int(row.get("periode_stage", 0)),
                        code=row.get("code", "").strip()
                    )
                    
                    # Ajouter binôme si présent
                    binome_id = row.get("binome_id", "").strip()
                    if binome_id and binome_id != "":
                        el.binome_id = int(binome_id)
                    
                    eleves.append(el)
                    
                except (KeyError, ValueError) as e:
                    logger.error(f"Erreur ligne élève {row.get('id_eleve', '?')}: {e}")
                    continue
        
        if not eleves:
            raise DataLoadError("Aucun élève valide chargé")
        
        # Résoudre les binômes (références croisées)
        eleves_dict = {e.id_eleve: e for e in eleves}
        for el in eleves:
            if hasattr(el, 'binome_id') and el.binome_id:
                if el.binome_id in eleves_dict:
                    el.binome = eleves_dict[el.binome_id]
        
        logger.info(f"✓ {len(eleves)} élèves chargés")
        return eleves
    
    except Exception as e:
        raise DataLoadError(f"Erreur chargement élèves: {e}")

# =============================================================================
# STAGES (Chargement avec stages_lookup - identique à model_V5_03_C)
# =============================================================================

def load_stages(stages_path: Path) -> Dict[Tuple[str, int], List[Dict]]:
    """
    Charge les stages avec structure stages_lookup (logique model_V5_03_C)
    
    Returns:
        Dict[(niveau_name, periode) -> List[Dict]]: stages_lookup
            Chaque dict contient: {"nom", "debut", "fin", "niveau_obj"}
    """
    stages_lookup = collections.defaultdict(list)
    
    if not stages_path.exists():
        logger.warning(f"Fichier stages introuvable: {stages_path}, aucun stage chargé")
        return dict(stages_lookup)
    
    logger.info("Chargement des stages...")
    
    try:
        with open(stages_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    # Skip rows with empty week values
                    if not row.get("deb_semaine") or not row.get("fin_semaine"):
                        continue
                    
                    niveau_name = row["pour_niveau"].strip()
                    periode = int(row["periode"])
                    
                    # Parse niveau object
                    try:
                        niveau_obj = niveau[niveau_name]
                    except KeyError:
                        logger.warning(f"Niveau inconnu pour stage: {niveau_name}")
                        continue
                    
                    # Ajouter au lookup
                    stages_lookup[(niveau_name, periode)].append({
                        "nom": row["nom_stage"].strip(),
                        "debut": int(float(row["deb_semaine"])),
                        "fin": int(float(row["fin_semaine"])),
                        "niveau_obj": niveau_obj
                    })
                    count += 1
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Erreur lecture stage: {e}")
                    continue
        
        logger.info(f"✓ {count} stages chargés dans stages_lookup")
        return dict(stages_lookup)
    
    except Exception as e:
        logger.error(f"Erreur chargement stages: {e}")
        return dict(stages_lookup)

# =============================================================================
# CALENDRIERS (Chargement avec (semaine, slot_idx) - identique à model_V5_03_C)
# =============================================================================

def load_calendars(data_dir: Path) -> Dict[niveau, Set[Tuple[int, int]]]:
    """
    Charge les calendriers d'indisponibilité (logique model_V5_03_C)
    
    Returns:
        Dict[niveau -> Set[(semaine, slot_idx)]]: calendar_unavailability
            slot_idx = jour * 2 + (0 si matin, 1 si après-midi)
    """
    calendar_unavailability = collections.defaultdict(set)
    
    cal_files = {
        niveau.DFAS01: data_dir / 'calendrier_DFAS01.csv',
        niveau.DFAS02: data_dir / 'calendrier_DFASS02.csv',  # Note le double S (comme dans model_V5_03_C)
        niveau.DFTCC: data_dir / 'calendrier_DFTCC.csv'
    }
    
    logger.info("Chargement des calendriers...")
    
    for niv, fpath in cal_files.items():
        if not fpath.exists():
            logger.warning(f"Calendrier introuvable: {fpath}")
            continue
        
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    try:
                        semaine = int(row.get("semaine", 0))
                        jour = int(row.get("jour", 0))  # 0=Lun, 1=Mar, 2=Mer, 3=Jeu, 4=Ven
                        
                        # Déterminer période (matin/après-midi)
                        period_str = row.get("period", "").strip().lower()
                        if period_str in ["matin", "am"]:
                            period_offset = 0
                        elif period_str in ["aprem", "pm", "après-midi", "apresmidi"]:
                            period_offset = 1
                        else:
                            # Default: toute la journée (ajouter matin et après-midi)
                            slot_matin = jour * 2 + 0
                            slot_aprem = jour * 2 + 1
                            calendar_unavailability[niv].add((semaine, slot_matin))
                            calendar_unavailability[niv].add((semaine, slot_aprem))
                            count += 2
                            continue
                        
                        slot_idx = jour * 2 + period_offset
                        calendar_unavailability[niv].add((semaine, slot_idx))
                        count += 1
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Erreur lecture calendrier {niv.name}: {e}")
                        continue
                
                logger.info(f"✓ Calendrier {niv.name}: {count} indisponibilités")
        
        except Exception as e:
            logger.error(f"Erreur chargement calendrier {niv.name}: {e}")
    
    return dict(calendar_unavailability)

# =============================================================================
# PÉRIODES (Hardcodées - identique à model_V5_03_C)
# =============================================================================

def load_periodes() -> List[Periode]:
    """
    Retourne les périodes hardcodées (logique model_V5_03_C)
    
    Returns:
        List[Periode]: Liste des 6 périodes
    """
    periodes = [
        Periode(0, 34, 44),  # Période 0: semaines 34-44
        Periode(1, 45, 51),  # Période 1: semaines 45-51
        Periode(2, 1, 8),    # Période 2: semaines 1-8
        Periode(3, 9, 15),   # Période 3: semaines 9-15
        Periode(4, 16, 22),  # Période 4: semaines 16-22
        Periode(5, 23, 30)   # Période 5: semaines 23-30
    ]
    
    logger.info(f"✓ {len(periodes)} périodes hardcodées chargées")
    return periodes

# =============================================================================
# FONCTION PRINCIPALE DE CHARGEMENT
# =============================================================================

def load_all_data   (data_dir: Path) -> Dict:
    """
    Charge toutes les données (wrapper principal pour optimizer)
    
    Args:
        data_dir: Répertoire contenant les fichiers CSV
    
    Returns:
        Dict contenant:
            - disciplines: List[discipline]
            - eleves: List[eleve]
            - stages_lookup: Dict[(niveau_name, periode) -> List[Dict]]
            - calendar_unavailability: Dict[niveau -> Set[(semaine, slot_idx)]]
            - periodes: List[Periode]
    
    Raises:
        DataLoadError: Si des données essentielles sont manquantes
    """
    logger.info("=" * 80)
    logger.info("CHARGEMENT DES DONNÉES (LOADERS - Model V5_03_C)")
    logger.info("=" * 80)
    
    try:
        # Charger disciplines (hardcodées)
        disciplines = load_disciplines()
        
        # Charger élèves
        eleves_path = data_dir / 'eleves_with_code.csv'
        eleves = load_eleves(eleves_path)
        
        # Charger stages
        stages_path = data_dir / 'stages.csv'
        stages_lookup = load_stages(stages_path)
        
        # Charger calendriers
        calendar_unavailability = load_calendars(data_dir)
        
        # Charger périodes (hardcodées)
        periodes = load_periodes()
        
        logger.info("=" * 80)
        logger.info("✓ CHARGEMENT TERMINÉ")
        logger.info(f"  Disciplines: {len(disciplines)}")
        logger.info(f"  Élèves: {len(eleves)}")
        logger.info(f"  Stages: {sum(len(v) for v in stages_lookup.values())} entrées")
        logger.info(f"  Calendriers: {sum(len(v) for v in calendar_unavailability.values())} indisponibilités")
        logger.info(f"  Périodes: {len(periodes)}")
        logger.info("=" * 80)
        
        return {
            'disciplines': disciplines,
            'eleves': eleves,
            'stages_lookup': stages_lookup,
            'calendar_unavailability': calendar_unavailability,
            'periodes': periodes
        }
    
    except Exception as e:
        raise DataLoadError(f"Erreur lors du chargement des données: {e}")

# =============================================================================
# HELPER: Créer dictionnaire élève par ID
# =============================================================================

def create_eleve_dict(eleves: List[eleve]) -> Dict[int, eleve]:
    """
    Crée un dictionnaire {id_eleve -> eleve} pour accès rapide
    
    Args:
        eleves: Liste des élèves
    
    Returns:
        Dict[int, eleve]: Dictionnaire indexé par ID
    """
    return {e.id_eleve: e for e in eleves}

# =============================================================================
# HELPER: Créer stages_eleves depuis stages_lookup
# =============================================================================

def create_stages_eleves(eleves: List[eleve], stages_lookup: Dict) -> Dict[int, List[stage]]:
    """
    Crée stages_eleves (logique model_V5_03_C)
    
    Args:
        eleves: Liste des élèves
        stages_lookup: Dict[(niveau_name, periode) -> List[Dict]]
    
    Returns:
        Dict[eleve_id -> List[stage]]: Stages par élève
    """
    stages_eleves = {}
    
    for el in eleves:
        if el.periode_stage > 0:
            key = (el.annee.name, el.periode_stage)
            if key in stages_lookup:
                stages_eleves[el.id_eleve] = [
                    stage(
                        d["nom"],
                        d["debut"],
                        d["fin"],
                        d["niveau_obj"],
                        el.periode_stage
                    )
                    for d in stages_lookup[key]
                ]
    
    return stages_eleves
