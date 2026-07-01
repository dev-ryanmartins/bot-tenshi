# Tenshi Bot

Bot Discord do Imperio Tenshi com site Python integrado, memoria documental em PDFs, IA via OpenRouter, comandos administrativos, academia, matrimonios, empregos e painel web.

## Comandos

O bot aceita os dois formatos de prefixo abaixo:

```text
tenshi ajuda
Tenshi, ajuda
```

Os comandos de moderação `nota`, `aviso`, `historico` e `info` também estão disponíveis como comandos de barra. Exemplos:

```text
tenshi nota @usuario observação interna
tenshi aviso @usuario motivo do aviso
tenshi historico @usuario
tenshi info @usuario
```

Use `tenshi ajuda` no Discord para consultar o catálogo completo. Notas e avisos são persistidos em `data/tenshi.db` com `aiosqlite`.

## Deploy na Railway como Worker

Este repositorio ja esta pronto para manter o bot online na Railway e servir o site Python integrado no mesmo processo:

- `railway.json` define o start command `python main.py`.
- `Procfile` define o processo `worker: python main.py`.
- `Dockerfile` força build Python 3.11 e evita conflito com o workspace Node.
- `requirements.txt` na raiz lista as dependencias Python usadas pelo bot.
- O token do Discord deve ficar apenas em variavel de ambiente.
- O site usa automaticamente a porta `PORT` da Railway e responde em `/health`.

### 1. Criar o servico

1. Abra a Railway.
2. Crie um novo projeto.
3. Escolha **Deploy from GitHub repo**.
4. Selecione `dev-ryanmartins/bot-tenshi`.
5. Configure o servico como **Worker**.

### 2. Variaveis obrigatorias na Railway

Coloque estas variaveis em **Variables**:

```env
DISCORD_TOKEN=seu_token_do_discord
OPENROUTER_API_KEY=sua_chave_openrouter
ADMIN_USERNAME=Alloy
ADMIN_PASSWORD=uma_senha_forte
ADMIN_SECRET=um_segredo_forte
ENABLE_SITE=1
```

Tambem deixei o arquivo `railway.env.example` com os nomes exatos das variaveis para voce copiar para o painel da Railway.

Nao coloque token ou chave direto no codigo e nao envie `.env` para o GitHub. As chaves reais devem ficar apenas em **Railway -> Variables**.

Nao configure `PORT`, `SITE_PORT` ou `SITE_HOST` na Railway. A propria Railway fornece `PORT`, e o codigo usa `0.0.0.0` automaticamente dentro dela.

### 3. Ativar o site na Railway

Para abrir o site no navegador:

1. Clique no servico do bot na Railway.
2. Abra **Settings**.
3. Va em **Networking -> Public Networking**.
4. Clique em **Generate Domain**.
5. Copie a URL gerada, por exemplo `https://seu-app.up.railway.app`.
6. Volte em **Variables** e adicione:

```env
TENSHI_SITE_URL=https://seu-app.up.railway.app
```

Depois clique em **Redeploy**. O bot e o site sobem juntos pelo mesmo comando `python main.py`.

Para manter notas e avisos entre redeploys, monte um **Volume** da Railway em `/data` e defina `TENSHI_DB_PATH=/data/tenshi.db`. Sem volume, o bot continua funcionando, mas o SQLite acompanha o ciclo de vida do container.

### 4. Start command

O start command ja esta salvo em `railway.json`:

```bash
python main.py
```

O `Procfile` tambem esta configurado:

```Procfile
worker: python main.py
```

Se o painel da Railway pedir manualmente, use exatamente esse comando.

### 5. Erro comum: `DISCORD_TOKEN nao encontrado`

Se os logs mostrarem:

```text
DISCORD_TOKEN nao encontrado no ambiente
```

o Worker iniciou corretamente, mas a variavel nao foi cadastrada no servico certo da Railway.

Confira:

1. Abra o projeto na Railway.
2. Clique no servico do bot, o **Worker**.
3. Abra **Variables**.
4. Cadastre `DISCORD_TOKEN` exatamente com esse nome.
5. Cadastre tambem `OPENROUTER_API_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_SECRET` e `ENABLE_SITE`.
6. Clique em **Redeploy** no ultimo deploy.

Nao coloque aspas ao redor do token e nao adicione espacos antes ou depois do valor.

## Rodar em VPS Linux com PM2

### 1. Instale Python, Git e PM2

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nodejs npm
sudo npm install -g pm2
```

### 2. Baixe o projeto

```bash
git clone https://github.com/dev-ryanmartins/bot-tenshi.git
cd bot-tenshi
```

### 3. Configure o ambiente

```bash
cp .env.example .env
nano .env
```

Preencha no `.env`:

```env
DISCORD_TOKEN=seu_token_do_discord
OPENROUTER_API_KEY=sua_chave_openrouter
ADMIN_USERNAME=Alloy
ADMIN_PASSWORD=uma_senha_forte
ADMIN_SECRET=um_segredo_forte
SITE_HOST=0.0.0.0
SITE_PORT=8081
TENSHI_SITE_URL=http://IP_DA_SUA_VPS:8081
ENABLE_SITE=1
```

Nunca publique o `.env` no GitHub.

### 4. Instale as dependencias Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r artifacts/tenshi-bot/requirements.txt
```

### 5. Inicie 24h com PM2

```bash
pm2 start ecosystem.config.cjs
pm2 save
pm2 startup
```

Depois do `pm2 startup`, copie e rode o comando que o PM2 mostrar na tela.

### 6. Comandos uteis

```bash
pm2 status
pm2 logs tenshi-bot
pm2 restart tenshi-bot
pm2 stop tenshi-bot
```

O site integrado fica em:

```text
http://IP_DA_SUA_VPS:8081
```

## Rodar localmente no Windows

```powershell
.\start_bot_24h.ps1
```

Para abrir apenas o site:

```powershell
.\start_site.ps1
```

## Arquivos importantes

- `main.py`: entrada principal do projeto.
- `artifacts/tenshi-bot/main.py`: bot Discord.
- `artifacts/tenshi-bot/site_server.py`: site Python integrado.
- `artifacts/tenshi-bot/academia_curriculo.py`: curriculo oficial da Academia Imperial.
- `ecosystem.config.cjs`: configuracao PM2 para VPS.
- `.env.example`: modelo seguro das variaveis de ambiente.

## Seguranca

- O arquivo `.env` fica ignorado pelo Git.
- Nao suba tokens do Discord, chaves OpenRouter, logs, caches ou `node_modules`.
- Se um token ja foi exposto em conversa ou print, gere outro no painel oficial antes de usar em producao.
