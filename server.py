import json
import socket
import threading
from decimal import Decimal

import auth
import faturas
import funcionarios
import pecas
import veiculos
from auth import ErroNegocio, criar_primeiro_gestor
from db import criar_tabelas

HOST = "0.0.0.0"
PORT = 5000

# Junta as ações de todos os módulos num único dicionário.
# Quando houver um módulo de reparações, basta acrescentá-lo aqui.
ACOES = {}
for modulo in (auth, funcionarios, veiculos, pecas, faturas):
    ACOES.update(modulo.ACOES)


def _serializar(obj):
    """Converte tipos que o JSON não conhece (Decimal, datas...)."""
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)


def enviar(sock, resposta):
    texto = json.dumps(resposta, default=_serializar, ensure_ascii=False)
    sock.sendall((texto + "\n").encode("utf-8"))


def processar(mensagem, sessao):
    acao = mensagem.get("acao")
    dados = mensagem.get("dados") or {}
    funcao = ACOES.get(acao)
    if funcao is None:
        raise ErroNegocio(f"Ação '{acao}' não reconhecida.")
    resultado = funcao(dados, sessao) or {}
    return {"status": "sucesso", **resultado}


def tratar_cliente(sock, endereco):
    print(f"[+] Cliente ligado: {endereco}")
    sessao = {"utilizador": None}  # cada ligação tem a sua sessão
    try:
        with sock, sock.makefile("r", encoding="utf-8", newline="\n") as leitura:
            for linha in leitura:  # um pedido JSON por linha
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    resposta = processar(json.loads(linha), sessao)
                except json.JSONDecodeError:
                    resposta = {"status": "erro", "mensagem": "Pedido inválido."}
                except ErroNegocio as e:
                    resposta = {"status": "erro", "mensagem": str(e)}
                except Exception as e:
                    print(f"[!] Erro interno com {endereco}: {e!r}")
                    resposta = {"status": "erro", "mensagem": "Erro interno do servidor."}
                enviar(sock, resposta)
    except OSError as e:
        print(f"[!] Ligação com {endereco} perdida: {e}")
    finally:
        print(f"[-] Conexão fechada com {endereco}")


def iniciar_servidor():
    criar_tabelas()
    criar_primeiro_gestor()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(5)
    print(f"Servidor a ouvir na porta {PORT}")

    try:
        while True:
            sock, endereco = servidor.accept()
            threading.Thread(
                target=tratar_cliente, args=(sock, endereco), daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\nA encerrar o servidor...")
    finally:
        servidor.close()


if __name__ == "__main__":
    iniciar_servidor()
