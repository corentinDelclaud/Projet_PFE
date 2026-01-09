class calendar:
    
    weeks = 52
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    periods = ["Matin", "ApresMidi"]
    
    
    def __init__(self):
        self.weeks = 52
        self.days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
        self.periods = ["Matin", "ApresMidi"]
        
    def get_weeks(self) -> int:
        return self.weeks
    def get_days(self) -> list[str]:
        return self.days
    def get_periods(self) -> list[str]:
        return self.periods
    def __str__(self):
        return f"Calendar(weeks={self.weeks}, days={self.days}, periods={self.periods})"
    def __repr__(self):
        return self.__str__()
    