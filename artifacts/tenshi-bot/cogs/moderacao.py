import discord
from discord.ext import commands
from utils import embed_imperial, IMPERADOR_ID


class Moderacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_ban(self, message, args):
        if not message.author.guild_permissions.ban_members:
            await message.channel.send(embed=embed_imperial("🚫 Sem Permissão", "*Os guardas imperiais bloqueiam sua passagem...*\nVocê não possui autoridade para banir.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓ Erro", "Mencione o usuário: `Tenshi, ban @usuario [motivo]`", 0x8B0000))
            return

        alvo = message.mentions[0]
        motivo_parts = [a for a in args if not a.startswith("<@")]
        motivo = " ".join(motivo_parts) if motivo_parts else "Decreto Imperial sem motivo declarado"

        try:
            await alvo.send(embed=embed_imperial(
                "⚖️ Decreto Imperial de Banimento",
                f"*O selo imperial foi aposto em seu pergaminho...*\n\nVocê foi banido do Império de Tenshi.\n**Motivo:** {motivo}",
                0x8B0000
            ))
        except Exception:
            pass

        try:
            await message.guild.ban(alvo, reason=motivo)
            embed = discord.Embed(
                title="⚖️ DECRETO IMPERIAL — BANIMENTO",
                description=f"*O nome de {alvo.display_name} foi riscado dos Pergaminhos Imperiais para sempre...*",
                color=0x8B0000
            )
            embed.add_field(name="👤 Banido", value=alvo.display_name, inline=True)
            embed.add_field(name="⚖️ Motivo", value=motivo, inline=True)
            embed.add_field(name="🏛️ Autoridade", value=message.author.display_name, inline=True)
            embed.set_footer(text="⚖️ O Império de Tenshi não tolera a desonra")
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌ Falha", "Não possuo permissão para banir este usuário.", 0x8B0000))

    async def handle_kick(self, message, args):
        if not message.author.guild_permissions.kick_members:
            await message.channel.send(embed=embed_imperial("🚫 Sem Permissão", "Você não possui autoridade para expulsar membros.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓ Erro", "Mencione o usuário: `Tenshi, kick @usuario [motivo]`", 0x8B0000))
            return

        alvo = message.mentions[0]
        motivo_parts = [a for a in args if not a.startswith("<@")]
        motivo = " ".join(motivo_parts) if motivo_parts else "Expulso por decreto imperial"

        try:
            await message.guild.kick(alvo, reason=motivo)
            embed = discord.Embed(
                title="👢 DECRETO IMPERIAL — EXPULSÃO",
                description=f"*{alvo.display_name} foi escoltado para fora dos portões imperiais pelos guardas...*",
                color=0xFF8C00
            )
            embed.add_field(name="👤 Expulso", value=alvo.display_name, inline=True)
            embed.add_field(name="⚖️ Motivo", value=motivo, inline=True)
            embed.set_footer(text="🏛️ Os portões de Tenshi permanecem selados para os indignos")
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌ Falha", "Não possuo permissão para expulsar este usuário.", 0x8B0000))

    async def handle_mute(self, message, args):
        if not message.author.guild_permissions.moderate_members:
            await message.channel.send(embed=embed_imperial("🚫 Sem Permissão", "Você não possui autoridade para silenciar membros.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓ Erro", "Mencione o usuário: `Tenshi, mute @usuario`", 0x8B0000))
            return

        alvo = message.mentions[0]

        mute_role = discord.utils.get(message.guild.roles, name="Silenciado")
        if not mute_role:
            try:
                mute_role = await message.guild.create_role(name="Silenciado", reason="Criado pelo Bot Tenshi")
                for canal in message.guild.channels:
                    await canal.set_permissions(mute_role, send_messages=False, speak=False)
            except Exception:
                await message.channel.send(embed=embed_imperial("❌ Erro", "Não foi possível criar o cargo de silêncio.", 0x8B0000))
                return

        try:
            await alvo.add_roles(mute_role)
            embed = discord.Embed(
                title="🔇 DECRETO IMPERIAL — SILÊNCIO",
                description=f"*A voz de {alvo.display_name} foi selada pelos magos imperiais...*\n\nSeus lábios estão lacrados nos domínios de Tenshi.",
                color=0x4B0082
            )
            embed.add_field(name="👤 Silenciado", value=alvo.display_name, inline=True)
            embed.add_field(name="🏛️ Autoridade", value=message.author.display_name, inline=True)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌ Falha", "Não possuo permissão para silenciar este usuário.", 0x8B0000))

    async def handle_clear(self, message, args):
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send(embed=embed_imperial("🚫 Sem Permissão", "Você não possui autoridade para limpar mensagens.", 0x8B0000))
            return

        quantidade = 10
        for a in args:
            if a.isdigit():
                quantidade = min(int(a), 100)
                break

        try:
            deletadas = await message.channel.purge(limit=quantidade + 1)
            confirmacao = await message.channel.send(embed=embed_imperial(
                "🧹 Purificação Imperial",
                f"*{len(deletadas) - 1} mensagens foram varridas pelo vento imperial...*\n\nO canal foi purificado por ordem do Império.",
                0x006400
            ))
            import asyncio
            await asyncio.sleep(5)
            await confirmacao.delete()
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌ Falha", "Não possuo permissão para deletar mensagens.", 0x8B0000))

    async def handle_decreto(self, message, args):
        if message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫 Proibido", "*Apenas o Imperador Alloy pode emitir decretos imperiais.*", 0x8B0000))
            return

        if not args:
            await message.channel.send(embed=embed_imperial("❓ Erro", "Inclua a mensagem do decreto: `Tenshi, decreto [mensagem]`", 0x8B0000))
            return

        mensagem_decreto = " ".join(args)

        try:
            await message.delete()
        except Exception:
            pass

        embed = discord.Embed(
            title="📜 ⚜️ DECRETO IMPERIAL DE TENSHI ⚜️ 📜",
            description=f"*Os sinos dourados do palácio imperial ecoam por todo o reino...*\n\n"
                       f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                       f"**{mensagem_decreto}**\n\n"
                       f"━━━━━━━━━━━━━━━━━━━━━━",
            color=0xFFD700
        )
        embed.set_author(name="⚜️ Imperador Alloy — Soberano Supremo de Tenshi", icon_url=message.author.display_avatar.url)
        embed.set_footer(text="📜 Pelo poder eterno do trono imperial — que todos os súditos obedeçam")
        await message.channel.send(embed=embed)
