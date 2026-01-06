class discipline:
    id_discipline : int
    nom_discipline : str
    salle : str
    nb_fauteuil : int
    en_binome : bool
    quota : int
    
    def __init__(self, id_discipline: int, nom_discipline: str, salle: str, nb_fauteuil: int, en_binome: bool, quota: int):
        self.id_discipline = id_discipline
        self.nom_discipline = nom_discipline
        self.salle = salle
        self.nb_fauteuil = nb_fauteuil
        self.en_binome = en_binome
        self.quota = quota