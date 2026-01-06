import niveaux.niveau as niveaux
class eleve:
    id_eleve : int
    nom : str
    prenom : str | None
    niveau : niveaux
    binome : "eleve"
    vacpref : int
    
    def __init__(self, id_eleve: int, nom: str, prenom: str, niveau: niveaux, binome: "eleve", vacpref: int):
        self.id_eleve = id_eleve
        self.nom = nom
        self.prenom = prenom
        self.niveau = niveau
        self.binome = binome
        self.vacpref = vacpref

    def __repr__(self):
        return f"eleve(id_eleve={self.id_eleve}, nom='{self.nom}', prenom='{self.prenom}', niveau='{self.niveau}', binome={self.binome}, vacpref={self.vacpref})"
    def to_dict(self):
        return {
            "id_eleve": self.id_eleve,
            "nom": self.nom,
            "prenom": self.prenom,
            "niveau": self.niveau,
            "binome": self.binome.id_eleve if self.binome else None,
            "vacpref": self.vacpref
        }
        
    @staticmethod
    def from_dict(data: dict, eleve_lookup: dict):
        binome_id = data.get("binome")
        binome_eleve = eleve_lookup.get(binome_id) if binome_id is not None else None
        return eleve(
            id_eleve=data.get("id_eleve"),
            nom=data.get("nom"),
            prenom=data.get("prenom"),
            niveau=data.get("niveau"),
            binome=binome_eleve,
            vacpref=data.get("vacpref")
        )        
        