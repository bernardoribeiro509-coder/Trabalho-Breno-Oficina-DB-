"""Acesso à base de dados. Todos os módulos da equipa usam este ficheiro."""
from contextlib import contextmanager

from pymysql.cursors import DictCursor

from connect import start_connection

TABELAS = [
    """
    CREATE TABLE IF NOT EXISTS utilizadores (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        nome VARCHAR(100) NOT NULL,
        role VARCHAR(20) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS veiculos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        marca VARCHAR(50) NOT NULL,
        modelo VARCHAR(50) NOT NULL,
        matricula VARCHAR(20) NOT NULL UNIQUE,
        quilometragem INT NOT NULL DEFAULT 0,
        cliente_id INT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reparacoes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        data DATE NOT NULL,
        tipo_servico VARCHAR(100) NOT NULL,
        veiculo_id INT NOT NULL,
        cliente_id INT NOT NULL,
        mecanico_id INT NULL,
        estado VARCHAR(20) NOT NULL DEFAULT 'Agendada',
        observacoes TEXT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pecas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        codigo VARCHAR(50) NOT NULL UNIQUE,
        preco DECIMAL(10,2) NOT NULL,
        quantidade INT NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reparacao_pecas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        reparacao_id INT NOT NULL,
        peca_id INT NOT NULL,
        quantidade INT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS faturas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        reparacao_id INT NOT NULL,
        valor_total DECIMAL(10,2) NOT NULL,
        pago BOOLEAN NOT NULL DEFAULT FALSE,
        metodo_pagamento VARCHAR(30) NULL,
        data_emissao DATE NOT NULL
    )
    """,
]


def criar_tabelas():
    conn = start_connection()
    try:
        with conn.cursor() as cur:
            for sql in TABELAS:
                cur.execute(sql)
        conn.commit()
    finally:
        conn.close()


def consultar(sql, params=(), um=False):
    """SELECT. Devolve uma lista de dicionários (ou um só dicionário se um=True)."""
    conn = start_connection()
    try:
        with conn.cursor(DictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchone() if um else cur.fetchall()
    finally:
        conn.close()


def executar(sql, params=()):
    """INSERT/UPDATE/DELETE. Devolve o id gerado (lastrowid)."""
    conn = start_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


@contextmanager
def transacao():
    """Para operações com vários passos (ex.: abater stock + registar peça usada).

    with transacao() as cur:
        cur.execute(...)
        cur.execute(...)
    Faz commit no fim, ou rollback se houver erro.
    """
    conn = start_connection()
    try:
        with conn.cursor(DictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
