from periode import Periode as periode
class vacation:
    semaine : int # semaine de l'année (1 à 52)
    jour: int # jour de la semaine sauf samedi et dimanche (0 à 4)
    period : periode
    
    def __init__(self, semaine: int, jour: int, period: periode):
        self.semaine = semaine
        self.jour = jour
        self.period = period