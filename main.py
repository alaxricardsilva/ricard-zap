import os
import sys
from fastapi import FastAPI, Request, HTTPException
import requests
import json
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env no início de tudo
load_dotenv()

# --- Diagnóstico e Validação das Variáveis de Ambiente ---
print("--- Verificando Variáveis de Ambiente na Inicialização ---")

VARS_TO_CHECK = {
    "CHATWOOT_URL": os.getenv("CHATWOOT_URL"),
    "CHATWOOT_ACCOUNT_ID": os.getenv("CHATWOOT_ACCOUNT_ID"),
    "CHATWOOT_INBOX_ID": os.getenv("CHATWOOT_INBOX_ID"),
    "CHATWOOT_API_TOKEN": os.getenv("CHATWOOT_API_TOKEN"),
    "WUZAPI_API_URL": os.getenv("WUZAPI_API_URL"),
    "WUZAPI_API_TOKEN": os.getenv("WUZAPI_API_TOKEN"),
    "WUZAPI_INSTANCE_NAME": os.getenv("WUZAPI_INSTANCE_NAME"),
}

missing_vars = []
for var_name, value in VARS_TO_CHECK.items():
    if not value:
        print(f"❌ ERRO: Variável de ambiente '{var_name}' NÃO ENCONTRADA.")
        missing_vars.append(var_name)
    else:
        if "TOKEN" in var_name:
            print(f"✅ OK: Variável '{var_name}' carregada (termina com '...{value[-4:]}').")
        else:
            print(f"✅ OK: Variável '{var_name}' carregada com o valor: {value}")

print("----------------------------------------------------")

if missing_vars:
    print(f"ERRO CRÍTICO: A aplicação não pode iniciar porque as seguintes variáveis de ambiente obrigatórias estão faltando: {', '.join(missing_vars)}")
    print("Por favor, configure-as no seu ambiente (EasyPanel, arquivo .env, etc.) e reinicie a aplicação.")
    sys.exit(1)

# Atribuição das variáveis após a validação bem-sucedida
CHATWOOT_URL = VARS_TO_CHECK["CHATWOOT_URL"]
CHATWOOT_ACCOUNT_ID = VARS_TO_CHECK["CHATWOOT_ACCOUNT_ID"]
CHATWOOT_INBOX_ID = VARS_TO_CHECK["CHATWOOT_INBOX_ID"]
CHATWOOT_API_TOKEN = VARS_TO_CHECK["CHATWOOT_API_TOKEN"]
WUZAPI_API_URL = VARS_TO_CHECK["WUZAPI_API_URL"]
WUZAPI_API_TOKEN = VARS_TO_CHECK["WUZAPI_API_TOKEN"]
WUZAPI_INSTANCE_NAME = VARS_TO_CHECK["WUZAPI_INSTANCE_NAME"]

HEADERS = {'api_access_token': CHATWOOT_API_TOKEN, 'Content-Type': 'application/json'}

# Cria a aplicação FastAPI
app = FastAPI(title="Ponte Ricard-ZAP", version="1.0.0")

# --- Variáveis e Funções para WuzAPI (Envio) ---
WUZAPI_INSTANCE_NAME = os.getenv("WUZAPI_INSTANCE_NAME")
WUZAPI_API_URL = os.getenv("WUZAPI_API_URL")
WUZAPI_API_TOKEN = os.getenv("WUZAPI_API_TOKEN")

def send_message_via_wuzapi(phone_number: str, message: str):
    """Envia uma mensagem de texto para um número via WuzAPI."""
    if not all([WUZAPI_API_URL, WUZAPI_API_TOKEN, WUZAPI_INSTANCE_NAME]):
        print("ERRO: Variáveis de ambiente da WuzAPI para envio não configuradas (WUZAPI_INSTANCE_NAME, WUZAPI_API_URL, WUZAPI_API_TOKEN).")
        return

    # Monta a URL e o payload para a API da WuzAPI.
    # ATENÇÃO: A estrutura do endpoint e do payload é uma suposição comum.
    # Pode precisar de ajuste dependendo da documentação exata da sua versão da WuzAPI.
    send_url = f"{WUZAPI_API_URL}/message/sendText/{WUZAPI_INSTANCE_NAME}"
    payload = {
        "number": phone_number,
        "message": {
            "text": message
        }
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "apikey": WUZAPI_API_TOKEN  # WuzAPI geralmente usa 'apikey' no header
    }
    
    try:
        print(f"Enviando mensagem para {phone_number} via WuzAPI.")
        response = requests.post(send_url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Mensagem enviada para a WuzAPI com sucesso. Resposta: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"ERRO ao enviar mensagem para a WuzAPI: {e}")
        if e.response is not None:
            print(f"Status da Resposta: {e.response.status_code}")
            print(f"Corpo da Resposta: {e.response.text}")

# --- FUNÇÕES DE INTERAÇÃO COM O CHATWOOT ---

def search_contact(phone_number: str):
    """Busca um contato no Chatwoot pelo número de telefone."""
    # Remove o '+' se já existir para a busca
    search_phone = phone_number.replace('+', '')
    search_endpoint = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}/contacts/search"
    params = {'q': search_phone}
    try:
        print("--- Depuração da Requisição para o Chatwoot ---")
        print(f"URL da Requisição: {search_endpoint}")
        print(f"Cabeçalhos (Headers): {HEADERS}")
        print(f"Parâmetros (Params): {params}")
        print("---------------------------------------------")
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
        # 1. Obter o corpo JSON bruto da solicitação
        data = await request.json()
        print("--- Webhook Recebido do Wuzapi ---")
        print(json.dumps(data, indent=2))
        print("------------------------------------")

        # Primeiro, vamos determinar a fonte dos dados
        raw_data = data
        if "jsonData" in data and isinstance(data.get("jsonData"), str):
            print("Formato de webhook detectado: Dados dentro de 'jsonData'.")
            try:
                raw_data = json.loads(data["jsonData"])
            except json.JSONDecodeError:
                print("Erro: Falha ao decodificar o JSON em 'jsonData'.")
                raise HTTPException(status_code=400, detail="JSON inválido no campo jsonData.")
        elif "event" in data and "type" in data:
            print("Formato de webhook detectado: Dados no corpo principal.")
        else:
            print("Ignorando webhook: formato de dados não reconhecido.")
            return {"status": "ignored", "reason": "unrecognized data format"}

        # Agora, com os dados corretos, processamos o evento
        event_type = raw_data.get("type")
        event_data = raw_data.get("event", {})
        info = event_data.get("Info", {})

        # 5. Processar apenas eventos de "Message" e ignorar o resto
        if event_type == "Message" and not info.get("IsGroup") and info.get("Chat") != "status@broadcast":
            message = event_data.get("Message", {})
            
            # Lógica de extração de telefone e nome, adaptada para múltiplos formatos.
            sender_raw = event_data.get('Sender')
            if sender_raw and '@' in sender_raw:
                sender_phone = sender_raw.split('@')[0]
                sender_name = info.get("PushName", sender_phone)
            else:
                print("Campo 'Sender' do evento não encontrado/inválido. Tentando fallback para campos de nível raiz.")
                sender_phone = str(raw_data.get("sender", ""))
                sender_name = raw_data.get("name", sender_phone)

            if not sender_phone:
                print("Ignorando mensagem: Número do remetente não pôde ser determinado.")
                return {"status": "ignored", "reason": "Could not determine sender phone number"}
            message_content = message.get("conversation") # Para mensagens de texto

            # Lida com outros tipos de mensagem, se necessário no futuro
            message_type = info.get("Type")
            if message_type != "text" and not message_content:
                # Por enquanto, vamos apenas dizer que tipo de mídia foi recebido
                message_content = f"[{message_type.capitalize()} recebida]"

            if not message_content:
                print("Ignorando mensagem: Conteúdo vazio.")
                return {"status": "ignored", "reason": "empty message content"}

            # 6. Buscar ou Criar Contato no Chatwoot
            contact_id = search_or_create_contact(sender_name, sender_phone)
            if not contact_id:
                raise HTTPException(status_code=500, detail="Falha ao buscar ou criar contato no Chatwoot.")

            # 7. Buscar ou Criar Conversa
            conversation_id = find_or_create_conversation(contact_id)
            if not conversation_id:
                raise HTTPException(status_code=500, detail="Falha ao buscar ou criar conversa no Chatwoot.")

            # 8. Enviar Mensagem para a Conversa
            send_message_to_conversation(conversation_id, message_content)
            
            print("Webhook processado com sucesso.")
            return {"status": "success", "message": "Webhook processado com sucesso."}

        else:
            is_group = info.get("IsGroup", "desconhecido")
            print(f"Ignorando evento: tipo '{event_type}' ou é de grupo '{is_group}'.")
            return {"status": "ignored", "reason": f"Event type '{event_type}' or group message"}

    except Exception as e:
        print(f"Erro fatal ao processar o webhook: {e}")
        # Retorna um erro 500 para o chamador (WuzAPI)
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor da ponte: {e}")


# Endpoint de teste
@app.get("/")
def read_root():
    return {"message": "Ponte Ricard-ZAP -> Chatwoot está no ar!"}


# --- Webhook para Receber Mensagens do Chatwoot (para enviar ao WhatsApp) ---
@app.post("/webhook/chatwoot")
async def handle_chatwoot_webhook(request: Request):
    """Recebe webhooks do Chatwoot e envia a mensagem para o cliente via WuzAPI."""
    try:
        data = await request.json()
        print("--- Webhook Recebido do Chatwoot ---")
        print(json.dumps(data, indent=2))

        # Ignora mensagens privadas ou que não sejam de saída
        if data.get("private") or data.get("message_type") != "outgoing":
            print("Ignorando webhook: Mensagem privada ou não é de saída.")
            return {"status": "ignored", "reason": "private or not outgoing message"}

        # Ignora se não for uma mensagem de um agente (para evitar loops)
        sender_type = data.get("sender", {}).get("type")
        if sender_type not in ["agent_bot", "user"]:
             print(f"Ignorando webhook: Remetente não é um agente (tipo: {sender_type}).")
             return {"status": "ignored", "reason": "sender is not an agent"}

        content = data.get("content")
        contact_phone = data.get("conversation", {}).get("meta", {}).get("sender", {}).get("phone_number")
        
        # O número de telefone no Chatwoot pode ter um "+". A WuzAPI pode não precisar dele.
        if contact_phone:
            clean_phone = contact_phone.replace("+", "")
        else:
            print("ERRO: Não foi possível encontrar o número de telefone do contato no webhook do Chatwoot.")
            return {"status": "error", "reason": "phone number not found"}

        if not content:
            print("Ignorando webhook: Conteúdo da mensagem está vazio.")
            return {"status": "ignored", "reason": "empty content"}

        # Envia a mensagem usando nossa nova função
        send_message_via_wuzapi(phone_number=clean_phone, message=content)

        return {"status": "success"}

    except Exception as e:
        print(f"ERRO CRÍTICO ao processar webhook do Chatwoot: {e}")
        return {"status": "error", "detail": str(e)}
