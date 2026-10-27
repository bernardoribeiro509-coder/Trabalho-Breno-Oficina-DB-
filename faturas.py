"""Faturação e relatórios."""
from auth import (
    ErroNegocio,
    PermissaoNegada,
    como_decimal,
    como_int,
    exigir_login,
    exigir_role,
)
from db import consultar, executar
from modelos import Cliente, Gestor

METODOS_PAGAMENTO = ("Dinheiro", "Cartão", "MB Way", "Transferência")


def calcular_custo_pecas(reparacao_id):
    linha = consultar(
        "SELECT COALESCE(SUM(rp.quantidade * p.preco), 0) AS total "
        "FROM reparacao_pecas rp JOIN pecas p ON p.id = rp.peca_id "
        "WHERE rp.reparacao_id=%s",
        (reparacao_id,),
        um=True,
    )
    return linha["total"]


def calcular_total(custo_pecas, custo_servico):
    return custo_pecas + custo_servico


def gerar_fatura(dados, sessao):
    exigir_role(sessao, Gestor.ROLE)
    reparacao_id = como_int(dados.get("reparacao_id"), "reparacao_id")
    custo_servico = como_decimal(dados.get("custo_servico"), "custo_servico")

    rep = consultar(
        "SELECT id, estado FROM reparacoes WHERE id=%s", (reparacao_id,), um=True
    )
    if not rep:
        raise ErroNegocio("Reparação não encontrada.")
    if rep["estado"] != "Concluída":
        raise ErroNegocio("Só se podem faturar reparações concluídas.")
    if consultar("SELECT id FROM faturas WHERE reparacao_id=%s", (reparacao_id,), um=True):
        raise ErroNegocio("Esta reparação já tem fatura.")

    custo_pecas = calcular_custo_pecas(reparacao_id)
    total = calcular_total(custo_pecas, custo_servico)
    fatura_id = executar(
        "INSERT INTO faturas (reparacao_id, custo_pecas, custo_servico, valor_total, data_emissao) "
        "VALUES (%s, %s, %s, %s, CURDATE())",
        (reparacao_id, custo_pecas, custo_servico, total),
    )
    return {
        "mensagem": "Fatura criada.",
        "id": fatura_id,
        "custo_pecas": custo_pecas,
        "custo_servico": custo_servico,
        "valor_total": total,
    }


def registar_pagamento(dados, sessao):
    exigir_role(sessao, Gestor.ROLE)
    fatura_id = como_int(dados.get("fatura_id"), "fatura_id")
    metodo = (dados.get("metodo") or "").strip()
    if metodo not in METODOS_PAGAMENTO:
        raise ErroNegocio("Método inválido. Usa: " + ", ".join(METODOS_PAGAMENTO) + ".")

    fatura = consultar("SELECT id, pago FROM faturas WHERE id=%s", (fatura_id,), um=True)
    if not fatura:
        raise ErroNegocio("Fatura não encontrada.")
    if fatura["pago"]:
        raise ErroNegocio("Esta fatura já foi paga.")

    executar(
        "UPDATE faturas SET pago=TRUE, metodo_pagamento=%s WHERE id=%s",
        (metodo, fatura_id),
    )
    return {"mensagem": "Pagamento registado."}


def listar_faturas(dados, sessao):
    """Gestor vê todas; cliente vê só as suas."""
    user = exigir_login(sessao)
    if user.ROLE == Gestor.ROLE:
        faturas = consultar("SELECT * FROM faturas ORDER BY id DESC")
    elif user.ROLE == Cliente.ROLE:
        faturas = consultar(
            "SELECT f.* FROM faturas f JOIN reparacoes r ON r.id = f.reparacao_id "
            "WHERE r.cliente_id=%s ORDER BY f.id DESC",
            (user.id,),
        )
    else:
        raise PermissaoNegada("Não tens permissão para esta operação.")
    return {"faturas": faturas}


def ver_fatura(dados, sessao):
    """Fatura de uma reparação (o cliente só vê as suas)."""
    user = exigir_login(sessao)
    reparacao_id = como_int(dados.get("reparacao_id"), "reparacao_id")
    rep = consultar(
        "SELECT cliente_id FROM reparacoes WHERE id=%s", (reparacao_id,), um=True
    )
    if not rep:
        raise ErroNegocio("Reparação não encontrada.")
    if user.ROLE == Cliente.ROLE and rep["cliente_id"] != user.id:
        raise PermissaoNegada("Não tens permissão para ver esta fatura.")
    fatura = consultar(
        "SELECT * FROM faturas WHERE reparacao_id=%s", (reparacao_id,), um=True
    )
    if not fatura:
        raise ErroNegocio("Esta reparação ainda não tem fatura.")
    return {"fatura": fatura}


def historico_reparacoes(dados, sessao):
    exigir_role(sessao, Gestor.ROLE)
    return {"reparacoes": consultar("SELECT * FROM reparacoes ORDER BY id DESC")}


ACOES = {
    "GERAR_FATURA": gerar_fatura,
    "REGISTAR_PAGAMENTO": registar_pagamento,
    "LISTAR_FATURAS": listar_faturas,
    "VER_FATURA": ver_fatura,
    "HISTORICO_REPARACOES": historico_reparacoes,
}
