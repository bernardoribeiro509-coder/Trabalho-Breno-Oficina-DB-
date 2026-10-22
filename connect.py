import pymysql

def start_connection():
    return pymysql.connect(
        host="gateway01.eu-central-1.prod.aws.tidbcloud.com",
        user="cmE1xkqsg64fwEZ.root",
        password="KRohaNQbP8ELovTW",
        database="oficina",
        port=4000,
        ssl={"ssl": True}  # Ativa a segurança exigida pelo TiDB Cloud sem falhas de certificado
    )

if __name__ == "__main__":
    try:
        conexao = start_connection()
        if conexao.open:
            print("[+] Ligação ao TiDB Cloud na nuvem bem-sucedida!")
            conexao.close()
    except Exception as e:
        print(f"[-] Erro ao ligar à base de dados: {e}")