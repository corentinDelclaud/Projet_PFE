from typing import Optional

class niveaux:
   id_niveau : int
   nom_niveau : str
   
   periodes_stages_actives : Optional[list[tuple[int, int]]]  #début et fin des périodes de stage en semaines min : 1 et max : 52
   
   def __init__(self, id_niveau: int, nom_niveau: str, periodes_stages_actives: Optional[list[tuple[int, int]]]):
       self.id_niveau = id_niveau
       self.nom_niveau = nom_niveau
       self.periodes_stages_actives = periodes_stages_actives
   
       