from connect import start_connection

def registar_peca(nome, codigo, preco, quantidade):
    c = start_connection(); cur = c.cursor()
    cur.execute("INSERT INTO pecas (nome, codigo, preco, quantidade) VALUES (%s,%s,%s,%s)", (nome, codigo, preco, quantidade))
    c.commit(); c.close()
    return {"status": "sucesso"}

def listar_pecas():
    c = start_connection(); cur = c.cursor()
    cur.execute("SELECT id, nome, codigo, preco, quantidade FROM pecas")
    r = [(i, n, cod, float(p), q) for i, n, cod, p, q in cur.fetchall()]
    c.close()
    return r

def atualizar_peca(peca_id, preco, quantidade):
    c = start_connection(); cur = c.cursor()
    cur.execute("UPDATE pecas SET preco=%s, quantidade=%s WHERE id=%s", (preco, quantidade, peca_id))
    c.commit(); c.close()
    return {"status": "sucesso"}

def tem_stock(peca_id, quantidade):
    c = start_connection(); cur = c.cursor()
    cur.execute("SELECT quantidade FROM pecas WHERE id=%s", (peca_id,))
    q = cur.fetchone()[0]
    c.close()
    return q >= quantidade

def usar_peca(reparacao_id, peca_id, quantidade):
    c = start_connection(); cur = c.cursor()
    cur.execute("SELECT preco, quantidade, nome FROM pecas WHERE id=%s", (peca_id,))
    preco, stock, nome = cur.fetchone()
    if stock < quantidade:
        c.close()
        return {"status": "erro", "mensagem": "Stock insuficiente."}
    cur.execute("INSERT INTO reparacao_pecas (reparacao_id, peca_id, quantidade, preco_unitario) VALUES (%s,%s,%s,%s)", (reparacao_id, peca_id, quantidade, preco))
    cur.execute("UPDATE pecas SET quantidade=%s WHERE id=%s", (stock - quantidade, peca_id))
    c.commit(); c.close()
    if stock - quantidade < 5:
        return {"status": "sucesso", "alerta": "ALERTA_STOCK_BAIXO", "peca": nome}
    return {"status": "sucesso"}