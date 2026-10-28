import pymysql

def start_connection():
    return pymysql.connect(
        host="gateway01.eu-central-1.prod.aws.tidbcloud.com",
        user="cmE1xkqsg64fwEZ.root",
        password="LIZMR4e3RDu9tuDr",
        database="oficina",
        port=4000,
        ssl={"ssl": True},
    )

if __name__ == "__main__":
    try:
        conexao = start_connection()
        if conexao.open:
            print("[+] Ligação ao TiDB Cloud bem-sucedida!")
            conexao.close()
    except Exception as e:
        print(f"[-] Erro ao ligar à base de dados: {e}")
