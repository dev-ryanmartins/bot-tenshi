# Tenshi Bot

Bot Discord do Imperio Tenshi com site Python integrado, memoria documental em PDFs, IA via OpenRouter, comandos administrativos, academia, matrimonios, empregos e painel web.

## Deploy na Railway como Worker

Este repositorio ja esta pronto para manter o bot online como Worker na Railway:

- `railway.json` define o start command `python main.py`.
- `Procfile` define o processo `worker: python main.py`.
- `Dockerfile` força build Python 3.11 e evita conflito com o workspace Node.
- `requirements.txt` na raiz lista as dependencias Python usadas pelo bot.
- O token do Discord deve ficar apenas em variavel de ambiente.
- O Worker nao precisa de dominio publico nem healthcheck HTTP para manter o bot online.

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

Nao coloque o token direto no codigo e nao envie `.env` para o GitHub.

Para Worker, nao configure `PORT`, `SITE_PORT` ou `SITE_HOST`. Se depois voce quiser abrir o painel web publicamente, crie um Web Service separado ou gere dominio publico e adicione `TENSHI_SITE_URL`.

### 3. Start command

O start command ja esta salvo em `railway.json`:

```bash
python main.py
```

O `Procfile` tambem esta configurado:

```Procfile
worker: python main.py
```

Se o painel da Railway pedir manualmente, use exatamente esse comando.

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
