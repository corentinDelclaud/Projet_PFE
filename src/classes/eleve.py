"""
Module: eleve.py
Représentation d'un étudiant en odontologie avec ses contraintes et préférences.

Ce module définit la classe Eleve qui encapsule toutes les informations nécessaires
pour l'affectation optimale d'un étudiant aux différentes vacations hospitalières.
Chaque étudiant possède des contraintes de disponibilité, des préférences de planning
et des obligations liées à son niveau d'étude et ses stages externes.
"""

import sys
import os

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.jour_preference import jour_pref
from classes.enum.niveaux import niveau


class eleve:
    """
    Représente un étudiant en odontologie avec toutes ses caractéristiques.
    
    Attributes:
        id_eleve (int): Identifiant unique de l'étudiant (ex: 4011 pour 4A-étudiant 11)
        id_binome (int): Identifiant du binôme associé (même valeur pour 2 étudiants binômés)
        jour_preference (jour_pref): Objet représentant les jours préférentiels de l'étudiant
        meme_jour (int): Contrainte de jour fixe pour certaines disciplines
                         0=pas de contrainte, 1=lundi, 2=mardi, 3=mercredi, 4=jeudi, 5=vendredi
        annee (niveau): Niveau d'étude (4A/DFASO1, 5A/DFASO2, 6A/DFTCC)
        periode_stage (int): Index de la période de stage interne si applicable (0 si aucun)
        periode_stage_ext (int): Index de la période de stage externe si applicable (0 si aucun)
    
    Note:
        Les stages créent des indisponibilités qui doivent être prises en compte lors
        de l'optimisation. L'étudiant ne peut pas être affecté pendant ses périodes de stage.
    """
    
    # Annotations de type pour une meilleure clarté du code
    id_eleve: int
    id_binome: int
    jour_preference: jour_pref
    meme_jour: int
    annee: niveau
    periode_stage: int
    periode_stage_ext: int
    
    def __init__(
        self, 
        id_eleve: int, 
        id_binome: int, 
        jour_preference: jour_pref, 
        annee: niveau,
        meme_jour: int = 0, 
        periode_stage: int = 0, 
        periode_stage_ext: int = 0
    ):
        """
        Initialise un étudiant avec ses caractéristiques personnelles.
        
        Args:
            id_eleve: Identifiant unique (doit correspondre à l'ID dans le CSV)
            id_binome: ID du binôme (deux étudiants en binôme partagent le même ID)
            jour_preference: Objet contenant les préférences de jours (bonus si respecté)
            annee: Niveau académique (détermine les disciplines accessibles et les quotas)
            meme_jour: Jour fixe souhaité pour certaines disciplines comme la Pédodontie (optionnel)
            periode_stage: Numéro de période de stage interne (0 si pas de stage, optionnel)
            periode_stage_ext: Numéro de période de stage externe (0 si pas de stage, optionnel)
        
        Example:
            >>> etudiant = eleve(
            ...     id_eleve=4011,
            ...     id_binome=401,  # Binôme avec l'étudiant 4012 qui a le même id_binome
            ...     jour_preference=jour_pref(lundi=True, mardi=False, ...),
            ...     annee=niveau.DFASO1,
            ...     meme_jour=2  # Préfère le mardi pour certaines disciplines
            ... )
        """
        self.id_eleve = id_eleve
        self.id_binome = id_binome
        self.jour_preference = jour_preference
        self.annee = annee
        self.meme_jour = meme_jour
        self.periode_stage = periode_stage
        self.periode_stage_ext = periode_stage_ext