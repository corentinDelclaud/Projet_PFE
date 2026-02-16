"""
Data loading utilities with error handling
"""
import csv
import sys
import os
import ast
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import collections

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
    """Custom exception for data loading errors"""
    pass

def load_disciplines(disciplines_path: Path, periodes_path: Path) -> List[discipline]:
    """
    Load disciplines from CSV with Python dict/list format
    
    Args:
        disciplines_path: Path to disciplines.csv
        periodes_path: Path to periodes.csv (not used in your format)
    
    Returns:
        List[discipline]: List of configured disciplines
    
    Raises:
        DataLoadError: If files are missing or data is invalid
    """
    if not disciplines_path.exists():
        raise DataLoadError(f"Fichier disciplines introuvable: {disciplines_path}")
    
    try:
        disciplines = []
        
        with open(disciplines_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, 1):
                try:
                    disc_id = int(row['id_discipline'])
                    nom = row['nom_discipline'].strip()
                    
                    # Parse nb_eleve (format: "{1: 20, 2: 20, ...}")
                    nb_eleve_dict = ast.literal_eval(row['nb_eleve'])
                    nb_eleve = [nb_eleve_dict.get(i, 0) for i in range(1, 11)]
                    
                    # Parse en_binome
                    en_binome = row['en_binome'].strip().lower() == 'true'
                    
                    # Parse quota (format: "{'DFAS01': 50, 'DFAS02': 50, 'DFTCC': 50}")
                    quota_dict = ast.literal_eval(row['quota'])
                    quota = [
                        quota_dict.get('DFAS01', 0),
                        quota_dict.get('DFAS02', 0),
                        quota_dict.get('DFTCC', 0)
                    ]
                    
                    # Parse presence (format: "{1: True, 2: True, ...}")
                    presence_dict = ast.literal_eval(row['presence'])
                    presence = [presence_dict.get(i, False) for i in range(1, 11)]
                    
                    # Parse annee (format: "['DFAS01', 'DFAS02', 'DFTCC']")
                    annee_list = ast.literal_eval(row['annee'])
                    annee = []
                    niveau_map = {'DFAS01': 4, 'DFAS02': 5, 'DFTCC': 6}
                    for niv_str in annee_list:
                        if niv_str in niveau_map:
                            annee.append(niveau_map[niv_str])
                    
                    if not annee:
                        logger.warning(f"Discipline {nom}: Aucune année définie, ignorée")
                        continue
                    
                    # Create discipline
                    disc = discipline(
                        id_discipline=disc_id,
                        nom_discipline=nom,
                        nb_eleve=nb_eleve,
                        en_binome=en_binome,
                        quota=quota,
                        presence=presence,
                        annee=annee
                    )
                    
                    # Apply advanced constraints
                    _apply_discipline_constraints(disc, row)
                    
                    disciplines.append(disc)
                    
                except (KeyError, ValueError, SyntaxError) as e:
                    logger.error(f"Erreur ligne {idx} disciplines: {e}")
                    continue
        
        if not disciplines:
            raise DataLoadError("Aucune discipline valide chargée")
        
        logger.info(f"✓ {len(disciplines)} disciplines chargées")
        return disciplines
    
    except Exception as e:
        raise DataLoadError(f"Erreur chargement disciplines: {e}")

def _apply_discipline_constraints(disc: discipline, row: dict):
    """Apply advanced constraints from CSV row to discipline"""
    try:
        # Frequence vacations
        freq = int(row.get('frequence_vacations', 0))
        if freq > 1:
            disc.modif_frequence_vacations(freq)
        
        # Nb vacations par semaine
        nb_vac = int(row.get('nb_vacations_par_semaine', 0))
        if nb_vac > 0:
            disc.modif_nb_vacations_par_semaine(nb_vac)
        
        # Repartition semestrielle (format: "{1: 2, 2: 2}")
        rep_str = row.get('repartition_semestrielle', '').strip()
        if rep_str and rep_str != "{1: 0, 2: 0}":
            try:
                rep_dict = ast.literal_eval(rep_str)
                rep = [rep_dict.get(1, 0), rep_dict.get(2, 0)]
                if sum(rep) > 0:
                    disc.modif_repartition_semestrielle(rep)
            except (ValueError, SyntaxError):
                pass
        
        # Paire jours (format: "[(0, 1), (2, 3), (0, 4)]")
        pairs_str = row.get('paire_jours', '').strip()
        if pairs_str and pairs_str != "[]":
            try:
                pairs = ast.literal_eval(pairs_str)
                if pairs:
                    disc.modif_paire_jours(pairs)
            except (ValueError, SyntaxError):
                pass
        
        # Mixité groupes
        mixite = int(row.get('mixite_groupes', 0))
        if mixite > 0:
            disc.modif_mixite_groupes(mixite)
        
        # Repartition continuité (format: "(1, 12)")
        rep_cont_str = row.get('repartition_continuite', '').strip()
        if rep_cont_str and rep_cont_str != "(0, 0)":
            try:
                limit, distance = ast.literal_eval(rep_cont_str)
                if limit > 0:
                    disc.modif_repetition_continuite(limit, distance)
            except (ValueError, SyntaxError):
                pass
        
        # Priorité niveau (format: "['DFAS01', 'DFAS02', 'DFTCC']")
        prio_str = row.get('priorite_niveau', '').strip()
        if prio_str and prio_str != "[]":
            try:
                prio_list = ast.literal_eval(prio_str)
                niveau_map = {'DFAS01': 4, 'DFAS02': 5, 'DFTCC': 6}
                prio = [niveau_map[n] for n in prio_list if n in niveau_map]
                if prio:
                    disc.modif_priorite_niveau(prio)
            except (ValueError, SyntaxError):
                pass
        
        # Remplacement niveau (format: "{'DFAS02': {'niveau_remplacant': 'DFTCC', 'quota': 7}}")
        remp_str = row.get('remplacement_niveau', '').strip()
        if remp_str and remp_str != "{}":
            try:
                remp_dict = ast.literal_eval(remp_str)
                niveau_map = {'DFAS01': 4, 'DFAS02': 5, 'DFTCC': 6}
                remplacements = []
                for niv_from_str, config in remp_dict.items():
                    niv_from = niveau_map.get(niv_from_str.replace('_2', ''))
                    niv_to_str = config.get('niveau_remplacant')
                    niv_to = niveau_map.get(niv_to_str)
                    quota = config.get('quota', 0)
                    if niv_from and niv_to and quota > 0:
                        remplacements.append((niv_from, niv_to, quota))
                if remplacements:
                    disc.modif_remplacement_niveau(remplacements)
            except (ValueError, SyntaxError):
                pass
        
        # Take jour pref
        if row.get('take_jour_pref', '').strip().lower() == 'true':
            disc.modif_take_jour_pref(True)
        
        # Be filled
        if row.get('be_filled', '').strip().lower() == 'true':
            disc.modif_fill_requirement(True)
    
    except Exception as e:
        logger.warning(f"Erreur application contraintes {disc.nom_discipline}: {e}")

def load_eleves(eleves_path: Path) -> List[eleve]:
    """
    Load students with validation
    
    Args:
        eleves_path: Path to eleves_with_code.csv
    
    Returns:
        List[eleve]: List of students
    
    Raises:
        DataLoadError: If file is missing or data is invalid
    """
    if not eleves_path.exists():
        raise DataLoadError(f"Fichier élèves introuvable: {eleves_path}")
    
    try:
        eleves = []
        with open(eleves_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, 1):
                try:
                    # Get jour preference
                    jour_pref_str = row.get("jour_preference", "lundi").strip().lower()
                    try:
                        jp = jour_pref[jour_pref_str]
                    except KeyError:
                        logger.warning(f"Élève ligne {idx}: jour_preference invalide '{jour_pref_str}', utilisation 'lundi'")
                        jp = jour_pref.lundi
                    
                    # Get niveau
                    annee_str = row.get("annee", "").strip()
                    try:
                        niv = niveau[annee_str]
                    except KeyError:
                        logger.warning(f"Élève ligne {idx}: année invalide '{annee_str}', ignoré")
                        continue
                    
                    new_eleve = eleve(
                        id_eleve=int(row["id_eleve"]),
                        id_binome=int(row.get("id_binome", 0)),
                        jour_preference=jp,
                        annee=niv
                    )
                    new_eleve.periode_stage = int(row.get("periode_stage", 0))
                    eleves.append(new_eleve)
                    
                except (KeyError, ValueError) as e:
                    logger.warning(f"Erreur ligne {idx} élèves: {e}")
                    continue
        
        if not eleves:
            raise DataLoadError("Aucun élève valide chargé")
        
        logger.info(f"✓ {len(eleves)} élèves chargés")
        return eleves
    
    except Exception as e:
        raise DataLoadError(f"Erreur chargement élèves: {e}")

def load_stages(stages_path: Path) -> Dict:
    """
    Load stages configuration
    
    Args:
        stages_path: Path to stages.csv
    
    Returns:
        Dict: Stages lookup dictionary
    """
    stages_lookup = collections.defaultdict(list)
    
    if not stages_path.exists():
        logger.warning(f"Fichier stages introuvable: {stages_path}, aucun stage chargé")
        return stages_lookup
    
    try:
        with open(stages_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for idx, row in enumerate(reader, 1):
                try:
                    niveau_str = row.get("pour_niveau", "").strip()
                    if not niveau_str:
                        continue
                    
                    periode = int(float(row.get("periode", 0)))
                    if periode == 0:
                        continue
                    
                    # Parse debut and fin semaine
                    deb = row.get("deb_semaine", "").strip()
                    fin = row.get("fin_semaine", "").strip()
                    
                    # Skip if no dates
                    if not deb or not fin or deb == 'nan' or fin == 'nan':
                        continue
                    
                    deb_semaine = int(float(deb))
                    fin_semaine = int(float(fin))
                    
                    key = (niveau_str, periode)
                    stages_lookup[key].append({
                        "nom": row.get("nom_stage", "").strip(),
                        "debut": deb_semaine,
                        "fin": fin_semaine,
                        "niveau_obj": niveau[niveau_str]
                    })
                    count += 1
                    
                except (KeyError, ValueError) as e:
                    logger.warning(f"Erreur ligne {idx} stages: {e}")
                    continue
        
        logger.info(f"✓ {count} stages chargés")
        return dict(stages_lookup)
    
    except Exception as e:
        logger.error(f"Erreur chargement stages: {e}")
        return stages_lookup

def load_calendars(data_dir: Path) -> Dict:
    """
    Load calendar unavailability data
    
    Args:
        data_dir: Directory containing calendar CSV files
    
    Returns:
        Dict: Calendar unavailability by niveau
    """
    calendar_unavailability = collections.defaultdict(set)
    
    cal_files = {
        niveau.DFAS01: data_dir / 'calendrier_DFAS01.csv',
        niveau.DFAS02: data_dir / 'calendrier_DFAS02.csv',
        niveau.DFTCC: data_dir / 'calendrier_DFTCC.csv'
    }
    
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
                        semaine_str = row.get("Semaine", "").replace("S", "").strip()
                        if not semaine_str:
                            continue
                        
                        s = int(semaine_str)
                        if s == 0 or s > 52 or s == 53:
                            continue
                        
                        # Check each period (1-10)
                        for i in range(1, 11):
                            val = row.get(str(i), "").strip()
                            if val:  # If not empty, it's unavailable
                                calendar_unavailability[niv].add((s, i-1))
                                count += 1
                    except (ValueError, KeyError) as e:
                        continue
                
                logger.info(f"✓ Calendrier {niv.name}: {count} indisponibilités")
        
        except Exception as e:
            logger.error(f"Erreur chargement calendrier {niv.name}: {e}")
    
    return dict(calendar_unavailability)

def load_periodes(periodes_path: Path) -> List[Periode]:
    """
    Load periodes configuration from CSV
    
    Args:
        periodes_path: Path to periodes.csv
    
    Returns:
        List[Periode]: List of periods
    """
    if not periodes_path.exists():
        logger.warning(f"Fichier periodes introuvable: {periodes_path}, utilisation des périodes par défaut")
        # Fallback to hardcoded periods
        periodes = [
            Periode(0, 34, 44),
            Periode(1, 45, 51),
            Periode(2, 1, 8),
            Periode(3, 9, 15),
            Periode(4, 16, 22),
            Periode(5, 23, 30)
        ]
        logger.info(f"✓ {len(periodes)} périodes par défaut chargées")
        return periodes
    
    try:
        periodes = []
        with open(periodes_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Read directly from CSV (already in week numbers)
                    periode_id = int(row['periode'])
                    deb_semaine = int(row['deb_semaine'])
                    fin_semaine = int(row['fin_semaine'])
                    
                    if deb_semaine > 0 and fin_semaine > 0:
                        periodes.append(Periode(periode_id, deb_semaine, fin_semaine))
                        
                except (ValueError, KeyError) as e:
                    logger.warning(f"Ligne période invalide ignorée: {e}")
                    continue
        
        if not periodes:
            logger.warning("Aucune période valide dans le CSV, utilisation des périodes par défaut")
            periodes = [
                Periode(0, 34, 44),
                Periode(1, 45, 51),
                Periode(2, 1, 8),
                Periode(3, 9, 15),
                Periode(4, 16, 22),
                Periode(5, 23, 30)
            ]
        
        # Sort by ID
        periodes.sort(key=lambda p: p.id)
        
        logger.info(f"✓ {len(periodes)} périodes chargées depuis CSV")
        return periodes
        
    except Exception as e:
        logger.error(f"Erreur chargement periodes: {e}, utilisation des périodes par défaut")
        periodes = [
            Periode(0, 34, 44),
            Periode(1, 45, 51),
            Periode(2, 1, 8),
            Periode(3, 9, 15),
            Periode(4, 16, 22),
            Periode(5, 23, 30)
        ]
        return periodes