import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def start_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        port=int(os.environ["DB_PORT"]),
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

