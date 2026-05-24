# Bot Tenshi — Discord RPG Imperial

Bot Discord completo para o servidor do Império de Tenshi, com RPG, economia, IA (Groq), eventos automáticos, facções, tarot/runas e duelos PvP.

## Run & Operate

- `Bot Tenshi` — workflow principal que roda o bot Discord (python3 main.py)
- Required env: `DISCORD_TOKEN`, `GROQ_API_KEY`, `IMPERADOR_ID` (opcional — ID Discord do Alloy)

## Stack

- Python 3.11 + discord.py 2.3.2
- IA: Groq Cloud (llama3-70b-8192)
- Banco de dados: JSON local em `artifacts/tenshi-bot/data/`
- Keep Alive: Flask na porta 8090

## Where things live

- `artifacts/tenshi-bot/main.py` — ponto de entrada e roteador de comandos
- `artifacts/tenshi-bot/cogs/` — módulos separados por funcionalidade
- `artifacts/tenshi-bot/database.py` — acesso ao banco JSON
- `artifacts/tenshi-bot/utils.py` — constantes, embed helper, cooldowns
- `artifacts/tenshi-bot/data/` — dados persistidos (db.json, faccoes.json)

## Módulos (cogs)

- `rpg.py` — perfil, treino, missões, interações de roleplay
- `economia.py` — carteira, loja, compras
- `faccoes.py` — entrar em facções, ranking
- `mistico.py` — tarot e runas diários
- `duelo.py` — duelos PvP com apostas
- `eventos.py` — invasões automáticas em background
- `moderacao.py` — ban, kick, mute, clear, decreto imperial
- `loremaster.py` — narrativas RPG e profecias geradas por IA (Groq)

## Comandos (prefixo: "Tenshi,")

- `Tenshi, status` — perfil imperial
- `Tenshi, treinar` — ganhar poder (cooldown 30min)
- `Tenshi, missao` — aceitar missão imperial
- `Tenshi, carteira` / `loja` / `comprar [id]` — economia
- `Tenshi, entrar [facção]` / `ranking` — facções
- `Tenshi, tarot` / `runa` — místico diário
- `Tenshi, duelo @user [aposta]` — combate PvP
- `Tenshi, cronica [militar/politico/esoterico]` — lore com IA
- `Tenshi, evento-lore` — profecia (ADM)
- `Tenshi, decreto [msg]` — decreto imperial (Alloy)
- `Tenshi, invasao` — iniciar invasão manual (ADM)

## Architecture decisions

- Roteamento via `on_message` com prefixo `tenshi,` ao invés de slash commands, para linguagem natural
- JSON local para persistência leve (sem banco de dados externo necessário)
- Groq `llama3-70b-8192` para geração de lore/crônicas/profecias
- Eventos de invasão rodam em background task com intervalos aleatórios (1-2h)
- Keep Alive Flask na porta 8090 para compatibilidade com UptimeRobot

## User preferences

- Bot em português (PT-BR), linguagem imersiva e imperial
- Respostas em Discord Embeds com cores escuras/imperiais
- Imperador Alloy recebe tratamento especial em todos os comandos

## Gotchas

- Definir `IMPERADOR_ID` nos secrets com o ID Discord do dono para ativar poderes especiais do Alloy
- O banco de dados fica em `artifacts/tenshi-bot/data/` — não apagar em produção
- Invasões automáticas disparam a cada 1-2 horas aleatoriamente no primeiro canal disponível
