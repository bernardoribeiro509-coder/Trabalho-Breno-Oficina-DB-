
from auth import (
    ErroNegocio,
    como_int,
    criar_utilizador,
    exigir_role,
    hash_password,
)
from db import consultar, executar
from modelos import Gestor, Mecanico

ROLES_FUNCIONARIO = (Mecanico.ROLE, Gestor.ROLE)


def _total_gestores():
    linha = consultar(
        "SELECT COUNT(*) AS total FROM utilizadores WHERE role=%s", (Gestor.ROLE,), um=True
    )
    return linha["total"]


def _obter_funcionario(id_):
    id_ = como_int(id_, "id")
    linha = consultar("SELECT * FROM utilizadores WHERE id=%s", (id_,), um=True)
    if not linha or linha["role"] not in ROLES_FUNCIONARIO:
        raise ErroNegocio("Funcionário não encontrado.")
    return linha


def listar_funcionarios(dados, sessao):
    exigir_role(sessao, Gestor.s)
    return {
        "funcionarios": consultar(
            "SELECT id, username, nome, role FROM utilizadores "
            "WHERE role IN (%s, %s) ORDER BY nome",
            ROLES_FUNCIONARIO,
        )
    }


def adicionar_funcionario(dados, sessao):
    exigir_role(sessao, Gestor.ROLE)
    role = dados.get("role")
    if role not in ROLES_FUNCIONARIO:
        raise ErroNegocio("O role tem de ser ROLE_MECANICO ou ROLE_GESTOR.")
    novo_id = criar_utilizador(
        dados.get("username"), dados.get("password"), dados.get("nome"), role
    )
    return {"id": novo_id, "mensagem": "Funcionário adicionado."}


def remover_funcionario(dados, sessao):
    gestor = exigir_role(sessao, Gestor.ROLE)
    func = _obter_funcionario(dados.get("id"))
    if func["id"] == gestor.id:
        raise ErroNegocio("Não podes remover a tua própria conta.")
    if func["role"] == Gestor.ROLE and _total_gestores() <= 1:
        raise ErroNegocio("Não podes remover o último gestor.")
    executar("DELETE FROM utilizadores WHERE id=%s", (func["id"],))
    return {"mensagem": "Funcionário removido."}


def atualizar_funcionario(dados, sessao):
    exigir_role(sessao, Gestor.ROLE)
    func = _obter_funcionario(dados.get("id"))

    campos, valores = [], []
    if dados.get("nome"):
        campos.append("nome=%s")
        valores.append(dados["nome"].strip())
    if dados.get("password"):
        if len(dados["password"]) < 6:
            raise ErroNegocio("A password tem de ter pelo menos 6 caracteres.")
        campos.append("password_hash=%s")
        valores.append(hash_password(dados["password"]))
    if dados.get("role"):
        if dados["role"] not in ROLES_FUNCIONARIO:
            raise ErroNegocio("O role tem de ser ROLE_MECANICO ou ROLE_GESTOR.")
        if (
            func["role"] == Gestor.ROLE
            and dados["role"] != Gestor.ROLE
            and _total_gestores() <= 1
        ):
            raise ErroNegocio("Não podes tirar o role ao último gestor.")
        campos.append("role=%s")
        valores.append(dados["role"])

    if not campos:
        raise ErroNegocio("Nada para atualizar.")
    valores.append(func["id"])
    executar(f"UPDATE utilizadores SET {', '.join(campos)} WHERE id=%s", tuple(valores))
    return {"mensagem": "Funcionário atualizado."}


def listar_mecanicos(dados, sessao):
    exigir_role(sessao, Gestor.ROLE)
    return {
        "mecanicos": consultar(
            "SELECT id, username, nome FROM utilizadores WHERE role=%s ORDER BY nome",
            (Mecanico.ROLE,),
        )
    }


ACOES = {
    "LISTAR_FUNCIONARIOS": listar_funcionarios,
    "ADICIONAR_FUNCIONARIO": adicionar_funcionario,
    "REMOVER_FUNCIONARIO": remover_funcionario,
    "ATUALIZAR_FUNCIONARIO": atualizar_funcionario,
    "LISTAR_MECANICOS": listar_mecanicos,
}
