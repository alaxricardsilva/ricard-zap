
import requests
import os

# --- INSTRUÇÕES ---
# 1. Substitua o valor de CHATWOOT_API_TOKEN abaixo pelo seu token real.
# 2. Salve este arquivo.
# 3. Abra um terminal no diretório /root/Projetos/Ricard-ZAP/
# 4. Execute o comando: python test_chatwoot.py

# --- DADOS PARA O TESTE ---
# URL base da sua instância do Chatwoot (sem a barra no final)
CHATWOOT_URL = "https://chat.ricardtech.top"

# ID da sua conta no Chatwoot (geralmente é 1, como vimos na URL)
CHATWOOT_ACCOUNT_ID = "1"

# O Token de Acesso da API do seu perfil de usuário no Chatwoot
CHATWOOT_API_TOKEN = "MJFcBLLuTgresHixfYgD4dar"

# Um número de telefone para teste (pode ser qualquer um)
TEST_PHONE_NUMBER = "+558188526072"
# -------------------------


# Montando os cabeçalhos e o endpoint da API
HEADERS = {
    'Content-Type': 'application/json; charset=utf-8',
    'api_access_token': CHATWOOT_API_TOKEN
}
search_endpoint = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts/search"
params = {'q': TEST_PHONE_NUMBER}

print("--- Iniciando Teste de Conexão com a API do Chatwoot ---")
print(f"URL da Requisição: {search_endpoint}")
print(f"Cabeçalhos (Headers): {{'api_access_token': '{'********' if CHATWOOT_API_TOKEN != 'COLE_SEU_TOKEN_DE_ACESSO_AQUI' else 'VAZIO'}'}}")
print(f"Parâmetros (Params): {params}")
print("------------------------------------------------------")

try:
    # A requisição real, idêntica à que está no main.py
    response = requests.get(search_endpoint, headers=HEADERS, params=params)

    print(f"\n--- Resultado ---")
    print(f"Status Code: {response.status_code}")
    print(f"Resposta (Response Body):")
    try:
        # Tenta imprimir a resposta como JSON, se possível
        print(response.json())
    except requests.exceptions.JSONDecodeError:
        # Se não for JSON, imprime como texto
        print(response.text)

    print("-----------------\n")

    if response.status_code == 200:
        print("✅ SUCESSO! A conexão com a API do Chatwoot foi bem-sucedida.")
        print("Isso significa que seu Token, URL e ID da Conta estão corretos e funcionando.")
    elif response.status_code == 401:
        print("❌ FALHA (401 Unauthorized): A autenticação falhou.")
        print("Verifique se o 'CHATWOOT_API_TOKEN' está 100% correto, sem espaços ou caracteres extras.")
        print("Copie e cole o token diretamente da tela do seu perfil no Chatwoot para o script.")
    else:
        print(f"⚠️ FALHA ({response.status_code}): Ocorreu um erro inesperado.")
        print("A resposta do servidor foi impressa acima para análise.")


except requests.exceptions.SSLError as e:
    print("\n--- Resultado ---")
    print("❌ FALHA (Erro de SSL): Não foi possível verificar o certificado SSL do servidor.")
    print("Isso indica um problema com a configuração do HTTPS no seu domínio 'chat.ricardtech.top'.")
    print(f"Detalhes do erro: {e}")
    print("-----------------\n")

except requests.exceptions.ConnectionError as e:
    print("\n--- Resultado ---")
    print("❌ FALHA (Erro de Conexão): Não foi possível se conectar ao servidor.")
    print("Verifique se a URL 'CHATWOOT_URL' está correta e se não há um firewall bloqueando a conexão.")
    print(f"Detalhes do erro: {e}")
    print("-----------------\n")

except Exception as e:
    print(f"\nOcorreu um erro inesperado durante a execução do script: {e}")
