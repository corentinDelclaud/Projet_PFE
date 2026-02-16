"""
Module: vacation.py
Définition d'un créneau de vacation hospitalière.

Une vacation représente une unité de temps élémentaire dans le planning hospitalier.
Elle correspond à une demi-journée (matin ou après-midi) d'une semaine donnée.
C'est l'unité de base pour l'affectation des étudiants aux différentes disciplines.
"""

from classes.enum.demijournee import DemiJournee as dj


class vacation:
    """
    Représente un créneau temporel pour l'affectation hospitalière.
    
    Une vacation est un triplet (semaine, jour, période) qui définit un créneau
    unique dans le calendrier académique. Les étudiants sont affectés à des vacations
    selon les contraintes de chaque discipline et leur disponibilité.
    
    Attributes:
        semaine (int): Numéro de semaine dans l'année académique (1 à 52)
                      Attention: utiliser les semaines ISO pour cohérence
        jour (int): Jour de la semaine (0=Lundi, 1=Mardi, 2=Mercredi, 3=Jeudi, 4=Vendredi)
                   Week-ends exclus du système de planning
        period (DemiJournee): Période de la journée (MATIN ou APREM)
                             Défini par l'enum DemiJournee
    
    Note:
        Une vacation peut accueillir plusieurs étudiants simultanément selon
        le nombre de fauteuils disponibles dans la discipline concernée.
        Ex: Polyclinique peut avoir 20 fauteuils → 20 étudiants par vacation
    
    Example:
        >>> # Vacation du lundi matin de la semaine 15
        >>> vac = vacation(semaine=15, jour=0, period=DemiJournee.MATIN)
        >>> # Vacation du vendredi après-midi de la semaine 32
        >>> vac2 = vacation(semaine=32, jour=4, period=DemiJournee.APREM)
    """
    
    semaine: int
    jour: int
    period: dj
    
    def __init__(self, semaine: int, jour: int, period: dj):
        """
        Initialise une vacation avec ses coordonnées temporelles.
        
        Args:
            semaine: Numéro de semaine ISO (1-52)
            jour: Index du jour (0-4 pour Lun-Ven)
            period: Période MATIN ou APREM (enum DemiJournee)
        
        Raises:
            ValueError: Si les paramètres sont hors limites (implicite, peut être ajouté)
        """
        self.semaine = semaine
        self.jour = jour
        self.period = period