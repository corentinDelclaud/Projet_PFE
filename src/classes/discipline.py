class discipline:
    id_discipline : int
    nom_discipline : str
    salle : list[str] = [""] * 10
    nb_eleve : list[int] = [0] * 10  # Default 10 slots with 0 fauteuils
    en_binome : bool
    quota : list[int] = [0] * 3  # Default quota list for each year
    presence : list[bool] = [False] * 10  # Default presence list with 10 False values
    annee : list[int] = [4,5,6]  # Default to all years
    frequence_vacations : int = 0  # Fréquence des vacations à effectuer pour l’élève Toutes les X semaines : number input (1, 2, 3...) 1 = chaque semaine 2 = une semaine sur deux 3 = une semaine sur trois
    nb_vacations_par_semaine : int = 0  # Nombre de vacations par semaine à effectuer pour l’élève
    repartition_semestrielle : list[int] | None = None  # Répartition semestrielle du total des quotas [semestre1, semestre2] semestre1 + semestre2 = total des quotas
    paire_jours : list[(int, int )] | None = None  # indiquer que les vacations doivent être planifiées par paire sur les jours (Lundi, Mercredi) et (Mardi, Jeudi) -> [(0,2),(1,3)]
    mixite_groupes : int = 0  # Composition des groupes Mixité des niveaux  0 = Pas de contrainte, 1 = Exactement 1 élève de chaque niveau, 2 = Au moins 2 niveaux différents par vacation, 3 = Tous du même niveau
    repetition_continuite : int = 0  # Contrainte de continuité Éviter répétitions : 0 = Pas de contrainte 1 = Pas 2 fois de suite 2 = Pas 3 fois de suite 3 = Jamais plus de X fois (préciser X)
    priorite_niveau : list[int] | None = None # index 0 1st prio , index 1 2nd prio, index 2 3eme prio ( value 4,5,6 for year)
    remplacement_niveau : list[(int,int,int)]   # [X,Y,Z] with X année absente, Y année remplacement et Z quota  X,Y -> (4A, 5A, 6A)  quota -> number of students to replace at the vacation
    
    def __init__(self, id_discipline: int, nom_discipline: str, salle: list[str], nb_eleve: list[int], en_binome: bool, quota: list[int], presence: list[bool] = None, annee: list[int] = None):
        self.id_discipline = id_discipline
        self.nom_discipline = nom_discipline
        self.salle = salle
        self.nb_eleve = nb_eleve
        self.en_binome = en_binome
        self.quota = quota
        self.presence = presence if presence is not None else [False] * 10
        self.annee = annee if annee is not None else [4, 5, 6]
        
    def __repr__(self):
        return f"UIC(id_discipline={self.id_discipline}, nom='{self.nom_discipline}', fauteuil={self.nb_eleve}, binome={self.en_binome}, presence={self.presence})"
    def to_dict(self):
        return {
            "id_discipline": self.id_discipline,
            "nom": self.nom_discipline,
            "fauteuil": self.nb_eleve,
            "binome": self.en_binome,
            "quota": self.quota,
            "presence": self.presence
        }
    
    @staticmethod
    def from_dict(data: dict):
        return discipline(
            id_discipline=data.get("id_discipline"),
            nom_discipline=data.get("nom"),
            nb_eleve=data.get("fauteuil"),
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

    def modif_nb_eleve(self, index: int, nb: int):
        if 0 <= index < len(self.nb_eleve):
            self.nb_eleve[index] = nb
        else:
            raise IndexError("Index out of range for nb_eleve list")
        
    def multiple_modif_nb_eleve(self, indices: list[int], nbs: list[int]):
        if len(indices) != len(nbs):
            raise ValueError("Indices and nbs lists must have the same length")
        for i, nb in zip(indices, nbs):
            self.modif_nb_eleve(i, nb)
            
    def modif_salle(self, index: int, salle_name: str):
        if 0 <= index < len(self.salle):
            self.salle[index] = salle_name
        else:
            raise IndexError("Index out of range for salle list")
        
    def multiple_modif_salle(self, indices: list[int], salle_names: list[str]):
        if len(indices) != len(salle_names):
            raise ValueError("Indices and salle_names lists must have the same length")
        for i, name in zip(indices, salle_names):
            self.modif_salle(i, name)