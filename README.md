# Ponte de Integração WuzAPI ↔ Chatwoot

Este projeto é um serviço de ponte (bridge) construído em FastAPI (Python) que conecta uma instância da WuzAPI com uma caixa de entrada do tipo "API" no Chatwoot, permitindo uma comunicação bidirecional.

## Funcionalidades

- **Recebimento de Mensagens**: Recebe webhooks da WuzAPI sobre novas mensagens do WhatsApp (apenas conversas privadas 1:1) e as cria na conversa correta dentro do Chatwoot.
- **Envio de Respostas**: Recebe webhooks do Chatwoot quando um agente responde a uma conversa e envia essa resposta para o cliente final via WuzAPI.
- **Criação e Atualização de Contatos**: Se uma mensagem é recebida de um número que não existe no Chatwoot, um novo contato é criado automaticamente.
- **Sincronização de Avatar**: Busca a foto de perfil do contato no WhatsApp (via API `/user/avatar` do Sistema de API WhatsApp, com fallback para `/chat/getProfilePic`) e a envia para o Chatwoot via `avatar_url`, mantendo o avatar do contato atualizado.
- **Compatibilidade de Formato**: Processa múltiplos formatos de payload da WuzAPI / Sistema de API WhatsApp, incluindo o novo formato que utiliza `SenderAlt` (mapeamento de LID para número) e estruturas aninhadas, garantindo maior robustez.
- **Compatível com LID**: Utiliza `SenderAlt` sempre que disponível para resolver o número real por trás de IDs em formato LID, mantendo os contatos do Chatwoot organizados por número de telefone quando possível.
- **Ignora Grupos**: Mensagens provenientes de chats de grupo (`@g.us`, `IsGroup`, `isGroup`) são simplesmente ignoradas, tanto na entrada (WuzAPI → Chatwoot) quanto na saída (Chatwoot → WuzAPI).

## Como Funciona

A ponte utiliza dois endpoints de webhook para gerenciar o fluxo de mensagens:

1.  `POST /webhook/wuzapi`: **(Entrada)**
    - **Quem chama?** A WuzAPI.
    - **O que faz?** É acionado quando uma nova mensagem chega no WhatsApp. O serviço processa os dados (incluindo campos como `Info`, `Sender`, `SenderAlt`, `Chat`, `ChatJid`), identifica o remetente, encontra ou cria o contato/conversa no Chatwoot e posta a mensagem na caixa de entrada. Mensagens de grupos são ignoradas.
    - **Alias compatível**: Também aceita `POST /webhook-wuzapi` para facilitar a configuração em painéis que esperam este formato de caminho.
    - **Onde configurar?** A URL deste endpoint deve ser configurada no painel da sua instância WuzAPI / Sistema de API WhatsApp.

2.  `POST /webhook/chatwoot`: **(Saída)**
    - **Quem chama?** O Chatwoot.
    - **O que faz?** É acionado quando um agente envia uma resposta no Chatwoot (evento `message_created` e `message_type = outgoing`). O serviço pega essa resposta e a envia para o cliente final através da API de envio de mensagens da WuzAPI / Sistema de API WhatsApp (`/chat/send/text`).
    - **Alias compatível**: Também aceita `POST /webhook-chatwoot` para facilitar a configuração.
    - **Onde configurar?** A URL deste endpoint deve ser configurada no campo "URL do webhook" da sua caixa de entrada do tipo API no Chatwoot.

### Detalhes Técnicos da Integração

- **Fluxo WuzAPI → Chatwoot**:
  - O webhook recebe eventos do tipo `Message`.
  - Para identificar o remetente:
    - Usa `Info.SenderAlt` sempre que disponível; caso contrário, `Info.Sender`.
    - Extrai o número base removendo o sufixo (`@s.whatsapp.net`, `@lid`, etc.) quando se trata de contato individual.
  - Se o evento indicar chat de grupo (`Chat`/`ChatJid` terminando em `@g.us` ou flags `IsGroup`/`isGroup` verdadeiras), a mensagem é ignorada e não é criada nenhuma conversa no Chatwoot.
  - A sincronização de avatar:
    - Consulta primeiro `POST /user/avatar` no Sistema de API WhatsApp (campo `results.url`).
    - Se não houver resultado, faz fallback para `GET /chat/getProfilePic`.
    - Envia a URL do avatar para o Chatwoot via `avatar_url` na criação/atualização de contato.

- **Fluxo Chatwoot → WuzAPI**:
  - O webhook recebe eventos `message_created` de saída (`message_type = outgoing`) enviados por agentes (`sender.type = agent_bot` ou `user`).
  - A partir do payload, obtém o `phone_number` do contato na conversa, procurando em:
    - `conversation.meta.sender.phone_number`;
    - `conversation.contact.phone_number`;
    - `sender.phone_number` do próprio payload.
  - Se o webhook não trouxer `phone_number`, a ponte faz uma chamada extra à API do Chatwoot (`GET /api/v1/accounts/:account_id/conversations/:conversation_id`) para recuperar o número do contato antes de enviar a mensagem.
  - Se o número contiver `@` (indicando JID de grupo), a mensagem é ignorada, pois grupos não são suportados.
  - O número é normalizado removendo qualquer caractere que não seja dígito (por exemplo, `+55 (81) 99999-9999` vira `5581999999999`) e enviado no campo `number` para o endpoint `/chat/send/text`.
  - A autenticação com a API de envio é feita pelo header `token`, conforme especificação do Sistema de API WhatsApp.

## Configuração

Para executar este projeto, você precisa configurar as seguintes variáveis de ambiente.

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto ou configure estas variáveis diretamente na sua plataforma de deploy (ex: EasyPanel).

```env
# ====================================
# === CONFIGURAÇÕES DO CHATWOOT ===
# ====================================

# URL da sua instância do Chatwoot (ex: https://chat.meudominio.com)
CHATWOOT_URL=""

# ID da sua conta no Chatwoot (geralmente 1)
CHATWOOT_ACCOUNT_ID=""

# ID da sua caixa de entrada do tipo "API" onde as mensagens aparecerão
CHATWOOT_INBOX_ID=""

# Token de acesso do seu perfil de agente no Chatwoot
CHATWOOT_API_TOKEN=""

# ====================================
# === CONFIGURAÇÕES DA WUZAPI ===
# ====================================

# URL base da API da sua instância WuzAPI (ex: https://api.wuzapi.com.br)
WUZAPI_API_URL=""

# Nome da instância WuzAPI que será usada para enviar as mensagens
WUZAPI_INSTANCE_NAME=""

# Token (API Key) da sua instância WuzAPI
WUZAPI_API_TOKEN=""
```

### Passos para Deploy

1.  Clone este repositório.
2.  Preencha as variáveis de ambiente conforme descrito acima.
3.  Faça o deploy da aplicação usando Docker (ou o método de sua preferência).
4.  Configure o webhook na WuzAPI para apontar para `https://SUA_URL_DA_PONTE/webhook/wuzapi`.
5.  Configure o webhook na sua caixa de entrada do Chatwoot para apontar para `https://SUA_URL_DA_PONTE/webhook/chatwoot`.

## Executando Localmente (Para Desenvolvimento)

1.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
2.  Preencha o arquivo `.env`.
3.  Inicie o servidor:
    ```bash
    uvicorn main:app --reload
    ```
