import discord
import asyncio
import json
import os
import re
from datetime import datetime, timezone, timedelta
from utils import embed_imperial, IMPERADOR_ID, SEP, RODAPE_IMPERIAL
from database import get_user, save_user
from database_infractions import register_infraction, get_infractions
from ia_router import ia_soberana, ia_analitica
from bot_logger import bot_logger


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

    def _tem_manage_roles(self, message) -> bool:
        try:
            return message.author.guild_permissions.manage_roles or message.author.guild_permissions.administrator
        except Exception:
            return False

    def _nome_cargo_tenshi(self, nome: str, emoji: str = "最", nivel: str | None = None) -> str:
        base = f"” ͎ᵎ  ⊰ {emoji}  {nome.strip()}"
        if nivel:
            base = f"{base}  ʚ 最—{nivel}"
        return base[:100]

    async def handle_criar_cargo_imperial(self, message, args):
        if not self._tem_manage_roles(message) and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para criar cargos imperiais.", 0x6B0000))
            return
        if not args:
            await message.channel.send(embed=embed_imperial(
                "❓ Criar Cargo Imperial",
                "`Tenshi, criar-cargo 👑 Rei --nivel 1`\n"
                "`Tenshi, criar-cargo 最 Guarda Imperial`\n\n"
                "Formato gerado: `” ͎ᵎ  ⊰ [emoji]  [nome]`",
                0x2B0A3D,
            ))
            return

        tokens = list(args)
        nivel = None
        if "--nivel" in tokens:
            idx = tokens.index("--nivel")
            if idx + 1 < len(tokens):
                nivel = tokens[idx + 1]
            tokens = tokens[:idx] + tokens[idx + 2:]

        emoji = "最"
        if tokens and (not tokens[0].replace("-", "").isalnum() or tokens[0].startswith("<:") or tokens[0].startswith("<a:")):
            emoji = tokens.pop(0)

        nome_base = " ".join(tokens).strip()
        if not nome_base:
            await message.channel.send(embed=embed_imperial("❓", "Informe o nome do cargo.", 0x6B0000))
            return

        nome_cargo = self._nome_cargo_tenshi(nome_base, emoji, nivel)
        existente = discord.utils.get(message.guild.roles, name=nome_cargo)
        if existente:
            await message.channel.send(embed=embed_imperial("⚜️ Cargo Existente", f"O cargo {existente.mention} já existe.", 0x9E7815))
            return
        try:
            cargo = await message.guild.create_role(
                name=nome_cargo,
                color=discord.Color(0x9E7815),
                mentionable=True,
                reason=f"Cargo imperial criado por {message.author} via Tenshi Bot",
            )
            await message.channel.send(embed=embed_imperial(
                "⚜️ Cargo Imperial Criado",
                f"**Nome:** {cargo.mention}\n"
                f"**Estética:** `{nome_cargo}`\n"
                f"**Criado por:** {message.author.mention}",
                0xFFD700,
            ))
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Não tenho permissão/hierarquia para criar esse cargo.", 0x6B0000))
        except Exception as exc:
            await message.channel.send(embed=embed_imperial("❌", f"Erro ao criar cargo: {str(exc)[:120]}", 0x6B0000))

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
            await register_infraction(alvo.id, "ban", motivo, message.author.id)
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

    def _carregar_palavras_proibidas(self, guild_id: int) -> set[str]:
        path = "data/palavras_proibidas.json"
        if not os.path.exists(path):
            return set()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get(str(guild_id), []))
        except Exception:
            return set()

    def _salvar_palavras_proibidas(self, guild_id: int, palavras: set[str]) -> None:
        path = "data/palavras_proibidas.json"
        os.makedirs("data", exist_ok=True)
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[str(guild_id)] = sorted(list(palavras))
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def verificar_palavras_proibidas(self, message: discord.Message) -> bool:
        """
        Analisa a mensagem em busca de palavras proibidas cadastradas.
        Se encontrada, remove a mensagem, avisa o usuário e registra infração.
        Retorna True se houve violação interceptada.
        """
        if not message.guild or message.author.bot:
            return False

        # Imperador e administradores não são bloqueados pelo filtro
        if message.author.id == IMPERADOR_ID:
            return False
        perms = getattr(message.author, "guild_permissions", None)
        if perms and perms.administrator:
            return False

        palavras = self._carregar_palavras_proibidas(message.guild.id)
        if not palavras:
            return False

        conteudo_lower = message.content.lower()
        palavras_encontradas = [p for p in palavras if re.search(rf"\b{re.escape(p)}\b", conteudo_lower)]
        if not palavras_encontradas:
            return False

        # Apagar a mensagem proibida
        try:
            await message.delete()
        except Exception:
            pass

        palavra_censurada = palavras_encontradas[0]
        bot_logger.warning(
            f"Palavra proibida interceptada: '{palavra_censurada}'",
            usuario=f"{message.author} ({message.author.id})",
            canal=getattr(message.channel, "name", "desconhecido"),
            servidor=message.guild.name,
        )

        # Registrar infração automática
        try:
            await register_infraction(
                user_id=message.author.id,
                infraction_type="aviso",
                reason=f"Uso de palavra proibida: '{palavra_censurada}'",
                moderator_id=self.bot.user.id if self.bot.user else IMPERADOR_ID,
            )
        except Exception:
            pass

        embed = discord.Embed(
            title="🚫 Palavra Proibida Detectada",
            description=(
                f"{message.author.mention}, sua mensagem foi removida por conter vocabulário proibido no Império.\n\n"
                f"**Termo interceptado:** `||{palavra_censurada}||`\n"
                f"*Mantenha a compostura para evitar penalidades severas.*\n\n{SEP}"
            ),
            color=0x8B0000,
        )
        embed.set_footer(text=RODAPE_IMPERIAL)
        try:
            aviso_msg = await message.channel.send(embed=embed)
            await asyncio.sleep(6)
            await aviso_msg.delete()
        except Exception:
            pass

        return True

    async def handle_proibir_palavra(self, message, args):
        """Adiciona uma ou mais palavras à lista de proibições do servidor."""
        perms = getattr(message.author, "guild_permissions", None)
        if not (message.author.id == IMPERADOR_ID or (perms and (perms.manage_messages or perms.administrator))):
            await message.channel.send(embed=embed_imperial("🚫", "Apenas moderadores podem proibir palavras.", 0x6B0000))
            return
        if not args:
            await message.channel.send(embed=embed_imperial("❓ Uso", "`tenshi proibir-palavra [palavra/termo]`", 0x2B0A3D))
            return

        termo = " ".join(args).lower().strip()
        palavras = self._carregar_palavras_proibidas(message.guild.id)
        if termo in palavras:
            await message.channel.send(embed=embed_imperial("⚠️ Já Proibida", f"O termo `{termo}` já consta na lista de palavras proibidas.", 0x9E7815))
            return

        palavras.add(termo)
        self._salvar_palavras_proibidas(message.guild.id, palavras)
        bot_logger.info(f"Palavra proibida adicionada: '{termo}' por {message.author} no servidor {message.guild.name}")
        await message.channel.send(embed=embed_imperial(
            "🛡️ Palavra Proibida Adicionada",
            f"O termo `{termo}` foi adicionado com sucesso ao filtro imperial.\n"
            f"Mensagens que contiverem essa palavra serão deletadas automaticamente.",
            0x1A5C2E
        ))

    async def handle_liberar_palavra(self, message, args):
        """Remove uma palavra da lista de proibições."""
        perms = getattr(message.author, "guild_permissions", None)
        if not (message.author.id == IMPERADOR_ID or (perms and (perms.manage_messages or perms.administrator))):
            await message.channel.send(embed=embed_imperial("🚫", "Apenas moderadores podem liberar palavras.", 0x6B0000))
            return
        if not args:
            await message.channel.send(embed=embed_imperial("❓ Uso", "`tenshi liberar-palavra [palavra/termo]`", 0x2B0A3D))
            return

        termo = " ".join(args).lower().strip()
        palavras = self._carregar_palavras_proibidas(message.guild.id)
        if termo not in palavras:
            await message.channel.send(embed=embed_imperial("⚠️ Não Encontrada", f"O termo `{termo}` não está na lista.", 0x9E7815))
            return

        palavras.remove(termo)
        self._salvar_palavras_proibidas(message.guild.id, palavras)
        bot_logger.info(f"Palavra proibida removida: '{termo}' por {message.author} no servidor {message.guild.name}")
        await message.channel.send(embed=embed_imperial(
            "🕊️ Palavra Liberada",
            f"O termo `{termo}` foi retirado do filtro imperial.",
            0x1A5C2E
        ))

    async def handle_palavras_proibidas(self, message, args):
        """Lista todas as palavras proibidas configuradas no servidor."""
        perms = getattr(message.author, "guild_permissions", None)
        if not (message.author.id == IMPERADOR_ID or (perms and (perms.manage_messages or perms.administrator))):
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para consultar palavras proibidas.", 0x6B0000))
            return

        palavras = self._carregar_palavras_proibidas(message.guild.id)
        if not palavras:
            await message.channel.send(embed=embed_imperial("📋 Palavras Proibidas", "Nenhuma palavra proibida cadastrada neste servidor.", 0x3D3D3D))
            return

        lista = "\n".join(f"• `{p}`" for p in sorted(list(palavras)))
        await message.channel.send(embed=embed_imperial(
            "📋 Palavras Proibidas do Servidor",
            f"Total de termos monitorados: **{len(palavras)}**\n\n{lista}",
            0x2B0A3D
        ))

    async def handle_ban(self, message, args):
        tem_perm = False
        try:
            tem_perm = message.author.guild_permissions.ban_members or message.author.guild_permissions.administrator
        except Exception:
            pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão imperial para banir membros.", 0x6B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓ Uso Correto", "`tenshi ban @usuario [motivo]`", 0x2B0A3D))
            return

        alvo = message.mentions[0]
        if alvo.id == IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "O Imperador está acima de qualquer banimento mortal.", 0x6B0000))
            return
        if alvo.id == message.author.id:
            await message.channel.send(embed=embed_imperial("🚫", "Não podes banir a ti mesmo.", 0x6B0000))
            return

        # Verificação de hierarquia de cargos
        if message.author.id != IMPERADOR_ID and alvo.top_role >= message.author.top_role:
            await message.channel.send(embed=embed_imperial("🚫", "Não podes banir alguém com cargo superior ou igual ao seu.", 0x6B0000))
            return

        motivo_tokens = [a for a in args if not a.startswith("<@")]
        motivo = " ".join(motivo_tokens).strip() or "Banido por decreto imperial"

        # Notificar alvo via DM antes do banimento
        try:
            dm_embed = discord.Embed(
                title="⚖️ BANIMENTO IMPERIAL",
                description=f"Você foi banido do servidor **{message.guild.name}**.\n**Motivo:** {motivo}",
                color=0x8B0000
            )
            dm_embed.set_footer(text=RODAPE_IMPERIAL)
            await alvo.send(embed=dm_embed)
        except Exception:
            pass

        try:
            await message.guild.ban(alvo, reason=f"{motivo} (Por: {message.author})")
            await register_infraction(alvo.id, "ban", motivo, message.author.id)
            bot_logger.command(str(message.author), message.author.id, f"ban {alvo}", str(message.guild.name), True)

            embed = discord.Embed(
                title="⚖️ BANIMENTO IMPERIAL",
                description=(
                    f"**Alvo:** {alvo.mention} (`{alvo.id}`)\n"
                    f"**Moderador:** {message.author.mention}\n"
                    f"**Motivo:** *{motivo}*\n\n"
                    f"{SEP}\n*O decreto foi executado e registrado nas crônicas imperiais.*"
                ),
                color=0x8B0000
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Não possuo permissão ou hierarquia para banir este usuário.", 0x6B0000))
        except Exception as exc:
            bot_logger.error(f"Erro ao executar ban de {alvo.id}: {exc}", exc=exc)
            await message.channel.send(embed=embed_imperial("❌", f"Erro ao aplicar banimento: {str(exc)[:100]}", 0x6B0000))

    async def handle_kick(self, message, args):
        tem_perm = False
        try:
            tem_perm = message.author.guild_permissions.kick_members or message.author.guild_permissions.administrator
        except Exception:
            pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão imperial para expulsar membros.", 0x6B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓ Uso Correto", "`tenshi kick @usuario [motivo]`", 0x2B0A3D))
            return

        alvo = message.mentions[0]
        if alvo.id == IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "O Imperador não pode ser expulso.", 0x6B0000))
            return
        if alvo.id == message.author.id:
            await message.channel.send(embed=embed_imperial("🚫", "Não podes expulsar a ti mesmo.", 0x6B0000))
            return

        if message.author.id != IMPERADOR_ID and alvo.top_role >= message.author.top_role:
            await message.channel.send(embed=embed_imperial("🚫", "Não podes expulsar alguém com cargo superior ou igual ao seu.", 0x6B0000))
            return

        motivo_tokens = [a for a in args if not a.startswith("<@")]
        motivo = " ".join(motivo_tokens).strip() or "Expulso por decreto imperial"

        try:
            dm_embed = discord.Embed(
                title="👢 EXPULSÃO IMPERIAL",
                description=f"Você foi expulso de **{message.guild.name}**.\n**Motivo:** {motivo}",
                color=0xFF8C00
            )
            dm_embed.set_footer(text=RODAPE_IMPERIAL)
            await alvo.send(embed=dm_embed)
        except Exception:
            pass

        try:
            await message.guild.kick(alvo, reason=f"{motivo} (Por: {message.author})")
            await register_infraction(alvo.id, "kick", motivo, message.author.id)
            bot_logger.command(str(message.author), message.author.id, f"kick {alvo}", str(message.guild.name), True)

            embed = discord.Embed(
                title="👢 EXPULSÃO IMPERIAL",
                description=(
                    f"**Alvo:** {alvo.mention} (`{alvo.id}`)\n"
                    f"**Moderador:** {message.author.mention}\n"
                    f"**Motivo:** *{motivo}*\n\n{SEP}"
                ),
                color=0xFF8C00
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Não possuo permissão ou hierarquia para expulsar este usuário.", 0x6B0000))
        except Exception as exc:
            bot_logger.error(f"Erro ao executar kick: {exc}", exc=exc)
            await message.channel.send(embed=embed_imperial("❌", f"Erro na expulsão: {str(exc)[:100]}", 0x6B0000))

    async def handle_mute(self, message, args):
        tem_perm = False
        try:
            tem_perm = message.author.guild_permissions.moderate_members or message.author.guild_permissions.administrator
        except Exception:
            pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão imperial para silenciar membros.", 0x6B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial(
                "❓ Uso Correto",
                "`tenshi mute @usuario [tempo] [motivo]`\n\n"
                "*Exemplos:*\n"
                "• `tenshi mute @usuario 10m flood`\n"
                "• `tenshi mute @usuario 2h desrespeito`\n"
                "• `tenshi mute @usuario 1d violação grave`",
                0x2B0A3D
            ))
            return

        alvo = message.mentions[0]
        if alvo.id == IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "O Imperador não pode ser silenciado.", 0x6B0000))
            return
        if alvo.id == message.author.id:
            await message.channel.send(embed=embed_imperial("🚫", "Não podes silenciar a ti mesmo.", 0x6B0000))
            return

        if message.author.id != IMPERADOR_ID and alvo.top_role >= message.author.top_role:
            await message.channel.send(embed=embed_imperial("🚫", "Não podes silenciar alguém com cargo superior ou igual ao seu.", 0x6B0000))
            return

        resto = [a for a in args if not a.startswith("<@")]
        minutos = 30
        motivo_partes = []

        if resto:
            primeiro = resto[0].lower()
            if primeiro.endswith("m") and primeiro[:-1].isdigit():
                minutos = int(primeiro[:-1])
                resto = resto[1:]
            elif primeiro.endswith("h") and primeiro[:-1].isdigit():
                minutos = int(primeiro[:-1]) * 60
                resto = resto[1:]
            elif primeiro.endswith("d") and primeiro[:-1].isdigit():
                minutos = int(primeiro[:-1]) * 1440
                resto = resto[1:]
            elif primeiro.isdigit():
                minutos = int(primeiro)
                resto = resto[1:]

        # Limite máximo da API do Discord é 28 dias
        minutos = max(1, min(minutos, 40320))
        motivo = " ".join(resto).strip() or "Silenciado por decreto imperial"

        try:
            fim = discord.utils.utcnow() + timedelta(minutes=minutos)
            await alvo.timeout(fim, reason=f"{motivo} (Por: {message.author})")
            await register_infraction(alvo.id, "mute", f"{motivo} ({minutos}m)", message.author.id, fim.isoformat())
            bot_logger.command(str(message.author), message.author.id, f"mute {alvo} {minutos}m", str(message.guild.name), True)

            tempo_formatado = f"{minutos} minutos" if minutos < 60 else f"{minutos//60} hora(s)"
            embed = discord.Embed(
                title="🔇 SILÊNCIO IMPERIAL",
                description=(
                    f"**Alvo:** {alvo.mention} (`{alvo.id}`)\n"
                    f"**Duração:** {tempo_formatado}\n"
                    f"**Moderador:** {message.author.mention}\n"
                    f"**Motivo:** *{motivo}*\n\n{SEP}"
                ),
                color=0x4B0082
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Não possuo permissão ou hierarquia para silenciar este usuário.", 0x6B0000))
        except Exception as exc:
            bot_logger.error(f"Erro ao executar mute: {exc}", exc=exc)
            await message.channel.send(embed=embed_imperial("❌", f"Erro no silenciamento: {str(exc)[:100]}", 0x6B0000))

    async def handle_aviso(self, message, args):
        """Registra uma advertência/aviso formal para um usuário."""
        perms = getattr(message.author, "guild_permissions", None)
        if not (message.author.id == IMPERADOR_ID or (perms and (perms.moderate_members or perms.manage_messages))):
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão imperial para aplicar avisos.", 0x6B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓ Uso Correto", "`tenshi aviso @usuario [motivo]`", 0x2B0A3D))
            return

        alvo = message.mentions[0]
        if alvo.id == IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "O Imperador não recebe advertências mortais.", 0x6B0000))
            return

        motivo_tokens = [a for a in args if not a.startswith("<@")]
        motivo = " ".join(motivo_tokens).strip() or "Conduta imprópria"

        try:
            await register_infraction(alvo.id, "aviso", motivo, message.author.id)
            todas = await get_infractions(alvo.id)
            total_avisos = sum(1 for i in todas if i.get("type") == "aviso")
            bot_logger.command(str(message.author), message.author.id, f"aviso {alvo}", str(message.guild.name), True)

            embed = discord.Embed(
                title="⚠️ ADVERTÊNCIA IMPERIAL",
                description=(
                    f"**Alvo:** {alvo.mention} (`{alvo.id}`)\n"
                    f"**Moderador:** {message.author.mention}\n"
                    f"**Total de Avisos:** {total_avisos}\n"
                    f"**Motivo:** *{motivo}*\n\n"
                    f"{SEP}\n*Reincidências poderão acarretar em prisão, silêncio ou exílio perpétuo.*"
                ),
                color=0xFF6600
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except Exception as exc:
            bot_logger.error(f"Erro ao registrar aviso: {exc}", exc=exc)
            await message.channel.send(embed=embed_imperial("❌", f"Falha ao registrar advertência: {str(exc)[:100]}", 0x6B0000))

    async def handle_clear(self, message, args):
        tem_perm = False
        try:
            tem_perm = message.author.guild_permissions.manage_messages or message.author.guild_permissions.administrator
        except Exception:
            pass
        if not tem_perm and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão imperial para apagar mensagens.", 0x6B0000))
            return

        qtd = 10
        for a in args:
            if a.isdigit():
                qtd = min(int(a), 100)
                break
        try:
            del_count = await message.channel.purge(limit=qtd + 1)
            msg = await message.channel.send(embed=embed_imperial("🧹 Purificação Imperial", f"**{len(del_count)-1}** mensagens removidas das crônicas do canal.", 0x006400))
            await asyncio.sleep(4)
            await msg.delete()
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Não tenho permissão para apagar mensagens neste canal.", 0x6B0000))
        except Exception as exc:
            bot_logger.error(f"Erro no purge: {exc}", exc=exc)

    async def handle_unmute(self, message, args):
        perms = getattr(message.author, "guild_permissions", None)
        if not (message.author.id == IMPERADOR_ID or (perms and (perms.moderate_members or perms.administrator))):
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para remover silêncios.", 0x6B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "`tenshi unmute @usuario`", 0x2B0A3D))
            return
        alvo = message.mentions[0]
        try:
            await alvo.timeout(None, reason=f"Silêncio revogado por {message.author}")
            bot_logger.command(str(message.author), message.author.id, f"unmute {alvo}", str(message.guild.name), True)
            await message.channel.send(embed=embed_imperial("🔊 Silêncio Revogado", f"{alvo.mention} teve a voz restabelecida no Império.", 0x006400))
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Não tenho permissão ou hierarquia suficiente.", 0x6B0000))
        except Exception as exc:
            await message.channel.send(embed=embed_imperial("❌", f"Erro: {str(exc)[:100]}", 0x6B0000))

    async def handle_unban(self, message, args):
        perms = getattr(message.author, "guild_permissions", None)
        if not (message.author.id == IMPERADOR_ID or (perms and (perms.ban_members or perms.administrator))):
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para revogar banimentos.", 0x6B0000))
            return
        if not args or not args[0].isdigit():
            await message.channel.send(embed=embed_imperial("❓", "`tenshi unban [ID do usuário]`", 0x2B0A3D))
            return
        alvo = discord.Object(id=int(args[0]))
        try:
            entrada = await message.guild.fetch_ban(alvo)
            await message.guild.unban(entrada.user, reason=f"Anistia concedida por {message.author}")
            bot_logger.command(str(message.author), message.author.id, f"unban {args[0]}", str(message.guild.name), True)
            await message.channel.send(embed=embed_imperial("🕊️ Banimento Revogado", f"**{entrada.user}** foi perdoado e pode retornar ao Império.", 0x006400))
        except discord.NotFound:
            await message.channel.send(embed=embed_imperial("❌", "Esse ID não consta na lista de banidos deste servidor.", 0x6B0000))
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Não tenho permissão para desbanir membros.", 0x6B0000))
        except Exception as exc:
            await message.channel.send(embed=embed_imperial("❌", f"Erro ao desbanir: {str(exc)[:100]}", 0x6B0000))

    async def handle_slowmode(self, message, args):
        perms = getattr(message.author, "guild_permissions", None)
        if not (message.author.id == IMPERADOR_ID or (perms and (perms.manage_channels or perms.administrator))):
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para alterar o modo lento.", 0x6B0000))
            return
        if not args or not args[0].isdigit():
            await message.channel.send(embed=embed_imperial("❓", "`tenshi slowmode [segundos]` (0 desativa)", 0x2B0A3D))
            return
        segundos = min(int(args[0]), 21600)
        try:
            await message.channel.edit(slowmode_delay=segundos, reason=f"Alterado por {message.author}")
            estado = "desativado" if segundos == 0 else f"definido em **{segundos}s**"
            await message.channel.send(embed=embed_imperial("⏱️ Modo Lento", f"Modo lento {estado} com sucesso.", 0x4B0082))
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Não tenho permissão para editar este canal.", 0x6B0000))

