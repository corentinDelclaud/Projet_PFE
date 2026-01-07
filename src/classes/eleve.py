import sys
import os

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau
class eleve:
    id_eleve : int
    nom : str
    id_binome : int
    jour_preference : jour_pref
    annee : niveau
    
    def __init__(self, id_eleve: int, nom: str, id_binome: int, jour_preference: jour_pref, annee: niveau):
        self.id_eleve = id_eleve
        self.nom = nom
        self.id_binome = id_binome
        self.jour_preference = jour_preference
        self.annee = annee