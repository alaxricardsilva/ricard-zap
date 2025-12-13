# Ponte de Integração WuzAPI ↔ Chatwoot

Este projeto é um serviço de ponte (bridge) construído em FastAPI (Python) que conecta uma instância da WuzAPI com uma caixa de entrada do tipo "API" no Chatwoot, permitindo uma comunicação bidirecional.

## Funcionalidades

- **Recebimento de Mensagens**: Recebe webhooks da WuzAPI sobre novas mensagens do WhatsApp (de conversas privadas e de grupos) e as cria na conversa correta dentro do Chatwoot.
- **Envio de Respostas**: Recebe webhooks do Chatwoot quando um agente responde a uma conversa e envia essa resposta para o cliente final via WuzAPI.
- **Criação e Atualização de Contatos**: Se uma mensagem é recebida de um número que não existe no Chatwoot, um novo contato é criado automaticamente.
- **Sincronização de Avatar**: Busca a foto de perfil do contato no WhatsApp (via WuzAPI) e a envia para o Chatwoot, mantendo o avatar do contato atualizado.
- **Compatibilidade de Formato**: Processa múltiplos formatos de payload da WuzAPI, incluindo o novo formato que utiliza `SenderAlt` e estruturas aninhadas, garantindo maior robustez.

## Como Funciona

A ponte utiliza dois endpoints de webhook para gerenciar o fluxo de mensagens:

1.  `POST /webhook/wuzapi`: **(Entrada)**
    - **Quem chama?** A WuzAPI.
    - **O que faz?** É acionado quando uma nova mensagem chega no WhatsApp. O serviço processa os dados, encontra ou cria o contato/conversa no Chatwoot e posta a mensagem na caixa de entrada.
    - **Onde configurar?** A URL deste endpoint deve ser configurada no painel da sua instância WuzAPI.

2.  `POST /webhook/chatwoot`: **(Saída)**
    - **Quem chama?** O Chatwoot.
    - **O que faz?** É acionado quando um agente envia uma resposta no Chatwoot. O serviço pega essa resposta e a envia para o cliente final através da API de envio de mensagens da WuzAPI.
    - **Onde configurar?** A URL deste endpoint deve ser configurada no campo "URL do webhook" da sua caixa de entrada do tipo API no Chatwoot.

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
