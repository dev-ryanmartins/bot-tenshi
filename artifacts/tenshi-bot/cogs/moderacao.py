import discord
import asyncio
from utils import embed_imperial, IMPERADOR_ID, SEP, RODAPE_IMPERIAL
from database import get_user, save_user
from ia_router import ia_soberana, ia_analitica


# ─────────────────────────────────────────────────────────────────────────────
# View de Julgamento com botões
# ─────────────────────────────────────────────────────────────────────────────
class JulgamentoView(discord.ui.View):
    def __init__(self, reu: discord.Member, juiz: discord.Member, bot):
        super().__init__(timeout=300)
        self.reu       = reu
        self.juiz      = juiz
        self.bot       = bot
        self.encerrado = False

    def _check_perm(self, interaction: discord.Interaction) -> bool:
        try:
            return interaction.user.guild_permissions.moderate_members or interaction.user.id == IMPERADOR_ID
        except Exception:
            return interaction.user.id == IMPERADOR_ID

    @discord.ui.button(label="🟩 Culpado — Masmorra", style=discord.ButtonStyle.danger)
    async def culpado(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_perm(interaction):
            await interaction.response.send_message("*Apenas magistrados imperiais podem julgar.*", ephemeral=True)
            return
        if self.encerrado:
            return
        self.encerrado = True
        self.clear_items()
        try:
            await self.reu.timeout(discord.utils.utcnow() + asyncio.timedelta(minutes=60))
        except Exception:
            pass
        embed = discord.Embed(
            title="⚖️ VEREDITO — CULPADO",
            description=(
                f"*O martelo imperial cai com estrondo...*\n{SEP}\n\n"
                f"**{self.reu.display_name}** foi declarado **CULPADO** pelos magistrados de Tenshi.\n\n"
                f"*Sentença: 60 minutos nas masmorras imperiais.*\n\n{SEP}"
            ),
            color=0x8B0000
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🟥 Traidor — Exílio", style=discord.ButtonStyle.danger)
    async def traidor(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_perm(interaction):
            await interaction.response.send_message("*Apenas magistrados imperiais podem julgar.*", ephemeral=True)
            return
        if self.encerrado:
            return
        self.encerrado = True
        self.clear_items()
        try:
            await self.reu.ban(reason="Julgamento Imperial — Exílio por traição")
        except Exception:
            pass
        embed = discord.Embed(
            title="🔴 VEREDITO — EXÍLIO PERPÉTUO",
            description=(
                f"*O decreto de exílio é assinado com tinta negra...*\n{SEP}\n\n"
                f"**{self.reu.display_name}** foi banido do Império de Tenshi por traição.\n\n"
                f"*Que nunca mais pise em nossas terras sagradas.*\n\n{SEP}"
            ),
            color=0x0D0D0D
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🕊️ Inocente — Absolver", style=discord.ButtonStyle.success)
    async def inocente(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_perm(interaction):
            await interaction.response.send_message("*Apenas magistrados imperiais podem julgar.*", ephemeral=True)
            return
        if self.encerrado:
            return
        self.encerrado = True
        self.clear_items()
        embed = discord.Embed(
            title="🕊️ VEREDITO — INOCENTE",
            description=(
                f"*A balança da justiça imperial pende para a inocência...*\n{SEP}\n\n"
                f"**{self.reu.display_name}** foi declarado **INOCENTE** e absolvido de todas as acusações.\n\n"
                f"*O Império reconhece sua honra. Que sua lealdade continue inabalável.*\n\n{SEP}"
            ),
            color=0x006400
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await interaction.response.edit_message(embed=embed, view=self)


class Moderacao:
    def __init__(self, bot):
        self.bot = bot

    async def handle_julgamento(self, message, args):
        if not message.mentions:
            await message.channel.send(embed=embed_imperial(
                "⚖️ Câmara de Julgamento",
                f"*Para abrir um julgamento imperial:*\n{SEP}\n`Tenshi, julgamento @usuario`\n\n"
                f"*Três veredictos disponíveis: Culpado, Traidor ou Inocente.*",
                0x2B0A3D
            ))
            return
        reu = message.mentions[0]
        if reu.id == IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "*O Imperador está acima de qualquer julgamento mortal.*", 0x6B0000))
            return
        embed = discord.Embed(
            title="⚖️ CÂMARA DE JULGAMENTO IMPERIAL",
            description=(
                f"*Os sinos da corte imperial ecoam pelo salão do trono...*\n{SEP}\n\n"
                f"**{reu.display_name}** comparece diante da Câmara Imperial.\n\n"
                f"*Magistrados e Administradores decidem o destino deste súdito.*\n\n{SEP}"
            ),
            color=0x2B0A3D
        )
        embed.set_footer(text=f"⚖️ A justiça de Tenshi é absoluta  •  {RODAPE_IMPERIAL}")
        view = JulgamentoView(reu, message.author, self.bot)
        await message.channel.send(embed=embed, view=view)

    async def handle_decreto(self, message, args):
        if message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "*Apenas o Imperador Alloy pode emitir decretos imperiais.*", 0x6B0000))
            return
        if not args:
            await message.channel.send(embed=embed_imperial("❓", "`Tenshi, decreto [mensagem do decreto]`", 0x6B0000))
            return
        texto = " ".join(args)
        try:
            await message.delete()
        except Exception:
            pass
        embed = discord.Embed(
            title="📜 ⚜️ DECRETO IMPERIAL DE TENSHI ⚜️ 📜",
            description=(
                f"*Pela voz divina do Soberano Eterno...*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**{texto}**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0xFFD700
        )
        embed.set_author(
            name="⚜️ IMPERADOR ALLOY — Soberano Supremo e Eterno",
            icon_url=message.author.display_avatar.url
        )
        embed.set_footer(text="📜 Pelo poder eterno do Trono Imperial — que todos obedeçam e sirvam")
        await message.channel.send(embed=embed)

    async def handle_promover_cargo(self, message, args):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.manage_roles
        except: pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para gerenciar cargos.", 0x6B0000))
            return
        if not message.mentions or len(args) < 2:
            await message.channel.send(embed=embed_imperial("❓", "`Tenshi, promover @usuario [nome do cargo no servidor]`", 0x6B0000))
            return
        alvo = message.mentions[0]
        cargo_nome = " ".join([a for a in args if not a.startswith("<@")])
        cargo = discord.utils.get(message.guild.roles, name=cargo_nome)
        if not cargo:
            await message.channel.send(embed=embed_imperial("❌", f"Cargo `{cargo_nome}` não encontrado no servidor.", 0x6B0000))
            return
        try:
            await alvo.add_roles(cargo)
            embed = discord.Embed(
                title="⚜️ DECRETO DE PROMOÇÃO",
                description=(
                    f"*O selo imperial foi aposto no pergaminho...*\n{SEP}\n\n"
                    f"**{alvo.display_name}** recebe o cargo **{cargo.name}** por ordem imperial.\n\n"
                    f"*Que sirva ao Império com toda sua nova autoridade.*\n\n{SEP}"
                ),
                color=0xFFD700
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Sem permissão para atribuir este cargo.", 0x6B0000))

    async def handle_punir_audacia(self, message, args):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.moderate_members
        except: pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão.", 0x6B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "`Tenshi, punir-audacia @usuario`", 0x6B0000))
            return
        alvo = message.mentions[0]
        if alvo.id == IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "*O Imperador está acima de qualquer punição mortal.*", 0x6B0000))
            return
        try:
            import datetime as dt
            fim = discord.utils.utcnow() + dt.timedelta(minutes=10)
            await alvo.timeout(fin=fim, reason="Audácia na Corte Imperial")
            embed = discord.Embed(
                title="🔇 PUNIÇÃO POR AUDÁCIA",
                description=(
                    f"*Os guardas imperiais se movem em silêncio...*\n{SEP}\n\n"
                    f"**{alvo.display_name}** foi silenciado por **10 minutos** por falta de decoro na corte imperial.\n\n"
                    f"*Na próxima vez, a punição será mais severa.*\n\n{SEP}"
                ),
                color=0x8B0000
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌", f"Erro: {str(e)[:80]}", 0x6B0000))

    async def handle_prender(self, message, args):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.moderate_members
        except: pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão.", 0x6B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "`Tenshi, prender @usuario [minutos] [motivo]`", 0x6B0000))
            return
        alvo = message.mentions[0]
        minutos = 30
        for a in args:
            if a.isdigit():
                minutos = min(int(a), 10080)
                break
        motivo_parts = [a for a in args if not a.startswith("<@") and not a.isdigit()]
        motivo = " ".join(motivo_parts) or "Encarcerado por ordem imperial"
        try:
            import datetime as dt
            fim = discord.utils.utcnow() + dt.timedelta(minutes=minutos)
            await alvo.timeout(fin=fim, reason=motivo)
            embed = discord.Embed(
                title="⛓️ APRISIONAMENTO IMPERIAL",
                description=(
                    f"*As correntes das masmorras de Tenshi fecham-se...*\n{SEP}\n\n"
                    f"**{alvo.display_name}** foi preso nas masmorras imperiais por **{minutos} minutos**.\n\n"
                    f"**Motivo:** *{motivo}*\n\n{SEP}"
                ),
                color=0x2C2F33
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌", f"Erro: {str(e)[:80]}", 0x6B0000))

    async def handle_exilar(self, message, args):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.ban_members
        except: pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para exilar.", 0x6B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "`Tenshi, exilar @usuario [motivo]`", 0x6B0000))
            return
        alvo = message.mentions[0]
        motivo = " ".join([a for a in args if not a.startswith("<@")]) or "Exilado por ordem imperial"
        try:
            await alvo.send(embed=embed_imperial(
                "⚖️ Exílio Imperial",
                f"*Você foi exilado do Império de Tenshi.*\n\n**Motivo:** {motivo}",
                0x8B0000
            ))
        except Exception:
            pass
        try:
            await message.guild.ban(alvo, reason=motivo)
            embed = discord.Embed(
                title="🔴 DECRETO DE EXÍLIO",
                description=(
                    f"*O nome foi riscado dos Pergaminhos Imperiais...*\n{SEP}\n\n"
                    f"**{alvo.display_name}** foi exilado para além das fronteiras de Tenshi.\n\n"
                    f"**Motivo:** *{motivo}*\n\n{SEP}"
                ),
                color=0x0D0D0D
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Sem permissão.", 0x6B0000))

    async def handle_anistia(self, message):
        if message.author.id != IMPERADOR_ID:
            tem_perm = False
            try: tem_perm = message.author.guild_permissions.administrator
            except: pass
            if not tem_perm:
                await message.channel.send(embed=embed_imperial("🚫", "Apenas o Imperador ou Administradores podem conceder anistia.", 0x6B0000))
                return
        embed = discord.Embed(
            title="🕊️ ANISTIA REAL — PERDÃO IMPERIAL",
            description=(
                f"*O Imperador Alloy estende a mão da misericórdia...*\n{SEP}\n\n"
                f"**Todos os avisos e advertências** foram apagados dos registros imperiais.\n\n"
                f"*Um novo começo para todos os súditos de Tenshi. Que não abusem desta graça.*\n\n{SEP}"
            ),
            color=0x006400
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_lockdown(self, message):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.administrator
        except: pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para trancar portões.", 0x6B0000))
            return
        embed = discord.Embed(
            title="🔒 PORTÕES TRANCADOS — ALERTA IMPERIAL",
            description=(
                f"*Os guardas imperiais fecham os portões do Império...*\n{SEP}\n\n"
                f"**Modo de emergência ativado!**\n\n"
                f"*O acesso ao Império de Tenshi está restrito. Apenas membros confirmados podem interagir.*\n\n"
                f"*Use este canal apenas para comunicados oficiais.*\n\n{SEP}"
            ),
            color=0xFF0000
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_tesouro(self, message, args):
        if message.author.id != IMPERADOR_ID:
            tem_perm = False
            try: tem_perm = message.author.guild_permissions.administrator
            except: pass
            if not tem_perm:
                await message.channel.send(embed=embed_imperial("🚫", "Apenas o Imperador ou Administradores controlam o Tesouro Imperial.", 0x6B0000))
                return
        if not args:
            await message.channel.send(embed=embed_imperial("❓", "`Tenshi, tesouro [sacar/depositar/confiscar] [valor] @usuario`", 0x6B0000))
            return
        operacao = args[0].lower()
        valor = 0
        for a in args[1:]:
            if a.isdigit():
                valor = int(a)
                break
        alvo_id = message.mentions[0].id if message.mentions else None

        if operacao in ("depositar", "adicionar") and alvo_id and valor > 0:
            user = get_user(alvo_id)
            user["moedas"] += valor
            save_user(alvo_id, user)
            await message.channel.send(embed=embed_imperial(
                "🏦 Tesouro Imperial — Depósito",
                f"**+{valor} moedas** adicionadas para {message.mentions[0].display_name} por decreto imperial.",
                0x006400
            ))
        elif operacao in ("sacar", "remover", "confiscar") and alvo_id and valor > 0:
            user = get_user(alvo_id)
            user["moedas"] = max(0, user["moedas"] - valor)
            save_user(alvo_id, user)
            await message.channel.send(embed=embed_imperial(
                "🏦 Tesouro Imperial — Confisco",
                f"**{valor} moedas** confiscadas de {message.mentions[0].display_name} por decreto imperial.",
                0x8B0000
            ))
        else:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, tesouro depositar 100 @usuario` ou `tesouro confiscar 100 @usuario`", 0x6B0000))

    async def handle_veto(self, message, args):
        if message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Apenas o Imperador Alloy pode exercer o Poder de Veto.", 0x6B0000))
            return
        alvo_str = " ".join(args) if args else "a ação"
        embed = discord.Embed(
            title="🚫 ⚜️ PODER DE VETO IMPERIAL ⚜️ 🚫",
            description=(
                f"*Uma aura dourada emana do Trono...*\n{SEP}\n\n"
                f"O **Imperador Alloy** exerceu o Poder de Veto sobre: **{alvo_str}**\n\n"
                f"*Esta decisão é irrevogável e tem efeito imediato em todos os domínios de Tenshi.*\n\n{SEP}"
            ),
            color=0xFFD700
        )
        embed.set_author(name="⚜️ Veto do Imperador Alloy", icon_url=message.author.display_avatar.url)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def handle_ban(self, message, args):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.ban_members
        except: pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para banir.", 0x6B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "`Tenshi, ban @usuario [motivo]`", 0x6B0000))
            return
        alvo  = message.mentions[0]
        motivo = " ".join([a for a in args if not a.startswith("<@")]) or "Banido por decreto"
        try:
            await message.guild.ban(alvo, reason=motivo)
            embed = discord.Embed(
                title="⚖️ BANIMENTO IMPERIAL", color=0x8B0000,
                description=f"**{alvo.display_name}** foi banido do Império.\n**Motivo:** *{motivo}*"
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Sem permissão.", 0x6B0000))

    async def handle_kick(self, message, args):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.kick_members
        except: pass
        if not tem_perm:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão.", 0x6B0000))
            return
        if not message.mentions:
            return
        alvo  = message.mentions[0]
        motivo = " ".join([a for a in args if not a.startswith("<@")]) or "Expulso por decreto"
        try:
            await message.guild.kick(alvo, reason=motivo)
            await message.channel.send(embed=embed_imperial("👢 Expulsão", f"**{alvo.display_name}** foi expulso. *{motivo}*", 0xFF8C00))
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Sem permissão.", 0x6B0000))

    async def handle_mute(self, message, args):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.moderate_members
        except: pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão.", 0x6B0000))
            return
        if not message.mentions:
            return
        alvo = message.mentions[0]
        try:
            import datetime as dt
            fim = discord.utils.utcnow() + dt.timedelta(minutes=30)
            await alvo.timeout(fin=fim, reason="Silenciado por decreto")
            await message.channel.send(embed=embed_imperial("🔇 Silenciado", f"**{alvo.display_name}** foi silenciado por 30 minutos.", 0x4B0082))
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌", str(e)[:80], 0x6B0000))

    async def handle_clear(self, message, args):
        tem_perm = False
        try: tem_perm = message.author.guild_permissions.manage_messages
        except: pass
        if not tem_perm:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão.", 0x6B0000))
            return
        qtd = 10
        for a in args:
            if a.isdigit():
                qtd = min(int(a), 100)
                break
        try:
            del_count = await message.channel.purge(limit=qtd + 1)
            msg = await message.channel.send(embed=embed_imperial("🧹 Purificação", f"**{len(del_count)-1}** mensagens removidas.", 0x006400))
            await asyncio.sleep(4)
            await msg.delete()
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Sem permissão.", 0x6B0000))
