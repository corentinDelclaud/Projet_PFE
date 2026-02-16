''' 
LOADERS - Adapté pour Model V5_03_C

Ce module de chargement charge les données depuis les fichiers CSV:
 - Disciplines chargées depuis disciplines.csv
 - Élèves chargés depuis eleves_with_code.csv
 - Stages chargés avec stages_lookup (dict de listes de dicts)
 - Calendriers chargés avec (semaine, slot_idx) comme clé
 - Périodes chargées depuis periodes.csv
 
'''
import sys
import os
import logging
import csv
import collections
import ast
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.discipline import discipline
from classes.eleve import eleve
from classes.stage import stage
from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau
from classes.periode import Periode

logger = logging.getLogger(__name__)

class DataLoadError(Exception):
    """Exception personnalisée pour les erreurs de chargement"""
    pass

# =============================================================================
# HELPERS DE PARSING
# =============================================================================

def parse_csv_value(value: str) -> Any:
    """
    Parse une valeur CSV qui peut contenir dict, list, tuple, etc.
    
    Args:
        value: Chaîne à parser
    
    Returns:
        La valeur parsée (dict, list, int, bool, str, etc.)
    """
    if not value or value.strip() == '':
        return None
    
    value = value.strip()
    
    # Try to evaluate as Python literal
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        # Return as string if parsing fails
        return value

def convert_dict_keys_to_int(d: Dict) -> Dict:
    """
    Convertit les clés d'un dictionnaire en entiers
    
    Args:
        d: Dictionnaire avec clés strings
    
    Returns:
        Dictionnaire avec clés entières
    """
    if not isinstance(d, dict):
        return d
    return {int(k): v for k, v in d.items()}

# =============================================================================
# DISCIPLINES (Chargement depuis CSV)
# =============================================================================

def load_disciplines(disciplines_path: Path) -> List[discipline]:
    """
    Charge les disciplines depuis disciplines.csv
    
    Args:
        disciplines_path: Chemin vers disciplines.csv
    
    Returns:
        List[discipline]: Liste des disciplines configurées
    
    Raises:
        DataLoadError: Si le fichier est manquant ou invalide
    """
    if not disciplines_path.exists():
        raise DataLoadError(f"Fichier disciplines introuvable: {disciplines_path}")
    
    logger.info("Chargement des disciplines depuis CSV...")
    
    try:
        disciplines = []
        with open(disciplines_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Parse basic fields
                    id_disc = int(row['id_discipline'])
                    nom = row['nom_discipline'].strip()
                    
                    # Parse nb_eleve (dict with int keys)
                    nb_eleve_dict = parse_csv_value(row['nb_eleve'])
                    nb_eleve = convert_dict_keys_to_int(nb_eleve_dict)
                    # Convert to list [val for week 1-10]
                    nb_eleve_list = [nb_eleve.get(i, 0) for i in range(1, 11)]
                    
                    # Parse en_binome
                    en_binome = parse_csv_value(row['en_binome'])
                    
                    # Parse quota (dict)
                    quota_dict = parse_csv_value(row['quota'])
                    # Convert to list [DFAS01, DFAS02, DFTCC]
                    quota_list = [
                        quota_dict.get('DFAS01', 0),
                        quota_dict.get('DFAS02', 0),
                        quota_dict.get('DFTCC', 0)
                    ]
                    
                    # Parse presence (dict with int keys)
                    presence_dict = parse_csv_value(row['presence'])
                    presence = convert_dict_keys_to_int(presence_dict)
                    presence_list = [presence.get(i, True) for i in range(1, 11)]
                    
                    # Parse annee (list of niveau codes)
                    annee_list = parse_csv_value(row['annee'])
                    # Convert to niveau indices: DFAS01=4, DFAS02=5, DFTCC=6
                    annee_indices = []
                    for niveau_code in annee_list:
                        if niveau_code == 'DFAS01':
                            annee_indices.append(4)
                        elif niveau_code == 'DFAS02':
                            annee_indices.append(5)
                        elif niveau_code == 'DFTCC':
                            annee_indices.append(6)
                    
                    # Create discipline instance
                    disc = discipline(
                        id_disc,
                        nom,
                        nb_eleve_list,
                        en_binome,
                        quota_list,
                        presence_list,
                        annee_indices
                    )
                    
                    # Apply presence modifications
                    disc.multiple_modif_presence(
                        list(range(10)),
                        presence_list
                    )
                    
                    # Parse and apply additional configurations
                    # frequence_vacations
                    freq_vac = parse_csv_value(row.get('frequence_vacations', '0'))
                    if freq_vac and freq_vac > 0:
                        disc.modif_frequence_vacations(freq_vac)
                    
                    # nb_vacations_par_semaine
                    nb_vac_semaine = parse_csv_value(row.get('nb_vacations_par_semaine', '0'))
                    if nb_vac_semaine and nb_vac_semaine > 0:
                        disc.modif_nb_vacations_par_semaine(nb_vac_semaine)
                    
                    # repartition_semestrielle
                    rep_sem = parse_csv_value(row.get('repartition_semestrielle', '{}'))
                    if rep_sem and isinstance(rep_sem, dict) and rep_sem:
                        rep_list = [rep_sem.get(1, 0), rep_sem.get(2, 0)]
                        if any(rep_list):
                            try:
                                disc.modif_repartition_semestrielle(rep_list)
                            except ValueError as e:
                                logger.warning(f"Discipline {nom}: répartition semestrielle ignorée - {e}")
                    
                    # paire_jours
                    paire_jours = parse_csv_value(row.get('paire_jours', '[]'))
                    if paire_jours and len(paire_jours) > 0:
                        disc.modif_paire_jours(paire_jours)
                    
                    # mixite_groupes
                    mixite = parse_csv_value(row.get('mixite_groupes', '0'))
                    if mixite and mixite > 0:
                        disc.modif_mixite_groupes(mixite)
                    
                    # repartition_continuite
                    rep_cont = parse_csv_value(row.get('repartition_continuite', '(0, 0)'))
                    if rep_cont and isinstance(rep_cont, tuple) and rep_cont != (0, 0):
                        disc.modif_repetition_continuite(rep_cont[0], rep_cont[1])
                    
                    # priorite_niveau
                    priorite = parse_csv_value(row.get('priorite_niveau', '[]'))
                    if priorite and len(priorite) > 0:
                        # Convert niveau names to indices
                        priorite_indices = []
                        for niv in priorite:
                            if niv == 'DFAS01':
                                priorite_indices.append(4)
                            elif niv == 'DFAS02':
                                priorite_indices.append(5)
                            elif niv == 'DFTCC':
                                priorite_indices.append(6)
                        if priorite_indices:
                            disc.modif_priorite_niveau(priorite_indices)
                    
                    # remplacement_niveau
                    remplacement = parse_csv_value(row.get('remplacement_niveau', '{}'))
                    if remplacement and isinstance(remplacement, dict) and remplacement:
                        # Format CSV: {'DFAS02': {'niveau_remplacant': 'DFTCC', 'quota': 7}}
                        # Format attendu: [(niveau_absent, niveau_remplacant, quota)]
                        remp_list = []
                        for niv_key, remp_info in remplacement.items():
                            if isinstance(remp_info, dict):
                                # Parse niveau absent (from key like 'DFAS02' or 'DFAS02_2')
                                if 'DFAS01' in niv_key:
                                    niv_idx = 4
                                elif 'DFAS02' in niv_key:
                                    niv_idx = 5
                                elif 'DFTCC' in niv_key:
                                    niv_idx = 6
                                else:
                                    logger.warning(f"Niveau inconnu dans remplacement: {niv_key}")
                                    continue
                                
                                # Parse niveau remplaçant
                                remp_niv = remp_info.get('niveau_remplacant', '')
                                if remp_niv == 'DFAS01':
                                    remp_idx = 4
                                elif remp_niv == 'DFAS02':
                                    remp_idx = 5
                                elif remp_niv == 'DFTCC':
                                    remp_idx = 6
                                else:
                                    logger.warning(f"Niveau remplaçant inconnu: {remp_niv}")
                                    continue
                                
                                # Le 'quota' dans le CSV est le pourcentage attendu par l'optimizer
                                quota_remp = remp_info.get('quota', 0)
                                if quota_remp > 0:
                                    remp_list.append((niv_idx, remp_idx, quota_remp))
                        
                        if remp_list:
                            disc.modif_remplacement_niveau(remp_list)
                    
                    # take_jour_pref
                    take_jour = parse_csv_value(row.get('take_jour_pref', 'False'))
                    if take_jour:
                        disc.modif_take_jour_pref(True)
                    
                    # be_filled
                    be_filled = parse_csv_value(row.get('be_filled', 'False'))
                    if be_filled:
                        disc.modif_fill_requirement(True)
                    
                    # meme_jour_semaine
                    meme_jour = parse_csv_value(row.get('meme_jour_semaine', 'False'))
                    if meme_jour:
                        disc.modif_meme_jour(True)
                    
                    disciplines.append(disc)
                    
                except (KeyError, ValueError, TypeError) as e:
                    logger.error(f"Erreur lecture discipline {row.get('id_discipline', '?')}: {e}")
                    continue
        
        if not disciplines:
            raise DataLoadError("Aucune discipline valide chargée")
        
        logger.info(f"✓ {len(disciplines)} disciplines chargées depuis CSV")
        return disciplines
    
    except Exception as e:
        raise DataLoadError(f"Erreur chargement disciplines: {e}")

# =============================================================================
# ÉLÈVES (Chargement depuis CSV - identique à model_V5_03_C)
# =============================================================================

def load_eleves(eleves_path: Path) -> List[eleve]:
    """
    Charge les élèves depuis eleves_with_code.csv
    
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
                    # Parse jour preference (jour_pref is an Enum)
                    jour_pref_str = row.get("jour_preference", "lundi").strip().lower()
                    
                    # Map string to jour_pref enum
                    if jour_pref_str == "lundi":
                        jour_preference = jour_pref.lundi
                    elif jour_pref_str == "mardi":
                        jour_preference = jour_pref.mardi
                    elif jour_pref_str == "mercredi":
                        jour_preference = jour_pref.mercredi
                    elif jour_pref_str == "jeudi":
                        jour_preference = jour_pref.jeudi
                    elif jour_pref_str == "vendredi":
                        jour_preference = jour_pref.vendredi
                    else:
                        jour_preference = jour_pref.lundi  # Default: Lundi
                    
                    # Parse niveau
                    annee_str = row.get("annee", "DFAS01").strip()
                    try:
                        annee_niveau = niveau[annee_str]
                    except KeyError:
                        logger.warning(f"Niveau inconnu '{annee_str}' pour élève {row.get('id_eleve')}, utilisation DFAS01 par défaut")
                        annee_niveau = niveau.DFAS01
                    
                    # Extraire id_eleve et id_binome
                    id_eleve = int(row["id_eleve"])
                    id_binome_str = row.get("id_binome", "").strip()
                    id_binome = int(id_binome_str) if id_binome_str else id_eleve
                    
                    # Parse jour_similaire (meme_jour)
                    jour_similaire = int(row.get("jour_similaire", 0))
                    
                    # Parse periode_stage_ext
                    periode_stage_ext = int(row.get("periode_stage_ext", 0))
                    
                    # Créer élève avec la bonne signature
                    el = eleve(
                        id_eleve=id_eleve,
                        id_binome=id_binome,
                        jour_preference=jour_preference,
                        annee=annee_niveau,
                        meme_jour=jour_similaire,
                        periode_stage=int(row.get("periode_stage", 0)),
                        periode_stage_ext=periode_stage_ext
                    )
                    
                    eleves.append(el)
                    
                except (KeyError, ValueError) as e:
                    logger.error(f"Erreur ligne élève {row.get('id_eleve', '?')}: {e}")
                    continue
        
        if not eleves:
            raise DataLoadError("Aucun élève valide chargé")
        
        # Convert mutual binome references to common group IDs
        # CSV format: student A has id_binome=B, student B has id_binome=A
        # Optimizer expects: both A and B have the same group ID
        binome_map = {}  # Maps old id_binome to new group_id
        for el in eleves:
            if el.id_binome != el.id_eleve:
                # This student is in a binome
                pair = tuple(sorted([el.id_eleve, el.id_binome]))
                if pair not in binome_map:
                    # Use the smaller ID as the group ID
                    binome_map[pair] = pair[0]
        
        # Apply the group IDs
        for el in eleves:
            if el.id_binome != el.id_eleve:
                pair = tuple(sorted([el.id_eleve, el.id_binome]))
                if pair in binome_map:
                    el.id_binome = binome_map[pair]
        
        logger.info(f"✓ {len(eleves)} élèves chargés (dont {len(binome_map)} paires de binômes)")
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
    Charge les calendriers d'indisponibilité depuis les fichiers CSV
    
    Le format des CSV est:
    Semaine,1,2,3,4,5,6,7,8,9,10
    S34,F,F,F,F,C,C,C,C,C,C
    ...
    
    Où les colonnes 1-10 correspondent aux créneaux:
    1=Lundi Matin, 2=Lundi Après-midi, 3=Mardi Matin, 4=Mardi Après-midi, ...
    
    Et les valeurs sont:
    - C: Cours (disponible)
    - F: Férié (indisponible)
    - E: Examen (indisponible)
    - vide: indisponible
    
    Returns:
        Dict[niveau -> Set[(semaine, slot_idx)]]: calendar_unavailability
            slot_idx = créneau - 1 (pour indexation à partir de 0)
    """
    calendar_unavailability = collections.defaultdict(set)
    
    cal_files = {
        niveau.DFAS01: data_dir / 'calendrier_DFAS01.csv',
        niveau.DFAS02: data_dir / 'calendrier_DFAS02.csv',
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
                        # Extract week number from 'Semaine' column (format: S34 -> 34)
                        semaine_str = row.get("Semaine", "").strip()
                        if not semaine_str or not semaine_str.startswith("S"):
                            continue
                        semaine = int(semaine_str[1:])
                        
                        # Check each slot (columns 1-10)
                        for slot_idx in range(1, 11):
                            slot_str = str(slot_idx)
                            if slot_str not in row:
                                continue
                            
                            value = row[slot_str].strip().upper()
                            
                            # If not 'C' (Cours), then it's unavailable
                            if value != 'C':
                                # slot_idx is 1-10, convert to 0-9 for internal use
                                calendar_unavailability[niv].add((semaine, slot_idx - 1))
                                count += 1
                    
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Erreur lecture calendrier {niv.name}: {e}")
                        continue
                
                logger.info(f"✓ Calendrier {niv.name}: {count} indisponibilités")
        
        except Exception as e:
            logger.error(f"Erreur chargement calendrier {niv.name}: {e}")
    
    return dict(calendar_unavailability)

# =============================================================================
# PÉRIODES (Chargement depuis CSV)
# =============================================================================

def load_periodes(periodes_path: Path) -> List[Periode]:
    """
    Charge les périodes depuis periodes.csv
    
    Args:
        periodes_path: Chemin vers periodes.csv
    
    Returns:
        List[Periode]: Liste des périodes
    
    Raises:
        DataLoadError: Si le fichier est manquant ou invalide
    """
    if not periodes_path.exists():
        raise DataLoadError(f"Fichier périodes introuvable: {periodes_path}")
    
    logger.info("Chargement des périodes depuis CSV...")
    
    try:
        periodes = []
        with open(periodes_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    periode = Periode(
                        int(row['periode']),
                        int(row['deb_semaine']),
                        int(row['fin_semaine'])
                    )
                    periodes.append(periode)
                except (KeyError, ValueError) as e:
                    logger.error(f"Erreur lecture période {row.get('id_periode', '?')}: {e}")
                    continue
        
        if not periodes:
            raise DataLoadError("Aucune période valide chargée")
        
        # Sort by periode number
        periodes.sort(key=lambda p: p.id_periode if hasattr(p, 'id_periode') else 0)
        
        logger.info(f"✓ {len(periodes)} périodes chargées depuis CSV")
        return periodes
    
    except Exception as e:
        raise DataLoadError(f"Erreur chargement périodes: {e}")

# =============================================================================
# FONCTION PRINCIPALE DE CHARGEMENT
# =============================================================================

def load_all_data(data_dir: Path) -> Dict:
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
    logger.info("CHARGEMENT DES DONNÉES (LOADERS - depuis CSV)")
    logger.info("=" * 80)
    
    try:
        # Charger disciplines depuis CSV
        disciplines_path = data_dir / 'disciplines.csv'
        disciplines = load_disciplines(disciplines_path)
        
        # Charger élèves
        eleves_path = data_dir / 'eleves_with_code.csv'
        eleves = load_eleves(eleves_path)
        
        # Charger stages
        stages_path = data_dir / 'stages.csv'
        stages_lookup = load_stages(stages_path)
        
        # Charger calendriers
        calendar_unavailability = load_calendars(data_dir)
        
        # Charger périodes depuis CSV
        periodes_path = data_dir / 'periodes.csv'
        periodes = load_periodes(periodes_path)
        
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
