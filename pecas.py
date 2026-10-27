from connect import start_connection

def registar_peca(nome, codigo, preco, quantidade):
    conexao = start_connection()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO pecas (nome, codigo, preco, quantidade) VALUES (%s, %s, %s, %s)", (nome, codigo, preco, quantidade))
    conexao.commit()
    conexao.close()
    return {"status": "sucesso"}

def listar_pecas():
    conexao = start_connection()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, codigo, preco, quantidade FROM pecas")
    pecas = cursor.fetchall()
    conexao.close()
    return [(peca_id, nome, codigo, float(preco), quantidade) for peca_id, nome, codigo, preco, quantidade in pecas]

def atualizar_peca(peca_id, preco, quantidade):
    conexao = start_connection()
    cursor = conexao.cursor()
    cursor.execute("UPDATE pecas SET preco=%s, quantidade=%s WHERE id=%s", (preco, quantidade, peca_id))
    conexao.commit()
    conexao.close()
    return {"status": "sucesso"}

def tem_stock(peca_id, quantidade_pedida):
    conexao = start_connection()
    cursor = conexao.cursor()
    cursor.execute("SELECT quantidade FROM pecas WHERE id=%s", (peca_id,))
    quantidade_atual = cursor.fetchone()[0]
    conexao.close()
    return quantidade_atual >= quantidade_pedida

def usar_peca(reparacao_id, peca_id, quantidade_usada):
    conexao = start_connection()
    cursor = conexao.cursor()
    cursor.execute("SELECT nome, quantidade FROM pecas WHERE id=%s", (peca_id,))
    nome_peca, stock_atual = cursor.fetchone()
    if stock_atual < quantidade_usada:
        conexao.close()
        return {"status": "erro", "mensagem": "Stock insuficiente."}
    novo_stock = stock_atual - quantidade_usada
    cursor.execute("INSERT INTO reparacao_pecas (reparacao_id, peca_id, quantidade_utilizada) VALUES (%s, %s, %s)", (reparacao_id, peca_id, quantidade_usada))
    cursor.execute("UPDATE pecas SET quantidade=%s WHERE id=%s", (novo_stock, peca_id))
    conexao.commit()
    conexao.close()
    if novo_stock < 5:
        return {"status": "sucesso", "alerta": "ALERTA_STOCK_BAIXO", "peca": nome_peca}
    return {"status": "sucesso"}