class stage:
    id_stage : int = -1
    nom_stage : str
    debut_stage : int #semaine de debut du stage
    fin_stage : int #semaine de fin du stage
    
    def __init__(self, nom_stage: str, debut_stage: int, fin_stage: int):
        self.id_stage = stage.id_stage + 1
        stage.id_stage += 1
        self.nom_stage = nom_stage
        self.debut_stage = debut_stage
        self.fin_stage = fin_stage