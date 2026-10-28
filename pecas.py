
from auth import (
    ErroNegocio,
    PermissaoNegada,
    como_decimal,
    como_int,
    exigir_role,
)
from db import consultar, executar, transacao
from modelos import Gestor, Mecanico

STOCK_MINIMO = 5


def tem_stock(peca_id, quantidade_pedida):
    linha = consultar("SELECT quantidade FROM pecas WHERE id=%s", (peca_id,), um=True)
    return bool(linha) and linha["quantidade"] >= quantidade_pedida


def registar_peca(dados, sessao):
    exigir_role(sessao, Gestor.ROLE)
    nome = (dados.get("nome") or "").strip()
    codigo = (dados.get("codigo") or "").strip().upper()
    if not nome or not codigo:
        raise ErroNegocio("Nome e código são obrigatórios.")
    preco = como_decimal(dados.get("preco"), "preco")
    quantidade = como_int(dados.get("quantidade"), "quantidade")
    if quantidade < 0:
        raise ErroNegocio("A quantidade não pode ser negativa.")
    if consultar("SELECT id FROM pecas WHERE codigo=%s", (codigo,), um=True):
        raise ErroNegocio("Já existe uma peça com esse código.")
    novo_id = executar(
        "INSERT INTO pecas (nome, codigo, preco, quantidade) VALUES (%s, %s, %s, %s)",
        (nome, codigo, preco, quantidade),
    )
    return {"id": novo_id, "mensagem": "Peça registada."}


def listar_pecas(dados, sessao):
    exigir_role(sessao, Gestor.ROLE, Mecanico.ROLE)
    return {
        "pecas": consultar(
            "SELECT id, nome, codigo, preco, quantidade FROM pecas ORDER BY nome"
        )
    }


def atualizar_peca(dados, sessao):
    exigir_role(sessao, Gestor.ROLE)
    peca_id = como_int(dados.get("id"), "id")
    if not consultar("SELECT id FROM pecas WHERE id=%s", (peca_id,), um=True):
        raise ErroNegocio("Peça não encontrada.")

    campos, valores = [], []
    if dados.get("preco") not in (None, ""):
        campos.append("preco=%s")
        valores.append(como_decimal(dados["preco"], "preco"))
    if dados.get("quantidade") not in (None, ""):
        quantidade = como_int(dados["quantidade"], "quantidade")
        if quantidade < 0:
            raise ErroNegocio("A quantidade não pode ser negativa.")
        campos.append("quantidade=%s")
        valores.append(quantidade)
    if not campos:
        raise ErroNegocio("Nada para atualizar.")

    valores.append(peca_id)
    executar(f"UPDATE pecas SET {', '.join(campos)} WHERE id=%s", tuple(valores))
    return {"mensagem": "Peça atualizada."}


def verificar_stock(dados, sessao):
    exigir_role(sessao, Gestor.ROLE, Mecanico.ROLE)
    peca_id = como_int(dados.get("peca_id"), "peca_id")
    quantidade = como_int(dados.get("quantidade"), "quantidade")
    return {"disponivel": tem_stock(peca_id, quantidade)}


def usar_peca(dados, sessao):
    user = exigir_role(sessao, Mecanico.ROLE, Gestor.ROLE)
    reparacao_id = como_int(dados.get("reparacao_id"), "reparacao_id")
    peca_id = como_int(dados.get("peca_id"), "peca_id")
    quantidade = como_int(dados.get("quantidade"), "quantidade")
    if quantidade <= 0:
        raise ErroNegocio("A quantidade tem de ser maior que zero.")

    rep = consultar(
        "SELECT id, mecanico_id FROM reparacoes WHERE id=%s", (reparacao_id,), um=True
    )
    if not rep:
        raise ErroNegocio("Reparação não encontrada.")
    if user.ROLE == Mecanico.ROLE and rep["mecanico_id"] != user.id:
        raise PermissaoNegada("Esta reparação não está atribuída a ti.")

    with transacao() as cur:
        cur.execute("SELECT nome, quantidade FROM pecas WHERE id=%s FOR UPDATE", (peca_id,))
        peca = cur.fetchone()
        if not peca:
            raise ErroNegocio("Peça não encontrada.")
        if peca["quantidade"] < quantidade:
            raise ErroNegocio(f"Stock insuficiente (disponível: {peca['quantidade']}).")
        novo_stock = peca["quantidade"] - quantidade
        cur.execute(
            "INSERT INTO reparacao_pecas (reparacao_id, peca_id, quantidade) VALUES (%s, %s, %s)",
            (reparacao_id, peca_id, quantidade),
        )
        cur.execute("UPDATE pecas SET quantidade=%s WHERE id=%s", (novo_stock, peca_id))

    resposta = {"mensagem": "Peça registada na reparação."}
    if novo_stock < STOCK_MINIMO:
        resposta["alerta"] = "ALERTA_STOCK_BAIXO"
        resposta["peca"] = peca["nome"]
        resposta["stock_atual"] = novo_stock
    return resposta


ACOES = {
    "REGISTAR_PECA": registar_peca,
    "LISTAR_PECAS": listar_pecas,
    "ATUALIZAR_PECA": atualizar_peca,
    "VERIFICAR_STOCK": verificar_stock,
    "USAR_PECA": usar_peca,
}
