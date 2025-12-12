import os
from fastapi import FastAPI, Request, HTTPException
import requests
import json

# --- CONFIGURAÇÃO (Lida a partir de Variáveis de Ambiente) ---
# O EasyPanel vai injetar esses valores no contêiner.
CHATWOOT_URL = os.getenv("CHATWOOT_URL")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID")
CHATWOOT_INBOX_ID = os.getenv("CHATWOOT_INBOX_ID")
CHATWOOT_API_TOKEN = os.getenv("CHATWOOT_API_TOKEN")

# Validação para garantir que as variáveis foram configuradas
if not all([CHATWOOT_URL, CHATWOOT_ACCOUNT_ID, CHATWOOT_INBOX_ID, CHATWOOT_API_TOKEN]):
    raise RuntimeError("Erro: Uma ou mais variáveis de ambiente do Chatwoot não foram definidas!")

HEADERS = {'api_access_token': CHATWOOT_API_TOKEN, 'Content-Type': 'application/json'}

# Cria a aplicação FastAPI
app = FastAPI(title="Ponte Ricard-ZAP", version="1.0.0")

# --- FUNÇÃO PARA ATUALIZAR O AVATAR ---
def update_contact_avatar(contact_id: int, avatar_url: str):
    if not avatar_url:
        print(f"Contato {contact_id}: Nenhuma URL de avatar fornecida.")
        return
    try:
        response = requests.get(avatar_url, stream=True)
        response.raise_for_status()
        avatar_endpoint = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts/{contact_id}/avatar"
        files = {'avatar': response.content}
        # Para o avatar, o header não deve ser 'application/json'
        avatar_headers = {'api_access_token': CHATWOOT_API_TOKEN}
        upload_response = requests.post(avatar_endpoint, headers=avatar_headers, files=files)
        upload_response.raise_for_status()
        print(f"Contato {contact_id}: Avatar atualizado com sucesso!")
    except Exception as e:
        print(f"Erro ao atualizar avatar para o contato {contact_id}: {e}")

# --- ENDPOINT DO WEBHOOK ---
@app.post("/webhook/wuzapi")
async def handle_wuzapi_webhook(request: Request):
    try:
        data = await request.json()
        print("--- Webhook Recebido do Wuzapi ---")
        print(json.dumps(data, indent=2))
        print("------------------------------------")
        
        # =================================================================
        # AQUI ENTRARÁ A LÓGICA PARA FALAR COM O CHATWOOT (próximo passo)
        # =================================================================

        return {"status": "success", "message": "Webhook recebido com sucesso."}
    except Exception as e:
        print(f"Erro ao processar o webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor da ponte.")

# Endpoint de teste
@app.get("/")
def read_root():
    return {"message": "Ponte Ricard-ZAP -> Chatwoot está no ar!"}
