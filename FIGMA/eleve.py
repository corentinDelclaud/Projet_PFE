class eleve:
    id_eleve : int
    nom : str
    id_binome : int
    
    def __init__(self, id_eleve: int, nom: str, id_binome: int):
        self.id_eleve = id_eleve
        self.nom = nom
        self.id_binome = id_binome