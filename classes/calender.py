import calendar

debut_annee_hospitaliere : str
fin_annee_hospitaliere :str  
jours_de_la_semaine : list[str] = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois_de_l_annee : list[str] = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
def obtenir_jours_dans_mois(annee: int, mois: int) -> int:
    """Retourne le nombre de jours dans un mois donné d'une année spécifique."""
    return calendar.monthrange(annee, mois)[1]

def est_annee_bissextile(annee: int) -> bool:
    """Détermine si une année est bissextile."""
    return calendar.isleap(annee)
def obtenir_jour_de_la_semaine(annee: int, mois: int, jour: int) -> str:
    """Retourne le jour de la semaine pour une date donnée."""
    jour_index = calendar.weekday(annee, mois, jour)
    return jours_de_la_semaine[jour_index]

def generer_calendrier_mensuel(annee: int, mois: int) -> str:
    """Génère un calendrier mensuel sous forme de chaîne de caractères."""
    cal = calendar.TextCalendar()
    return cal.formatmonth(annee, mois)

def generer_calendrier_annuel(annee: int) -> str:
    """Génère un calendrier annuel sous forme de chaîne de caractères."""
    cal = calendar.TextCalendar()
    return cal.formatyear(annee)
def obtenir_semaine_de_l_annee(annee: int, mois: int, jour: int) -> int:
    """Retourne le numéro de la semaine dans l'année pour une date donnée."""
    return calendar.weekday(annee, mois, jour) + 1  # +1 pour que la semaine commence à 1 au lieu de 0
def obtenir_jour_de_l_annee(annee: int, mois: int, jour: int) -> int:
    """Retourne le jour de l'année pour une date donnée."""
    return (calendar.datetime.date(annee, mois, jour) - calendar.datetime.date(annee, 1, 1)).days + 1


