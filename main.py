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

# --- FUNÇÕES DE INTERAÇÃO COM O CHATWOOT ---

def search_contact(phone_number: str):
    """Busca um contato no Chatwoot pelo número de telefone."""
    # Remove o '+' se já existir para a busca
    search_phone = phone_number.replace('+', '')
    search_endpoint = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts/search"
    params = {'q': search_phone}
    try:
        response = requests.get(search_endpoint, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        if data["meta"]["count"] > 0:
            # Itera para encontrar a correspondência exata, pois a busca é ampla
            for contact in data["payload"]:
                if contact.get("phone_number", "").endswith(search_phone):
                    print(f"Contato encontrado: ID {contact['id']} para o número {phone_number}")
                    return contact
        print(f"Nenhum contato encontrado para o número {phone_number}")
        return None
    except Exception as e:
        print(f"Erro ao buscar contato com número {phone_number}: {e}")
        return None

def create_contact(name: str, phone_number: str):
    """Cria um novo contato no Chatwoot."""
    contact_endpoint = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts"
    # Garante que o número de telefone tenha o prefixo '+'
    if not phone_number.startswith('+'):
        phone_number = f"+{phone_number}"
        
    payload = {
        "inbox_id": CHATWOOT_INBOX_ID,
        "name": name,
        "phone_number": phone_number
    }
    try:
        response = requests.post(contact_endpoint, headers=HEADERS, json=payload)
        response.raise_for_status()
        contact = response.json()["payload"]["contact"]
        print(f"Contato criado: ID {contact['id']} para {name} ({phone_number})")
        return contact
    except Exception as e:
        print(f"Erro ao criar contato para {name} ({phone_number}): {e}")
        return None

def search_or_create_contact(name: str, phone_number: str):
    """Busca um contato e, se não encontrar, cria um novo, retornando o ID."""
    contact = search_contact(phone_number)
    if contact:
        return contact['id']
    
    new_contact = create_contact(name, phone_number)
    return new_contact['id'] if new_contact else None

def find_or_create_conversation(contact_id: int):
    """Busca uma conversa existente para o contato ou cria uma nova."""
    conv_endpoint = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts/{contact_id}/conversations"
    try:
        response = requests.get(conv_endpoint, headers=HEADERS)
        response.raise_for_status()
        conversations = response.json()["payload"]
        if conversations:
            conv_id = conversations[0]['id']
            print(f"Conversa encontrada: ID {conv_id} para o contato {contact_id}")
            return conv_id
        
        print(f"Nenhuma conversa encontrada para o contato {contact_id}. Criando uma nova...")
        create_conv_endpoint = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations"
        payload = { "inbox_id": CHATWOOT_INBOX_ID, "contact_id": contact_id }
        create_response = requests.post(create_conv_endpoint, headers=HEADERS, json=payload)
        create_response.raise_for_status()
        new_conv_id = create_response.json()['id']
        print(f"Conversa criada: ID {new_conv_id} para o contato {contact_id}")
        return new_conv_id
        
    except Exception as e:
        print(f"Erro ao buscar ou criar conversa para o contato {contact_id}: {e}")
        return None

def send_message_to_conversation(conversation_id: int, message_content: str):
    """Envia uma mensagem para uma conversa específica no Chatwoot."""
    message_endpoint = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages"
    payload = {"content": message_content, "message_type": "incoming"}
    try:
        response = requests.post(message_endpoint, headers=HEADERS, json=payload)
        response.raise_for_status()
        print(f"Mensagem enviada com sucesso para a conversa {conversation_id}")
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar mensagem para a conversa {conversation_id}: {e}")
        return None

def update_contact_avatar(contact_id: int, avatar_url: str):
    if not avatar_url:
        print(f"Contato {contact_id}: Nenhuma URL de avatar fornecida.")
        return
    try:
        response = requests.get(avatar_url, stream=True)
        response.raise_for_status()
        avatar_endpoint = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts/{contact_id}/avatar"
        files = {'avatar': response.content}
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
        
        # --- LÓGICA DE PROCESSAMENTO DO WEBHOOK ---
        event_type = data.get("event")
        payload = data.get("data", {})

        # 1. Processar apenas eventos de mensagem recebida
        if event_type == "messages.upsert":
            message_type = payload.get("message", {}).get("type")
            if message_type not in ["text", "image", "video", "audio", "file"]:
                print(f"Ignorando tipo de mensagem não suportado: {message_type}")
                return {"status": "ignored", "reason": "unsupported message type"}

            sender_phone = payload.get("key", {}).get("remoteJid").split('@')[0]
            sender_name = payload.get("pushName", sender_phone)
            message_content = payload.get("message", {}).get("text", {}).get("text", "")
            
            # Para outros tipos de mídia, você pode querer registrar a URL ou um placeholder
            if not message_content:
                message_content = f"[{message_type.capitalize()} recebida]"

            # 2. Buscar ou Criar Contato no Chatwoot
            contact_id = search_or_create_contact(sender_name, sender_phone)
            if not contact_id:
                raise HTTPException(status_code=500, detail="Falha ao buscar ou criar contato no Chatwoot.")

            # 3. Buscar ou Criar Conversa
            conversation_id = find_or_create_conversation(contact_id)
            if not conversation_id:
                raise HTTPException(status_code=500, detail="Falha ao buscar ou criar conversa no Chatwoot.")

            # 4. Enviar Mensagem para a Conversa
            send_message_to_conversation(conversation_id, message_content)

            # 5. Tentar atualizar o avatar (se disponível)
            profile_pic_url = payload.get("profilePicUrl")
            if profile_pic_url:
                update_contact_avatar(contact_id, profile_pic_url)

        return {"status": "success", "message": "Webhook processado com sucesso."}

        return {"status": "success", "message": "Webhook recebido com sucesso."}
    except Exception as e:
        print(f"Erro ao processar o webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor da ponte.")

# Endpoint de teste
@app.get("/")
def read_root():
    return {"message": "Ponte Ricard-ZAP -> Chatwoot está no ar!"}
