class discipline:
    id_discipline : int
    nom_discipline : str
    nb_eleve : list[int] = [0] * 10  # Default 10 slots with 0 fauteuils
    en_binome : bool
    quota : list[int] = [0] * 3  # Default quota list for each year
    presence : list[bool] = [False] * 10  # Default presence list with 10 False values
    annee : list[int] = [4,5,6]  # Default to all years
    frequence_vacations : int = 0  # Fréquence des vacations à effectuer pour l’élève Toutes les X semaines : number input (1, 2, 3...), 0 = pas de contrainte, 1 = chaque semaine 2 = une semaine sur deux 3 = une semaine sur trois
    nb_vacations_par_semaine : int = 0  # Nombre de vacations par semaine à effectuer pour l’élève, 0 = pas de contrainte
    repartition_semestrielle : list[int] | None = None  # Répartition semestrielle du total des quotas [semestre1 (int), semestre2(int)] semestre1 + semestre2 = total des quotas
    paire_jours : list[tuple[int, int]] | None = None  # indiquer que les vacations doivent être planifiées par paire sur les jours (Lundi, Mercredi) ou (Mardi, Jeudi) -> [(0,2),(1,3)]
    mixite_groupes : int = 0  # Composition des groupes Mixité des niveaux  0 = Pas de contrainte, 1 = Exactement 1 élève de chaque niveau, 2 = Au moins 2 niveaux différents par vacation, 3 = Tous du même niveau
    repetition_continuite : tuple[int,int] = (0,0)  # Contrainte de continuité (X,Y)  X : Éviter répétitions : 0 = Pas de contrainte 1 = Pas 2 fois de suite 2 = Pas 3 fois de suite 3 = Jamais plus de X fois (préciser X)  Y : distance en semaines pour la contrainte de continuité (ex: 12 semaines = 3 mois)
    priorite_niveau : list[int] | None = None # index 0 1st prio , index 1 2nd prio, index 2 3eme prio ( value 4,5,6 for year)
    remplacement_niveau : list[(int,int,int)]   # [X,Y,Z] with X année absente, Y année remplacement et Z quota  X,Y -> (4A, 5A, 6A)  quota -> number of students to replace at the vacation
    take_jour_pref : bool = False  # Prendre en compte les jours préférentiels de l'élève
    be_filled : bool = False  # Discipline impérativement remplie sur ces vacations
    def __init__(self, id_discipline: int, nom_discipline: str, nb_eleve: list[int], en_binome: bool, quota: list[int], presence: list[bool] = None, annee: list[int] = None, **kwargs):
        self.id_discipline = id_discipline
        self.nom_discipline = nom_discipline
        self.nb_eleve = nb_eleve
        self.en_binome = en_binome
        self.quota = quota
        self.presence = presence if presence is not None else [False] * 10
        self.annee = annee if annee is not None else [4, 5, 6]
        
        # Optional arguments handling
        self.frequence_vacations = kwargs.get('frequence_vacations', 0)
        self.nb_vacations_par_semaine = kwargs.get('nb_vacations_par_semaine', 0)
        self.repartition_semestrielle = kwargs.get('repartition_semestrielle', None)
        self.paire_jours = kwargs.get('paire_jours', None)
        self.mixite_groupes = kwargs.get('mixite_groupes', 0)
        self.repetition_continuite = kwargs.get('repetition_continuite', 0)
        self.priorite_niveau = kwargs.get('priorite_niveau', None)
        self.remplacement_niveau = kwargs.get('remplacement_niveau', [])
        
    def __repr__(self):
        return f"UIC(id_discipline={self.id_discipline}, nom='{self.nom_discipline}', fauteuil={self.nb_eleve}, binome={self.en_binome}, presence={self.presence}, quota={self.quota}, annee={self.annee}, frequence_vacations={self.frequence_vacations}, nb_vacations_par_semaine={self.nb_vacations_par_semaine}, repartition_semestrielle={self.repartition_semestrielle}, paire_jours={self.paire_jours}, mixite_groupes={self.mixite_groupes}, repetition_continuite={self.repetition_continuite}, priorite_niveau={self.priorite_niveau}, remplacement_niveau={self.remplacement_niveau})"
    
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
            
            
    def modif_quota(self, index: int, quota_value: int):
        if 0 <= index < len(self.quota):
            self.quota[index] = quota_value
        else:
            raise IndexError("Index out of range for quota list")
        
    def multiple_modif_quota(self, indices: list[int], quota_values: list[int]):
        if len(indices) != len(quota_values):
            raise ValueError("Indices and quota_values lists must have the same length")
        for i, value in zip(indices, quota_values):
            self.modif_quota(i, value)
            
    def display_info(self):
        print(f"Discipline ID: {self.id_discipline}")
        print(f"Nom de la discipline: {self.nom_discipline}")
        print(f"Nombre d'élèves par fauteuil: {self.nb_eleve}")
        print(f"En binôme: {self.en_binome}")
        print(f"Quota par année: {self.quota}")
        print(f"Présence: {self.presence}")
        
    #frequence_vacations : int = 0  # Fréquence des vacations à effectuer pour l’élève Toutes les X semaines : number input (1, 2, 3...) 1 = chaque semaine 2 = une semaine sur deux 3 = une semaine sur trois
    def modif_frequence_vacations(self, frequence: int):
        self.frequence_vacations = frequence
    #nb_vacations_par_semaine : int = 0  # Nombre de vacations par semaine à effectuer pour l’élève
    def modif_nb_vacations_par_semaine(self, nb_vacations: int):
        self.nb_vacations_par_semaine = nb_vacations
    #repartition_semestrielle : list[int] | None = None  # Répartition semestrielle du total des quotas [semestre1, semestre2] semestre1 + semestre2 = total des quotas
    def modif_repartition_semestrielle(self, repartition: list[int]):
        if sum(repartition) != self.quota[0]:
            raise ValueError("La somme de la répartition semestrielle doit être égale au total des quotas des quatrièmes années")
        if sum(repartition) != self.quota[1]:
            raise ValueError("La somme de la répartition semestrielle doit être égale au total des quotas des cinquièmes années")
        if sum(repartition) != self.quota[2]:
            raise ValueError("La somme de la répartition semestrielle doit être égale au total des quotas des sixièmes années")
        self.repartition_semestrielle = repartition
    #paire_jours : list[(int, int )] | None = None  # indiquer que les vacations doivent être planifiées par paire sur les jours (Lundi, Mercredi) et (Mardi, Jeudi) -> [(0,2),(1,3)]
    def modif_paire_jours(self, paires: list[(int, int)]):
        self.paire_jours = paires
    #mixite_groupes : int = 0  # Composition des groupes Mixité des niveaux  0 = Pas de contrainte, 1 = Exactement 1 élève de chaque niveau, 2 = Au moins 2 niveaux différents par vacation, 3 = Tous du même niveau
    def modif_mixite_groupes(self, mixite: int):
        self.mixite_groupes = mixite
    #repetition_continuite : int = 0  # Contrainte de continuité Éviter répétitions : 0 = Pas de contrainte 1 = Pas 2 fois de suite 2 = Pas 3 fois de suite 3 = Jamais plus de X fois (préciser X)
    def modif_repetition_continuite(self, repetition: int, distance: int):
        self.repetition_continuite = (repetition, distance)
    #priorite_niveau : list[int] | None = None # index 0 1st prio , index 1 2nd prio, index 2 3eme prio ( value 4,5,6 for year)
    def modif_priorite_niveau(self, priorites: list[int]):
        if len(priorites) > 3:
            raise ValueError("La liste des priorités doit contenir exactement 3 éléments")
        self.priorite_niveau = priorites
    #remplacement_niveau : list[(int,int,int)] 
    def modif_remplacement_niveau(self, remplacements: list[(int,int,int)]):
        self.remplacement_niveau = remplacements
    def modif_take_jour_pref(self, take: bool):
        self.take_jour_pref = take
    def modif_fill_requirement(self, be_filled: bool):
        self.be_filled = be_filled