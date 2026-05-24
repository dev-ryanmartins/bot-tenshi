"""
Módulo Cotidiano — Funcionalidades 12-16
12. Crônicas do cotidiano (#jornal-dia-a-dia)
13. Consulta psicológica por IA
14. Bar e embriaguez
15. Diário de viagem
16. Clima dinâmico
"""
import discord
import random
import asyncio
from datetime import datetime, timedelta
from database import get_user, save_user
from utils import SEP, RODAPE_IMPERIAL

COR_IMPERIAL = 0x2C3E50
COR_DOURADO  = 0x9E7815
COR_PRETO    = 0x111111
COR_SUCESSO  = 0x1A5C2E
COR_PERIGO   = 0x7B1F1F
COR_NEUTRO   = 0x3D3D3D

def embed_soberano(titulo: str, descricao: str, cor: int = COR_IMPERIAL) -> discord.Embed:
    e = discord.Embed(title=titulo, description=descricao, color=cor)
    e.set_footer(text=RODAPE_IMPERIAL)
    return e

# ─── CLIMA ────────────────────────────────────────────────────────────────────
CLIMAS = [
    {"nome": "Céu Limpo",         "emoji": "☀️",  "efeito": "normal",     "descricao": "Condições ideais. Todos os bônus de lazer estão ativos."},
    {"nome": "Chuva Suave",       "emoji": "🌧️",  "efeito": "chuva",      "descricao": "Canais externos concedem 50% menos bônus."},
    {"nome": "Neblina Arcana",    "emoji": "🌫️",  "efeito": "neblina",    "descricao": "Missões têm 10% mais recompensa. Clima misterioso."},
    {"nome": "Tempestade",        "emoji": "⛈️",  "efeito": "tempestade", "descricao": "Treinamento externo suspenso. Duelos têm +15% de dano."},
    {"nome": "Chuva Ácida",       "emoji": "☣️",  "efeito": "chuva_acida","descricao": "Canais abertos (#parque, #praça) CAUSAM fadiga ao invés de curar."},
    {"nome": "Vento Imperial",    "emoji": "💨",  "efeito": "vento",      "descricao": "Viagens de trem têm cooldown reduzido em 20%."},
    {"nome": "Neve Mística",      "emoji": "❄️",  "efeito": "neve",       "descricao": "Treinos externos custam 15% mais fadiga."},
]

_clima_atual: dict = {"clima": CLIMAS[0], "proxima_troca": datetime.utcnow()}

# ─── BAR ─────────────────────────────────────────────────────────────────────
BEBIDAS = {
    "cerveja_imperial": {"nome": "Cerveja Imperial",   "preco": 25,  "duracao": 20, "nivel": 1},
    "vinho_sombrio":    {"nome": "Vinho das Sombras",  "preco": 50,  "duracao": 40, "nivel": 2},
    "absinto_arcano":   {"nome": "Absinto Arcano",     "preco": 100, "duracao": 60, "nivel": 3},
    "elixir_loucura":   {"nome": "Elixir da Loucura",  "preco": 200, "duracao": 90, "nivel": 4},
}

def _distorcer_texto(texto: str, nivel: int) -> str:
    if nivel == 0:
        return texto
    chars = list(texto)
    swaps = min(nivel * 3, len(chars) // 3)
    for _ in range(swaps):
        i = random.randint(0, len(chars) - 1)
        if chars[i].isalpha():
            if random.random() < 0.4:
                chars[i] = random.choice("aeiouaeiou")
            elif random.random() < 0.3:
                chars[i] = chars[i] * 2
    if nivel >= 2 and random.random() < 0.3:
        chars.insert(random.randint(0, len(chars)), "*hic*")
    if nivel >= 3 and random.random() < 0.4:
        chars.insert(random.randint(0, len(chars)), "...")
    return "".join(chars)

# ─── NARRATIVAS DE VIAGEM ─────────────────────────────────────────────────────
NARRATIVAS_TREM = [
    "O trem cortou a névoa da manhã enquanto {nome} olhava pela janela embaçada. As luzes da cidade ficaram para trás, substituídas pela imensidão das terras imperiais. Ao longe, as torres de {destino} surgiam como sentinelas douradas no horizonte. A jornada durou pouco, mas o silêncio contemplativo dentro do vagão pareceu uma eternidade bem-vinda.",
    "Entre uma parada e outra, {nome} observou um casal de comerciantes debatendo sobre as últimas tensões entre facções. O cheiro de café quente e pergaminhos velhos impregnava o vagão de primeira classe. Quando as portas de {destino} se abriram, {nome} desceu com o olhar mais aguçado — o trem sempre revela o pulso do Império.",
    "O conductor do trem, um veterano com medalhas imperiais desbotadas no colete, fez o comunicado habitual em voz grave: *Chegando à estação de {destino}.* {nome} recolheu seus pertences e cruzou a plataforma entre viajantes de toda espécie. Uma nova localidade, as mesmas regras do jogo.",
    "A chuva batia nos vidros enquanto o trem rasgava a escuridão. {nome} aproveitou o trajeto para reler anotações antigas sobre {destino} — sua história, seus perigos, suas oportunidades. Quando o trem frenou, havia algo diferente no olhar: determinação calibrada.",
]

# ─── CONSULTA PSICOLÓGICA (sem IA real — respostas filosóficas pré-definidas) ──
RESPOSTAS_PSICOLOGO = [
    "A dor que você descreve não é fraqueza — é o sinal de que algo importou. O Estoicismo nos ensina: *controle o que é seu, liberte o que não é.* O fardo que carrega tem nome. Nomeá-lo é o primeiro passo para depô-lo.",
    "O Império exige muito de seus guerreiros. Mas até as pedras mais resistentes precisam de descanso para não se tornarem pó. Permita-se a pausa sem culpa — isso não é rendição. É estratégia.",
    "Há uma distinção fundamental entre sentir e ser governado pelo sentimento. Você sente — isso é humano. Mas a narrativa que conta sobre esse sentimento pode ser reescrita com mais compaixão por você mesmo.",
    "O que você descreve ressoa com o que Marco Aurélio chamou de 'o obstáculo que se torna o caminho'. A adversidade não define seu caráter — revela o que já estava lá. E o que vejo aqui tem solidez.",
    "Às vezes, o ruído interno precisa apenas ser ouvido, não resolvido. Falar é, por si só, um ato terapêutico. Você já deu o passo mais difícil ao verbalizar. Continue.",
]


class CotidianoCog:
    def __init__(self, bot):
        self.bot = bot
        self._loop_clima_iniciado    = False
        self._loop_cronica_iniciado  = False
        self._mensagens_gerais: list = []

    def cog_load(self):
        if not self._loop_clima_iniciado:
            self._loop_clima_iniciado = True
            self.bot.loop.create_task(self._loop_clima())
        if not self._loop_cronica_iniciado:
            self._loop_cronica_iniciado = True
            self.bot.loop.create_task(self._loop_cronica_diaria())

    # 12. CRÔNICA DO COTIDIANO
    async def handle_cronica_diaria(self, message):
        embed = discord.Embed(
            title="Jornal do Dia-a-Dia — Tenshi",
            description=f"*Edição de {datetime.utcnow().strftime('%d/%m/%Y')}*\n{SEP}",
            color=COR_IMPERIAL
        )
        if self._mensagens_gerais:
            amostra = random.sample(self._mensagens_gerais, min(3, len(self._mensagens_gerais)))
            cronica = (
                f"*Nossa equipe de jornalistas monitorou os canais públicos de Tenshi e preparou o seguinte resumo do cotidiano:*\n\n"
                + "\n\n".join(f"— *\"{m['texto'][:120]}...\"* — reportado em {m['canal']}" for m in amostra)
                + f"\n\n*O Império segue seu ritmo. Novos acontecimentos amanhã.*"
            )
        else:
            cronica = "*Os jornalistas circularam pelas praças e canais do Império. O dia foi tranquilo — ou, ao menos, os fatos relevantes permanecem confidenciais.*"
        embed.description += f"\n\n{cronica}"
        embed.set_footer(text="Jornal do Cotidiano  •  Império Tenshi")
        await message.channel.send(embed=embed)

    def registrar_mensagem_geral(self, canal: str, texto: str):
        self._mensagens_gerais.append({"canal": canal, "texto": texto})
        if len(self._mensagens_gerais) > 50:
            self._mensagens_gerais.pop(0)

    # 13. PSICÓLOGO
    async def handle_psicologo(self, message, args):
        if not args:
            await message.channel.send(embed=embed_soberano(
                "Consultório Imperial",
                "Você pode falar livremente. Tudo aqui é confidencial.\n\nUse `Tenshi, psicologo [seu desabafo]`.",
                COR_IMPERIAL
            ))
            return
        texto_usuario = " ".join(args)
        resposta = random.choice(RESPOSTAS_PSICOLOGO)
        embed = discord.Embed(
            title="Consulta Imperial — Confidencial",
            color=COR_IMPERIAL
        )
        embed.add_field(name="Você disse", value=f"*\"{texto_usuario[:200]}\"*", inline=False)
        embed.add_field(name="Resposta da Terapeuta", value=resposta, inline=False)
        embed.set_footer(text="Esta sessão é confidencial  •  Império Tenshi")
        await message.author.send(embed=embed)
        await message.channel.send(embed=embed_soberano("Sessão Iniciada", "Sua consulta foi enviada de forma privada.", COR_SUCESSO))

    # 14. BAR — BEBER
    async def handle_beber(self, message, args):
        if not args:
            embed = discord.Embed(title="🍺 Bar Imperial", color=COR_IMPERIAL)
            embed.description = "*O barman aguarda seu pedido.*\n\n"
            for bid, b in BEBIDAS.items():
                embed.description += f"**{b['nome']}** — {b['preco']} moedas | Duração: {b['duracao']}min\n`Tenshi, beber {bid}`\n\n"
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return
        bid = args[0].lower()
        if bid not in BEBIDAS:
            await message.channel.send(embed=embed_soberano("Item Não Encontrado", f"Bebida `{bid}` não consta no cardápio.", COR_NEUTRO))
            return
        bebida = BEBIDAS[bid]
        user   = get_user(message.author.id)
        if user["moedas"] < bebida["preco"]:
            await message.channel.send(embed=embed_soberano("Saldo Insuficiente", f"Preço: {bebida['preco']} moedas.", COR_PERIGO))
            return
        user["moedas"] -= bebida["preco"]
        user["embriaguez"] = {
            "nivel":    bebida["nivel"],
            "expira":   (datetime.utcnow() + timedelta(minutes=bebida["duracao"])).isoformat(),
            "bebida":   bebida["nome"],
        }
        save_user(message.author.id, user)
        await message.channel.send(embed=embed_soberano(
            f"Pedido Registrado",
            f"**{bebida['nome']}** servido.\n\nSeus textos no #GERAL serão afetados pelos próximos **{bebida['duracao']} minutos**.",
            COR_IMPERIAL
        ))

    def processar_embriaguez(self, user_id: int, texto: str) -> str | None:
        user = get_user(user_id)
        emb  = user.get("embriaguez")
        if not emb:
            return None
        expira = datetime.fromisoformat(emb["expira"])
        if datetime.utcnow() > expira:
            user["embriaguez"] = None
            save_user(user_id, user)
            return None
        return _distorcer_texto(texto, emb["nivel"])

    # 15. DIÁRIO DE VIAGEM
    async def gerar_narrativa_viagem(self, nome: str, destino: str, canal_viagem):
        if not canal_viagem:
            return
        narrativa = random.choice(NARRATIVAS_TREM).format(nome=nome, destino=destino)
        embed = discord.Embed(
            title=f"Diário de Viagem — {nome}",
            description=f"*{datetime.utcnow().strftime('%d/%m/%Y, %H:%M UTC')}*\n{SEP}\n\n{narrativa}",
            color=COR_IMPERIAL
        )
        embed.set_footer(text="Canal #viajando-pelo-mundo  •  Império Tenshi")
        try:
            await canal_viagem.send(embed=embed)
        except Exception:
            pass

    # 16. CLIMA
    async def handle_clima(self, message):
        global _clima_atual
        clima = _clima_atual["clima"]
        proxima = _clima_atual["proxima_troca"]
        embed = discord.Embed(title=f"{clima['emoji']} Boletim Meteorológico Imperial", color=COR_IMPERIAL)
        embed.add_field(name="Condição Atual",  value=clima["nome"],           inline=True)
        embed.add_field(name="Efeito Ativo",    value=clima["descricao"],       inline=False)
        embed.add_field(name="Próxima Atualização", value=proxima.strftime("%H:%M UTC"), inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    def get_clima_atual(self) -> dict:
        return _clima_atual["clima"]

    # ── LOOPS AUTOMÁTICOS ─────────────────────────────────────────────────────

    async def _loop_clima(self):
        await self.bot.wait_until_ready()
        global _clima_atual
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            if agora >= _clima_atual["proxima_troca"]:
                novo = random.choice(CLIMAS)
                _clima_atual = {"clima": novo, "proxima_troca": agora + timedelta(hours=6)}
                for guild in self.bot.guilds:
                    for ch in guild.text_channels:
                        if "clima" in ch.name.lower():
                            try:
                                await ch.send(embed=discord.Embed(
                                    title=f"{novo['emoji']} Atualização Climática",
                                    description=f"**Nova condição:** {novo['nome']}\n\n{novo['descricao']}",
                                    color=COR_IMPERIAL
                                ))
                            except Exception:
                                pass
                            break
            await asyncio.sleep(3600)

    async def _loop_cronica_diaria(self):
        await self.bot.wait_until_ready()
        ultimo_dia = None
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            dia   = agora.date()
            if agora.hour == 20 and dia != ultimo_dia and self._mensagens_gerais:
                ultimo_dia = dia
                for guild in self.bot.guilds:
                    for ch in guild.text_channels:
                        if "jornal-dia-a-dia" in ch.name.lower():
                            amostra = random.sample(self._mensagens_gerais, min(3, len(self._mensagens_gerais)))
                            cronica = "\n\n".join(f"— *\"{m['texto'][:100]}...\"* em {m['canal']}" for m in amostra)
                            embed = discord.Embed(
                                title=f"Jornal do Cotidiano — {dia.strftime('%d/%m/%Y')}",
                                description=f"*Resumo editorial do dia:*\n{SEP}\n\n{cronica}",
                                color=COR_IMPERIAL
                            )
                            embed.set_footer(text="Redação do Império Tenshi")
                            try:
                                await ch.send(embed=embed)
                            except Exception:
                                pass
                            break
            await asyncio.sleep(1800)
