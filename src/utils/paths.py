import sys
from pathlib import Path


def get_app_root():
    """
    Retourne le dossier racine de l'application :
    - En mode développement : dossier parent de src/
    - En mode exécutable : dossier contenant l'exécutable
    """
    if getattr(sys, 'frozen', False):
        # Mode exécutable : utiliser le dossier de l'exécutable
        return Path(sys.executable).parent
    else:
        # Mode développement : remonter de src/ vers la racine
        return Path(__file__).parent.parent.parent


def get_data_dir():
    """Retourne le dossier data/ persistant"""
    data_dir = get_app_root() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_resultat_dir():
    """Retourne le dossier resultat/ persistant"""
    resultat_dir = get_app_root() / "resultat"
    resultat_dir.mkdir(exist_ok=True)
    return resultat_dir


def get_logs_dir():
    """Retourne le dossier logs/ persistant"""
    logs_dir = get_app_root() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir