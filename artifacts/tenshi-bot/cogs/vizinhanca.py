import discord
import asyncio
import random
from datetime import datetime, timedelta
from database import (
    get_user, save_user,
    get_vizinhanca, save_vizinhanca,
    registrar_casa_canal, get_casa_by_canal,
    cobrar_condominio_semanal,
)
from utils import embed_imperial, SEP, RODAPE_IMPERIAL

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DO CONDOMÍNIO
# ─────────────────────────────────────────────────────────────────────────────

TAXA_COMPRA   = 800    # moedas para comprar uma casa
TAXA_ALUGUEL  = 200    # moedas para alugar uma casa
TAXA_SEMANAL  = 50     # taxa de condomínio/aluguel semanal
COOLDOWN_DESCANSO = 5 * 60  # 5 minutos entre usos de descanso

# Bônus de regeneração de energia por canal de lazer (fadiga removida por uso)
BONUS_LAZER = {
    "piscina":  20,   # dobro de energia
    "jardim":   8,
    "praça":    8,
    "quadra":   12,
    "garagem":  6,
}

# Crônicas e fofocas anônimas do condomínio geradas aleatoriamente pela IA
CRONICAS_CONDOMINIO = [
    "*Os vizinhos da casa-7 ouviram sons estranhos vindo da casa-3 às 3h da manhã. Ninguém sabe o que aconteceu.*",
    "*Uma flor misteriosa apareceu na porta da casa-12 hoje de manhã. Quem teria deixado?*",
    "*O gato preto do condomínio foi visto entrando na casa-5 sem ser convidado. Três vezes.*",
    "*Fontes anônimas relatam que alguém da casa-9 estaria realizando rituais às quartas-feiras no jardim.*",
    "*A luz da casa-2 ficou acesa a noite toda. Dizem que havia música tocando baixinho até o amanhecer.*",
    "*Alguém deixou uma nota anônima embaixo da porta da casa-15: 'Eu sei o que você fez no mercado negro'.*",
    "*Os moradores da praça viram um vulto de manto negro cruzar o pátio rapidamente ao entardecer. Coincidência?*",
    "*A torneira da piscina ficou ligada durante toda a madrugada. O porteiro jura que estava trancada.*",
    "*Duas casas do mesmo corredor receberam flores brancas esta semana. Ambas de moradores da facção dos Místicos.*",
    "*Rumores dizem que o dono da casa-1 estaria planejando uma festa secreta — apenas os mais poderosos foram convidados.*",
    "*A placa do jardim foi encontrada virada de cabeça para baixo hoje. Ninguém assumiu a responsabilidade.*",
    "*Dizem que a casa-11 esconde uma passagem secreta no quarto dos fundos. Verdade ou lenda urbana de Tenshi?*",
]

# Nomes imersivos para as casas numeradas
def get_nome_casa(numero: int) -> str:
    nomes = {
        1: "Residência Aurora",  2: "Chalé das Sombras",  3: "Abrigo do Crepúsculo",
        4: "Morada Imperial",    5: "Lar da Chama Viva",  6: "Casarão do Véu",
        7: "Mansão Sussurrante", 8: "Porto Sereno",       9: "Toca do Oráculo",
        10: "Villa Estrelada",  11: "Ninho do Trovão",   12: "Refúgio Místico",
        13: "Forte Interior",   14: "Encruzilhada",      15: "Torre dos Sonhos",
        16: "Casa do Guardião", 17: "Morada Arcana",     18: "Palacete do Fim",
    }
    return nomes.get(numero, f"Casa-{numero}")


# ─────────────────────────────────────────────────────────────────────────────
# BOTÃO INDIVIDUAL DE CASA (painel da portaria)
# ─────────────────────────────────────────────────────────────────────────────

class BotaoCasaCondominio(discord.ui.Button):
    def __init__(self, numero: int, dados: dict):
        self.numero = numero
        self.dados  = dados
        ocupada = dados.get("id_dono") is not None
        alugada = dados.get("status_aluguel") == "alugada"
        if ocupada and alugada:
            emoji = "🟡"
            style = discord.ButtonStyle.grey
            label = f"Casa-{numero} 🔑"
        elif ocupada:
            emoji = "🔴"
            style = discord.ButtonStyle.red
            label = f"Casa-{numero} 🏠"
        else:
            emoji = "🟢"
            style = discord.ButtonStyle.green
            label = f"Casa-{numero}"
        super().__init__(label=label, style=style, custom_id=f"portaria_casa_{numero}")

    async def callback(self, interaction: discord.Interaction):
        dados = get_vizinhanca().get(str(self.numero), {})
        user  = get_user(interaction.user.id)
        dono  = dados.get("id_dono")
        nome_casa = get_nome_casa(self.numero)

        if dono is not None and str(dono) != str(interaction.user.id):
            membro_nome = f"<@{dono}>"
            status_txt = "🔑 Alugada" if dados.get("status_aluguel") == "alugada" else "🏠 Comprada"
            await interaction.response.send_message(
                embed=embed_imperial(
                    f"🔒 {nome_casa} — Ocupada",
                    f"Esta residência pertence a {membro_nome}.\nStatus: **{status_txt}**",
                    0x8B0000
                ),
                ephemeral=True
            )
            return

        if str(dono) == str(interaction.user.id) if dono else False:
            moradores = dados.get("lista_moradores", [])
            await interaction.response.send_message(
                embed=embed_imperial(
                    f"🏠 {nome_casa} — Sua Residência",
                    f"Você já mora aqui!\n\n"
                    f"👥 **Moradores convidados:** {len(moradores)}\n"
                    f"🏷️ **Status:** {dados.get('status_aluguel','comprada').capitalize()}\n\n"
                    f"Use `Tenshi, convidar @usuario` para dar acesso a visitas.",
                    0x2B6CB0
                ),
                ephemeral=True
            )
            return

        total = user["moedas"] + user.get("conta_banco", 0)
        embed = discord.Embed(
            title=f"🏠 {nome_casa}",
            description=f"*Uma residência disponível no condomínio imperial...*\n{SEP}",
            color=0x8B6914
        )
        embed.add_field(name="💰 Comprar", value=f"**{TAXA_COMPRA}** moedas (permanente*)", inline=True)
        embed.add_field(name="🔑 Alugar",  value=f"**{TAXA_ALUGUEL}** moedas + **{TAXA_SEMANAL}/semana**", inline=True)
        embed.add_field(name="💼 Seu saldo", value=f"**{total}** moedas", inline=False)
        embed.set_footer(text=f"*Taxa semanal de condomínio: {TAXA_SEMANAL} moedas  •  {RODAPE_IMPERIAL}")
        view = ConfirmarAquisicaoCasa(self.numero, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
# VIEW: CONFIRMAR COMPRA OU ALUGUEL
# ─────────────────────────────────────────────────────────────────────────────

class ConfirmarAquisicaoCasa(discord.ui.View):
    def __init__(self, numero: int, user_id: int):
        super().__init__(timeout=60)
        self.numero  = numero
        self.user_id = user_id

    @discord.ui.button(label="🏠 Comprar", style=discord.ButtonStyle.green)
    async def comprar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Esta confirmação não é sua!", ephemeral=True)
            return
        ok, msg = await _adquirir_casa(interaction, self.numero, "comprada")
        cor = 0x006400 if ok else 0x8B0000
        self.clear_items()
        await interaction.response.edit_message(
            embed=embed_imperial("✅ Compra Realizada!" if ok else "❌ Erro", msg, cor),
            view=self
        )

    @discord.ui.button(label="🔑 Alugar", style=discord.ButtonStyle.blurple)
    async def alugar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Esta confirmação não é sua!", ephemeral=True)
            return
        ok, msg = await _adquirir_casa(interaction, self.numero, "alugada")
        cor = 0x2B6CB0 if ok else 0x8B0000
        self.clear_items()
        await interaction.response.edit_message(
            embed=embed_imperial("✅ Aluguel Confirmado!" if ok else "❌ Erro", msg, cor),
            view=self
        )

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=embed_imperial("🚪 Cancelado", "Nenhuma transação foi realizada.", 0x2C2F33),
            view=None
        )


async def _adquirir_casa(interaction: discord.Interaction, numero: int, modo: str) -> tuple[bool, str]:
    viz = get_vizinhanca()
    chave = str(numero)
    dados = viz.get(chave, {})
    nome_casa = get_nome_casa(numero)

    if dados.get("id_dono") is not None:
        return False, "Esta residência já foi adquirida por outro morador."

    user = get_user(interaction.user.id)
    if user.get("casa_condominio"):
        return False, "Você já possui uma residência no condomínio. Devolva-a antes de adquirir outra."

    custo = TAXA_COMPRA if modo == "comprada" else TAXA_ALUGUEL
    total = user["moedas"] + user.get("conta_banco", 0)
    if total < custo:
        return False, f"Saldo insuficiente. Você tem **{total}** moedas e precisa de **{custo}**."

    # Descontar custo
    if user["moedas"] >= custo:
        user["moedas"] -= custo
    else:
        resto = custo - user["moedas"]
        user["moedas"] = 0
        user["conta_banco"] = user.get("conta_banco", 0) - resto

    user["casa_condominio"] = numero
    save_user(interaction.user.id, user)

    # Registrar no banco de dados de vizinhança
    viz[chave] = {
        "numero": numero,
        "nome": nome_casa,
        "id_canal": dados.get("id_canal"),
        "id_dono": str(interaction.user.id),
        "lista_moradores": [],
        "status_aluguel": modo,
        "data_aquisicao": datetime.utcnow().isoformat(),
        "ultima_cobranca": datetime.utcnow().isoformat(),
    }
    save_vizinhanca(viz)

    # Alterar permissões do canal no Discord em tempo real
    canal = None
    canal_id = dados.get("id_canal")
    if canal_id and interaction.guild:
        canal = interaction.guild.get_channel(int(canal_id))
    if canal is None and interaction.guild:
        # Procurar pelo nome casa-N
        nome_canal = f"casa-{numero}"
        for ch in interaction.guild.text_channels:
            if ch.name.lower() == nome_canal:
                canal = ch
                # Salvar o ID encontrado
                viz[chave]["id_canal"] = str(ch.id)
                save_vizinhanca(viz)
                break

    if canal:
        try:
            membro = interaction.guild.get_member(interaction.user.id)
            if membro:
                await canal.set_permissions(membro, read_messages=True, send_messages=True)
        except Exception:
            pass

    tipo_txt = "comprada com sucesso" if modo == "comprada" else "alugada com sucesso"
    taxa_txt = f"\n💸 Taxa semanal de condomínio: **{TAXA_SEMANAL} moedas/semana**" if modo == "alugada" else f"\n🏛️ Taxa de condomínio semanal: **{TAXA_SEMANAL} moedas/semana**"
    return True, (
        f"**{nome_casa}** foi {tipo_txt}!\n"
        f"Você agora tem acesso exclusivo ao canal `casa-{numero}`.\n{taxa_txt}\n\n"
        f"Use `Tenshi, convidar @usuario` para convidar moradores."
    )


# ─────────────────────────────────────────────────────────────────────────────
# VIEW: PAINEL DA PORTARIA (18 casas)
# ─────────────────────────────────────────────────────────────────────────────

class PainelPortaria(discord.ui.View):
    def __init__(self, vizinhanca: dict, pagina: int = 0):
        super().__init__(timeout=180)
        self.vizinhanca = vizinhanca
        self.pagina = pagina
        self._build()

    def _build(self):
        self.clear_items()
        inicio = self.pagina * 9
        fim    = inicio + 9
        nums   = list(range(1, 19))[inicio:fim]
        for n in nums:
            dados = self.vizinhanca.get(str(n), {})
            self.add_item(BotaoCasaCondominio(n, dados))
        if self.pagina > 0:
            b = discord.ui.Button(label="◀ Anterior", style=discord.ButtonStyle.blurple, row=3)
            b.callback = self._anterior
            self.add_item(b)
        if fim < 18:
            b = discord.ui.Button(label="Próxima ▶", style=discord.ButtonStyle.blurple, row=3)
            b.callback = self._proxima
            self.add_item(b)

    async def _proxima(self, interaction: discord.Interaction):
        self.pagina += 1
        self._build()
        await interaction.response.edit_message(view=self)

    async def _anterior(self, interaction: discord.Interaction):
        self.pagina -= 1
        self._build()
        await interaction.response.edit_message(view=self)


# ─────────────────────────────────────────────────────────────────────────────
# COG PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class Vizinhanca:
    def __init__(self, bot):
        self.bot = bot
        self._cobranca_iniciada = False
        self._cronica_iniciada  = False

    def cog_load(self):
        if not self._cobranca_iniciada:
            self._cobranca_iniciada = True
            self.bot.loop.create_task(self._loop_cobranca_semanal())
        if not self._cronica_iniciada:
            self._cronica_iniciada = True
            self.bot.loop.create_task(self._loop_cronicas_condominio())

    # ── PAINEL DA PORTARIA ────────────────────────────────────────────────────

    async def handle_portaria(self, message):
        viz = get_vizinhanca()
        ocupadas   = sum(1 for v in viz.values() if v.get("id_dono"))
        disponiveis = 18 - ocupadas

        embed = discord.Embed(
            title="🏘️ CONDOMÍNIO IMPERIAL — PORTARIA",
            description=(
                f"*Bem-vindo à Vizinhança do Condomínio de Tenshi.*\n{SEP}\n\n"
                f"🟢 **{disponiveis}** residências disponíveis  |  🔴 **{ocupadas}** ocupadas\n\n"
                f"**Compra:** {TAXA_COMPRA} moedas  •  **Aluguel:** {TAXA_ALUGUEL} moedas + {TAXA_SEMANAL}/semana\n\n"
                f"Clique na residência desejada para adquiri-la.\n"
                f"🟢 Disponível  🔴 Comprada  🟡 Alugada"
            ),
            color=0x8B6914
        )
        embed.set_footer(text=f"🏛️ Condomínio Tenshi  •  {RODAPE_IMPERIAL}")
        view = PainelPortaria(viz, pagina=0)
        await message.channel.send(embed=embed, view=view)

    # ── MINHA CASA NO CONDOMÍNIO ──────────────────────────────────────────────

    async def handle_meu_lar(self, message):
        user = get_user(message.author.id)
        numero = user.get("casa_condominio")
        if not numero:
            await message.channel.send(embed=embed_imperial(
                "🏠 Sem Residência",
                "*Você não possui uma residência no condomínio.*\n\nVá até `#portaria` ou use `Tenshi, portaria` para adquirir uma.",
                0x2C2F33
            ))
            return
        viz = get_vizinhanca()
        dados = viz.get(str(numero), {})
        moradores = dados.get("lista_moradores", [])
        moradores_fmt = "\n".join(f"• <@{m}>" for m in moradores) or "*Nenhum convidado*"
        embed = discord.Embed(
            title=f"🏠 {get_nome_casa(numero)} (Casa-{numero})",
            description=f"*Sua residência no Condomínio Imperial de Tenshi.*\n{SEP}",
            color=0x2B6CB0
        )
        embed.add_field(name="🏷️ Status",     value=dados.get("status_aluguel", "comprada").capitalize(), inline=True)
        embed.add_field(name="💸 Taxa semanal", value=f"{TAXA_SEMANAL} moedas", inline=True)
        embed.add_field(name="👥 Convidados",  value=moradores_fmt, inline=False)
        embed.set_footer(text=f"Use 'Tenshi, convidar @usuario' para dar acesso  •  {RODAPE_IMPERIAL}")
        await message.channel.send(embed=embed)

    # ── CONVIDAR VISITANTE ────────────────────────────────────────────────────

    async def handle_convidar(self, message, args):
        user = get_user(message.author.id)
        numero = user.get("casa_condominio")
        if not numero:
            await message.channel.send(embed=embed_imperial(
                "❌ Sem Residência",
                "Você não possui uma residência no condomínio para receber visitas.",
                0x8B0000
            ))
            return

        if not message.mentions:
            await message.channel.send(embed=embed_imperial(
                "❓ Como Usar",
                "Mencione o usuário que deseja convidar:\n`Tenshi, convidar @usuario`",
                0x2C2F33
            ))
            return

        alvo = message.mentions[0]
        viz  = get_vizinhanca()
        chave = str(numero)
        dados = viz.get(chave, {})
        moradores = dados.get("lista_moradores", [])

        if str(alvo.id) in moradores:
            await message.channel.send(embed=embed_imperial(
                "ℹ️ Já Convidado",
                f"{alvo.mention} já possui acesso à sua residência.",
                0x2B6CB0
            ))
            return

        moradores.append(str(alvo.id))
        dados["lista_moradores"] = moradores
        viz[chave] = dados
        save_vizinhanca(viz)

        # Dar permissão no canal
        canal = await self._get_canal_casa(message.guild, numero, dados)
        if canal:
            try:
                await canal.set_permissions(alvo, read_messages=True, send_messages=True)
            except Exception:
                pass

        await message.channel.send(embed=discord.Embed(
            title="🤝 CONVITE ACEITO",
            description=(
                f"*As portas se abrem...*\n{SEP}\n\n"
                f"{alvo.mention} foi convidado(a) para **{get_nome_casa(numero)}**!\n"
                f"Agora tem acesso ao canal `casa-{numero}`.\n\n"
                f"Use `Tenshi, expulsar @{alvo.name}` para remover o acesso."
            ),
            color=0x2B6CB0
        ))

    # ── EXPULSAR VISITANTE ────────────────────────────────────────────────────

    async def handle_expulsar(self, message, args):
        user = get_user(message.author.id)
        numero = user.get("casa_condominio")
        if not numero:
            await message.channel.send(embed=embed_imperial(
                "❌ Sem Residência",
                "Você não possui uma residência no condomínio.",
                0x8B0000
            ))
            return

        if not message.mentions:
            await message.channel.send(embed=embed_imperial(
                "❓ Como Usar",
                "Mencione o usuário que deseja expulsar:\n`Tenshi, expulsar @usuario`",
                0x2C2F33
            ))
            return

        alvo = message.mentions[0]
        viz  = get_vizinhanca()
        chave = str(numero)
        dados = viz.get(chave, {})
        moradores = dados.get("lista_moradores", [])

        if str(alvo.id) not in moradores:
            await message.channel.send(embed=embed_imperial(
                "ℹ️ Não Encontrado",
                f"{alvo.mention} não está na lista de convidados da sua residência.",
                0x2C2F33
            ))
            return

        moradores.remove(str(alvo.id))
        dados["lista_moradores"] = moradores
        viz[chave] = dados
        save_vizinhanca(viz)

        # Remover permissão no canal
        canal = await self._get_canal_casa(message.guild, numero, dados)
        if canal:
            try:
                await canal.set_permissions(alvo, overwrite=None)
            except Exception:
                pass

        await message.channel.send(embed=discord.Embed(
            title="🚪 VISITANTE REMOVIDO",
            description=(
                f"*As portas se fecham...*\n{SEP}\n\n"
                f"{alvo.mention} foi removido(a) de **{get_nome_casa(numero)}**.\n"
                f"O acesso ao canal `casa-{numero}` foi revogado."
            ),
            color=0x8B0000
        ))

    # ── DEVOLVER / ABANDONAR CASA ─────────────────────────────────────────────

    async def handle_devolver_casa(self, message):
        user = get_user(message.author.id)
        numero = user.get("casa_condominio")
        if not numero:
            await message.channel.send(embed=embed_imperial(
                "❌ Sem Residência",
                "Você não possui uma residência no condomínio para devolver.",
                0x8B0000
            ))
            return

        viz   = get_vizinhanca()
        chave = str(numero)
        dados = viz.get(chave, {})
        nome  = get_nome_casa(numero)

        # Reembolso parcial se comprada (30%)
        reembolso = 0
        status = dados.get("status_aluguel", "comprada")
        if status == "comprada":
            reembolso = int(TAXA_COMPRA * 0.3)
            user["moedas"] = user.get("moedas", 0) + reembolso

        # Remover permissões de todos os moradores
        canal = await self._get_canal_casa(message.guild, numero, dados)
        if canal:
            moradores_ids = [dados.get("id_dono")] + dados.get("lista_moradores", [])
            for uid in moradores_ids:
                if uid:
                    membro = message.guild.get_member(int(uid))
                    if membro:
                        try:
                            await canal.set_permissions(membro, overwrite=None)
                        except Exception:
                            pass

        # Resetar registro
        viz[chave] = {
            "numero": numero,
            "nome": nome,
            "id_canal": dados.get("id_canal"),
            "id_dono": None,
            "lista_moradores": [],
            "status_aluguel": "disponivel",
            "data_aquisicao": None,
            "ultima_cobranca": None,
        }
        save_vizinhanca(viz)
        user["casa_condominio"] = None
        save_user(message.author.id, user)

        desc = f"**{nome}** foi devolvida ao condomínio.\nA residência está disponível para novos moradores."
        if reembolso:
            desc += f"\n\n💰 Reembolso de **{reembolso} moedas** creditado na sua carteira."
        await message.channel.send(embed=embed_imperial("🏚️ Residência Devolvida", desc, 0x556B2F))

    # ── DESCANSO NOS CANAIS DE LAZER ─────────────────────────────────────────

    async def handle_descanso_lazer(self, message):
        nome_canal = message.channel.name.lower() if message.channel else ""
        local = None
        for k in BONUS_LAZER:
            if k in nome_canal:
                local = k
                break

        if not local:
            await message.channel.send(embed=embed_imperial(
                "🌿 Descanso",
                "*Este lugar não oferece bônus especial de lazer...*\n\nPara bônus especiais, use este comando em: #piscina, #jardim, #praça, #quadra ou #garagem.",
                0x2C2F33
            ))
            return

        user = get_user(message.author.id)
        agora = datetime.utcnow()
        ultimo = user.get("ultimo_descanso_lazer")
        if ultimo:
            diferenca = (agora - datetime.fromisoformat(ultimo)).total_seconds()
            if diferenca < COOLDOWN_DESCANSO:
                restante = int((COOLDOWN_DESCANSO - diferenca) / 60)
                await message.channel.send(embed=embed_imperial(
                    "⏳ Descanso em Recarga",
                    f"*Você ainda está se recuperando...*\n\nAguarde mais **{restante} minuto(s)** para usar o bônus de lazer novamente.",
                    0x2C2F33
                ))
                return

        bonus = BONUS_LAZER[local]
        fadiga_atual = user.get("fadiga", 0)
        nova_fadiga = max(0, fadiga_atual - bonus)
        user["fadiga"] = nova_fadiga
        user["ultimo_descanso_lazer"] = agora.isoformat()
        save_user(message.author.id, user)

        descricoes = {
            "piscina": f"*{message.author.display_name} mergulha nas águas cristalinas da piscina imperial...*\n\nAs ondas suaves dissolvem toda a tensão. A fadiga cai **{bonus} pontos** (bônus duplo!).",
            "jardim":  f"*{message.author.display_name} caminha entre as flores e árvores do jardim...*\n\nO aroma das ervas imperiais restaura as energias. Fadiga reduzida em **{bonus} pontos**.",
            "praça":   f"*{message.author.display_name} senta-se na praça e observa o movimento do condomínio...*\n\nA convivência revitaliza o espírito. Fadiga reduzida em **{bonus} pontos**.",
            "quadra":  f"*{message.author.display_name} pratica exercícios leves na quadra poliesportiva...*\n\nO corpo aquecido pela atividade física revigora a mente. Fadiga reduzida em **{bonus} pontos**.",
            "garagem": f"*{message.author.display_name} passa um tempo cuidando do veículo na garagem...*\n\nA meditação prática acalma os pensamentos. Fadiga reduzida em **{bonus} pontos**.",
        }

        embed = discord.Embed(
            title=f"{'🏊' if local == 'piscina' else '🌿' if local in ('jardim','praça') else '🏃' if local == 'quadra' else '🚗'} DESCANSO — {local.upper()}",
            description=descricoes.get(local, "*Você descansa...*"),
            color=0x006400 if local != "piscina" else 0x1E90FF
        )
        embed.add_field(name="😴 Fadiga Removida", value=f"**-{bonus}** pontos", inline=True)
        embed.add_field(name="📊 Fadiga Atual",    value=f"**{nova_fadiga}** pontos", inline=True)
        if local == "piscina":
            embed.set_footer(text="🏊 A piscina concede regeneração dupla de energia!")
        await message.channel.send(embed=embed)

        # Lança crônica de condomínio aleatoriamente (20% de chance)
        if random.random() < 0.20:
            await asyncio.sleep(2)
            await self._lancar_cronica_aleatoria(message.channel)

    # ── LISTAR MORADORES DO CONDOMÍNIO ────────────────────────────────────────

    async def handle_moradores(self, message):
        viz = get_vizinhanca()
        embed = discord.Embed(
            title="🏘️ MORADORES DO CONDOMÍNIO",
            description=f"*Lista completa dos residentes do Condomínio Imperial...*\n{SEP}",
            color=0x8B6914
        )
        for n in range(1, 19):
            dados = viz.get(str(n), {})
            dono  = dados.get("id_dono")
            if dono:
                status = dados.get("status_aluguel", "comprada").capitalize()
                moradores = dados.get("lista_moradores", [])
                valor = f"👤 <@{dono}> ({status})"
                if moradores:
                    valor += f"\n👥 Convidados: {len(moradores)}"
            else:
                valor = "🟢 Disponível"
            embed.add_field(name=f"🏠 Casa-{n} — {get_nome_casa(n)}", value=valor, inline=True)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    # ── CRÔNICA DO CONDOMÍNIO (comando manual) ────────────────────────────────

    async def handle_cronica_condominio(self, message):
        cronica = random.choice(CRONICAS_CONDOMINIO)
        embed = discord.Embed(
            title="📰 CRÔNICA DO CONDOMÍNIO",
            description=(
                f"*Os jornaleiros anônimos do Condomínio Imperial revelam...*\n{SEP}\n\n"
                f"{cronica}\n\n{SEP}"
            ),
            color=0x4B0082
        )
        embed.set_footer(text="🔒 Identidade do informante protegida")
        await message.channel.send(embed=embed)

    # ── AUXILIARES INTERNOS ───────────────────────────────────────────────────

    async def _get_canal_casa(self, guild, numero: int, dados: dict):
        if not guild:
            return None
        canal_id = dados.get("id_canal")
        if canal_id:
            canal = guild.get_channel(int(canal_id))
            if canal:
                return canal
        nome_canal = f"casa-{numero}"
        for ch in guild.text_channels:
            if ch.name.lower() == nome_canal:
                viz = get_vizinhanca()
                viz[str(numero)]["id_canal"] = str(ch.id)
                save_vizinhanca(viz)
                return ch
        return None

    async def _lancar_cronica_aleatoria(self, canal):
        cronica = random.choice(CRONICAS_CONDOMINIO)
        embed = discord.Embed(
            title="📰 FOFOCA DO CONDOMÍNIO",
            description=(
                f"*Um bilhete anônimo circula entre os moradores...*\n{SEP}\n\n"
                f"{cronica}"
            ),
            color=0x4B0082
        )
        embed.set_footer(text="🔒 Fonte anônima — Condomínio Tenshi")
        try:
            await canal.send(embed=embed)
        except Exception:
            pass

    # ── LOOP: COBRANÇA SEMANAL ────────────────────────────────────────────────

    async def _loop_cobranca_semanal(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            # Cobrar todo domingo às 00:00 UTC
            if agora.weekday() == 6 and agora.hour == 0 and agora.minute < 5:
                await self._executar_cobranca()
            await asyncio.sleep(300)  # Verificar a cada 5 minutos

    async def _executar_cobranca(self):
        viz    = get_vizinhanca()
        despejados = []

        for chave, dados in list(viz.items()):
            dono_id = dados.get("id_dono")
            if not dono_id:
                continue
            ultima = dados.get("ultima_cobranca")
            if ultima:
                diff = (datetime.utcnow() - datetime.fromisoformat(ultima)).total_seconds()
                if diff < 6 * 24 * 3600:  # Menos de 6 dias
                    continue

            user = get_user(int(dono_id))
            total = user.get("moedas", 0) + user.get("conta_banco", 0)
            if total >= TAXA_SEMANAL:
                if user["moedas"] >= TAXA_SEMANAL:
                    user["moedas"] -= TAXA_SEMANAL
                else:
                    resto = TAXA_SEMANAL - user["moedas"]
                    user["moedas"] = 0
                    user["conta_banco"] = user.get("conta_banco", 0) - resto
                dados["ultima_cobranca"] = datetime.utcnow().isoformat()
                save_user(int(dono_id), user)
            else:
                # Despejar: zerar registro, revogar permissões
                despejados.append((chave, dados, dono_id))
                numero = int(chave)
                viz[chave] = {
                    "numero": numero,
                    "nome": get_nome_casa(numero),
                    "id_canal": dados.get("id_canal"),
                    "id_dono": None,
                    "lista_moradores": [],
                    "status_aluguel": "disponivel",
                    "data_aquisicao": None,
                    "ultima_cobranca": None,
                }
                user["casa_condominio"] = None
                save_user(int(dono_id), user)

        save_vizinhanca(viz)

        # Notificar despejados em todos os servidores
        if despejados:
            for guild in self.bot.guilds:
                for chave, dados, dono_id in despejados:
                    canal_id = dados.get("id_canal")
                    numero   = int(chave)
                    if canal_id:
                        canal = guild.get_channel(int(canal_id))
                        if canal:
                            try:
                                await canal.set_permissions(guild.get_member(int(dono_id)), overwrite=None)
                            except Exception:
                                pass
                canal_notif = guild.system_channel
                if canal_notif:
                    ids_fmt = ", ".join(f"<@{d}>" for _, _, d in despejados)
                    try:
                        await canal_notif.send(embed=embed_imperial(
                            "🔒 DESPEJO IMPERIAL — CONDOMÍNIO",
                            f"*Por falta de pagamento da taxa semanal de condomínio...*\n\n"
                            f"Os seguintes moradores foram despejados e suas casas devolvidas ao mercado:\n{ids_fmt}\n\n"
                            f"*Para reaver uma residência, visite a portaria e adquira novamente.*",
                            0x8B0000
                        ))
                    except Exception:
                        pass

    # ── LOOP: CRÔNICAS AUTOMÁTICAS ─────────────────────────────────────────────

    async def _loop_cronicas_condominio(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # Lançar crônica a cada 4-8 horas aleatoriamente
            espera = random.randint(4 * 3600, 8 * 3600)
            await asyncio.sleep(espera)
            for guild in self.bot.guilds:
                canal = None
                for ch in guild.text_channels:
                    if "praça" in ch.name.lower() or "praca" in ch.name.lower() or "jardim" in ch.name.lower():
                        canal = ch
                        break
                if canal:
                    try:
                        await self._lancar_cronica_aleatoria(canal)
                    except Exception:
                        pass
