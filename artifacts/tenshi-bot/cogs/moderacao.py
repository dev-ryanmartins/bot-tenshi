import discord
import asyncio
from utils import embed_imperial, IMPERADOR_ID


class Moderacao:
    def __init__(self, bot):
        self.bot = bot

    async def handle_ban(self, message, args):
        if not message.author.guild_permissions.ban_members:
            await message.channel.send(embed=embed_imperial("🚫 Sem Permissão", "Você não possui autoridade para banir.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, ban @usuario [motivo]`", 0x8B0000))
            return
        alvo = message.mentions[0]
        motivo = " ".join([a for a in args if not a.startswith("<@")]) or "Decreto Imperial"
        try:
            await alvo.send(embed=embed_imperial("⚖️ Banimento", f"Você foi banido de Tenshi.\n**Motivo:** {motivo}", 0x8B0000))
        except Exception:
            pass
        try:
            await message.guild.ban(alvo, reason=motivo)
            embed = discord.Embed(title="⚖️ DECRETO IMPERIAL — BANIMENTO", color=0x8B0000)
            embed.add_field(name="👤 Banido", value=alvo.display_name, inline=True)
            embed.add_field(name="⚖️ Motivo", value=motivo, inline=True)
            embed.add_field(name="🏛️ Autoridade", value=message.author.display_name, inline=True)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Sem permissão para banir.", 0x8B0000))

    async def handle_kick(self, message, args):
        if not message.author.guild_permissions.kick_members:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para expulsar.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, kick @usuario [motivo]`", 0x8B0000))
            return
        alvo = message.mentions[0]
        motivo = " ".join([a for a in args if not a.startswith("<@")]) or "Expulso por decreto"
        try:
            await message.guild.kick(alvo, reason=motivo)
            embed = discord.Embed(title="👢 DECRETO — EXPULSÃO", color=0xFF8C00)
            embed.add_field(name="👤 Expulso", value=alvo.display_name, inline=True)
            embed.add_field(name="⚖️ Motivo", value=motivo, inline=True)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Sem permissão.", 0x8B0000))

    async def handle_mute(self, message, args):
        if not message.author.guild_permissions.moderate_members:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para silenciar.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, mute @usuario`", 0x8B0000))
            return
        alvo = message.mentions[0]
        mute_role = discord.utils.get(message.guild.roles, name="Silenciado Imperial")
        if not mute_role:
            try:
                mute_role = await message.guild.create_role(name="Silenciado Imperial")
                for canal in message.guild.channels:
                    await canal.set_permissions(mute_role, send_messages=False, speak=False)
            except Exception:
                await message.channel.send(embed=embed_imperial("❌", "Não foi possível criar o cargo de silêncio.", 0x8B0000))
                return
        try:
            await alvo.add_roles(mute_role)
            await message.channel.send(embed=embed_imperial("🔇 Silenciado", f"*{alvo.display_name}* foi silenciado pelos magos imperiais.", 0x4B0082))
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Sem permissão.", 0x8B0000))

    async def handle_clear(self, message, args):
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send(embed=embed_imperial("🚫", "Sem permissão para limpar mensagens.", 0x8B0000))
            return
        quantidade = 10
        for a in args:
            if a.isdigit():
                quantidade = min(int(a), 100)
                break
        try:
            deletadas = await message.channel.purge(limit=quantidade + 1)
            msg = await message.channel.send(embed=embed_imperial("🧹 Purificação Imperial", f"**{len(deletadas)-1}** mensagens removidas.", 0x006400))
            await asyncio.sleep(5)
            await msg.delete()
        except discord.Forbidden:
            await message.channel.send(embed=embed_imperial("❌", "Sem permissão.", 0x8B0000))

    async def handle_decreto(self, message, args):
        if message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫", "Apenas o Imperador Alloy emite decretos.", 0x8B0000))
            return
        if not args:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, decreto [mensagem]`", 0x8B0000))
            return
        mensagem_decreto = " ".join(args)
        try:
            await message.delete()
        except Exception:
            pass
        embed = discord.Embed(
            title="📜 ⚜️ DECRETO IMPERIAL DE TENSHI ⚜️ 📜",
            description=f"━━━━━━━━━━━━━━━━━━━━━━\n\n**{mensagem_decreto}**\n\n━━━━━━━━━━━━━━━━━━━━━━",
            color=0xFFD700
        )
        embed.set_author(name="⚜️ Imperador Alloy — Soberano Supremo de Tenshi", icon_url=message.author.display_avatar.url)
        embed.set_footer(text="📜 Pelo poder eterno do trono imperial — que todos obedeçam")
        await message.channel.send(embed=embed)
