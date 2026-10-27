import socket
import json
 
HOST = '127.0.0.1'  # Muda para o IP do PC onde corre o servidor
PORT = 5000
 
 
def enviar(sock, acao, dados=None):
    """Envia um pedido JSON ao servidor e devolve a resposta (dict)."""
    pedido = {"acao": acao, "dados": dados or {}}
    sock.sendall(json.dumps(pedido).encode('utf-8'))
    resposta = sock.recv(4096)
    if not resposta:
        raise ConnectionError("O servidor fechou a ligação.")
    return json.loads(resposta.decode('utf-8'))
 
 
def fazer_login(sock):
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    resposta = enviar(sock, "LOGIN", {"email": email, "password": password})
 
    if resposta.get("status") == "sucesso":
        print(f"\nBem-vindo, {resposta['nome']} ({resposta['role']})\n")
        return resposta
    print(f"Erro: {resposta.get('mensagem')}")
    return None
 
 
def adicionar_funcionario(sock):
    nome = input("Nome: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    tipo = input("Tipo (ex: ROLE_FUNCIONARIO / ROLE_GESTOR): ").strip()
    resposta = enviar(sock, "ADICIONAR_FUNCIONARIO", {
        "nome": nome, "email": email, "password": password, "tipo": tipo
    })
    print(resposta.get("mensagem"))
 
 
def atualizar_funcionario(sock):
    user_id = input("ID do funcionário: ").strip()
    nome = input("Novo nome: ").strip()
    email = input("Novo email: ").strip()
    resposta = enviar(sock, "ATUALIZAR_FUNCIONARIO", {
        "id": user_id, "nome": nome, "email": email
    })
    print(resposta.get("mensagem"))
 
 
def remover_funcionario(sock):
    user_id = input("ID do funcionário a remover: ").strip()
    resposta = enviar(sock, "REMOVER_FUNCIONARIO", {"id": user_id})
    print(resposta.get("mensagem"))
 
 
def menu_gestor(sock):
    opcoes = {
        "1": adicionar_funcionario,
        "2": atualizar_funcionario,
        "3": remover_funcionario,
    }
    while True:
        print("\n--- Menu Gestor ---")
        print("1. Adicionar funcionário")
        print("2. Atualizar funcionário")
        print("3. Remover funcionário")
        print("0. Sair")
        escolha = input("Opção: ").strip()
 
        if escolha == "0":
            break
        funcao = opcoes.get(escolha)
        if funcao:
            funcao(sock)
        else:
            print("Opção inválida.")
 
 
def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"Não foi possível ligar a {HOST}:{PORT}. O servidor está a correr?")
        return
 
    print(f"Ligado ao servidor {HOST}:{PORT}")
 
    try:
        utilizador = None
        while utilizador is None:
            utilizador = fazer_login(sock)
 
        if utilizador["role"] == "ROLE_GESTOR":
            menu_gestor(sock)
        else:
            print("Este perfil ainda não tem funcionalidades disponíveis.")
    except (ConnectionError, OSError) as e:
        print(f"Ligação perdida: {e}")
    except KeyboardInterrupt:
        print("\nA sair...")
    finally:
        sock.close()
        print("Ligação terminada.")
 
 
if __name__ == "__main__":
    main()



print("esta a rodar")