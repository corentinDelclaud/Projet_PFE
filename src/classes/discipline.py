"""
Module: discipline.py
Modélisation d'une discipline hospitalière avec toutes ses contraintes.

Ce module définit la classe Discipline qui encapsule la configuration complète d'un service
hospitalier: capacité d'accueil (fauteuils), quotas pédagogiques par niveau, contraintes
de planification (fréquence, continuité, mixité), et règles métier spécifiques.

C'est le cœur de la configuration du problème d'optimisation, car chaque discipline possède
ses propres règles qui doivent être respectées lors de l'affectation des étudiants.

Author: Corentin DELCLAUD & Poomedy RUNGEN
Date: 2025-2026
Version: V5_03_C
"""


class discipline:
    """
    Représente une discipline hospitalière avec sa configuration et ses contraintes.
    
    Une discipline (ex: Polyclinique, Parodontologie, Urgences) définit:
    - Sa capacité d'accueil: nombre de fauteuils disponibles par créneau
    - Ses quotas: nombre de vacations que chaque étudiant doit effectuer dans l'année
    - Ses disponibilités: quels créneaux (LunMatin, LunAprem, ...) sont ouverts
    - Ses contraintes: règles de planification complexes (binômes, fréquence, mixité...)
    
    === ATTRIBUTS DE BASE ===
    
    id_discipline (int): Identifiant unique de la discipline (1-13)
    nom_discipline (str): Nom complet (ex: "Parodontologie")
    nb_eleve (list[int]): Nombre de fauteuils par créneau (10 valeurs pour LunM, LunA, MarM, MarA, MerM, MerA, JeuM, JeuA, VenM, VenA)
    en_binome (bool): Si True, les étudiants doivent venir par binôme (même vacation)
    quota (list[int]): Nombre de vacations à effectuer [4A, 5A, 6A] dans l'année
    presence (list[bool]): Disponibilité par créneau (True=ouvert, False=fermé), 10 valeurs
    annee (list[int]): Niveaux autorisés dans cette discipline (ex: [4,5,6] ou [5,6] uniquement)
    
    === CONTRAINTES AVANCÉES (optionnelles) ===
    
    TIMING & FRÉQUENCE:
    --------------------
    frequence_vacations (int): Fréquence de vacation
        - 0 = pas de contrainte (défaut)
        - 1 = chaque semaine
        - 2 = une semaine sur deux
        - 3 = une semaine sur trois
        
    nb_vacations_par_semaine (int): Limite de vacations par semaine
        - 0 = pas de limite (défaut)
        - N = maximum N vacations par semaine
        
    repartition_semestrielle (list[int] | None): Répartition des quotas entre semestres
        - None = pas de contrainte (défaut)
        - [nb_sem1, nb_sem2] où nb_sem1 + nb_sem2 = quota total
        - Ex: [25, 25] pour répartir 50 vacations équitablement
    
    CONTRAINTES DE JOURS:
    ---------------------
    paire_jours (list[tuple[int, int]] | None): Paires de jours obligatoires
        - None = pas de contrainte (défaut)
        - Ex: [(0,2), (1,3)] = (Lun+Mer) OU (Mar+Jeu)
        - Utilisé pour disciplines nécessitant 2 demi-journées/semaine
        
    take_jour_pref (bool): Prendre en compte les préférences de jour
        - False = ignorer les préférences (défaut)
        - True = bonus au score si jour préférentiel respecté
        
    meme_jour (bool): Essayer de regrouper sur même jour
        - False = pas de contrainte (défaut)
        - True = tenter de planifier toutes les vacations le même jour ou adjacent
        - Utile pour disciplines comme Pédodontie (continuité de suivi)
    
    COMPOSITION DES GROUPES:
    ------------------------
    mixite_groupes (int): Règle de composition des groupes par niveau
        - 0 = pas de contrainte (défaut)
        - 1 = exactement 1 élève de chaque niveau (rare)
        - 2 = au moins 2 niveaux différents par vacation (diversité)
        - 3 = tous du même niveau (homogénéité)
        
    priorite_niveau (list[int] | None): Ordre de priorité d'affectation
        - None = pas de priorité (défaut)
        - Ex: [5, 6, 4] = 1ère priorité 5A, 2ème priorité 6A, 3ème priorité 4A
        - Utilisé quand une discipline a plus de demandes que de places
        
    remplacement_niveau (list[tuple[int, int, int]]): Règles de remplacement entre niveaux
        - [] = pas de remplacement (défaut)
        - Ex: [(5, 6, 7), (5, 4, 5)] = remplacer 7 étudiants de 5A par des 6A, et 5 étudiants de 5A par des 4A
        - Format: (niveau_absent, niveau_remplaçant, nombre_à_remplacer)
    
    CONTINUITÉ TEMPORELLE:
    ----------------------
    repetition_continuite (tuple[int, int]): Évite les répétitions trop rapprochées
        - (0, 0) = pas de contrainte (défaut)
        - (type_contrainte, distance_semaines)
        - Ex: (1, 12) = pas 2 fois de suite sur une fenêtre de 12 semaines
        - Type: 1=pas 2x suite, 2=pas 3x suite, etc.
    
    CONTRAINTES D'OBLIGATION:
    -------------------------
    be_filled (bool): Discipline impérative (doit être remplie à 100%)
        - False = pas obligatoire (défaut)
        - True = TOUS les créneaux doivent être remplis au maximum de capacité
        - Utilisé pour disciplines critiques (Stérilisation, BLOC)
    
    === EXEMPLE D'UTILISATION ===
    
    >>> # Configuration de la Polyclinique (discipline la plus courante)
    >>> poly = discipline(
    ...     id_discipline=1,
    ...     nom_discipline="Polyclinique",
    ...     nb_eleve=[20]*10,      # 20 fauteuils tous les créneaux
    ...     en_binome=True,         # Étudiants en binôme
    ...     quota=[50, 50, 50],     # 50 vacations/an par niveau
    ...     presence=[True]*10      # Ouvert tous les créneaux
    ... )
    >>> poly.modif_nb_vacations_par_semaine(2)  # Maximum 2 vacations/semaine
    >>> poly.modif_take_jour_pref(True)         # Respecter préférences
    
    >>> # Configuration de la Parodontologie (plus spécialisé)
    >>> paro = discipline(
    ...     id_discipline=2,
    ...     nom_discipline="Parodontologie",
    ...     nb_eleve=[0,4,4,4,4,4,4,4,4,4],  # Pas ouvert lundi matin, 4 fauteuils ailleurs
    ...     en_binome=False,                  # Pas de binôme
    ...     quota=[6, 6, 6],                  # 6 vacations/an seulement
    ...     presence=[False, True, True, True, True, True, True, True, True, True],
    ...     annee=[4, 5, 6]                   # Tous niveaux acceptés
    ... )
    >>> paro.modif_mixite_groupes(2)  # Au moins 2 niveaux différents par vacation
    """
    
    # === DÉCLARATION DES ATTRIBUTS AVEC VALEURS PAR DÉFAUT ===
    id_discipline: int
    nom_discipline: str
    nb_eleve: list[int] = [0] * 10
    en_binome: bool
    quota: list[int] = [0] * 3
    presence: list[bool] = [False] * 10
    annee: list[int] = [4, 5, 6]
    frequence_vacations: int = 0
    nb_vacations_par_semaine: int = 0
    repartition_semestrielle: list[int] | None = None
    paire_jours: list[tuple[int, int]] | None = None
    mixite_groupes: int = 0
    repetition_continuite: tuple[int, int] = (0, 0)
    priorite_niveau: list[int] | None = None
    remplacement_niveau: list[tuple[int, int, int]] = []
    take_jour_pref: bool = False
    be_filled: bool = False
    meme_jour: bool = False
    
    def __init__(
        self, 
        id_discipline: int, 
        nom_discipline: str, 
        nb_eleve: list[int], 
        en_binome: bool, 
        quota: list[int], 
        presence: list[bool] = None, 
        annee: list[int] = None, 
        **kwargs
    ):
        """
        Initialise une discipline avec sa configuration de base.
        
        Les contraintes avancées sont définies via kwargs ou via les méthodes modif_*.
        
        Args:
            id_discipline: ID unique (1-13 dans la config actuelle)
            nom_discipline: Nom lisible par humain
            nb_eleve: Liste de 10 entiers (capacité par créneau)
            en_binome: True si discipline nécessite des binômes
            quota: Liste de 3 entiers [4A, 5A, 6A] (vacations/an)
            presence: Liste de 10 bool (ouverture créneaux), défaut [False]*10
            annee: Liste d'int [4,5,6] (niveaux autorisés), défaut tous
            **kwargs: Contraintes avancées (voir attributs de classe)
        
        Raises:
            ValueError: Si les listes n'ont pas la bonne taille
        """
        self.id_discipline = id_discipline
        self.nom_discipline = nom_discipline
        self.nb_eleve = nb_eleve
        self.en_binome = en_binome
        self.quota = quota
        self.presence = presence if presence is not None else [False] * 10
        self.annee = annee if annee is not None else [4, 5, 6]
        
        # Extraction des kwargs pour les contraintes avancées
        # Pattern utilisé pour éviter un constructeur avec 15+ paramètres
        self.frequence_vacations = kwargs.get('frequence_vacations', 0)
        self.nb_vacations_par_semaine = kwargs.get('nb_vacations_par_semaine', 0)
        self.repartition_semestrielle = kwargs.get('repartition_semestrielle', None)
        self.paire_jours = kwargs.get('paire_jours', None)
        self.mixite_groupes = kwargs.get('mixite_groupes', 0)
        self.repetition_continuite = kwargs.get('repetition_continuite', (0, 0))
        self.priorite_niveau = kwargs.get('priorite_niveau', None)
        self.remplacement_niveau = kwargs.get('remplacement_niveau', [])
        self.take_jour_pref = kwargs.get('take_jour_pref', False)
        self.be_filled = kwargs.get('be_filled', False)
        self.meme_jour = kwargs.get('meme_jour', False)
    
    def __repr__(self):
        """Représentation textuelle pour debugging."""
        return (
            f"discipline(id={self.id_discipline}, nom='{self.nom_discipline}', "
            f"fauteuils={self.nb_eleve}, binome={self.en_binome}, "
            f"quota={self.quota}, presence={self.presence})"
        )
    
    # === MÉTHODES DE SÉRIALISATION (pour sauvegarde/import config) ===
    
    def to_dict(self) -> dict:
        """
        Convertit la discipline en dictionnaire JSON-serializable.
        
        Utilisé pour sauvegarder la configuration dans un fichier JSON
        ou pour l'API REST.
        
        Returns:
            dict: Représentation dictionnaire (sans contraintes avancées)
        """
        return {
            "id_discipline": self.id_discipline,
            "nom": self.nom_discipline,
            "fauteuil": self.nb_eleve,
            "binome": self.en_binome,
            "quota": self.quota,
            "presence": self.presence
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'discipline':
        """
        Crée une discipline depuis un dictionnaire.
        
        Pattern Factory pour désérialisation JSON.
        
        Args:
            data: Dict contenant les clés requises
        
        Returns:
            discipline: Instance configurée
        """
        return discipline(
            id_discipline=data.get("id_discipline"),
            nom_discipline=data.get("nom"),
            nb_eleve=data.get("fauteuil"),
            en_binome=data.get("binome"),
            quota=data.get("quota"),
            presence=data.get("presence", [False] * 10)
        )
    
    # === MÉTHODES DE MODIFICATION DES ATTRIBUTS DE BASE ===
    
    def modif_presence(self, index: int, status: bool):
        """
        Modifie l'ouverture d'un créneau spécifique.
        
        Args:
            index: Index du créneau (0=LunM, 1=LunA, ..., 9=VenA)
            status: True=ouvert, False=fermé
        
        Raises:
            IndexError: Si index hors limites [0-9]
        """
        if 0 <= index < len(self.presence):
            self.presence[index] = status
        else:
            raise IndexError(f"Index {index} hors limites pour presence (attendu 0-9)")
    
    def multiple_modif_presence(self, indices: list[int], status: list[bool]):
        """
        Modifie plusieurs créneaux en une seule opération.
        
        Équivalent à un batch update pour éviter les boucles multiples.
        
        Args:
            indices: Liste des index à modifier
            status: Liste des nouveaux statuts (même taille que indices)
        
        Raises:
            ValueError: Si les listes n'ont pas la même taille
        
        Example:
            >>> disc.multiple_modif_presence([0, 2, 4], [True, True, False])
            # Ouvre LunM et MarM, ferme MerM
        """
        if len(indices) != len(status):
            raise ValueError("indices et status doivent avoir la même longueur")
        for i, s in zip(indices, status):
            self.modif_presence(i, s)
    
    def modif_nb_eleve(self, index: int, nb: int):
        """
        Modifie la capacité (nb de fauteuils) d'un créneau.
        
        Args:
            index: Index du créneau (0-9)
            nb: Nouveau nombre de fauteuils
        
        Raises:
            IndexError: Si index invalide
        """
        if 0 <= index < len(self.nb_eleve):
            self.nb_eleve[index] = nb
        else:
            raise IndexError(f"Index {index} hors limites pour nb_eleve")
    
    def multiple_modif_nb_eleve(self, indices: list[int], nbs: list[int]):
        """Modification batch de capacités. Voir multiple_modif_presence."""
        if len(indices) != len(nbs):
            raise ValueError("indices et nbs doivent avoir la même longueur")
        for i, nb in zip(indices, nbs):
            self.modif_nb_eleve(i, nb)
    
    def modif_quota(self, index: int, quota_value: int):
        """
        Modifie le quota pour un niveau donné.
        
        Args:
            index: 0=4A, 1=5A, 2=6A
            quota_value: Nouveau quota (nombre de vacations/an)
        
        Raises:
            IndexError: Si index invalide (doit être 0-2)
        """
        if 0 <= index < len(self.quota):
            self.quota[index] = quota_value
        else:
            raise IndexError(f"Index {index} invalide pour quota (attendu 0-2)")
    
    def multiple_modif_quota(self, indices: list[int], quota_values: list[int]):
        """Modification batch de quotas. Voir multiple_modif_presence."""
        if len(indices) != len(quota_values):
            raise ValueError("indices et quota_values doivent avoir la même longueur")
        for i, value in zip(indices, quota_values):
            self.modif_quota(i, value)
    
    def display_info(self):
        """Affiche un résumé de la configuration (utile pour debugging)."""
        print(f"=== Discipline ID {self.id_discipline}: {self.nom_discipline} ===")
        print(f"Capacité fauteuils: {self.nb_eleve}")
        print(f"Fonctionne en binôme: {self.en_binome}")
        print(f"Quotas par année: {self.quota} (4A/5A/6A)")
        print(f"Présence créneaux: {self.presence}")
        print(f"Niveaux autorisés: {self.annee}")
    
    # === MÉTHODES DE MODIFICATION DES CONTRAINTES AVANCÉES ===
    
    def modif_frequence_vacations(self, frequence: int):
        """
        Définit la fréquence de vacation (toutes les X semaines).
        
        Args:
            frequence: 0=libre, 1=chaque sem, 2=1/2, 3=1/3, etc.
        
        Example:
            >>> pedo.modif_frequence_vacations(2)  # Pédodontie: une semaine sur deux
        """
        self.frequence_vacations = frequence
    
    def modif_nb_vacations_par_semaine(self, nb_vacations: int):
        """
        Limite le nombre de vacations par semaine pour un étudiant.
        
        Args:
            nb_vacations: Maximum de vacations/semaine (0=illimité)
        
        Example:
            >>> poly.modif_nb_vacations_par_semaine(2)  # Max 2 polycliniques/semaine
        """
        self.nb_vacations_par_semaine = nb_vacations
    
    def modif_repartition_semestrielle(self, repartition: list[int]):
        """
        Impose une répartition équitable entre les deux semestres.
        
        Args:
            repartition: [nb_sem1, nb_sem2] où sum = quota
        
        Raises:
            ValueError: Si la somme ne correspond pas aux quotas
        
        Note:
            Cette méthode vérifie actuellement que sum(repartition) == quota[i]
            pour CHAQUE niveau, ce qui implique la même répartition pour tous.
            À ajuster si besoin de répartitions différenciées par niveau.
        """
        # Validation: la somme doit égaler chaque quota
        # TODO: Permettre des répartitions différentes par niveau?
        if sum(repartition) != self.quota[0]:
            raise ValueError(f"Somme répartition ({sum(repartition)}) ≠ quota 4A ({self.quota[0]})")
        if sum(repartition) != self.quota[1]:
            raise ValueError(f"Somme répartition ({sum(repartition)}) ≠ quota 5A ({self.quota[1]})")
        if sum(repartition) != self.quota[2]:
            raise ValueError(f"Somme répartition ({sum(repartition)}) ≠ quota 6A ({self.quota[2]})")
        self.repartition_semestrielle = repartition
    
    def modif_paire_jours(self, paires: list[tuple[int, int]]):
        """
        Définit les paires de jours obligatoires pour cette discipline.
        
        Args:
            paires: Liste de tuples (jour1, jour2) où jours ∈ [0-4]
        
        Example:
            >>> poly.modif_paire_jours([(0, 2), (1, 3)])
            # Polyclinique doit être (Lun+Mer) OU (Mar+Jeu)
        """
        self.paire_jours = paires
    
    def modif_mixite_groupes(self, mixite: int):
        """
        Définit la règle de composition des groupes par niveau.
        
        Args:
            mixite: 0=libre, 1=1 de chaque, 2=min 2 niveaux, 3=même niveau
        
        Example:
            >>> paro.modif_mixite_groupes(2)  # Paro: au moins 2 niveaux différents
            >>> urgence.modif_mixite_groupes(3)  # Urgence: tous même niveau
        """
        self.mixite_groupes = mixite
    
    def modif_repetition_continuite(self, repetition: int, distance: int):
        """
        Évite les répétitions trop rapprochées dans le temps.
        
        Args:
            repetition: Type de contrainte (1=pas 2x suite, 2=pas 3x suite...)
            distance: Fenêtre temporelle en semaines
        
        Example:
            >>> occl.modif_repetition_continuite(1, 12)
            # Occlusodontie: pas 2 fois de suite sur 12 semaines
        """
        self.repetition_continuite = (repetition, distance)
    
    def modif_priorite_niveau(self, priorites: list[int]):
        """
        Définit l'ordre de priorité d'affectation par niveau.
        
        Args:
            priorites: Liste ordonnée [1st, 2nd, 3rd] avec valeurs 4, 5 ou 6
        
        Raises:
            ValueError: Si la liste contient plus de 3 éléments
        
        Example:
            >>> pedo.modif_priorite_niveau([5, 6, 4])
            # Pédodontie: priorité 5A > 6A > 4A
        """
        if len(priorites) > 3:
            raise ValueError("Maximum 3 niveaux de priorité (4A, 5A, 6A)")
        self.priorite_niveau = priorites
    
    def modif_remplacement_niveau(self, remplacements: list[tuple[int, int, int]]):
        """
        Définit les règles de remplacement entre niveaux.
        
        Utilisé quand un niveau ne peut pas remplir tous les créneaux
        et qu'un autre niveau peut combler.
        
        Args:
            remplacements: Liste de (niveau_absent, remplaçant, quota)
        
        Example:
            >>> urg.modif_remplacement_niveau([(5, 6, 7), (5, 4, 5)])
            # Urgence: remplacer 7×5A par 6A et 5×5A par 4A
        """
        self.remplacement_niveau = remplacements
    
    def modif_take_jour_pref(self, take: bool):
        """
        Active/désactive la prise en compte des préférences de jour.
        
        Args:
            take: True pour appliquer un bonus si jour préférentiel respecté
        
        Note:
            Ajoute des points au score d'optimisation si l'étudiant est affecté
            à son jour préférentiel. N'est pas une contrainte dure.
        """
        self.take_jour_pref = take
    
    def modif_fill_requirement(self, be_filled: bool):
        """
        Rend la discipline obligatoirement remplie (contrainte dure).
        
        Args:
            be_filled: True pour forcer le remplissage à 100%
        
        Example:
            >>> bloc.modif_fill_requirement(True)  # BLOC doit être plein
            >>> ste.modif_fill_requirement(True)   # Stérilisation aussi
        """
        self.be_filled = be_filled
    
    def modif_meme_jour(self, meme_jour: bool):
        """
        Tente de regrouper toutes les vacations sur le même jour/adjacent.
        
        Args:
            meme_jour: True pour activer cette contrainte souple
        
        Note:
            Utilisé principalement pour la Pédodontie où il est préférable
            que l'étudiant ait toutes ses vacations le même jour de la semaine
            (ex: tous les mardis) pour la continuité du suivi patient.
        """
        self.meme_jour = meme_jour
