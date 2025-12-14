# Ponte de Integração WuzAPI ↔ Chatwoot

Este projeto é um serviço de ponte (bridge) construído em FastAPI (Python) que conecta uma instância da WuzAPI com uma caixa de entrada do tipo "API" no Chatwoot, permitindo uma comunicação bidirecional.

## Funcionalidades

- **Recebimento de Mensagens**: Recebe webhooks da WuzAPI sobre novas mensagens do WhatsApp (de conversas privadas e de grupos) e as cria na conversa correta dentro do Chatwoot.
- **Envio de Respostas**: Recebe webhooks do Chatwoot quando um agente responde a uma conversa e envia essa resposta para o cliente final via WuzAPI.
- **Criação e Atualização de Contatos**: Se uma mensagem é recebida de um número que não existe no Chatwoot, um novo contato é criado automaticamente.
- **Sincronização de Avatar**: Busca a foto de perfil do contato ou grupo no WhatsApp (via API `/user/avatar` do Sistema de API WhatsApp, com fallback para `/chat/getProfilePic`) e a envia para o Chatwoot via `avatar_url`, mantendo o avatar do contato atualizado.
- **Compatibilidade de Formato**: Processa múltiplos formatos de payload da WuzAPI / Sistema de API WhatsApp, incluindo o novo formato que utiliza `SenderAlt` (mapeamento de LID para número) e estruturas aninhadas, garantindo maior robustez.
- **Compatível com Grupos**: Identifica automaticamente se a mensagem veio de grupo (`@g.us`, `IsGroup`, `isGroup`) e cria um contato específico para o grupo (ex.: `[GRUPO] Nome do grupo`) no Chatwoot, preservando o `chatId` do grupo.
- **Compatível com LID**: Utiliza `SenderAlt` sempre que disponível para resolver o número real por trás de IDs em formato LID, mantendo os contatos do Chatwoot organizados por número de telefone quando possível.

## Como Funciona

A ponte utiliza dois endpoints de webhook para gerenciar o fluxo de mensagens:

1.  `POST /webhook/wuzapi`: **(Entrada)**
    - **Quem chama?** A WuzAPI.
    - **O que faz?** É acionado quando uma nova mensagem chega no WhatsApp. O serviço processa os dados (incluindo campos como `Info`, `Sender`, `SenderAlt`, `Chat`, `ChatJid`), identifica se é conversa privada ou de grupo, encontra ou cria o contato/conversa no Chatwoot e posta a mensagem na caixa de entrada.
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
  - Para grupos:
    - Usa `Chat`/`ChatJid`/`Chat` no evento para identificar o `chatId` do grupo (tipicamente terminando em `@g.us`).
    - Cria/atualiza um contato no Chatwoot com nome `[GRUPO] Nome do grupo` e `phone_number = chatId`.
    - As mensagens aparecem no Chatwoot com o formato `Nome do remetente: conteúdo da mensagem`.
  - A sincronização de avatar:
    - Consulta primeiro `POST /user/avatar` no Sistema de API WhatsApp (campo `results.url`).
    - Se não houver resultado, faz fallback para `GET /chat/getProfilePic`.
    - Envia a URL do avatar para o Chatwoot via `avatar_url` na criação/atualização de contato.

- **Fluxo Chatwoot → WuzAPI**:
  - O webhook recebe eventos `message_created` de saída (`message_type = outgoing`) enviados por agentes (`sender.type = agent_bot` ou `user`).
  - A partir do payload, obtém o `phone_number` do contato na conversa.
    - Se for contato individual: remove apenas o `+` e envia o número em formato internacional (sem `+`) para o endpoint `/chat/send/text`.
    - Se for grupo: o `phone_number` armazenado é o próprio `chatId` do grupo (`...@g.us`), que é enviado diretamente no campo `number` para o Sistema de API WhatsApp.
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
