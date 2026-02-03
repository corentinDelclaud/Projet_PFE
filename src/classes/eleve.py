import sys
import os

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau
class eleve:
    id_eleve : int
    id_binome : int
    jour_preference : jour_pref
    meme_jour : int  #  1 : lundi, 2 : mardi, 3 : mercredi, 4 : jeudi, 5 : vendredi
    annee : niveau
    periode_stage : int
    periode_stage_ext : int
    
    def __init__(self, id_eleve: int, id_binome: int, jour_preference: jour_pref, annee: niveau,meme_jour: int = 0, periode_stage: int = 0, periode_stage_ext: int = 0):
        self.id_eleve = id_eleve
        self.id_binome = id_binome
        self.jour_preference = jour_preference
        self.annee = annee
        self.meme_jour = meme_jour
        self.periode_stage = periode_stage
        self.periode_stage_ext = periode_stage_ext