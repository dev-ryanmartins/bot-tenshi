# Tenshi Bot

Bot Discord do Império Tenshi com site Python integrado, memória documental em PDFs, IA via OpenRouter, comandos administrativos, academia, matrimônios, empregos e um painel de gerenciamento completo.

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

O Mercado Imperial possui itens comuns e avançados com requisitos de progressão. A portaria administra 50 casas únicas e cria automaticamente canais privados `casa-N` conforme forem adquiridos. Administradores podem usar `tenshi set-status` para editar o próprio personagem ou `tenshi set-status @usuario` para editar outro membro pelo painel de atributos e prestígios.

A Tenshi Academy também possui corpo docente: `tenshi professor @usuario` cadastra professores, assistentes, coordenação ou direção e permite escolher as disciplinas no próprio painel. `tenshi ministrar-aula [materia] [tema]` gera a aula assistida por IA e abre presença para os alunos. Foi adicionada a matéria "Psicologia Estratégica e Maestria", onde a IA atua como Conselheiro Estratégico no canal `#psicologia-e-estrategia`, oferecendo análises baseadas em 120 livros sobre poder e comportamento. Alunos aprovados recebem o diploma e um cargo de prestígio, como `🎓 │ Estrategista Imperial`. O fundador (ID `619302798751694849`) mantém acesso integral como Imperador, Diretor e Professor Imperial.

O painel `tenshi parentesco [@usuario]` cria e aplica cargos familiares mantendo a estética do servidor. O fundador é o Patriarca da Família; a lista inclui filhos, irmãos, `Cunhad@`, sobrinhos, netos, tios, primos, afilhados e vínculos personalizados. Ao casar com alguém já registrado como irmão ou irmã, o novo cônjuge recebe automaticamente o vínculo neutro `Cunhad@`. Use `tenshi meu-parentesco`, `tenshi lista-parentescos` e `tenshi arvore-familiar` para consultar os registros.

O comando `tenshi ajuda` abre uma central interativa com todas as categorias de comandos, navegação por menu e botões de página. O texto mestre continua auditável contra as rotas do bot para que nenhum comando fique escondido. Em caso de morte definitiva de um personagem, foi implementado um sistema de herança automática: o bot verifica se o falecido era casado e, em caso afirmativo, transfere a totalidade de seus bens (moedas, itens, propriedades) e títulos de nobreza para o cônjuge sobrevivente, isentando-o do imposto sobre herança.

O comando administrativo `tenshi painel-admin [@usuario]` (exclusivo para o Imperador e seu cônjuge) abre um painel interativo completo em um tópico privado. Ele centraliza `set-status`, gerenciamento de `parentesco` e a sincronização de cargos do Discord. O novo comando `tenshi auditar-cargos` varre o servidor, compara os cargos do Discord com o banco de dados e gera um relatório interativo para corrigir inconsistências. `tenshi organizar-canais` cria uma categoria com canais temáticos para comandos, fichas, mercado, Academia, família, aventuras, eventos e suporte, sem duplicar o que já existe. Foi implementada uma validação cruzada de permissões: o bot agora verifica os cargos reais de um membro no Discord antes de executar comandos restritos. Além disso, foi criado um sistema de eleições com voto secreto para cargos públicos, como o de Primeiro-Ministro, garantindo um processo democrático seguro e anônimo.

Os canais de notícias são funcionais: `tenshi jornal-policial` reúne ocorrências salvas no RPG e informes fictícios identificados, enquanto `tenshi jornal-cotidiano` publica vários acontecimentos públicos e crônicas do dia. Crimes como assaltos geram plantões automáticos no canal policial.

`tenshi mundo` abre o atlas mundial por continente e páginas de países. A cidade é pesquisada pelo usuário para contornar o limite de 25 opções dos menus do Discord; o bot cria um tópico com pontos turísticos, regiões para hospedagem, gastronomia, transporte, segurança e roteiro. `tenshi viagem-atual` consulta a jornada e `tenshi terminar-viagem` encerra e arquiva o tópico. A lista de países é atualizada por fonte mundial e mantida em cache, com catálogo de emergência quando a rede está indisponível.

`tenshi interagir-local` reconhece o canal atual e abre atividades próprias para cafeteria, sorveteria, laboratório, empresa, pet-shop, lojinha, casamento, cinema, banco, praça, lavanderia, parque, psicólogo, departamento policial, bar, beco e zoológico. Cada sessão usa tópico, pode ser encerrada com `tenshi terminar-interacao`, gera resumo privado para a equipe e remove o tópico ao final.

`tenshi cassino` oferece dez jogos com apostas debitadas da carteira, probabilidades favoráveis à casa, histórico financeiro e narração por IA nas derrotas. `tenshi zoologico` possui 24 habitats. `tenshi concurso-publico` aplica prova de cinco questões para dez carreiras policiais e jurídicas; nota 4/5 concede automaticamente um cargo seguindo a estética do servidor.

O comando administrativo `tenshi sincronizar-condominio` gera ou vincula os 50 canais residenciais preservando o prefixo visual dos canais já existentes. Além disso, o bot agora possui um sistema de IA que gera e atribui cargos estéticos automaticamente com base nas conquistas dos jogadores. Ao obter um diploma, uma nova profissão ou um título, a IA analisa a estética de cargos do servidor e cria uma nova role (ex: `🎓 │ Diplomado em Maestria`), atribuindo-a ao membro como um selo de prestígio.

Novos participantes recebem automaticamente o cargo estético `Membro`. Administradores usam `tenshi parentesco` para selecionar a pessoa e definir `Filho`, `Filha`, `Irmão`, `Irmã`, `Familiar` ou um vínculo personalizado. Casamentos aplicam `Familiar` e uma dissolução restaura o vínculo anterior.

## Deploy na Railway

Este repositorio ja esta pronto para manter o bot online na Railway e servir o site Python integrado no mesmo processo:

- `railway.json` define o start command `python main.py` e healthcheck em `/health`.
- `Procfile` define o processo `web: python main.py`.
- `Dockerfile` força build Python 3.11 e evita conflito com o workspace Node.
- `requirements.txt` na raiz lista as dependencias Python usadas pelo bot.
- O token do Discord deve ficar apenas em variavel de ambiente.
- O site usa automaticamente a porta `PORT` da Railway e responde em `/health`.

### 1. Criar o servico

1. Abra a Railway.
2. Crie um novo projeto.
3. Escolha **Deploy from GitHub repo**.
4. Selecione `dev-ryanmartins/bot-tenshi`.
5. Configure o servico como **Web Service** (nao Worker), pois o bot sobe o site HTTP no mesmo processo.

### 2. Variaveis obrigatorias na Railway

Coloque estas variaveis em **Variables**:

```env
DISCORD_TOKEN=seu_token_do_discord
OPENROUTER_API_KEY=sua_chave_openrouter
ADMIN_USERNAME=Alloy
ADMIN_PASSWORD=uma_senha_forte
ADMIN_SECRET=um_segredo_forte
ENABLE_SITE=1
TENSHI_DATA_DIR=/data
TENSHI_DB_PATH=/data/tenshi.db
```

Tambem deixei o arquivo `railway.env.example` com os nomes exatos das variaveis para voce copiar para o painel da Railway.

Nao coloque token ou chave direto no codigo e nao envie `.env` para o GitHub. As chaves reais devem ficar apenas em **Railway -> Variables**.

Nao configure `PORT`, `SITE_PORT` ou `SITE_HOST` na Railway. A propria Railway fornece `PORT`, e o codigo usa `0.0.0.0` automaticamente dentro dela.

### 3. Volume para persistir dados

Para manter fichas, economia, casas, notas e avisos entre redeploys:

1. No servico da Railway, abra **Volumes**.
2. Crie um volume montado em `/data`.
3. Confirme `TENSHI_DATA_DIR=/data` e `TENSHI_DB_PATH=/data/tenshi.db` nas variaveis.
4. Faca **Redeploy**.

Sem volume, o bot continua funcionando, mas JSON e SQLite acompanham o ciclo de vida do container.

### 4. Ativar o site na Railway

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

### 5. Start command

O start command ja esta salvo em `railway.json`:

```bash
python main.py
```

O `Procfile` tambem esta configurado:

```Procfile
web: python main.py
```

Se o painel da Railway pedir manualmente, use exatamente esse comando.

### 6. Erro comum: `DISCORD_TOKEN nao encontrado`

Se os logs mostrarem:

```text
DISCORD_TOKEN nao encontrado no ambiente
```

o Worker iniciou corretamente, mas a variavel nao foi cadastrada no servico certo da Railway.

Confira:

1. Abra o projeto na Railway.
2. Clique no servico do bot, o **Web Service**.
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
