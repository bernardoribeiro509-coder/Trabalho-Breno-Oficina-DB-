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

c = start_connection(); cur = c.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS faturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reparacao_id INT NOT NULL UNIQUE,
    total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (reparacao_id) REFERENCES reparacoes(id)
)""")
c.commit(); c.close()

if __name__ == "__main__":
    try:
        conexao = start_connection()
        if conexao.open:
            print("[+] Ligação ao TiDB Cloud bem-sucedida!")
            conexao.close()
    except Exception as e:
        print(f"[-] Erro ao ligar à base de dados: {e}")

