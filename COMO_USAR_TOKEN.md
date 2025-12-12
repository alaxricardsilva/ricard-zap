# Como Fazer Push para o GitHub Usando um Token de Acesso Pessoal (PAT)

O GitHub não aceita mais senhas para autenticação de operações Git na linha de comando. Em vez disso, você deve usar um **Token de Acesso Pessoal (Personal Access Token - PAT)**.

Este guia mostra como gerar um token e usá-lo para enviar suas alterações (`push`) para um repositório.

---

### Passo 1: Gerar um Token de Acesso Pessoal no GitHub

1.  **Acesse as Configurações do GitHub:**
    *   Faça login na sua conta do GitHub.
    *   Clique na sua foto de perfil no canto superior direito e vá para **Settings**.

2.  **Navegue até a Seção de Desenvolvedor:**
    *   No menu à esquerda, role para baixo e clique em **Developer settings**.

3.  **Acesse os Tokens de Acesso Pessoal:**
    *   No menu à esquerda, clique em **Personal access tokens** e depois em **Tokens (classic)**.

4.  **Gere um Novo Token:**
    *   Clique no botão **"Generate new token"** e depois em **"Generate new token (classic)"**.
    *   **Note (Nome):** Dê um nome descritivo ao seu token (ex: `push-ricard-zap`).
    *   **Expiration (Validade):** Escolha uma data de validade para o token. É uma boa prática de segurança não deixar que os tokens durem para sempre.
    *   **Select scopes (Permissões):** Marque a caixa de seleção principal chamada **`repo`**. Isso dará ao token permissão total para gerenciar seus repositórios (públicos e privados), o que é necessário para fazer o `push`.

5.  **Copie o Token:**
    *   Role até o final da página e clique em **"Generate token"**.
    *   **IMPORTANTE:** O GitHub mostrará seu token **apenas uma vez**. Copie-o imediatamente e guarde-o em um local seguro (como um gerenciador de senhas). Se você perder o token, terá que gerar um novo.

---

### Passo 2: Fazer o Push Usando o Token

A forma mais direta de usar o token é incluí-lo na URL do comando `git push`.

**Atenção:** Este método é funcional, mas deixa seu token visível no histórico de comandos do seu terminal. Por segurança, considere usar um token com data de expiração curta.

**Comando:**

Use o seguinte modelo de comando, substituindo os valores entre `< >`:

```bash
git push https://<SEU_USUARIO>:<SEU_TOKEN>@github.com/<SEU_USUARIO>/<NOME_DO_REPOSITORIO>.git <NOME_DA_BRANCH>
```

**Exemplo para o seu repositório `ricard-zap`:**

1.  Copie o comando abaixo.
2.  Substitua `<SEU_TOKEN_AQUI>` pelo token que você gerou no Passo 1.
3.  Execute o comando no seu terminal, dentro da pasta do projeto.

```bash
git push https://alaxricardsilva:<SEU_TOKEN_AQUI>@github.com/alaxricardsilva/ricard-zap.git main
```

Após executar este comando, suas alterações serão enviadas para o branch `main` do seu repositório no GitHub.

---

### Passo 3: Criando uma Release (Versão) no GitHub

Criar uma "Release" é uma forma profissional de marcar uma versão estável do seu projeto. O processo envolve criar uma "tag" (etiqueta) e depois enviá-la para o GitHub.

**1. Crie a Tag Localmente:**

Depois de enviar seu código com sucesso (Passo 2), execute o comando abaixo no terminal para criar uma etiqueta de versão. Substitua `v1.0.0` pelo número da versão desejada e a mensagem por algo descritivo.

```bash
git tag -a v1.0.0 -m "v1.0.0: Descrição das alterações nesta versão"
```

**Exemplo:**
```bash
git tag -a v1.0.0 -m "v1.0.0: Lançamento inicial da integração WuzAPI e Chatwoot"
```

**2. Envie a Tag para o GitHub:**

A tag criada existe apenas localmente. Para enviá-la ao GitHub, você precisa fazer um `push` específico para ela, usando o mesmo método de autenticação com token.

**Comando:**
```bash
git push https://<SEU_USUARIO>:<SEU_TOKEN>@github.com/<SEU_USUARIO>/<NOME_DO_REPOSITORIO>.git <NOME_DA_TAG>
```

**Exemplo para a tag `v1.0.0`:**
```bash
git push https://alaxricardsilva:<SEU_TOKEN_AQUI>@github.com/alaxricardsilva/ricard-zap.git v1.0.0
```

**3. Crie a Release na Interface do GitHub:**

- Vá para a página do seu repositório no GitHub.
- Clique em **"Releases"** na barra lateral direita.
- Clique em **"Create a new release"** ou **"Draft a new release"**.
- No campo "Choose a tag", selecione a tag que você acabou de enviar (ex: `v1.0.0`).
- Dê um título e uma descrição detalhada para a sua release, explicando o que mudou.
- Clique em **"Publish release"**.

Pronto! Agora você tem uma versão oficial do seu projeto documentada no GitHub.
