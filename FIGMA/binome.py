from types_binome import type_binome
class binome : 
    id_binome : int
    type : type_binome
    
    def __init__(self, id_binome: int, type: type_binome):
        self.id_binome = id_binome
        self.type = type