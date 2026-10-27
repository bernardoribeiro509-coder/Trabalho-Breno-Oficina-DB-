import mysql.connector

ROLE_CLIENTE, ROLE_MECANICO, ROLE_GESTOR = "ROLE_CLIENTE", "ROLE_MECANICO", "ROLE_GESTOR"
CONFIG_BD = {"host": "localhost", "user": "root", "password": "", "database": "oficina"}


class BaseDados:

    def executar(self, sql, params=(), um=False):
        ligacao = mysql.connector.connect(**CONFIG_BD)
        try:
            cursor = ligacao.cursor(dictionary=True)
            cursor.execute(sql, params)
            if sql.lstrip().upper().startswith("SELECT"):
                linhas = cursor.fetchone() if um else cursor.fetchall()
                return self._para_json(linhas)
            ligacao.commit()
            return cursor.lastrowid
        finally:
            ligacao.close()

    @staticmethod
    def _para_json(dados):
        for linha in ([dados] if isinstance(dados, dict) else dados or []):
            for k, v in linha.items():
                if not isinstance(v, (int, float, str, type(None))):
                    linha[k] = str(v)
        return dados


class GestorVeiculos(BaseDados):

    def _obter(self, user, veiculo_id):
        v = self.executar("SELECT * FROM veiculos WHERE id=%s", (veiculo_id,), um=True)
        if not v:
            raise ValueError("Veículo não encontrado.")
        if user["role"] == ROLE_CLIENTE and v["cliente_id"] != user["id"]:
            raise ValueError("Não tem permissão para aceder a este veículo.")
        return v

    def registar(self, user, marca, modelo, matricula, cliente_id=None):
        if user["role"] == ROLE_CLIENTE:
            cliente_id = user["id"]
        elif user["role"] != ROLE_GESTOR or not cliente_id:
            raise ValueError("Só cliente ou gestor (com cliente_id) registam veículos.")
        matricula = (matricula or "").strip().upper()
        if not marca or not modelo:
            raise ValueError("Marca e modelo são obrigatórios.")
        partes = matricula.split("-")
        if len(partes) != 3 or not all(len(p) == 2 and p.isalnum() for p in partes):
            raise ValueError("Matrícula inválida (formato AA-00-AA).")
        if self.executar("SELECT id FROM veiculos WHERE matricula=%s", (matricula,), um=True):
            raise ValueError("Já existe um veículo com essa matrícula.")
        novo_id = self.executar(
            "INSERT INTO veiculos (marca, modelo, matricula, quilometragem, cliente_id) "
            "VALUES (%s, %s, %s, 0, %s)", (marca, modelo, matricula, cliente_id))
        return self._obter(user, novo_id)

    def atualizar_km(self, user, veiculo_id, quilometragem):
        v = self._obter(user, veiculo_id)
        if int(quilometragem) < v["quilometragem"]:
            raise ValueError("A quilometragem não pode ser inferior à atual.")
        self.executar("UPDATE veiculos SET quilometragem=%s WHERE id=%s",
                      (int(quilometragem), veiculo_id))
        return self._obter(user, veiculo_id)

    def listar(self, user):
        if user["role"] == ROLE_CLIENTE:
            return self.executar("SELECT * FROM veiculos WHERE cliente_id=%s", (user["id"],))
        return self.executar("SELECT * FROM veiculos")

    def historico(self, user, veiculo_id):
        self._obter(user, veiculo_id)  
        return self.executar(
            "SELECT r.*, u.nome AS mecanico_nome FROM reparacoes r "
            "LEFT JOIN utilizadores u ON u.id = r.mecanico_id "
            "WHERE r.veiculo_id=%s ORDER BY r.id DESC", (veiculo_id,))

    def remover(self, user, veiculo_id):
        if user["role"] != ROLE_GESTOR:
            raise ValueError("Apenas o gestor pode remover veículos.")
        self._obter(user, veiculo_id)
        self.executar("DELETE FROM veiculos WHERE id=%s", (veiculo_id,))


def processar_pedido_veiculo(gestor, user, pedido):
    cmd, vid = pedido.get("comando"), pedido.get("veiculo_id")
    try:
        if cmd == "REGISTAR_VEICULO":
            dados = gestor.registar(user, pedido.get("marca"), pedido.get("modelo"),
                                    pedido.get("matricula"), pedido.get("cliente_id"))
        elif cmd == "ATUALIZAR_VEICULO":
            dados = gestor.atualizar_km(user, vid, pedido.get("quilometragem"))
        elif cmd == "LISTAR_VEICULOS":
            dados = gestor.listar(user)
        elif cmd == "HISTORICO_VEICULO":
            dados = gestor.historico(user, vid)
        elif cmd == "REMOVER_VEICULO":
            gestor.remover(user, vid)
            dados = None
        else:
            return {"status": "ERRO", "mensagem": f"Comando desconhecido: {cmd}"}
        return {"status": "OK", "dados": dados}
    except (ValueError, TypeError) as e:
        return {"status": "ERRO", "mensagem": str(e)}
    except Exception as e:
        return {"status": "ERRO", "mensagem": f"Erro na base de dados: {e}"}