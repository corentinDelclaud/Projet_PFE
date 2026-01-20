class Periode:
    #les différentes périodes possibles de l'année
    #il y en a 6 de 0 à 5
    #on peut alors relier chaque stage à sa période
    id : int
    semaine_debut : int
    semaine_fin : int
    
    
    def __init__(self, id: int, semaine_debut: int, semaine_fin: int):
        self.id = id
        self.semaine_debut = semaine_debut
        self.semaine_fin = semaine_fin    
    def modif_semaine_debut(self, semaine_debut: int):
        self.semaine_debut = semaine_debut
    def modif_semaine_fin(self, semaine_fin: int):
        self.semaine_fin = semaine_fin
    