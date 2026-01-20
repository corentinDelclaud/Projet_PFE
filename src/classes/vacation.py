from classes.enum.demijournee import DemiJournee as dj
class vacation:
    semaine : int # semaine de l'année (1 à 52)
    jour: int # jour de la semaine sauf samedi et dimanche (0 à 4)
    period : dj # demi-journée (matin ou après-midi)
    
    def __init__(self, semaine: int, jour: int, period: dj):
        self.semaine = semaine
        self.jour = jour
        self.period = period