# dawai breno

VEICULOS = {}


def registar_veiculo(marca, modelo, matricula, cliente, quilometragem=0):
	
	if any(not isinstance(valor, str) or not valor.strip()
		   for valor in (marca, modelo, matricula, cliente)):
		raise ValueError("Marca, modelo, matrícula e cliente são obrigatórios.")
	if isinstance(quilometragem, bool) or not isinstance(quilometragem, int) or quilometragem < 0:
		raise ValueError("A quilometragem deve ser um inteiro não negativo.")

	matricula = matricula.strip().upper()
	if matricula in VEICULOS:
		raise ValueError("Já existe um veículo com essa matrícula.")

	veiculo = {
		"marca": marca.strip(),
		"modelo": modelo.strip(),
		"matricula": matricula,
		"cliente": cliente.strip(),
		"quilometragem": quilometragem,
		"reparacoes": [],
	}
	VEICULOS[matricula] = veiculo
	return veiculo


def obter_veiculo(matricula):
	
	if not isinstance(matricula, str):
		raise ValueError("A matrícula deve ser texto.")
	try:
		return VEICULOS[matricula.strip().upper()]
	except KeyError:
		raise ValueError("Veículo não encontrado.") from None


def atualizar_dados_veiculo(matricula, quilometragem):
	
	veiculo = obter_veiculo(matricula)
	if isinstance(quilometragem, bool) or not isinstance(quilometragem, int) or quilometragem < 0:
		raise ValueError("A quilometragem deve ser um inteiro não negativo.")
	if quilometragem < veiculo["quilometragem"]:
		raise ValueError("A quilometragem não pode diminuir.")
	veiculo["quilometragem"] = quilometragem
	return veiculo


def consultar_historico_reparacoes(matricula):
	
	return list(obter_veiculo(matricula)["reparacoes"])


def associar_reparacao(matricula, reparacao):
	
	if not isinstance(reparacao, dict):
		raise ValueError("A reparação deve ser um dicionário.")
	obter_veiculo(matricula)["reparacoes"].append(reparacao)


def remover_veiculo(matricula, perfil):
	
	if not isinstance(perfil, str) or perfil.strip().casefold() != "gestor":
		raise PermissionError("Só o gestor pode remover veículos.")
	veiculo = obter_veiculo(matricula)
	del VEICULOS[veiculo["matricula"]]
	return veiculo
