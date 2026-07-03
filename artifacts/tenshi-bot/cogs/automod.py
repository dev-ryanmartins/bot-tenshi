"""Advanced Auto-Moderation System"""

import json
import os
import re
from datetime import UTC, datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands
from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial

DATA_FILE = "data/automod.json"
COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


def _load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return _create_default_config()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return _create_default_config()


def _save_data(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _create_default_config() -> dict:
    return {
        "enabled": True,
        "rules": {
            "spam": {
                "enabled": True,
                "max_messages": 10,
                "time_window": 60,
                "action": "mute"
            },
            "caps": {
                "enabled": True,
                "max_caps": 70,
                "min_length": 5,
                "action": "warn"
            },
            "links": {
                "enabled": False,
                "allowed_domains": [],
                "action": "delete"
            },
            "bad_words": {
                "enabled": True,
                "words": ["palavra1", "palavra2"],  # Placeholder
                "action": "delete"
            },
            "mentions": {
                "enabled": True,
                "max_mentions": 5,
                "action": "warn"
            }
        },
        "whitelist": {
            "users": [str(IMPERADOR_ID)],
            "roles": [],
            "channels": []
        },
        "violations": {}
    }


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_history = {}

    async def handle_automod_config(self, message, args):
        """Configura o auto-mod."""
        if not message.author.guild_permissions.administrator and message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem configurar o auto-mod.", COR_PERIGO))
            return

        if not args:
            await self._show_config(message)
            return

        action = args[0].lower()
        
        if action == "enable":
            data = _load_data()
            data["enabled"] = True
            _save_data(data)
            await message.channel.send(embed=_embed("✅ Auto-Mod Ativado", "O sistema de auto-moderação foi ativado.", COR_SUCESSO))
        
        elif action == "disable":
            data = _load_data()
            data["enabled"] = False
            _save_data(data)
            await message.channel.send(embed=_embed("✅ Auto-Mod Desativado", "O sistema de auto-moderação foi desativado.", COR_NEUTRO))
        
        elif action == "spam":
            await self._configure_spam(message, args[1:])
        
        elif action == "caps":
            await self._configure_caps(message, args[1:])
        
        elif action == "links":
            await self._configure_links(message, args[1:])
        
        elif action == "badwords":
            await self._configure_badwords(message, args[1:])
        
        elif action == "mentions":
            await self._configure_mentions(message, args[1:])
        
        elif action == "whitelist":
            await self._configure_whitelist(message, args[1:])
        
        else:
            await message.channel.send(embed=_embed("❌ Ação Inválida", "Ações disponíveis: enable, disable, spam, caps, links, badwords, mentions, whitelist", COR_NEUTRO))

    async def _show_config(self, message):
        """Mostra a configuração atual."""
        data = _load_data()
        rules = data["rules"]
        
        status = "✅ Ativado" if data["enabled"] else "❌ Desativado"
        
        linhas = [
            f"**Status:** {status}\n",
            f"📝 **Spam:** {'✅' if rules['spam']['enabled'] else '❌'} (Max: {rules['spam']['max_messages']} msgs/{rules['spam']['time_window']}s)",
            f"🔤 **Caps:** {'✅' if rules['caps']['enabled'] else '❌'} (Max: {rules['caps']['max_caps']}%)",
            f"🔗 **Links:** {'✅' if rules['links']['enabled'] else '❌'}",
            f"🚫 **Bad Words:** {'✅' if rules['bad_words']['enabled'] else '❌'} ({len(rules['bad_words']['words'])} palavras)",
            f"👥 **Mentions:** {'✅' if rules['mentions']['enabled'] else '❌'} (Max: {rules['mentions']['max_mentions']})"
        ]
        
        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("⚙️ Configuração Auto-Mod", descricao, COR_DOURADO))

    async def _configure_spam(self, message, args):
        """Configura a regra de spam."""
        data = _load_data()
        
        if not args:
            await message.channel.send(embed=_embed("📝 Configurar Spam", "Use: `tenshi automod spam [max_msgs] [tempo_segundos]`", COR_NEUTRO))
            return
        
        try:
            max_msgs = int(args[0])
            time_window = int(args[1]) if len(args) > 1 else 60
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Valores devem ser números.", COR_PERIGO))
            return
        
        data["rules"]["spam"]["max_messages"] = max_msgs
        data["rules"]["spam"]["time_window"] = time_window
        data["rules"]["spam"]["enabled"] = True
        _save_data(data)
        
        await message.channel.send(embed=_embed("✅ Spam Configurado", f"Max: {max_msgs} mensagens em {time_window} segundos.", COR_SUCESSO))

    async def _configure_caps(self, message, args):
        """Configura a regra de caps."""
        data = _load_data()
        
        if not args:
            await message.channel.send(embed=_embed("📝 Configurar Caps", "Use: `tenshi automod caps [max_porcentagem]`", COR_NEUTRO))
            return
        
        try:
            max_caps = int(args[0])
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Valor deve ser um número (0-100).", COR_PERIGO))
            return
        
        data["rules"]["caps"]["max_caps"] = max_caps
        data["rules"]["caps"]["enabled"] = True
        _save_data(data)
        
        await message.channel.send(embed=_embed("✅ Caps Configurado", f"Máximo de {max_caps}% de letras maiúsculas.", COR_SUCESSO))

    async def _configure_links(self, message, args):
        """Configura a regra de links."""
        data = _load_data()
        
        if not args:
            data["rules"]["links"]["enabled"] = not data["rules"]["links"]["enabled"]
            _save_data(data)
            status = "ativada" if data["rules"]["links"]["enabled"] else "desativada"
            await message.channel.send(embed=_embed("✅ Links", f"Regra de links {status}.", COR_SUCESSO))
            return
        
        if args[0].lower() == "add":
            domain = args[1] if len(args) > 1 else None
            if domain:
                data["rules"]["links"]["allowed_domains"].append(domain)
                data["rules"]["links"]["enabled"] = True
                _save_data(data)
                await message.channel.send(embed=_embed("✅ Domínio Adicionado", f"{domain} agora é permitido.", COR_SUCESSO))
        
        elif args[0].lower() == "remove":
            domain = args[1] if len(args) > 1 else None
            if domain and domain in data["rules"]["links"]["allowed_domains"]:
                data["rules"]["links"]["allowed_domains"].remove(domain)
                _save_data(data)
                await message.channel.send(embed=_embed("✅ Domínio Removido", f"{domain} removido da lista.", COR_SUCESSO))

    async def _configure_badwords(self, message, args):
        """Configura a regra de palavras proibidas."""
        data = _load_data()
        
        if not args:
            await message.channel.send(embed=_embed("📝 Configurar Bad Words", "Use: `tenshi automod badwords [add/remove] [palavra]`", COR_NEUTRO))
            return
        
        if args[0].lower() == "add":
            word = args[1] if len(args) > 1 else None
            if word:
                data["rules"]["bad_words"]["words"].append(word.lower())
                data["rules"]["bad_words"]["enabled"] = True
                _save_data(data)
                await message.channel.send(embed=_embed("✅ Palavra Adicionada", f"'{word}' adicionada à lista.", COR_SUCESSO))
        
        elif args[0].lower() == "remove":
            word = args[1] if len(args) > 1 else None
            if word and word.lower() in data["rules"]["bad_words"]["words"]:
                data["rules"]["bad_words"]["words"].remove(word.lower())
                _save_data(data)
                await message.channel.send(embed=_embed("✅ Palavra Removida", f"'{word}' removida da lista.", COR_SUCESSO))

    async def _configure_mentions(self, message, args):
        """Configura a regra de mentions."""
        data = _load_data()
        
        if not args:
            await message.channel.send(embed=_embed("📝 Configurar Mentions", "Use: `tenshi automod mentions [max_mentions]`", COR_NEUTRO))
            return
        
        try:
            max_mentions = int(args[0])
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Valor deve ser um número.", COR_PERIGO))
            return
        
        data["rules"]["mentions"]["max_mentions"] = max_mentions
        data["rules"]["mentions"]["enabled"] = True
        _save_data(data)
        
        await message.channel.send(embed=_embed("✅ Mentions Configurado", f"Máximo de {max_mentions} menções por mensagem.", COR_SUCESSO))

    async def _configure_whitelist(self, message, args):
        """Configura a whitelist."""
        data = _load_data()
        
        if not args:
            await message.channel.send(embed=_embed("📝 Whitelist", "Use: `tenshi automod whitelist [add/remove] [user/role/channel] [id]`", COR_NEUTRO))
            return
        
        action = args[0].lower()
        target_type = args[1].lower() if len(args) > 1 else None
        target_id = args[2] if len(args) > 2 else None
        
        if action == "add" and target_type and target_id:
            if target_type == "user":
                data["whitelist"]["users"].append(target_id)
            elif target_type == "role":
                data["whitelist"]["roles"].append(target_id)
            elif target_type == "channel":
                data["whitelist"]["channels"].append(target_id)
            _save_data(data)
            await message.channel.send(embed=_embed("✅ Adicionado à Whitelist", f"{target_type} {target_id} adicionado.", COR_SUCESSO))
        
        elif action == "remove" and target_type and target_id:
            if target_type == "user" and target_id in data["whitelist"]["users"]:
                data["whitelist"]["users"].remove(target_id)
            elif target_type == "role" and target_id in data["whitelist"]["roles"]:
                data["whitelist"]["roles"].remove(target_id)
            elif target_type == "channel" and target_id in data["whitelist"]["channels"]:
                data["whitelist"]["channels"].remove(target_id)
            _save_data(data)
            await message.channel.send(embed=_embed("✅ Removido da Whitelist", f"{target_type} {target_id} removido.", COR_SUCESSO))

    async def check_message(self, message):
        """Verifica se a mensagem viola alguma regra."""
        if message.author.bot:
            return False
        
        if not message.guild:
            return False
        
        data = _load_data()
        if not data["enabled"]:
            return False
        
        # Verificar whitelist
        user_id = str(message.author.id)
        role_ids = [str(role.id) for role in message.author.roles]
        channel_id = str(message.channel.id)
        
        if user_id in data["whitelist"]["users"]:
            return False
        if any(role in data["whitelist"]["roles"] for role in role_ids):
            return False
        if channel_id in data["whitelist"]["channels"]:
            return False
        
        violations = []
        
        # Verificar spam
        if data["rules"]["spam"]["enabled"]:
            if await self._check_spam(message, data["rules"]["spam"]):
                violations.append("spam")
        
        # Verificar caps
        if data["rules"]["caps"]["enabled"]:
            if await self._check_caps(message, data["rules"]["caps"]):
                violations.append("caps")
        
        # Verificar links
        if data["rules"]["links"]["enabled"]:
            if await self._check_links(message, data["rules"]["links"]):
                violations.append("links")
        
        # Verificar bad words
        if data["rules"]["bad_words"]["enabled"]:
            if await self._check_badwords(message, data["rules"]["bad_words"]):
                violations.append("badwords")
        
        # Verificar mentions
        if data["rules"]["mentions"]["enabled"]:
            if await self._check_mentions(message, data["rules"]["mentions"]):
                violations.append("mentions")
        
        # Aplicar ações
        for violation in violations:
            await self._apply_action(message, violation, data["rules"][violation]["action"])
        
        return len(violations) > 0

    async def _check_spam(self, message, rule):
        """Verifica spam."""
        user_id = str(message.author.id)
        now = datetime.now(UTC).timestamp()
        
        if user_id not in self.message_history:
            self.message_history[user_id] = []
        
        # Remover mensagens antigas
        self.message_history[user_id] = [
            ts for ts in self.message_history[user_id]
            if now - ts < rule["time_window"]
        ]
        
        self.message_history[user_id].append(now)
        
        return len(self.message_history[user_id]) > rule["max_messages"]

    async def _check_caps(self, message, rule):
        """Verifica excesso de caps."""
        content = message.content
        if len(content) < rule["min_length"]:
            return False
        
        caps = sum(1 for c in content if c.isupper())
        caps_percent = (caps / len(content)) * 100
        
        return caps_percent > rule["max_caps"]

    async def _check_links(self, message, rule):
        """Verifica links não permitidos."""
        url_pattern = re.compile(r'https?://\S+')
        urls = url_pattern.findall(message.content)
        
        if not urls:
            return False
        
        for url in urls:
            allowed = False
            for domain in rule["allowed_domains"]:
                if domain in url:
                    allowed = True
                    break
            if not allowed:
                return True
        
        return False

    async def _check_badwords(self, message, rule):
        """Verifica palavras proibidas."""
        content = message.content.lower()
        for word in rule["words"]:
            if word in content:
                return True
        return False

    async def _check_mentions(self, message, rule):
        """Verifica excesso de mentions."""
        mentions = len(message.mentions) + len(message.role_mentions)
        return mentions > rule["max_mentions"]

    async def _apply_action(self, message, violation, action):
        """Aplica a ação de moderação."""
        if action == "delete":
            try:
                await message.delete()
                await message.channel.send(f"🚫 Mensagem deletada por violar a regra: {violation}", delete_after=5)
            except discord.Forbidden:
                pass
        
        elif action == "warn":
            try:
                await message.channel.send(f"⚠️ Aviso: Esta mensagem viola a regra: {violation}", delete_after=10)
            except discord.Forbidden:
                pass
        
        elif action == "mute":
            try:
                await message.delete()
                # Em produção, aplicaria mute real
                await message.channel.send(f"🔇 Usuário mutado por spam: {message.author.mention}", delete_after=10)
            except discord.Forbidden:
                pass

    async def handle_automod_stats(self, message, args):
        """Mostra estatísticas do auto-mod."""
        data = _load_data()
        violations = data.get("violations", {})
        
        total_violations = sum(violations.values())
        
        linhas = [
            f"**Total de Violações:** {total_violations}",
            f"**Spam:** {violations.get('spam', 0)}",
            f"**Caps:** {violations.get('caps', 0)}",
            f"**Links:** {violations.get('links', 0)}",
            f"**Bad Words:** {violations.get('badwords', 0)}",
            f"**Mentions:** {violations.get('mentions', 0)}"
        ]
        
        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("📊 Estatísticas Auto-Mod", descricao, COR_DOURADO))
