"""
Cog de Infrações — Gerencia notas, avisos e histórico disciplinar.
Comandos:
  - tenshi notas [usuário]
  - tenshi info [usuário]
"""

from datetime import UTC, datetime

import discord
from database import get_user
from database_infractions import (
    get_infractions_summary,
    get_user_infractions,
)
from utils import RODAPE_IMPERIAL, SEP, embed_imperial


class Infractions:
    """Gerencia infrações, avisos e histórico disciplinar de usuários."""

    def __init__(self, bot):
        self.bot = bot

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

        # Recuperar resumo de infrações
        summary = await get_infractions_summary(target_user.id)
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

        embed.add_field(
            name="⚖️ Histórico Disciplinar",
            value=(
                f"**Avisos Ativos:** {avisos_total}\n"
                f"**Silências Ativos:** {mutes_total}\n"
                f"**Banimentos Ativos:** {bans_total}\n"
                f"**Total de Infrações:** {summary['total']}"
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
