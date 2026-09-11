import discord
import random
from database import (get_user, save_user, get_familias, save_familias,
                      criar_familia, entrar_familia)
from utils import embed_imperial

TIPOS_FAMILIA = {
    "familia": {
        "emoji": "👨‍👩‍👧",
        "cor": 0x8B0000,
        "cargos": ["Patriarca/Matriarca", "Consigliere", "Capo", "Soldato", "Associato"],
        "descricao": "Uma família unida por laços de sangue e lealdade. A honra acima de tudo.",
    },
    "mafia": {
        "emoji": "🔫",
        "cor": 0x1C1C1C,
        "cargos": ["Don", "Underboss", "Consigliere", "Capo", "Soldato"],
        "descricao": "Uma organização do submundo, onde o poder se compra e a lealdade se prova com sangue.",
    },
    "cla": {
        "emoji": "⚔️",
        "cor": 0x4B0082,
        "cargos": ["Lorde", "Alto Comandante", "Comandante", "Guerreiro", "Recruta"],
        "descricao": "Um clã de guerreiros juramentados, unidos por um código de honra inquebrantável.",
    },
}

MISSOES_FAMILIA = [
    {"nome": "Coleta de Proteção", "descricao": "Cobrar tributos dos comerciantes da cidade.", "recompensa_saldo": 100, "recompensa_pontos": 10},
    {"nome": "Emboscada Rival", "descricao": "Interceptar um carregamento da facção inimiga.", "recompensa_saldo": 150, "recompensa_pontos": 15},
    {"nome": "Reunião Secreta", "descricao": "Negociar uma aliança com um grupo neutro.", "recompensa_saldo": 80, "recompensa_pontos": 8},
    {"nome": "Eliminar Traidor", "descricao": "Um membro virou informante. Resolva a situação.", "recompensa_saldo": 200, "recompensa_pontos": 20},
    {"nome": "Lavagem de Moedas", "descricao": "Passar moedas de origem duvidosa pelo mercado imperial.", "recompensa_saldo": 120, "recompensa_pontos": 12},
]


class Familia:
    def __init__(self, bot):
        self.bot = bot

    async def handle_familia(self, message, args):
        if not args:
            await self._ajuda(message)
            return
        sub = args[0].lower()
        resto = args[1:]
        if sub == "criar":
            await self._criar(message, resto)
        elif sub == "entrar":
            await self._entrar(message, resto)
        elif sub == "info":
            await self._info(message)
        elif sub == "membros":
            await self._membros(message)
        elif sub in ("missao", "missão"):
            await self._missao(message)
        elif sub == "depositar":
            await self._depositar(message, resto)
        elif sub in ("ranking", "top"):
            await self._ranking(message)
        elif sub == "promover":
            await self._promover(message, resto)
        elif sub == "expulsar":
            await self._expulsar(message, resto)
        else:
            await self._ajuda(message)

    async def _ajuda(self, message):
        embed = discord.Embed(
            title="👨‍👩‍👧 SISTEMA DE FAMÍLIA & MÁFIA",
            description="Organize-se com sua tropa no Império de Tenshi.",
            color=0x8B0000
        )
        embed.add_field(name="📋 Comandos", value=(
            "`familia criar [nome] [familia/mafia/cla]` — Fundar (300 moedas)\n"
            "`familia entrar [id]` — Entrar numa organização\n"
            "`familia info` — Ver informações da sua org.\n"
            "`familia membros` — Listar membros e cargos\n"
            "`familia missao` — Missão coletiva de organização\n"
            "`familia depositar [v]` — Adicionar ao caixa\n"
            "`familia promover @user [cargo]` — Promover membro\n"
            "`familia expulsar @user` — Expulsar membro\n"
            "`familia ranking` — Ranking de organizações"
        ), inline=False)
        await message.channel.send(embed=embed)

    async def _criar(self, message, args):
        if len(args) < 2:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, familia criar [nome] [familia/mafia/cla]`", 0x8B0000))
            return
        tipo = args[-1].lower()
        if tipo not in TIPOS_FAMILIA:
            await message.channel.send(embed=embed_imperial("❌", "Tipo inválido. Use: `familia`, `mafia` ou `cla`", 0x8B0000))
            return
        nome = " ".join(args[:-1])
        ok, resultado = criar_familia(message.author.id, nome, tipo)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Erro", resultado, 0x8B0000))
            return
        info = TIPOS_FAMILIA[tipo]
        cargo_lider = info["cargos"][0]
        embed = discord.Embed(
            title=f"{info['emoji']} ORGANIZAÇÃO FUNDADA!",
            description=f"*O juramento foi feito. A organização está viva.*\n\n"
                       f"**{nome}** agora existe no submundo de Tenshi!\n\n"
                       f"*{info['descricao']}*",
            color=info["cor"]
        )
        embed.add_field(name="🆔 ID da Organização", value=f"`{resultado}`", inline=True)
        embed.add_field(name="👑 Seu Cargo", value=cargo_lider, inline=True)
        embed.add_field(name="📋 Próximos passos", value=(
            "• `familia membros` — Ver membros\n"
            "• `familia missao` — Iniciar missão\n"
            "• Compartilhe o ID para recrutar membros"
        ), inline=False)
        await message.channel.send(embed=embed)

    async def _entrar(self, message, args):
        if not args:
            await message.channel.send(embed=embed_imperial("❓", "Informe o ID da organização: `Tenshi, familia entrar [id]`", 0x8B0000))
            return
        fid = args[0]
        ok, cargo = entrar_familia(message.author.id, fid)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Erro", cargo, 0x8B0000))
            return
        familias = get_familias()
        familia = familias[fid]
        info = TIPOS_FAMILIA.get(familia["tipo"], TIPOS_FAMILIA["familia"])
        embed = discord.Embed(
            title=f"{info['emoji']} JURAMENTO FEITO",
            description=f"*Você cruzou a linha. Agora pertence a* **{familia['nome']}**.\n\n"
                       f"*O código de silêncio está em vigor. A lealdade é tudo.*",
            color=info["cor"]
        )
        embed.add_field(name="💼 Seu Cargo", value=cargo, inline=True)
        embed.add_field(name="👥 Membros", value=str(len(familia["membros"])), inline=True)
        await message.channel.send(embed=embed)

    async def _info(self, message):
        user = get_user(message.author.id)
        fid = user.get("familia_id")
        if not fid:
            await message.channel.send(embed=embed_imperial("❌", "Você não pertence a nenhuma organização.", 0x8B0000))
            return
        familias = get_familias()
        familia = familias.get(fid)
        if not familia:
            return
        info = TIPOS_FAMILIA.get(familia["tipo"], TIPOS_FAMILIA["familia"])
        fundada = familia.get("fundada", "")[:10]
        embed = discord.Embed(
            title=f"{info['emoji']} {familia['nome'].upper()}",
            description=f"*{info['descricao']}*",
            color=info["cor"]
        )
        embed.add_field(name="🆔 ID", value=f"`{fid}`", inline=True)
        embed.add_field(name="📅 Fundada", value=fundada, inline=True)
        embed.add_field(name="👥 Membros", value=str(len(familia["membros"])), inline=True)
        embed.add_field(name="🏆 Pontos", value=str(familia.get("pontos", 0)), inline=True)
        embed.add_field(name="💰 Caixa", value=f"**{familia.get('saldo', 0)}** moedas", inline=True)
        embed.add_field(name="⚔️ Missões", value=str(familia.get("missoes_completas", 0)), inline=True)
        try:
            lider = await self.bot.fetch_user(int(familia["lider"]))
            embed.add_field(name=f"👑 {info['cargos'][0]}", value=lider.display_name, inline=False)
        except Exception:
            pass
        embed.set_footer(text=f"{info['emoji']} {TIPOS_FAMILIA[familia['tipo']]['descricao'][:60]}...")
        await message.channel.send(embed=embed)

    async def _membros(self, message):
        user = get_user(message.author.id)
        fid = user.get("familia_id")
        if not fid:
            await message.channel.send(embed=embed_imperial("❌", "Você não pertence a nenhuma organização.", 0x8B0000))
            return
        familias = get_familias()
        familia = familias.get(fid)
        if not familia:
            return
        info = TIPOS_FAMILIA.get(familia["tipo"], TIPOS_FAMILIA["familia"])
        embed = discord.Embed(
            title=f"{info['emoji']} MEMBROS — {familia['nome']}",
            description="*O Omertà une todos os presentes nesta lista*",
            color=info["cor"]
        )
        for uid, dados in familia["membros"].items():
            try:
                membro = await self.bot.fetch_user(int(uid))
                nome_display = membro.display_name
            except Exception:
                nome_display = f"ID:{uid}"
            cargo = dados.get("cargo", "Membro")
            desde = dados.get("data_entrada", "")[:10]
            lider_mark = "👑 " if uid == familia["lider"] else ""
            embed.add_field(
                name=f"{lider_mark}{nome_display}",
                value=f"💼 {cargo} | 📅 Desde {desde}",
                inline=False
            )
        await message.channel.send(embed=embed)

    async def _missao(self, message):
        user = get_user(message.author.id)
        fid = user.get("familia_id")
        if not fid:
            await message.channel.send(embed=embed_imperial("❌", "Você não pertence a nenhuma organização.", 0x8B0000))
            return
        familias = get_familias()
        familia = familias.get(fid)
        if not familia:
            return
        info = TIPOS_FAMILIA.get(familia["tipo"], TIPOS_FAMILIA["familia"])
        missao = random.choice(MISSOES_FAMILIA)
        sucesso = random.random() > 0.3
        if sucesso:
            familia["saldo"] = familia.get("saldo", 0) + missao["recompensa_saldo"]
            familia["pontos"] = familia.get("pontos", 0) + missao["recompensa_pontos"]
            familia["missoes_completas"] = familia.get("missoes_completas", 0) + 1
            user["xp"] += 40
            save_user(message.author.id, user)
            save_familias(familias)
            embed = discord.Embed(
                title=f"{info['emoji']} MISSÃO CONCLUÍDA — {missao['nome']}",
                description=f"*{missao['descricao']}*\n\n✅ **Sucesso!** A organização se sai mais forte.",
                color=info["cor"]
            )
            embed.add_field(name="💰 Caixa +", value=f"**+{missao['recompensa_saldo']}** moedas", inline=True)
            embed.add_field(name="🏆 Pontos +", value=f"**+{missao['recompensa_pontos']}**", inline=True)
        else:
            embed = discord.Embed(
                title=f"{info['emoji']} MISSÃO FALHOU — {missao['nome']}",
                description=f"*{missao['descricao']}*\n\n❌ **Falhou.** Imprevistos complicaram a operação.",
                color=0x8B0000
            )
        embed.set_footer(text=f"Caixa atual: {familia.get('saldo', 0)} moedas")
        await message.channel.send(embed=embed)

    async def _depositar(self, message, args):
        user = get_user(message.author.id)
        fid = user.get("familia_id")
        if not fid:
            return
        valor = 0
        for a in args:
            if a.isdigit():
                valor = int(a)
                break
        if valor <= 0:
            await message.channel.send(embed=embed_imperial("❓", "Informe o valor: `Tenshi, familia depositar [valor]`", 0x8B0000))
            return
        if user["moedas"] < valor:
            await message.channel.send(embed=embed_imperial("❌", "Moedas insuficientes.", 0x8B0000))
            return
        familias = get_familias()
        familia = familias[fid]
        user["moedas"] -= valor
        familia["saldo"] = familia.get("saldo", 0) + valor
        save_user(message.author.id, user)
        save_familias(familias)
        await message.channel.send(embed=embed_imperial(
            "💰 Depósito na Organização",
            f"**{valor}** moedas adicionadas ao caixa de **{familia['nome']}**.\nCaixa: **{familia['saldo']}** moedas.",
            0x006400
        ))

    async def _ranking(self, message):
        familias = get_familias()
        if not familias:
            await message.channel.send(embed=embed_imperial("📊 Ranking", "Nenhuma organização registrada ainda.", 0x2C2F33))
            return
        ranking = sorted(familias.items(), key=lambda x: x[1].get("pontos", 0), reverse=True)
        embed = discord.Embed(
            title="🏆 RANKING DE ORGANIZAÇÕES",
            description="*As famílias mais poderosas do Império de Tenshi*",
            color=0x8B0000
        )
        medalhas = ["🥇", "🥈", "🥉"]
        for i, (fid, f) in enumerate(ranking[:10]):
            info = TIPOS_FAMILIA.get(f["tipo"], TIPOS_FAMILIA["familia"])
            medalha = medalhas[i] if i < 3 else f"#{i+1}"
            embed.add_field(
                name=f"{medalha} {info['emoji']} {f['nome']}",
                value=f"🏆 {f.get('pontos',0)} pts | 👥 {len(f['membros'])} membros | 💰 {f.get('saldo',0)} moedas",
                inline=False
            )
        await message.channel.send(embed=embed)

    async def _promover(self, message, args):
        user = get_user(message.author.id)
        fid = user.get("familia_id")
        if not fid:
            return
        familias = get_familias()
        familia = familias.get(fid)
        if not familia or familia["lider"] != str(message.author.id):
            await message.channel.send(embed=embed_imperial("🚫", "Apenas o líder pode promover membros.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "Mencione o membro: `Tenshi, familia promover @user [cargo]`", 0x8B0000))
            return
        alvo = message.mentions[0]
        args_sem_mention = [a for a in args if not a.startswith("<@")]
        novo_cargo = " ".join(args_sem_mention) if args_sem_mention else "Capitão"
        uid = str(alvo.id)
        if uid not in familia["membros"]:
            await message.channel.send(embed=embed_imperial("❌", "Este usuário não é membro.", 0x8B0000))
            return
        cargo_antigo = familia["membros"][uid]["cargo"]
        familia["membros"][uid]["cargo"] = novo_cargo
        save_familias(familias)
        alvo_user = get_user(alvo.id)
        alvo_user["cargo_familia"] = novo_cargo
        save_user(alvo.id, alvo_user)
        info = TIPOS_FAMILIA.get(familia["tipo"], TIPOS_FAMILIA["familia"])
        await message.channel.send(embed=embed_imperial(
            f"{info['emoji']} Promoção",
            f"**{alvo.display_name}**: {cargo_antigo} → **{novo_cargo}**",
            info["cor"]
        ))

    async def _expulsar(self, message, args):
        user = get_user(message.author.id)
        fid = user.get("familia_id")
        if not fid:
            return
        familias = get_familias()
        familia = familias.get(fid)
        if not familia or familia["lider"] != str(message.author.id):
            await message.channel.send(embed=embed_imperial("🚫", "Apenas o líder pode expulsar membros.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "Mencione quem expulsar: `Tenshi, familia expulsar @user`", 0x8B0000))
            return
        alvo = message.mentions[0]
        uid = str(alvo.id)
        if uid == familia["lider"]:
            await message.channel.send(embed=embed_imperial("❌", "O líder não pode ser expulso.", 0x8B0000))
            return
        if uid not in familia["membros"]:
            await message.channel.send(embed=embed_imperial("❌", "Este usuário não é membro.", 0x8B0000))
            return
        del familia["membros"][uid]
        save_familias(familias)
        alvo_user = get_user(alvo.id)
        alvo_user["familia_id"] = None
        alvo_user["cargo_familia"] = None
        save_user(alvo.id, alvo_user)
        await message.channel.send(embed=embed_imperial(
            "🚪 Membro Expulso",
            f"**{alvo.display_name}** foi expulso(a) de **{familia['nome']}**.",
            0x8B0000
        ))
