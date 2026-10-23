import socket
import threading
import json
import hashlib
from connect import start_connection

HOST = '0.0.0.0'
PORT = 5000

def fazer_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_primeiro_gestor():
    conexao = start_connection()
    cursor = conexao.cursor()
    cursor.execute("SELECT COUNT(*) FROM utilizadores WHERE role = 'ROLE_GESTOR'")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("\n[!] Sistema sem gestores. Precisa de um Gestor primeiro:")
        nome = input("Nome do primeiro Gestor: ")
        email = input("Email do primeiro Gestor: ")
        senha = input("Password do primeiro Gestor: ")
        senha_hash = fazer_hash(senha)
        
        cursor.execute(
            "INSERT INTO utilizadores (nome, email, senha, role) VALUES (%s, %s, %s, %s)",
            (nome, email, senha_hash, 'ROLE_GESTOR')
        )
        conexao.commit()
        print("Primeiro Gestor criado com sucesso na base de dados!\n")
        
    cursor.close()
    conexao.close()

def autenticar_utilizador(email, password):
    conexao = start_connection()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, senha, role FROM utilizadores WHERE email = %s", (email,))
    resultado = cursor.fetchone()
    cursor.close()
    conexao.close()
    
    if resultado:
        user_id, nome, senha_hash, role = resultado
        if senha_hash == fazer_hash(password):
            return {"status": "sucesso", "role": role, "id": user_id, "nome": nome}
            
    return {"status": "erro", "mensagem": "Email ou password incorretos."}

def gerir_funcionarios(acao, dados):
    conexao = start_connection()
    cursor = conexao.cursor()
    try:
        if acao == "ADICIONAR_FUNCIONARIO":
            nome = dados.get("nome")
            email = dados.get("email")
            password = fazer_hash(dados.get("password"))
            role = dados.get("tipo") 
            
            cursor.execute(
                "INSERT INTO utilizadores (nome, email, senha, role) VALUES (%s, %s, %s, %s)",
                (nome, email, password, role)
            )
            conexao.commit()
            return {"status": "sucesso", "mensagem": "Funcionário adicionado com sucesso."}
            
        elif acao == "ATUALIZAR_FUNCIONARIO":
            user_id = dados.get("id")
            nome = dados.get("nome")
            email = dados.get("email")
            
            cursor.execute(
                "UPDATE utilizadores SET nome = %s, email = %s WHERE id = %s",
                (nome, email, user_id)
            )
            conexao.commit()
            return {"status": "sucesso", "mensagem": "Funcionário atualizado com sucesso."}
            
        elif acao == "REMOVER_FUNCIONARIO":
            user_id = dados.get("id")
            cursor.execute("DELETE FROM utilizadores WHERE id = %s", (user_id,))
            conexao.commit()
            return {"status": "sucesso", "mensagem": "Funcionário removido com sucesso."}
            
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}
    finally:
        cursor.close()
        conexao.close()

def tratar_cliente(cliente_socket, endereco):
    print(f"[+] Cliente ligado: {endereco}")
    try:
        while True:
            dados_brutos = cliente_socket.recv(4096)
            if not dados_brutos:
                break
                
            mensagem = json.loads(dados_brutos.decode('utf-8'))
            acao = mensagem.get("acao")
            payload = mensagem.get("dados", {})
            
            resposta = {}
            if acao == "LOGIN":
                resposta = autenticar_utilizador(payload.get("email"), payload.get("password"))
            elif acao in ["ADICIONAR_FUNCIONARIO", "ATUALIZAR_FUNCIONARIO", "REMOVER_FUNCIONARIO"]:
                resposta = gerir_funcionarios(acao, payload)
            else:
                resposta = {"status": "erro", "mensagem": f"Ação '{acao}' não reconhecida pela Pessoa 1."}
                
            cliente_socket.sendall(json.dumps(resposta).encode('utf-8'))
    except Exception as e:
        print(f"Erro com o cliente {endereco}: {e}")
    finally:
        cliente_socket.close()
        print(f"Conexão fechada com {endereco}")

def iniciar_servidor():
    verificar_primeiro_gestor()
    
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(5)
    print(f"Servidor de Sockets a ouvir da porta {PORT}")
    
    try:
        while True:
            cliente_socket, endereco = servidor.accept()
            thread = threading.Thread(target=tratar_cliente, args=(cliente_socket, endereco))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nEncerrand o servidor...")
    finally:
        servidor.close()

if __name__ == "__main__":
    iniciar_servidor()