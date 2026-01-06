class cours:
    semaine : int # semaine de l'année (1 à 52)
    jour: int # jour de la semaine sauf samedi et dimanche (0 à 4)
    
    def __init__(self, semaine: int, jour: int):
        self.semaine = semaine
        self.jour = jour
    def __repr__(self):
        return f"cours(semaine={self.semaine}, jour={self.jour})"