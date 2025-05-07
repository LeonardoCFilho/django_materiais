import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd

# Carrega variáveis do .env
load_dotenv()

# Lê usuário e senha do banco
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

if not db_user or not db_password:
    raise ValueError("As variáveis DB_USER e DB_PASSWORD devem estar definidas no arquivo .env")

# Configurações da requisição
url = 'http://172.22.3.31:5011/api/query'
headers = {'Content-Type': 'application/json'}

# Nova consulta SQL
query = """
SELECT CO_MAT,
       DE_MAT,
       QT_SALDO_ATU
FROM SICAM.MATERIAL
WHERE TO_CHAR(CO_MAT) LIKE '30%'
  AND QT_SALDO_ATU > 0
ORDER BY DE_MAT
FETCH FIRST 10 ROWS ONLY
"""

# Corpo da requisição
payload = {
    'db_user': db_user,
    'db_password': db_password,
    'sql_query': query
}

# Envio da requisição
try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        data = response.json()
        '''columns = data.get("columns", [])
        rows = data.get("rows", [])

        # Cria DataFrame
        df = pd.DataFrame(rows, columns=columns)

        # Salva em Excel
        df.to_excel("resultado.xlsx", index=False)'''
        print("Arquivo Excel salvo como 'resultado.xlsx'")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        error_data = response.json()
        print(f"Erro: {error_data.get('error', 'Erro ao executar a consulta.')}")
except Exception as e:
    print(f"Erro: {str(e)}")