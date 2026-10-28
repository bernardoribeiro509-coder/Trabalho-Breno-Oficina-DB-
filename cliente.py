import getpass
import json
import socket

HOST_POR_DEFEITO = "192.168.2.118"  
PORT = 5000


class Ligacao:

    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port), timeout=10)
        self.sock.settimeout(30)
        self.leitura = self.sock.makefile("r", encoding="utf-8", newline="\n")

    def enviar(self, acao, dados=None):
        pedido = json.dumps({"acao": acao, "dados": dados or {}}, ensure_ascii=False)
        self.sock.sendall((pedido + "\n").encode("utf-8"))
        linha = self.leitura.readline()
        if not linha:
            raise ConnectionError("O servidor fechou a ligação.")
        return json.loads(linha)

    def fechar(self):
        try:
            self.leitura.close()
        finally:
            self.sock.close()



def pedir(texto):
    return input(f"{texto}: ").strip()


def mostrar(resposta):
    if resposta.get("status") == "sucesso":
        if resposta.get("mensagem"):
            print(resposta["mensagem"])
        if resposta.get("alerta"):
            print(f"!!! {resposta['alerta']}: {resposta.get('peca')} "
                  f"(stock: {resposta.get('stock_atual')})")
    else:
        print(f"Erro: {resposta.get('mensagem')}")


def listar(resposta, chave):
    if resposta.get("status") != "sucesso":
        mostrar(resposta)
        return
    itens = resposta.get(chave, [])
    if not itens:
        print("(sem resultados)")
    for item in itens:
        print(" | ".join(f"{k}={v}" for k, v in item.items()))


def correr_menu(titulo, opcoes):
    
    while True:
        print(f"\n--- {titulo} ---")
        for chave, (texto, _) in opcoes.items():
            print(f"{chave}. {texto}")
        print("0. Voltar / Sair")
        escolha = pedir("Opção")
        if escolha == "0":
            return
        if escolha in opcoes:
            opcoes[escolha][1]()
        else:
            print("Opção inválida.")


def fazer_login(lig):
    username = pedir("Username")
    password = getpass.getpass("Password: ")
    resposta = lig.enviar("LOGIN", {"username": username, "password": password})
    if resposta.get("status") == "sucesso":
        print(f"\nBem-vindo, {resposta['nome']} ({resposta['role']})\n")
        return resposta
    mostrar(resposta)
    return None


def registar_cliente(lig):
    mostrar(lig.enviar("REGISTAR_CLIENTE", {
        "nome": pedir("Nome"),
        "username": pedir("Username"),
        "password": getpass.getpass("Password (mín. 6): "),
    }))


def pedir_role(texto="Tipo de funcionário", opcional=False):
    roles = {"1": "ROLE_MECANICO", "2": "ROLE_GESTOR"}
    while True:
        extra = " (vazio = manter)" if opcional else ""
        escolha = pedir(f"{texto}{extra}\n  1. Mecânico\n  2. Gestor\nOpção")
        if opcional and escolha == "":
            return ""
        if escolha in roles:
            return roles[escolha]
        print("Opção inválida. Escolhe 1 ou 2.")



def menu_funcionarios(lig):
    def adicionar():
        mostrar(lig.enviar("ADICIONAR_FUNCIONARIO", {
            "nome": pedir("Nome"),
            "username": pedir("Username"),
            "password": getpass.getpass("Password (mín. 6): "),
            "role": pedir_role(),
        }))

    def atualizar():
        dados = {"id": pedir("ID do funcionário")}
        nome = pedir("Novo nome (vazio = manter)")
        role = pedir_role("Novo tipo", opcional=True)
        password = getpass.getpass("Nova password (vazio = manter): ")
        if nome:
            dados["nome"] = nome
        if role:
            dados["role"] = role
        if password:
            dados["password"] = password
        mostrar(lig.enviar("ATUALIZAR_FUNCIONARIO", dados))

    def remover():
        mostrar(lig.enviar("REMOVER_FUNCIONARIO", {"id": pedir("ID a remover")}))

    correr_menu("Funcionários", {
        "1": ("Listar", lambda: listar(lig.enviar("LISTAR_FUNCIONARIOS"), "funcionarios")),
        "2": ("Adicionar", adicionar),
        "3": ("Atualizar", atualizar),
        "4": ("Remover", remover),
    })


def menu_pecas(lig):
    def registar():
        mostrar(lig.enviar("REGISTAR_PECA", {
            "nome": pedir("Nome"),
            "codigo": pedir("Código"),
            "preco": pedir("Preço"),
            "quantidade": pedir("Quantidade"),
        }))

    def atualizar():
        mostrar(lig.enviar("ATUALIZAR_PECA", {
            "id": pedir("ID da peça"),
            "preco": pedir("Novo preço (vazio = manter)"),
            "quantidade": pedir("Nova quantidade (vazio = manter)"),
        }))

    correr_menu("Stock e peças", {
        "1": ("Listar", lambda: listar(lig.enviar("LISTAR_PECAS"), "pecas")),
        "2": ("Registar peça", registar),
        "3": ("Atualizar preço/quantidade", atualizar),
    })


def menu_veiculos_gestor(lig):
    def registar():
        mostrar(lig.enviar("REGISTAR_VEICULO", {
            "cliente_id": pedir("ID do cliente"),
            "marca": pedir("Marca"),
            "modelo": pedir("Modelo"),
            "matricula": pedir("Matrícula (AA-00-AA)"),
        }))

    def remover():
        mostrar(lig.enviar("REMOVER_VEICULO", {"veiculo_id": pedir("ID do veículo")}))

    def historico():
        listar(lig.enviar("HISTORICO_VEICULO", {"veiculo_id": pedir("ID do veículo")}),
               "reparacoes")

    correr_menu("Veículos", {
        "1": ("Listar", lambda: listar(lig.enviar("LISTAR_VEICULOS"), "veiculos")),
        "2": ("Registar para um cliente", registar),
        "3": ("Histórico de reparações", historico),
        "4": ("Remover", remover),
    })


def menu_faturas(lig):
    def gerar():
        mostrar(lig.enviar("GERAR_FATURA", {
            "reparacao_id": pedir("ID da reparação"),
            "custo_servico": pedir("Custo do serviço (€)"),
        }))

    def pagar():
        mostrar(lig.enviar("REGISTAR_PAGAMENTO", {
            "fatura_id": pedir("ID da fatura"),
            "metodo": pedir("Método (Dinheiro / Cartão / MB Way / Transferência)"),
        }))

    correr_menu("Faturação", {
        "1": ("Listar faturas", lambda: listar(lig.enviar("LISTAR_FATURAS"), "faturas")),
        "2": ("Gerar fatura", gerar),
        "3": ("Registar pagamento", pagar),
        "4": ("Histórico de reparações",
              lambda: listar(lig.enviar("HISTORICO_REPARACOES"), "reparacoes")),
    })


def pedir_estado():
    estados = {"1": "Agendada", "2": "Em curso", "3": "Concluída"}
    while True:
        escolha = pedir("Estado\n  Agendada (1)\n  Em curso (2)\n  Concluída (3)\nOpção")
        if escolha in estados:
            return estados[escolha]
        print("Opção inválida. Escolhe 1, 2 ou 3.")


def mudar_estado(lig):
    mostrar(lig.enviar("ATUALIZAR_ESTADO_REPARACAO", {
        "reparacao_id": pedir("ID da reparação"),
        "estado": pedir_estado(),
    }))


def observacoes(lig):
    mostrar(lig.enviar("ADICIONAR_OBSERVACOES", {
        "reparacao_id": pedir("ID da reparação"),
        "observacoes": pedir("Observações"),
    }))


def menu_reparacoes_gestor(lig):
    def criar():
        mostrar(lig.enviar("CRIAR_REPARACAO", {
            "veiculo_id": pedir("ID do veículo"),
            "tipo_servico": pedir("Tipo de serviço"),
            "data": pedir("Data AAAA-MM-DD (vazio = hoje)"),
            "mecanico_id": pedir("ID do mecânico (vazio = atribuir depois)"),
        }))

    def atribuir():
        mostrar(lig.enviar("ATRIBUIR_MECANICO", {
            "reparacao_id": pedir("ID da reparação"),
            "mecanico_id": pedir("ID do mecânico"),
        }))

    correr_menu("Reparações", {
        "1": ("Listar reparações", lambda: listar(lig.enviar("LISTAR_REPARACOES"), "reparacoes")),
        "2": ("Criar reparação", criar),
        "3": ("Atribuir mecânico", atribuir),
        "4": ("Listar mecânicos", lambda: listar(lig.enviar("LISTAR_MECANICOS"), "mecanicos")),
        "5": ("Mudar estado", lambda: mudar_estado(lig)),
        "6": ("Adicionar observações", lambda: observacoes(lig)),
    })


def menu_gestor(lig):
    correr_menu("Menu Gestor", {
        "1": ("Funcionários", lambda: menu_funcionarios(lig)),
        "2": ("Stock e peças", lambda: menu_pecas(lig)),
        "3": ("Veículos", lambda: menu_veiculos_gestor(lig)),
        "4": ("Faturação", lambda: menu_faturas(lig)),
        "5": ("Reparações", lambda: menu_reparacoes_gestor(lig)),
    })


def menu_cliente(lig):
    def registar():
        mostrar(lig.enviar("REGISTAR_VEICULO", {
            "marca": pedir("Marca"),
            "modelo": pedir("Modelo"),
            "matricula": pedir("Matrícula (AA-00-AA)"),
        }))

    def atualizar_km():
        mostrar(lig.enviar("ATUALIZAR_VEICULO", {
            "veiculo_id": pedir("ID do veículo"),
            "quilometragem": pedir("Nova quilometragem"),
        }))

    def historico():
        listar(lig.enviar("HISTORICO_VEICULO", {"veiculo_id": pedir("ID do veículo")}),
               "reparacoes")

    def ver_fatura():
        resposta = lig.enviar("VER_FATURA", {"reparacao_id": pedir("ID da reparação")})
        if resposta.get("status") == "sucesso":
            f = resposta["fatura"]
            print(f"Fatura #{f['id']} | total: {f['valor_total']} € | "
                  f"pago: {'sim' if f['pago'] else 'não'}")
        else:
            mostrar(resposta)

    correr_menu("Menu Cliente", {
        "1": ("Os meus veículos", lambda: listar(lig.enviar("LISTAR_VEICULOS"), "veiculos")),
        "2": ("Registar veículo", registar),
        "3": ("Atualizar quilometragem", atualizar_km),
        "4": ("Histórico de reparações de um veículo", historico),
        "5": ("Ver fatura de uma reparação", ver_fatura),
        "6": ("As minhas faturas", lambda: listar(lig.enviar("LISTAR_FATURAS"), "faturas")),
        "7": ("As minhas reparações", lambda: listar(lig.enviar("LISTAR_REPARACOES"), "reparacoes")),
    })



def menu_mecanico(lig):
    def usar_peca():
        mostrar(lig.enviar("USAR_PECA", {
            "reparacao_id": pedir("ID da reparação"),
            "peca_id": pedir("ID da peça"),
            "quantidade": pedir("Quantidade usada"),
        }))

    correr_menu("Menu Mecânico", {
        "1": ("Listar peças em stock", lambda: listar(lig.enviar("LISTAR_PECAS"), "pecas")),
        "2": ("Registar peça usada numa reparação", usar_peca),
        "3": ("As minhas reparações", lambda: listar(lig.enviar("LISTAR_REPARACOES"), "reparacoes")),
        "4": ("Mudar estado de uma reparação", lambda: mudar_estado(lig)),
        "5": ("Adicionar observações", lambda: observacoes(lig)),
    })


def main():
    HOST = input(f"IP do servidor: ").strip() or HOST_POR_DEFEITO
    try:
        lig = Ligacao(HOST, PORT)
    except OSError:
        print(f"Não foi possível ligar a {HOST}:{PORT}. O servidor está a correr?")
        return

    print(f"Ligado ao servidor {HOST}:{PORT}")

    try:
        utilizador = None
        while utilizador is None:
            print("\n1. Login\n2. Registar como cliente\n0. Sair")
            escolha = pedir("Opção")
            if escolha == "0":
                return
            if escolha == "1":
                utilizador = fazer_login(lig)
            elif escolha == "2":
                registar_cliente(lig)
            else:
                print("Opção inválida.")

        menus = {
            "ROLE_GESTOR": menu_gestor,
            "ROLE_CLIENTE": menu_cliente,
            "ROLE_MECANICO": menu_mecanico,
        }
        menus[utilizador["role"]](lig)
        lig.enviar("LOGOUT")
    except (ConnectionError, OSError) as e:
        print(f"Ligação perdida: {e}")
    except KeyboardInterrupt:
        print("\nA sair...")
    finally:
        lig.fechar()
        print("Ligação terminada.")


if __name__ == "__main__":
    main()
