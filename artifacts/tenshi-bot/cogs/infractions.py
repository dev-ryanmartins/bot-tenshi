"""
Cog de Infrações — Gerencia notas, avisos e histórico disciplinar.
Comandos:
  - tenshi notas [usuário]
  - tenshi info [usuário]
"""

from datetime import UTC, datetime
from types import SimpleNamespace

import discord
from discord import app_commands
from discord.ext import commands
from database import get_user
from database_infractions import (
    database,
    get_infractions_summary,
    get_user_infractions,
    register_infraction,
)
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, SEP, embed_imperial


class _InteractionChannel:
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction

    async def send(self, *args, **kwargs):
        if self.interaction.response.is_done():
            return await self.interaction.followup.send(*args, **kwargs)
        return await self.interaction.response.send_message(*args, **kwargs)


class Infractions(commands.Cog):
    """Gerencia infrações, avisos e histórico disciplinar de usuários."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _pode_moderar(member: discord.Member) -> bool:
        if member.id == IMPERADOR_ID:
            return True
        perms = getattr(member, "guild_permissions", None)
        return bool(perms and (perms.manage_messages or perms.moderate_members))

    async def handle_nota(self, message: discord.Message, args: list):
        """Salva uma nota interna de moderação vinculada a um usuário."""
        if not self._pode_moderar(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Sem permissão", "Este comando é restrito à moderação.", 0x8B0000))
            return
        if not message.mentions or len(args) < 2:
            await message.channel.send(embed=embed_imperial("📋 Uso", "`tenshi nota @usuario [texto]`", 0x8B4513))
            return
        alvo = message.mentions[0]
        texto = " ".join(arg for arg in args if not arg.startswith("<@" )).strip()
        if not texto:
            await message.channel.send(embed=embed_imperial("📋 Texto obrigatório", "Informe o conteúdo da nota.", 0x8B4513))
            return
        note_id = await database.add_note(alvo.id, texto[:1500], message.author.id)
        await message.channel.send(embed=embed_imperial(
            "✅ Nota registrada",
            f"Nota `#{note_id}` salva para {alvo.mention}.\n**Texto:** {texto[:1000]}",
            0x1A5C2E,
        ))

    async def handle_aviso(self, message: discord.Message, args: list):
        """Registra um aviso disciplinar no histórico SQLite."""
        if not self._pode_moderar(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Sem permissão", "Este comando é restrito à moderação.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("⚠️ Uso", "`tenshi aviso @usuario [motivo]`", 0x8B4513))
            return
        alvo = message.mentions[0]
        motivo = " ".join(arg for arg in args if not arg.startswith("<@")).strip() or "Sem motivo especificado"
        infraction_id = await register_infraction(alvo.id, "aviso", motivo[:1500], message.author.id)
        await message.channel.send(embed=embed_imperial(
            "⚠️ Aviso registrado",
            f"Aviso `#{infraction_id}` aplicado a {alvo.mention}.\n**Motivo:** {motivo[:1000]}",
            0xD97706,
        ))

    async def handle_historico(self, message: discord.Message, args: list):
        """Exibe notas internas e todas as infrações, inclusive inativas."""
        alvo = message.mentions[0] if message.mentions else message.author
        notes = await database.get_notes(alvo.id)
        infractions = await get_user_infractions(alvo.id, active_only=False)
        registros = [
            (item["created_at"], "📝 Nota", item["texto"], item.get("moderator_id"), True)
            for item in notes
        ] + [
            (
                item["created_at"], self._format_infraction_type(item["infraction_type"]),
                item.get("reason") or "Sem motivo especificado", item.get("moderator_id"),
                bool(item.get("is_active")),
            )
            for item in infractions
        ]
        registros.sort(key=lambda item: item[0], reverse=True)
        embed = discord.Embed(
            title=f"📚 Histórico — {alvo.display_name}",
            description=f"Notas e ocorrências registradas para {alvo.mention}.",
            color=0x8B4513,
        )
        if not registros:
            embed.description = f"{alvo.mention} não possui notas ou avisos registrados."
        for index, (data, tipo, texto, moderador, ativo) in enumerate(registros[:20], 1):
            status = "ativo" if ativo else "encerrado"
            embed.add_field(
                name=f"{index}. {tipo} • {self._format_date(data)}",
                value=f"{texto[:700]}\n**Responsável:** <@{moderador}> • **Status:** {status}",
                inline=False,
            )
        if len(registros) > 20:
            embed.set_footer(text=f"Exibindo 20 de {len(registros)} registros • {RODAPE_IMPERIAL}")
        else:
            embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    def _mensagem_interacao(self, interaction: discord.Interaction, usuario: discord.Member):
        return SimpleNamespace(
            author=interaction.user,
            channel=_InteractionChannel(interaction),
            guild=interaction.guild,
            mentions=[usuario],
        )

    @app_commands.command(name="nota", description="Registra uma nota interna de moderação.")
    async def slash_nota(self, interaction: discord.Interaction, usuario: discord.Member, texto: str):
        await self.handle_nota(self._mensagem_interacao(interaction, usuario), [usuario.mention, texto])

    @app_commands.command(name="aviso", description="Registra um aviso disciplinar.")
    async def slash_aviso(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str):
        await self.handle_aviso(self._mensagem_interacao(interaction, usuario), [usuario.mention, motivo])

    @app_commands.command(name="historico", description="Exibe notas e avisos de um usuário.")
    async def slash_historico(self, interaction: discord.Interaction, usuario: discord.Member):
        await self.handle_historico(self._mensagem_interacao(interaction, usuario), [usuario.mention])

    @app_commands.command(name="info", description="Exibe entrada no servidor e histórico disciplinar.")
    async def slash_info(self, interaction: discord.Interaction, usuario: discord.Member):
        await self.handle_info(self._mensagem_interacao(interaction, usuario), [usuario.mention])

    def _format_infraction_type(self, infraction_type: str) -> str:
        """Formata o tipo de infração para exibição."""
        tipo_map = {
            "aviso": "⚠️ Aviso",
            "mute": "🔇 Silêncio",
            "ban": "🚫 Banimento",
        }
        return tipo_map.get(infraction_type, f"❓ {infraction_type}")

    def _format_date(self, date_str: str) -> str:
        """Formata uma data ISO para formato amigável."""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d/%m/%Y às %H:%M")
        except Exception:
            return date_str

    async def handle_notas(self, message: discord.Message, args: list):
        """
        Comando: tenshi notas [usuário]
        Exibe todas as infrações registradas de um usuário.
        """
        if not args:
            embed = embed_imperial(
                title="📋 Notas de Conduta",
                descricao=(
                    "**Uso:** `tenshi notas @usuário` ou `tenshi notas ID`\n\n"
                    "Exibe o histórico de infrações do usuário.\n"
                    f"{SEP}"
                ),
                cor=0x8B4513,
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return

        # Resolver menção ou ID
        target_user = None
        if message.mentions:
            target_user = message.mentions[0]
        else:
            try:
                user_id = int(args[0])
                try:
                    target_user = await self.bot.fetch_user(user_id)
                except discord.NotFound:
                    embed = embed_imperial(
                        title="❌ Usuário não encontrado",
                        descricao=f"Não consegui encontrar o usuário com ID `{user_id}`.",
                        cor=0xFF0000,
                    )
                    embed.set_footer(text=RODAPE_IMPERIAL)
                    await message.channel.send(embed=embed)
                    return
            except ValueError:
                embed = embed_imperial(
                    title="❌ ID inválido",
                    descricao="Por favor, forneça uma menção @usuário ou um ID numérico.",
                    cor=0xFF0000,
                )
                embed.set_footer(text=RODAPE_IMPERIAL)
                await message.channel.send(embed=embed)
                return

        if not target_user:
            embed = embed_imperial(
                title="❌ Usuário inválido",
                descricao="Não consegui resolver o usuário.",
                cor=0xFF0000,
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return

        # Recuperar infrações
        infractions = await get_user_infractions(target_user.id, active_only=True)

        if not infractions:
            embed = embed_imperial(
                title="✅ Registro Limpo",
                descricao=(
                    f"{target_user.mention} possui um registro disciplinar impecável.\n"
                    "Sem infrações ativas registradas.\n"
                    f"{SEP}"
                ),
                cor=0x00AA00,
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return

        # Construir Embed com infrações
        embed = discord.Embed(
            title="📋 Notas de Conduta",
            description=(
                f"**Usuário:** {target_user.mention}\n"
                f"**ID:** `{target_user.id}`\n"
                f"**Total de Infrações Ativas:** `{len(infractions)}`\n"
                f"{SEP}\n"
            ),
            color=0x8B4513,
        )

        for i, infraction in enumerate(infractions, 1):
            tipo = self._format_infraction_type(infraction["infraction_type"])
            data = self._format_date(infraction["created_at"])
            motivo = infraction["reason"] or "Sem motivo especificado"
            moderador_id = infraction["moderator_id"]

            moderador_str = ""
            if moderador_id:
                try:
                    mod = await self.bot.fetch_user(moderador_id)
                    moderador_str = f"**Moderador:** {mod.name}\n"
                except discord.NotFound:
                    moderador_str = f"**Moderador ID:** `{moderador_id}`\n"

            validade = ""
            if infraction["expires_at"]:
                data_exp = self._format_date(infraction["expires_at"])
                validade = f"**Validade:** {data_exp}\n"

            field_value = (
                f"**Data:** {data}\n"
                f"{moderador_str}"
                f"{validade}"
                f"**Motivo:** {motivo}\n"
                f"**ID:** `{infraction['id']}`"
            )

            embed.add_field(
                name=f"{i}. {tipo}",
                value=field_value,
                inline=False,
            )

        embed.set_footer(text=RODAPE_IMPERIAL)
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else "")

        # Dividir em múltiplos embeds se necessário
        if len(embed.fields) > 10:
            # Enviar primeiro embed
            await message.channel.send(embed=embed)

            # Criar embeds adicionais
            remaining = infractions[10:]
            idx = 11
            while remaining:
                new_embed = discord.Embed(
                    title="📋 Notas de Conduta (continuação)",
                    description=f"**Usuário:** {target_user.mention}",
                    color=0x8B4513,
                )

                for infraction in remaining[:10]:
                    tipo = self._format_infraction_type(infraction["infraction_type"])
                    data = self._format_date(infraction["created_at"])
                    motivo = infraction["reason"] or "Sem motivo especificado"

                    field_value = (
                        f"**Data:** {data}\n"
                        f"**Motivo:** {motivo}\n"
                        f"**ID:** `{infraction['id']}`"
                    )

                    new_embed.add_field(
                        name=f"{idx}. {tipo}",
                        value=field_value,
                        inline=False,
                    )
                    idx += 1

                new_embed.set_footer(text=RODAPE_IMPERIAL)
                await message.channel.send(embed=new_embed)

                remaining = remaining[10:]
        else:
            await message.channel.send(embed=embed)

    async def handle_info(self, message: discord.Message, args: list):
        """
        Comando: tenshi info [usuário]
        Exibe informações do usuário incluindo histórico e tempo de conta.
        """
        if not args:
            embed = embed_imperial(
                title="ℹ️ Informações de Usuário",
                descricao=(
                    "**Uso:** `tenshi info @usuário` ou `tenshi info ID`\n\n"
                    "Exibe tempo de conta, avisos e histórico.\n"
                    f"{SEP}"
                ),
                cor=0x4169E1,
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return

        # Resolver menção ou ID
        target_user = None
        if message.mentions:
            target_user = message.mentions[0]
        else:
            try:
                user_id = int(args[0])
                try:
                    target_user = await self.bot.fetch_user(user_id)
                except discord.NotFound:
                    embed = embed_imperial(
                        title="❌ Usuário não encontrado",
                        descricao=f"Não consegui encontrar o usuário com ID `{user_id}`.",
                        cor=0xFF0000,
                    )
                    embed.set_footer(text=RODAPE_IMPERIAL)
                    await message.channel.send(embed=embed)
                    return
            except ValueError:
                embed = embed_imperial(
                    title="❌ ID inválido",
                    descricao="Por favor, forneça uma menção @usuário ou um ID numérico.",
                    cor=0xFF0000,
                )
                embed.set_footer(text=RODAPE_IMPERIAL)
                await message.channel.send(embed=embed)
                return

        if not target_user:
            embed = embed_imperial(
                title="❌ Usuário inválido",
                descricao="Não consegui resolver o usuário.",
                cor=0xFF0000,
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
            return

        # Calcular tempo de conta
        agora = datetime.now(UTC).replace(tzinfo=None)
        criado_em = target_user.created_at.replace(tzinfo=None)
        diferenca = agora - criado_em

        anos = diferenca.days // 365
        meses = (diferenca.days % 365) // 30
        dias = diferenca.days % 30

        tempo_conta = f"{anos} ano(s), {meses} mês(es) e {dias} dia(s)"
        criado_em_str = criado_em.strftime("%d/%m/%Y às %H:%M")

        # Recuperar resumo de infrações. O total inclui registros já encerrados.
        summary = await get_infractions_summary(target_user.id)
        todas_infracoes = await get_user_infractions(target_user.id, active_only=False)
        avisos_total = summary["avisos"]
        mutes_total = summary["mutes"]
        bans_total = summary["bans"]

        # Criar embed
        embed = discord.Embed(
            title="ℹ️ Informações de Usuário",
            description=(
                f"**{target_user.mention}**\n"
                f"**ID:** `{target_user.id}`\n"
                f"{SEP}"
            ),
            color=0x4169E1,
        )

        embed.add_field(
            name="📅 Tempo de Conta",
            value=(
                f"**Criada em:** {criado_em_str}\n"
                f"**Tempo decorrido:** {tempo_conta}"
            ),
            inline=False,
        )

        joined_at = getattr(target_user, "joined_at", None)
        embed.add_field(
            name="🏛️ Entrada no Servidor",
            value=(
                joined_at.strftime("%d/%m/%Y às %H:%M")
                if joined_at else "Data indisponível (usuário fora do servidor)."
            ),
            inline=False,
        )

        embed.add_field(
            name="⚖️ Histórico Disciplinar",
            value=(
                f"**Avisos Ativos:** {avisos_total}\n"
                f"**Silências Ativos:** {mutes_total}\n"
                f"**Banimentos Ativos:** {bans_total}\n"
                f"**Avisos registrados (total):** {sum(1 for i in todas_infracoes if i['infraction_type'] in {'aviso', 'warn', 'warn_manual'})}\n"
                f"**Total de infrações ativas:** {summary['total']}"
            ),
            inline=False,
        )

        # Verificar se há dados do perfil no sistema
        try:
            u_data = get_user(target_user.id)
            titulo = u_data.get("titulo", "Cidadão do Império")
            nivel = u_data.get("nivel", 1)
            xp = u_data.get("xp", 0)
            faccao = u_data.get("faccao", "Nenhuma")
            
            if not faccao or faccao == "None":
                faccao = "Nenhuma"

            embed.add_field(
                name="🎭 Perfil Imperial",
                value=(
                    f"**Título:** {titulo}\n"
                    f"**Nível:** {nivel}\n"
                    f"**Experiência:** {xp}\n"
                    f"**Facção:** {faccao}"
                ),
                inline=False,
            )
        except Exception:
            pass

        embed.set_footer(text=RODAPE_IMPERIAL)
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else "")

        await message.channel.send(embed=embed)
