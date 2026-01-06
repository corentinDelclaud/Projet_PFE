class UIC(object):
    id_discipline : int
    nom : str
    fauteuil : int
    binome : bool
    presence : list[bool] = [False] * 10  # Default presence list with 10 False values
    
    def __init__(self, id_discipline: int, nom: str, fauteuil: int, binome: bool, presence: list[bool] = None):
        self.id_discipline = id_discipline
        self.nom = nom
        self.fauteuil = fauteuil
        self.binome = binome
        self.presence = presence if presence is not None else [False] * 10
        
    def __repr__(self):
        return f"UIC(id_discipline={self.id_discipline}, nom='{self.nom}', fauteuil={self.fauteuil}, binome={self.binome})"
    def to_dict(self):
        return {
            "id_discipline": self.id_discipline,
            "nom": self.nom,
            "fauteuil": self.fauteuil,
            "binome": self.binome
        }
    
    @staticmethod
    def from_dict(data: dict):
        return UIC(
            id_discipline=data.get("id_discipline"),
            nom=data.get("nom"),
            fauteuil=data.get("fauteuil"),
            binome=data.get("binome")
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

    