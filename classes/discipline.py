class discipline:
    id_discipline : int
    nom_discipline : str
    salle : str
    nb_fauteuil : int
    en_binome : bool
    quota : int
    presence : list[bool] = [False] * 10  # Default presence list with 10 False values
    
    def __init__(self, id_discipline: int, nom_discipline: str, salle: str, nb_fauteuil: int, en_binome: bool, quota: int, presence: list[bool] = None):
        self.id_discipline = id_discipline
        self.nom_discipline = nom_discipline
        self.salle = salle
        self.nb_fauteuil = nb_fauteuil
        self.en_binome = en_binome
        self.quota = quota
        self.presence = presence if presence is not None else [False] * 10
        
    def __repr__(self):
        return f"UIC(id_discipline={self.id_discipline}, nom='{self.nom_discipline}', fauteuil={self.nb_fauteuil}, binome={self.en_binome}, presence={self.presence})"
    def to_dict(self):
        return {
            "id_discipline": self.id_discipline,
            "nom": self.nom_discipline,
            "fauteuil": self.nb_fauteuil,
            "binome": self.en_binome,
            "quota": self.quota,
            "presence": self.presence
        }
    
    @staticmethod
    def from_dict(data: dict):
        return discipline(
            id_discipline=data.get("id_discipline"),
            nom_discipline=data.get("nom"),
            nb_fauteuil=data.get("fauteuil"),
            en_binome=data.get("binome"),
            quota=data.get("quota"),
            presence=data.get("presence", [False] * 10)
        )

    def modif_presence(self, index: int, status: bool):
        if 0 <= index < len(self.presence):
            self.presence[index] = status
        else:
            raise IndexError("Index out of range for presence list")
        
    def multiple_modif_presence(self, indices: list[int], status: list[bool]):
        if len(indices) != len(status):
            raise ValueError("Indices and status lists must have the same length")
        for i, s in zip(indices, status):
            self.modif_presence(i, s)

    