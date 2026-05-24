import discord
import random
import asyncio
from datetime import datetime, timedelta
from database import get_user, save_user, add_pontos_faccao, calcular_nivel
from utils import (embed_imperial, embed_pegada, COOLDOWN_TREINO, IMPERADOR_ID,
                   SEP, RODAPE_IMPERIAL, CORES_PEGADA)

TREINOS_NARRATIVOS = [
    "💧 *Horas meditando sob a cachoeira gelada das montanhas do norte — o frio é apenas mais um inimigo a dobrar. Seu poder cresceu como a névoa que sobe das pedras...*",
    "⚔️ *Mil golpes contra a pedra sagrada da arena central. Os veteranos pararam para observar — raramente viam tal dedicação no olhar de alguém.*",
    "🌙 *Sob a lua cheia de Tenshi, você canalizou energia das constelações pelo corpo. Cada respiração expandia seu espírito como uma chama que se recusa a morrer.*",
    "🌊 *Você mergulhou nas profundezas do Rio Eterno e lutou contra a correnteza por horas. A pressão forja campeões. Você emergiu transformado.*",
    "🏹 *No campo de treino imperial, cada flecha disparada foi mais precisa que a anterior. Sua mente e corpo finalmente falam a mesma língua.*",
    "🧘 *Meditação profunda nas câmaras arcanas. O Mestre das Sombras observou em silêncio — e assentiu com respeito ao ver sua concentração.*",
    "🔥 *Você enfrentou o manequim de pedra de fogo por horas, absorvendo impacto após impacto. Seu corpo aprendeu o que as palavras não ensinam.*",
    "🌿 *Treinamento às escuras nas catacumbas, onde o único guia era o som e o instinto. Você aprendeu a sentir o perigo antes de vê-lo.*",
    "⚡ *As runas no tatame da arena pulsaram enquanto você canalizou cada movimento com intenção absoluta. O ar vibrou ao redor de você.*",
    "🦅 *No alto da Torre Sombria, você treinou contra o vento que corta como lâmina. O Império observava lá embaixo — pequeno, mas presente.*",
]

TREINOS_COM_DESCRICAO = [
    ("combate", "⚔️ *Seu treino de combate durou horas. Golpe após golpe, seu corpo foi esculpido pela disciplina imperial. A arena testemunhou evolução.*"),
    ("meditacao", "🧘 *A meditação profunda revelou segredos do éter de Tenshi. Sua mente expandiu além dos limites conhecidos.*"),
    ("magia", "🔮 *A prática arcana consumiu seu foco por horas. As runas responderam — você está crescendo.*"),
    ("espiritualidade", "✨ *Seu espírito toca algo além do físico. Uma calma inquietante e poderosa se instala.*"),
    ("estrategia", "📜 *Horas estudando os Tratados de Guerra do Imperador. Sua mente agora pensa três passos à frente.*"),
]

MISSOES = [
    {"nome": "Patrulha nas Fronteiras do Norte",         "emoji": "🏔️", "cor": 0x8B0000,
     "descricao": "Rumores de criaturas sombrias se aproximando das muralhas do norte. O Império precisa de vigilantes.",
     "narrativa": "🌑 *As tochas tremem enquanto você avança pelas fronteiras congeladas. Rastros enormes na neve... algo passou aqui.*\n\n*Após horas de patrulha, você identifica o perigo e retorna com informações cruciais. O Império está mais seguro.*",
     "xp": 80, "moedas": 60, "poder": 15, "min": 3},
    {"nome": "Missão Diplomática na Corte Rival",        "emoji": "👑", "cor": 0xFFD700,
     "descricao": "Uma delegação deve negociar termos com o clã rival. Eloquência e astúcia são essenciais.",
     "narrativa": "👑 *Os salões de mármore da corte rival. Cada palavra pesa mil espadas. Você manteve a compostura e fechou um acordo favorável a Tenshi.*",
     "xp": 100, "moedas": 90, "poder": 10, "min": 4},
    {"nome": "Investigação nas Catacumbas Místicas",     "emoji": "🔮", "cor": 0x4B0082,
     "descricao": "Runas foram ativadas nas profundezas. Um agente deve investigar antes que o portal se abra.",
     "narrativa": "🔮 *As paredes pulsam com luz violeta. Você decifrou o símbolo proibido nos últimos segundos — o portal foi selado. O equilíbrio de Tenshi preservado.*",
     "xp": 120, "moedas": 70, "poder": 25, "min": 5},
    {"nome": "Operação Clandestina no Submundo",         "emoji": "🖤", "cor": 0x1C1C1C,
     "descricao": "Infiltre a rede criminosa e recupere documentos secretos roubados da Corte Imperial.",
     "narrativa": "🌃 *Luzes fracas de tavernas clandestinas. Sua identidade ficou intacta. Os documentos, recuperados. O Imperador Alloy reconhecerá essa discreção.*",
     "xp": 110, "moedas": 100, "poder": 20, "min": 4},
    {"nome": "Auditoria Corporativa — Tenshi Enterprise","emoji": "🏢", "cor": 0x1E3A5F,
     "descricao": "Irregularidades em uma filial da Enterprise. Investigue e reporte ao CEO antes que vaze.",
     "narrativa": "📊 *Planilhas, contratos, reuniões tensas. Você encontrou a fraude e a expôs com evidências. A empresa está mais forte. O conselho aprova.*",
     "xp": 90, "moedas": 110, "poder": 5, "min": 3},
    {"nome": "Escolta de Relíquia Ancestral",            "emoji": "🗿", "cor": 0x8B6914,
     "descricao": "Uma relíquia sagrada de Tenshi precisa ser transportada com segurança pelas estradas do Império.",
     "narrativa": "🛡️ *Emboscadas, chuva e estradas traiçoeiras. Mas você manteve a relíquia segura até o destino. Os anciãos abençoam seu nome.*",
     "xp": 95, "moedas": 80, "poder": 18, "min": 4},
]

CLIMAS = [
    ("🌑 Névoa das Catacumbas",     "Os místicos sentem os véus rasgando. Habilidades arcanas estão amplificadas.", 0x4B0082),
    ("⚡ Tempestade Imperial",      "Relâmpagos dourados cortam o céu de Tenshi. Guerreiros ganham determinação extra.", 0x8B0000),
    ("☀️ Aurora Dourada",           "Um nascer do sol histórico ilumina o Império. Ânimo elevado, laços fortalecidos.", 0xFFD700),
    ("🌊 Maré do Destino",          "O Rio Eterno transborda com poder ancestral. Profecias se cumprem mais rapidamente.", 0x00CED1),
    ("🌿 Brisa das Planícies",      "Um vento calmo do leste traz paz e clareza mental ao Império.", 0x228B22),
    ("🔥 Cinzas do Vulcão Sombrio", "Cinzas quentes cobrem as ruas. O perigo está no ar — e com ele, oportunidade.", 0xFF4500),
    ("❄️ Inverno Eterno do Norte",  "Frio que corta os ossos desce das montanhas. Apenas os fortes prosperam hoje.", 0x708090),
]

PROFISSOES = {
    "ferreiro":    {"emoji": "⚒️", "desc": "Forja armas e armaduras imperiais. Acesso à criação de itens.", "bonus": "poder"},
    "alquimista":  {"emoji": "⚗️", "desc": "Cria poções e transmuta materiais. Acesso a consumíveis raros.", "bonus": "xp"},
    "escriba":     {"emoji": "📜", "desc": "Registra a história de Tenshi. Ganha XP extra em missões narrativas.", "bonus": "xp"},
    "mercador":    {"emoji": "💰", "desc": "Especialista em comércio. Desconto em compras e bônus em transferências.", "bonus": "moedas"},
    "guardiao":    {"emoji": "🛡️", "desc": "Protege o Império. Bônus defensivo em duelos.", "bonus": "poder"},
    "espiao":      {"emoji": "🌑", "desc": "Agente das sombras. Missões rendem mais moedas.", "bonus": "moedas"},
}


class RPG:
    def __init__(self, bot):
        self.bot = bot
        self.missoes_ativas: dict = {}

    async def handle_treinar(self, message, args=None):
        user = get_user(message.author.id)
        agora = datetime.utcnow()

        if user.get("ultimo_treino"):
            ultimo = datetime.fromisoformat(user["ultimo_treino"])
            diferenca = agora - ultimo
            if diferenca < timedelta(seconds=COOLDOWN_TREINO):
                restante = timedelta(seconds=COOLDOWN_TREINO) - diferenca
                mins = int(restante.total_seconds() // 60)
                segs = int(restante.total_seconds() % 60)
                pegada = user.get("pegada", "imperial")
                embed = discord.Embed(
                    title="⏳ RECUPERAÇÃO EM ANDAMENTO",
                    description=(
                        f"*Seu corpo ainda absorve as lições do último treino...*\n{SEP}\n\n"
                        f"Próximo treino disponível em: **{mins}m {segs}s**\n\n"
                        f"*Use `Tenshi, meditar` ou `Tenshi, descansar` enquanto aguarda.*"
                    ),
                    color=CORES_PEGADA.get(pegada, 0x2B0A3D)
                )
                embed.set_footer(text=RODAPE_IMPERIAL)
                await message.channel.send(embed=embed)
                return

        ganho_poder = random.randint(10, 28)
        ganho_xp    = random.randint(30, 65)
        pegada = user.get("pegada", "imperial")

        # Narrativa personalizada se o usuário descreveu a ação
        descricao_usuario = " ".join(args).lower() if args else ""
        if descricao_usuario:
            for keyword, narrativa_custom in TREINOS_COM_DESCRICAO:
                if keyword in descricao_usuario:
                    narrativa = narrativa_custom
                    break
            else:
                narrativa = random.choice(TREINOS_NARRATIVOS)
        else:
            narrativa = random.choice(TREINOS_NARRATIVOS)

        user["poder"] += ganho_poder
        user["xp"]    += ganho_xp
        nivel, xp_prox = calcular_nivel(user["xp"])
        user["nivel"]  = nivel
        user["ultimo_treino"] = agora.isoformat()

        if user.get("faccao"):
            add_pontos_faccao(user["faccao"], 2)

        save_user(message.author.id, user)

        embed = discord.Embed(
            title="⚡ TREINAMENTO IMPERIAL",
            description=f"{narrativa}\n\n{SEP}",
            color=CORES_PEGADA.get(pegada, 0x2B0A3D)
        )
        embed.add_field(name="📈 Ganhos", value=f"**+{ganho_poder} Poder** `•` **+{ganho_xp} XP**", inline=False)
        embed.add_field(name="💥 Poder Total",    value=f"**{user['poder']}**", inline=True)
        embed.add_field(name="✨ XP Total",       value=f"**{user['xp']}**",   inline=True)
        embed.add_field(name="📊 Nível",          value=f"**{nivel}**",        inline=True)
        embed.set_footer(text=f"⏳ Próximo treino em {COOLDOWN_TREINO // 60} minutos  •  {RODAPE_IMPERIAL}")
        await message.channel.send(embed=embed)

    async def handle_missao(self, message, args=None):
        user  = get_user(message.author.id)
        uid   = message.author.id
        pegada = user.get("pegada", "imperial")

        if uid in self.missoes_ativas:
            ma  = self.missoes_ativas[uid]
            fim = ma["fim"]
            restante = fim - datetime.utcnow()
            if restante.total_seconds() > 0:
                mins = int(restante.total_seconds() // 60)
                segs = int(restante.total_seconds() % 60)
                embed = discord.Embed(
                    title=f"⏳ EM MISSÃO — {ma['missao']['nome']}",
                    description=(
                        f"*Você já está em campo, guerreiro...*\n{SEP}\n\n"
                        f"*{ma['missao']['descricao']}*\n\n"
                        f"Retorno em: **{mins}m {segs}s**"
                    ),
                    color=ma["missao"]["cor"]
                )
                embed.set_footer(text=RODAPE_IMPERIAL)
                await message.channel.send(embed=embed)
                return

        missao = random.choice(MISSOES)
        fim    = datetime.utcnow() + timedelta(minutes=missao["min"])
        self.missoes_ativas[uid] = {"missao": missao, "fim": fim}

        embed = discord.Embed(
            title=f"{missao['emoji']} MISSÃO ACEITA — {missao['nome']}",
            description=(
                f"*Os selos imperiais foram apostos no pergaminho...*\n{SEP}\n\n"
                f"*{missao['descricao']}*\n\n{SEP}"
            ),
            color=missao["cor"]
        )
        embed.add_field(name="⏱️ Duração", value=f"**{missao['min']} minutos**", inline=True)
        embed.add_field(name="🏆 Recompensas", value=f"**+{missao['xp']} XP** `•` **+{missao['moedas']} Moedas** `•` **+{missao['poder']} Poder**", inline=False)
        embed.set_footer(text=f"O bot notificará quando concluir!  •  {RODAPE_IMPERIAL}")
        await message.channel.send(embed=embed)

        await asyncio.sleep(missao["min"] * 60)

        if uid in self.missoes_ativas:
            del self.missoes_ativas[uid]
            user = get_user(uid)
            user["xp"]     += missao["xp"]
            user["moedas"] += missao["moedas"]
            user["poder"]  += missao["poder"]
            user["missoes_completas"] = user.get("missoes_completas", 0) + 1
            nivel, _ = calcular_nivel(user["xp"])
            user["nivel"] = nivel
            if user.get("faccao"):
                add_pontos_faccao(user["faccao"], 5)
            save_user(uid, user)

            embed_conc = discord.Embed(
                title=f"🏆 {missao['emoji']} MISSÃO CONCLUÍDA — {missao['nome']}",
                description=f"{missao['narrativa']}\n\n{SEP}",
                color=0xFFD700
            )
            embed_conc.add_field(
                name="🎁 Recompensas Recebidas",
                value=f"**+{missao['xp']} XP** `•` **+{missao['moedas']} Moedas** `•` **+{missao['poder']} Poder**",
                inline=False
            )
            embed_conc.set_footer(text=RODAPE_IMPERIAL)
            try:
                await message.channel.send(f"{message.author.mention}", embed=embed_conc)
            except Exception:
                pass

    async def handle_meditar(self, message):
        user = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")
        ganho = random.randint(15, 45)
        habilidade_especial = random.random() < 0.08

        narrativa = random.choice([
            "*A mente se quieta. As paredes da câmara arcana dissolvem. Você toca algo além do físico...*",
            "*Cada respiração expande sua percepção. As runas no chão brilham levemente enquanto você mergulha no éter.*",
            "*O silêncio das catacumbas é perfeito. Você encontra o centro de si mesmo — calmo e imensurável.*",
            "*Vozes ancestrais de Tenshi sussurram através do véu. Você ouve, mas não entende ainda... mas logo entenderá.*",
        ])

        user["xp"] += ganho
        nivel, _ = calcular_nivel(user["xp"])
        user["nivel"] = nivel

        if habilidade_especial:
            habilidades_raras = [
                "Visão do Éter", "Reflexo das Sombras", "Voz do Trono",
                "Toque das Runas", "Memória Ancestral", "Passo Silencioso",
                "Aura Imperial", "Sussurro do Oráculo"
            ]
            nova_hab = random.choice(habilidades_raras)
            habs = user.get("habilidades", [])
            if nova_hab not in habs:
                habs.append(nova_hab)
                user["habilidades"] = habs

        save_user(message.author.id, user)

        embed = discord.Embed(
            title="🧘 MEDITAÇÃO PROFUNDA",
            description=f"{narrativa}\n\n{SEP}",
            color=CORES_PEGADA.get(pegada, 0x2B0A3D)
        )
        embed.add_field(name="✨ Ganho", value=f"**+{ganho} XP**", inline=True)
        if habilidade_especial and nova_hab not in user.get("habilidades", []):
            embed.add_field(name="⚡ DESPERTAR RARO!", value=f"Habilidade **{nova_hab}** foi descoberta!", inline=False)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_descansar(self, message):
        user = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")
        embed = discord.Embed(
            title="😴 REPOUSO IMPERIAL",
            description=(
                f"*{message.author.display_name} retira-se para seus aposentos...*\n{SEP}\n\n"
                "*O descanso restaura o espírito e prepara o corpo para novos desafios. "
                "Amanhã, as batalhas serão mais árduas — e você estará pronto.*\n\n"
                f"*Use `Tenshi, treinar` após o cooldown para continuar crescendo.*\n{SEP}"
            ),
            color=CORES_PEGADA.get(pegada, 0x2B0A3D)
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_clima(self, message):
        clima = random.choice(CLIMAS)
        embed = discord.Embed(
            title=f"{clima[0]}",
            description=(
                f"*Os meteorologistas da Torre Imperial registram as condições atuais...*\n{SEP}\n\n"
                f"*{clima[1]}*\n\n{SEP}"
            ),
            color=clima[2]
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_trabalhar(self, message):
        user = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")
        trabalhos = [
            ("🏗️ Pedreiro das Muralhas",    "Você ajudou a reforçar as muralhas do sul. Trabalho braçal, mas honrado.", 30, 25),
            ("📦 Carregador do Porto",       "Caixas e mais caixas. Seus braços doem mas seu bolso agradece.", 25, 20),
            ("📜 Escriba da Corte",          "Você copiou pergaminhos imperiais por horas. A tinta mancha, a sabedoria fica.", 20, 35),
            ("🌾 Agricultor Imperial",       "Os campos de Tenshi foram cultivados com suas mãos hoje.", 35, 15),
            ("🔧 Assistente do Ferreiro",    "Você soprou fole e carregou metal por horas. A forja agradece.", 28, 22),
            ("🛒 Assistente do Mercado",     "Ajudando comerciantes, aprendendo os fluxos do comércio imperial.", 22, 30),
            ("🌃 Observador Noturno",        "Patrulhando os cantos escuros enquanto a corte dormia.", 32, 28),
        ]
        trabalho = random.choice(trabalhos)
        user["moedas"] += trabalho[2]
        user["xp"]     += trabalho[3]
        nivel, _ = calcular_nivel(user["xp"])
        user["nivel"] = nivel
        save_user(message.author.id, user)

        embed = discord.Embed(
            title=f"💼 {trabalho[0]}",
            description=f"*{trabalho[1]}*\n\n{SEP}",
            color=CORES_PEGADA.get(pegada, 0x2B0A3D)
        )
        embed.add_field(name="💰 Ganho", value=f"**+{trabalho[2]} Moedas**", inline=True)
        embed.add_field(name="✨ XP",    value=f"**+{trabalho[3]}**",        inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_profissao(self, message, args):
        if not args:
            embed = discord.Embed(
                title="🏭 PROFISSÕES DE TENSHI",
                description=f"*Cada súdito tem seu caminho no Império...*\n{SEP}",
                color=0x2B0A3D
            )
            for nome, info in PROFISSOES.items():
                embed.add_field(
                    name=f"{info['emoji']} {nome.capitalize()}",
                    value=f"*{info['desc']}*\n`Tenshi, profissao {nome}`",
                    inline=False
                )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return
        prof = args[0].lower()
        if prof not in PROFISSOES:
            await message.channel.send(embed=embed_imperial("❌", f"Profissão inválida. Disponíveis: {', '.join(PROFISSOES.keys())}", 0x6B0000))
            return
        user = get_user(message.author.id)
        user["ficha"] = user.get("ficha", {})
        user["ficha"]["profissao"] = prof
        save_user(message.author.id, user)
        info = PROFISSOES[prof]
        embed = discord.Embed(
            title=f"{info['emoji']} PROFISSÃO REGISTRADA — {prof.upper()}",
            description=(
                f"*Os registros imperiais foram atualizados...*\n{SEP}\n\n"
                f"*{info['desc']}*\n\n"
                f"Bônus principal: **{info['bonus'].capitalize()}**\n{SEP}"
            ),
            color=0x2B0A3D
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_dado(self, message, args):
        tipo = args[0].lower() if args else "d20"
        dados = {"d4": 4, "d6": 6, "d8": 8, "d10": 10, "d12": 12, "d20": 20, "d100": 100}
        lados = dados.get(tipo, 20)
        resultado = random.randint(1, lados)
        if resultado == lados:
            desc = f"🎯 **CRÍTICO MÁXIMO!** `{resultado}/{lados}`\n\n*Os deuses de Tenshi sorriram para você!*"
            cor  = 0xFFD700
        elif resultado == 1:
            desc = f"💀 **FALHA CRÍTICA!** `{resultado}/{lados}`\n\n*Os dados conspiraram contra você hoje...*"
            cor  = 0x8B0000
        else:
            desc = f"🎲 Resultado: **`{resultado}`** de {lados}"
            cor  = 0x2B0A3D
        await message.channel.send(embed=discord.Embed(
            title=f"🎲 {tipo.upper()} — Dado Imperial",
            description=f"*O destino é lançado nos salões de Tenshi...*\n{SEP}\n\n{desc}\n\n{SEP}",
            color=cor
        ).set_footer(text=RODAPE_IMPERIAL))

    async def handle_interagir(self, message, args):
        if not args:
            await message.channel.send(embed=embed_imperial(
                "🎭 Interações de RP",
                f"*Ações disponíveis:*\n{SEP}\n`saudar` `proclamar` `reverenciar` `desafiar` `jurar` `consolar`\n\nUse: `Tenshi, rp [ação] [@user]`",
                0x2B0A3D
            ))
            return
        acao  = args[0].lower()
        alvo  = message.mentions[0] if message.mentions else None
        user  = get_user(message.author.id)
        pegada = user.get("pegada", "imperial")

        ACOES = {
            "saudar":     (lambda a: f"*{message.author.display_name} ergue a mão em saudação imperial para {a.display_name if a else 'a todos'}. Que Tenshi guie seus passos.*", "🤝"),
            "proclamar":  (lambda a: f"*{message.author.display_name} sobe ao pedestal e proclama lealdade absoluta ao Imperador Alloy e ao Império de Tenshi!*", "📣"),
            "reverenciar":(lambda a: f"*{message.author.display_name} curva-se em reverência profunda diante de {'**Imperador Alloy**' if a and a.id == IMPERADOR_ID else a.display_name if a else 'o Trono Imperial'}.*", "🙇"),
            "desafiar":   (lambda a: f"*{message.author.display_name} aponta para {a.display_name if a else '???'} com olhos de aço fundido...* \"Sua hora chegou. Use `Tenshi, duelo @{a.display_name if a else '???'}` para selar o destino!\"", "⚔️"),
            "jurar":      (lambda a: f"*{message.author.display_name} ajoelha e jura lealdade eterna {'ao Imperador Alloy' if a and a.id == IMPERADOR_ID else 'ao Império de Tenshi'}. Um voto que a morte não desfaz.*", "⚜️"),
            "consolar":   (lambda a: f"*{message.author.display_name} posa a mão no ombro de {a.display_name if a else 'um companheiro caído'}. \"O Império não esquece os que caem com honra.\"*", "🕊️"),
        }

        if acao not in ACOES:
            await message.channel.send(embed=embed_imperial("❓", f"Ações: {' • '.join(ACOES.keys())}", 0x6B0000))
            return

        fn, emoji = ACOES[acao]
        texto = fn(alvo)
        cor = 0xFFD700 if alvo and alvo.id == IMPERADOR_ID else CORES_PEGADA.get(pegada, 0x2B0A3D)
        embed = discord.Embed(description=f"{emoji} {texto}", color=cor)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)
