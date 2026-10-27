ROLE_CLIENTE = "ROLE_CLIENTE"
ROLE_MECANICO = "ROLE_MECANICO"
ROLE_GESTOR = "ROLE_GESTOR"


class Utilizador:
    """Classe base. Cada tipo de utilizador herda desta e define o seu ROLE."""

    ROLE = None
    DESCRICAO = "Utilizador"

    def __init__(self, id, username, nome):
        self.id = id
        self.username = username
        self.nome = nome

    def descricao(self):
        return f"{self.DESCRICAO}: {self.nome}"

    def para_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nome": self.nome,
            "role": self.ROLE,
        }

    @staticmethod
    def de_linha(linha):
        """Cria o objeto da subclasse certa a partir de uma linha da tabela utilizadores."""
        classe = _CLASSES.get(linha["role"])
        if classe is None:
            raise ValueError(f"Role desconhecido: {linha['role']}")
        return classe(linha["id"], linha["username"], linha["nome"])


class Cliente(Utilizador):
    ROLE = ROLE_CLIENTE
    DESCRICAO = "Cliente"


class Mecanico(Utilizador):
    ROLE = ROLE_MECANICO
    DESCRICAO = "Mecânico"


class Gestor(Utilizador):
    ROLE = ROLE_GESTOR
    DESCRICAO = "Gestor"


_CLASSES = {classe.ROLE: classe for classe in (Cliente, Mecanico, Gestor)}
ROLES = tuple(_CLASSES)
