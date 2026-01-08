import sys
import os
# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.enum.niveaux import niveau
class stage:
    id_stage : int = -1
    nom_stage : str
    periode : int
    pour_niveau : niveau
    debut_stage : int #semaine de debut du stage
    fin_stage : int #semaine de fin du stage
    
    def __init__(self, nom_stage: str, debut_stage: int, fin_stage: int, pour_niveau: niveau, periode: int):
        self.periode = periode
        self.pour_niveau = pour_niveau
        self.id_stage = stage.id_stage + 1
        stage.id_stage += 1
        self.nom_stage = nom_stage
        self.debut_stage = debut_stage
        self.fin_stage = fin_stage
        
    def __str__(self):
        return f"Stage(id_stage={self.id_stage}, nom_stage={self.nom_stage}, pour_niveau={self.pour_niveau}, debut_stage={self.debut_stage}, fin_stage={self.fin_stage}, periode={self.periode})"
    
    def __repr__(self):
        return self.__str__()
    
    def get_id_stage(self) -> int:
        return self.id_stage
    
    def get_nom_stage(self) -> str:
        return self.nom_stage
    def get_debut_stage(self) -> int:
        return self.debut_stage
    def get_fin_stage(self) -> int:
        return self.fin_stage
    def get_pour_niveau(self) -> niveau:
        return self.pour_niveau
    def get_periode(self) -> int:
        return self.periode
    
    def set_nom_stage(self, nom_stage: str):
        self.nom_stage = nom_stage
        
    def set_debut_stage(self, debut_stage: int):
        self.debut_stage = debut_stage
    def set_fin_stage(self, fin_stage: int):
        self.fin_stage = fin_stage
    def set_pour_niveau(self, pour_niveau: niveau):
        self.pour_niveau = pour_niveau
    def set_periode(self, periode: int):
        self.periode = periode