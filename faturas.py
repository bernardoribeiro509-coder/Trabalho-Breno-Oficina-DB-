from connect import start_connection

def calcular_custo(reparacao_id):
    c = start_connection(); 
    cur = c.cursor()
    cur.execute("""SELECT ts.preco_mao_de_obra + COALESCE(SUM(rp.quantidade * rp.preco_unitario), 0)
                   FROM reparacoes r
                   JOIN tipos_servico ts ON ts.id = r.tipo_servico_id
                   LEFT JOIN reparacao_pecas rp ON rp.reparacao_id = r.id
                   WHERE r.id=%s GROUP BY ts.preco_mao_de_obra""", (reparacao_id,))
    total = float(cur.fetchone()[0])
    c.close()
    return total

def gerar_fatura(reparacao_id):
    total = calcular_custo(reparacao_id)
    c = start_connection(); cur = c.cursor()
    cur.execute("INSERT INTO faturas (reparacao_id, total) VALUES (%s,%s)", (reparacao_id, total))
    c.commit(); c.close()
    return {"status": "sucesso", "total": total}

def registar_pagamento(reparacao_id, valor, metodo):
    c = start_connection(); cur = c.cursor()
    cur.execute("INSERT INTO pagamentos (reparacao_id, valor, metodo) VALUES (%s,%s,%s)", (reparacao_id, valor, metodo))
    c.commit(); c.close()
    return {"status": "sucesso"}

def historico_reparacoes():
    c = start_connection(); cur = c.cursor()
    cur.execute("SELECT id, data_agendada, estado, veiculo_id FROM reparacoes")
    r = cur.fetchall()
    c.close()
    return r

def historico_faturas():
    c = start_connection(); cur = c.cursor()
    cur.execute("SELECT id, reparacao_id, total FROM faturas")
    r = [(i, rep, float(t)) for i, rep, t in cur.fetchall()]
    c.close()
    return r