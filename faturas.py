from connect import start_connection

def calcular_total(custo_pecas, custo_servico):
    return custo_pecas + custo_servico


def gerar_fatura(id_reparacao, custo_pecas, custo_servico):

    total = calcular_total(
        custo_pecas,
        custo_servico
    )

    conn = start_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO faturas
    (id_reparacao,custo_pecas,custo_servico,total)
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(
        sql,
        (id_reparacao, custo_pecas, custo_servico, total)
    )

    conn.commit()

    print("Fatura criada!")
    print("Total:", total, "€")

    cursor.close()
    conn.close()


def registar_pagamento(id_fatura, metodo):

    conn = start_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE faturas
        SET metodo_pagamento=%s
        WHERE id=%s
        """,
        (metodo, id_fatura)
    )

    conn.commit()

    print("Pagamento registado!")

    cursor.close()
    conn.close()


def historico_faturas():

    conn = start_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM faturas")

    resultados = cursor.fetchall()

    for linha in resultados:
        print(linha)

    cursor.close()
    conn.close()


def historico_reparacoes():

    conn = start_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reparacoes")

    resultados = cursor.fetchall()

    for linha in resultados:
        print(linha)

    cursor.close()
    conn.close()