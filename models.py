class Utilizador:
    def __init__(self, id, nome, email, tipo):
        self.id = id
        self.nome = nome
        self.email = email
        self.tipo = tipo

class Cliente(Utilizador):
    def __init__(self, id, nome, email):
        super().__init__(id, nome, email, "ROLE_CLIENTE")

class Mecanico(Utilizador):
    def __init__(self, id, nome, email):
        super().__init__(id, nome, email, "ROLE_MECANICO")

class Gestor(Utilizador):
    def __init__(self, id, nome, email):
        super().__init__(id, nome, email, "ROLE_GESTOR")