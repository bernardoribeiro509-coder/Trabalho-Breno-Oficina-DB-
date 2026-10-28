
from datetime import date, datetime

from auth import ErroNegocio, PermissaoNegada, como_int, exigir_login, exigir_role
from db import consultar, executar
from modelos import Cliente, Gestor, Mecanico

ESTADOS = ("Agendada", "Em curso", "Concluída")


def _obter(user, veiculo_id):
    veiculo_id = como_int(veiculo_id, "veiculo_id")
    v = consultar("SELECT * FROM veiculos WHERE id=%s", (veiculo_id,), um=True)
    if not v:
        raise ErroNegocio("Veículo não encontrado.")
    if user.ROLE == Cliente.ROLE and v["cliente_id"] != user.id:
        raise PermissaoNegada("Não tens permissão para aceder a este veículo.")
    return v


def registar_veiculo(dados, sessao):
    user = exigir_role(sessao, Cliente.ROLE, Gestor.ROLE)

    if user.ROLE == Cliente.ROLE:
        cliente_id = user.id
    else:
        cliente_id = como_int(dados.get("cliente_id"), "cliente_id")
        dono = consultar(
            "SELECT id FROM utilizadores WHERE id=%s AND role=%s",
            (cliente_id, Cliente.ROLE),
            um=True,
        )
        if not dono:
            raise ErroNegocio("Cliente não encontrado.")

    marca = (dados.get("marca") or "").strip()
    modelo = (dados.get("modelo") or "").strip()
    matricula = (dados.get("matricula") or "").strip().upper()
    if not marca or not modelo:
        raise ErroNegocio("Marca e modelo são obrigatórios.")

    partes = matricula.split("-")
    if len(partes) != 3 or not all(len(p) == 2 and p.isalnum() for p in partes):
        raise ErroNegocio("Matrícula inválida (formato AA-00-AA).")
    if consultar("SELECT id FROM veiculos WHERE matricula=%s", (matricula,), um=True):
        raise ErroNegocio("Já existe um veículo com essa matrícula.")

    novo_id = executar(
        "INSERT INTO veiculos (marca, modelo, matricula, quilometragem, cliente_id) "
        "VALUES (%s, %s, %s, 0, %s)",
        (marca, modelo, matricula, cliente_id),
    )
    return {"mensagem": "Veículo registado.", "veiculo": _obter(user, novo_id)}


def atualizar_veiculo(dados, sessao):
    user = exigir_login(sessao)
    v = _obter(user, dados.get("veiculo_id"))
    km = como_int(dados.get("quilometragem"), "quilometragem")
    if km < v["quilometragem"]:
        raise ErroNegocio("A quilometragem não pode ser inferior à atual.")
    executar("UPDATE veiculos SET quilometragem=%s WHERE id=%s", (km, v["id"]))
    return {"mensagem": "Quilometragem atualizada.", "veiculo": _obter(user, v["id"])}


def listar_veiculos(dados, sessao):
    user = exigir_login(sessao)
    if user.ROLE == Cliente.ROLE:
        veiculos = consultar(
            "SELECT * FROM veiculos WHERE cliente_id=%s ORDER BY id", (user.id,)
        )
    else:
        veiculos = consultar("SELECT * FROM veiculos ORDER BY id")
    return {"veiculos": veiculos}


def historico_veiculo(dados, sessao):
    user = exigir_login(sessao)
    v = _obter(user, dados.get("veiculo_id"))
    reparacoes = consultar(
        "SELECT r.*, u.nome AS mecanico_nome FROM reparacoes r "
        "LEFT JOIN utilizadores u ON u.id = r.mecanico_id "
        "WHERE r.veiculo_id=%s ORDER BY r.id DESC",
        (v["id"],),
    )
    return {"reparacoes": reparacoes}


def remover_veiculo(dados, sessao):
    user = exigir_role(sessao, Gestor.ROLE)
    v = _obter(user, dados.get("veiculo_id"))
    em_uso = consultar(
        "SELECT COUNT(*) AS total FROM reparacoes WHERE veiculo_id=%s", (v["id"],), um=True
    )
    if em_uso["total"] > 0:
        raise ErroNegocio("Este veículo tem reparações associadas e não pode ser removido.")
    executar("DELETE FROM veiculos WHERE id=%s", (v["id"],))
    return {"mensagem": "Veículo removido."}

SELECT_REPARACOES = (
    "SELECT r.id, r.data, r.tipo_servico, r.estado, r.observacoes, "
    "r.veiculo_id, v.matricula, v.marca, v.modelo, "
    "r.cliente_id, c.nome AS cliente_nome, "
    "r.mecanico_id, m.nome AS mecanico_nome "
    "FROM reparacoes r "
    "JOIN veiculos v ON v.id = r.veiculo_id "
    "JOIN utilizadores c ON c.id = r.cliente_id "
    "LEFT JOIN utilizadores m ON m.id = r.mecanico_id "
)


def _obter_reparacao(user, reparacao_id):
    reparacao_id = como_int(reparacao_id, "reparacao_id")
    r = consultar("SELECT * FROM reparacoes WHERE id=%s", (reparacao_id,), um=True)
    if not r:
        raise ErroNegocio("Reparação não encontrada.")
    if user.ROLE == Mecanico.ROLE and r["mecanico_id"] != user.id:
        raise PermissaoNegada("Esta reparação não está atribuída a ti.")
    if user.ROLE == Cliente.ROLE and r["cliente_id"] != user.id:
        raise PermissaoNegada("Não tens permissão para aceder a esta reparação.")
    return r


def _validar_mecanico(mecanico_id):
    mecanico_id = como_int(mecanico_id, "mecanico_id")
    m = consultar(
        "SELECT id FROM utilizadores WHERE id=%s AND role=%s",
        (mecanico_id, Mecanico.ROLE),
        um=True,
    )
    if not m:
        raise ErroNegocio("Mecânico não encontrado.")
    return mecanico_id


def criar_reparacao(dados, sessao):
    exigir_role(sessao, Gestor.ROLE)
    veiculo_id = como_int(dados.get("veiculo_id"), "veiculo_id")
    veiculo = consultar("SELECT * FROM veiculos WHERE id=%s", (veiculo_id,), um=True)
    if not veiculo:
        raise ErroNegocio("Veículo não encontrado.")

    tipo = (dados.get("tipo_servico") or "").strip()
    if not tipo:
        raise ErroNegocio("O tipo de serviço é obrigatório.")

    texto_data = (dados.get("data") or "").strip()
    if texto_data:
        try:
            data = datetime.strptime(texto_data, "%Y-%m-%d").date()
        except ValueError:
            raise ErroNegocio("Data inválida (formato AAAA-MM-DD).")
    else:
        data = date.today()

    mecanico_id = None
    if str(dados.get("mecanico_id") or "").strip():
        mecanico_id = _validar_mecanico(dados["mecanico_id"])

    novo_id = executar(
        "INSERT INTO reparacoes (data, tipo_servico, veiculo_id, cliente_id, mecanico_id, estado) "
        "VALUES (%s, %s, %s, %s, %s, 'Agendada')",
        (data, tipo, veiculo_id, veiculo["cliente_id"], mecanico_id),
    )
    return {"id": novo_id, "mensagem": "Reparação criada."}


def atribuir_mecanico(dados, sessao):
    user = exigir_role(sessao, Gestor.ROLE)
    r = _obter_reparacao(user, dados.get("reparacao_id"))
    mecanico_id = _validar_mecanico(dados.get("mecanico_id"))
    executar("UPDATE reparacoes SET mecanico_id=%s WHERE id=%s", (mecanico_id, r["id"]))
    return {"mensagem": "Mecânico atribuído."}


def listar_reparacoes(dados, sessao):
    user = exigir_login(sessao)
    if user.ROLE == Gestor.ROLE:
        reparacoes = consultar(SELECT_REPARACOES + "ORDER BY r.id DESC")
    elif user.ROLE == Mecanico.ROLE:
        reparacoes = consultar(
            SELECT_REPARACOES + "WHERE r.mecanico_id=%s ORDER BY r.id DESC", (user.id,)
        )
    else:
        reparacoes = consultar(
            SELECT_REPARACOES + "WHERE r.cliente_id=%s ORDER BY r.id DESC", (user.id,)
        )
    return {"reparacoes": reparacoes}


def atualizar_estado_reparacao(dados, sessao):
    user = exigir_role(sessao, Mecanico.ROLE, Gestor.ROLE)
    r = _obter_reparacao(user, dados.get("reparacao_id"))
    estado = (dados.get("estado") or "").strip()
    if estado not in ESTADOS:
        raise ErroNegocio("Estado inválido. Usa: " + ", ".join(ESTADOS) + ".")
    if estado == "Concluída" and not r["mecanico_id"]:
        raise ErroNegocio("Atribui um mecânico antes de concluir a reparação.")
    executar("UPDATE reparacoes SET estado=%s WHERE id=%s", (estado, r["id"]))
    return {"mensagem": f"Estado atualizado para {estado}."}


def adicionar_observacoes(dados, sessao):
    user = exigir_role(sessao, Mecanico.ROLE, Gestor.ROLE)
    r = _obter_reparacao(user, dados.get("reparacao_id"))
    texto = (dados.get("observacoes") or "").strip()
    if not texto:
        raise ErroNegocio("Escreve as observações.")
    atuais = (r["observacoes"] or "").strip()
    novas = f"{atuais}\n{texto}" if atuais else texto
    executar("UPDATE reparacoes SET observacoes=%s WHERE id=%s", (novas, r["id"]))
    return {"mensagem": "Observações guardadas."}


ACOES = {
    "REGISTAR_VEICULO": registar_veiculo,
    "ATUALIZAR_VEICULO": atualizar_veiculo,
    "LISTAR_VEICULOS": listar_veiculos,
    "HISTORICO_VEICULO": historico_veiculo,
    "REMOVER_VEICULO": remover_veiculo,
    "CRIAR_REPARACAO": criar_reparacao,
    "ATRIBUIR_MECANICO": atribuir_mecanico,
    "LISTAR_REPARACOES": listar_reparacoes,
    "ATUALIZAR_ESTADO_REPARACAO": atualizar_estado_reparacao,
    "ADICIONAR_OBSERVACOES": adicionar_observacoes,
}
