import getpass
import hashlib
import hmac
import os

from db import consultar, executar
from modelos import ROLES, Gestor, Cliente, Utilizador

ITERACOES = 200_000


class ErroNegocio(Exception):
    """Erro que é mostrado ao cliente (dados inválidos, não encontrado, etc.)."""


class PermissaoNegada(ErroNegocio):
    pass




def hash_password(password):
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERACOES)
    return f"{salt.hex()}${h.hex()}"


def verificar_password(password, guardado):
    try:
        salt_hex, hash_hex = guardado.split("$")
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERACOES)
    return hmac.compare_digest(h.hex(), hash_hex)


def exigir_login(sessao):
    if sessao.get("utilizador") is None:
        raise PermissaoNegada("Tens de fazer login primeiro.")
    return sessao["utilizador"]


def exigir_role(sessao, *roles):
    user = exigir_login(sessao)
    if user.ROLE not in roles:
        raise PermissaoNegada("Não tens permissão para esta operação.")
    return user


def criar_utilizador(username, password, nome, role):
    username = (username or "").strip()
    nome = (nome or "").strip()
    if not username or not nome:
        raise ErroNegocio("Username e nome são obrigatórios.")
    if len(password or "") < 6:
        raise ErroNegocio("A password tem de ter pelo menos 6 caracteres.")
    if role not in ROLES:
        raise ErroNegocio("Tipo de utilizador inválido.")
    if consultar("SELECT id FROM utilizadores WHERE username=%s", (username,), um=True):
        raise ErroNegocio("Esse username já existe.")
    return executar(
        "INSERT INTO utilizadores (username, password_hash, nome, role) VALUES (%s,%s,%s,%s)",
        (username, hash_password(password), nome, role),
    )


def criar_primeiro_gestor():
    existe = consultar(
        "SELECT id FROM utilizadores WHERE role=%s LIMIT 1", (Gestor.ROLE,), um=True
    )
    if existe:
        return
    print("=== Primeira execução: criar o primeiro gestor ===")
    while True:
        try:
            username = input("Username: ")
            nome = input("Nome: ")
            password = getpass.getpass("Password: ")
            criar_utilizador(username, password, nome, Gestor.ROLE)
            print("[+] Gestor criado.\n")
            return
        except ErroNegocio as e:
            print(f"[-] {e}")


def login(dados, sessao):
    username = (dados.get("username") or "").strip()
    password = dados.get("password") or ""
    linha = consultar("SELECT * FROM utilizadores WHERE username=%s", (username,), um=True)
    if not linha or not verificar_password(password, linha["password_hash"]):
        raise ErroNegocio("Utilizador ou password incorretos.")
    user = Utilizador.de_linha(linha)
    sessao["utilizador"] = user
    return {"role": user.ROLE, "utilizador": user.para_dict()}


def logout(dados, sessao):
    sessao["utilizador"] = None
    return {}


def registar_cliente(dados, sessao):
    criar_utilizador(
        dados.get("username"), dados.get("password"), dados.get("nome"), Cliente.ROLE
    )
    return {"mensagem": "Cliente registado."}


ACOES = {
    "LOGIN": login,
    "LOGOUT": logout,
    "REGISTAR_CLIENTE": registar_cliente,
}
