"""
Sistema de Proteção Imperial e Parcerias - Finalização UPP
Proteção contra invasões e sistema de parcerias com IA
"""
import json
import os
import re
import time
from datetime import datetime, UTC
from typing import Optional

import discord
from discord.ext import commands

from ia_router import ia_narrativa
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, SEP, embed_imperial

PROTECAO_FILE = "data/protecao_imperial.json"
PARCERIAS_FILE = "data/parcerias.json"


def _carregar_protecao() -> dict:
    if not os.path.exists(PROTECAO_FILE):
        return {
            "usuarios_confianca": [],
            "servidores_bloqueados": [],
            "atividade_suspeita": {},
            "configuracoes": {
                "protecao_ativa": True,
                "max_tentativas": 5,
                "tempo_bloqueio": 3600,
                "alertar_imperador": True
            }
        }
    try:
        with open(PROTECAO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "usuarios_confianca": [],
            "servidores_bloqueados": [],
            "atividade_suspeita": {},
            "configuracoes": {
                "protecao_ativa": True,
                "max_tentativas": 5,
                "tempo_bloqueio": 3600,
                "alertar_imperador": True
            }
        }


def _salvar_protecao(data: dict):
    os.makedirs(os.path.dirname(PROTECAO_FILE), exist_ok=True)
    with open(PROTECAO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _carregar_parcerias() -> dict:
    if not os.path.exists(PARCERIAS_FILE):
        return {"parcerias": [], "historico": []}
    try:
        with open(PARCERIAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"parcerias": [], "historico": []}


def _salvar_parcerias(data: dict):
    os.makedirs(os.path.dirname(PARCERIAS_FILE), exist_ok=True)
    with open(PARCERIAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ProtecaoParcerias(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tentativas_login: dict[int, list] = {}
        self.ultima_atividade: dict[int, float] = {}

    def cog_load(self):
        """Inicializa o cog quando carregado."""
        print("✅ Sistema de Proteção Imperial e Parcerias carregado.")

    async def _verificar_acesso_admin(self, member: discord.Member) -> bool:
        """Verifica se o membro tem acesso administrativo."""
        if member.id == IMPERADOR_ID:
            return True
        if member.guild_permissions.administrator:
            return True
        return False

    async def _alertar_imperador(self, titulo: str, mensagem: str):
        """Envia alerta ao Imperador sobre atividade suspeita."""
        config = _carregar_protecao()
        if not config["configuracoes"].get("alertar_imperador", True):
            return

        imperador = self.bot.get_user(IMPERADOR_ID)
        if imperador:
            try:
                embed = discord.Embed(
                    title=f"🚨 {titulo}",
                    description=mensagem,
                    color=0xFF0000
                )
                embed.set_footer(text=RODAPE_IMPERIAL)
                await imperador.send(embed=embed)
            except Exception as e:
                print(f"Erro ao alertar imperador: {e}")

    async def _registrar_atividade_suspeita(self, user_id: int, atividade: str):
        """Registra atividade suspeita para análise."""
        config = _carregar_protecao()
        if "atividade_suspeita" not in config:
            config["atividade_suspeita"] = {}

        timestamp = datetime.now(UTC).isoformat()
        if user_id not in config["atividade_suspeita"]:
            config["atividade_suspeita"][user_id] = []

        config["atividade_suspeita"][user_id].append({
            "atividade": atividade,
            "timestamp": timestamp
        })

        # Manter apenas as últimas 50 atividades
        if len(config["atividade_suspeita"][user_id]) > 50:
            config["atividade_suspeita"][user_id] = config["atividade_suspeita"][user_id][-50:]

        _salvar_protecao(config)

    async def _verificar_comportamento_suspeito(self, member: discord.Member) -> bool:
        """Verifica comportamento suspeito de um membro."""
        config = _carregar_protecao()
        if not config["configuracoes"].get("protecao_ativa", True):
            return False

        # Verificar se é usuário de confiança
        if member.id in config.get("usuarios_confianca", []):
            return False

        # Verificar conta muito nova
        if member.created_at:
            dias_conta = (datetime.now(UTC) - member.created_at).days
            if dias_conta < 7:
                await self._registrar_atividade_suspeita(
                    member.id,
                    f"Conta muito nova ({dias_conta} dias)"
                )
                return True

        # Verificar se entrou recentemente no servidor
        if member.joined_at:
            dias_servidor = (datetime.now(UTC) - member.joined_at).days
            if dias_servidor < 1:
                await self._registrar_atividade_suspeita(
                    member.id,
                    f"Entrou recentemente no servidor ({dias_servidor} dias)"
                )
                return True

        return False

    async def _eh_conta_fantasma(self, member: discord.Member) -> bool:
        """Verifica se a conta é fantasma (muito nova e sem atividade)."""
        if not member.created_at:
            return False

        try:
            dias_conta = (datetime.now(UTC) - member.created_at).days
            
            # Critérios para conta fantasma
            if dias_conta < 3:  # Menos de 3 dias
                return True
            
            if dias_conta < 7 and not member.avatar:  # Menos de 7 dias sem avatar
                return True
        except Exception as e:
            print(f"Erro ao verificar conta fantasma: {e}")
        
        return False

    async def _extrair_info_servidor(self, invite_link: str) -> Optional[dict]:
        """Extrai informações do servidor a partir do link de convite."""
        try:
            # Padrão para links de convite do Discord
            match = re.search(r'(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discord(?:app)?\.com/invite)/([a-zA-Z0-9-]+)', invite_link)
            if not match:
                return None

            invite_code = match.group(1)
            
            # Tenta obter informações do convite
            try:
                invite = await self.bot.fetch_invite(invite_code)
                if invite.guild:
                    return {
                        "nome": invite.guild.name,
                        "id": invite.guild.id,
                        "membros": invite.approximate_member_count or 0,
                        "online": invite.approximate_presence_count or 0,
                        "descricao": invite.guild.description or "",
                        "icone": str(invite.guild.icon.url) if invite.guild.icon else None,
                        "codigo": invite_code
                    }
            except discord.NotFound:
                return None
            except discord.HTTPException:
                return None

        except Exception as e:
            print(f"Erro ao extrair info do servidor: {e}")
            return None

        return None

    async def _gerar_embed_parceria(self, info_servidor: dict) -> discord.Embed:
        """Gera embed de parceria usando IA."""
        prompt_sistema = (
            "Você é um diplomata imperial do Império de Tenshi. "
            "Crie um texto elegante e persuasivo para uma parceria entre servidores do Discord. "
            "O texto deve destacar os benefícios mútuos, a importância da aliança e o compromisso com a comunidade. "
            "Use linguagem formal mas acolhedora. Maximo 800 caracteres."
        )

        contexto = (
            f"Nome do servidor: {info_servidor['nome']}\n"
            f"Membros totais: {info_servidor['membros']}\n"
            f"Membros online: {info_servidor['online']}\n"
            f"Descrição: {info_servidor['descricao'] or 'Sem descrição'}\n\n"
            "Crie um texto de parceria que destaque a aliança entre o Império de Tenshi e este servidor."
        )

        texto_parceria = await ia_narrativa(prompt_sistema, contexto, max_tokens=600)

        embed = discord.Embed(
            title="🤝 Proposta de Parceria Imperial",
            description=texto_parceria,
            color=0x2B0A3D
        )

        if info_servidor['icone']:
            embed.set_thumbnail(url=info_servidor['icone'])

        embed.add_field(
            name="📊 Informações do Servidor",
            value=(
                f"**Nome:** {info_servidor['nome']}\n"
                f"**Membros:** {info_servidor['membros']}\n"
                f"**Online:** {info_servidor['online']}\n"
                f"**ID:** {info_servidor['id']}"
            ),
            inline=False
        )

        embed.add_field(
            name="🔗 Link de Convite",
            value=f"https://discord.gg/{info_servidor['codigo']}",
            inline=False
        )

        embed.set_footer(text=f"{RODAPE_IMPERIAL} • Finalização UPP")
        embed.timestamp = datetime.now(UTC)

        return embed

    @commands.command(name="protecao-imperial")
    async def cmd_protecao_imperial(self, ctx):
        """Painel de configuração da proteção imperial."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        cfg = config["configuracoes"]

        embed = discord.Embed(
            title="🛡️ Painel de Proteção Imperial",
            description=f"Status da proteção do servidor e configurações atuais.\n\n{SEP}",
            color=0x2B0A3D
        )

        status = "✅ Ativa" if cfg.get("protecao_ativa", True) else "❌ Inativa"
        embed.add_field(name="🔒 Status", value=status, inline=True)
        embed.add_field(name="⚠️ Máx Tentativas", value=str(cfg.get("max_tentativas", 5)), inline=True)
        embed.add_field(name="⏱️ Tempo Bloqueio", value=f"{cfg.get('tempo_bloqueio', 3600)}s", inline=True)
        embed.add_field(name="📢 Alertar Imperador", value="✅ Sim" if cfg.get("alertar_imperador", True) else "❌ Não", inline=True)
        embed.add_field(name="👥 Usuários Confiança", value=str(len(config.get("usuarios_confianca", []))), inline=True)
        embed.add_field(name="🚫 Servidores Bloqueados", value=str(len(config.get("servidores_bloqueados", []))), inline=True)

        embed.set_footer(text=RODAPE_IMPERIAL)
        await ctx.send(embed=embed)

    @commands.command(name="ativar-protecao")
    async def cmd_ativar_protecao(self, ctx):
        """Ativa a proteção imperial."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        config["configuracoes"]["protecao_ativa"] = True
        _salvar_protecao(config)

        await ctx.send(embed=embed_imperial("✅ Proteção Ativada", "*A proteção imperial foi ativada com sucesso.*", 0x2B0A3D))

    @commands.command(name="desativar-protecao")
    async def cmd_desativar_protecao(self, ctx):
        """Desativa a proteção imperial."""
        if ctx.author.id != IMPERADOR_ID:
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas o Imperador pode desativar a proteção.*", 0x6B0000))
            return

        config = _carregar_protecao()
        config["configuracoes"]["protecao_ativa"] = False
        _salvar_protecao(config)

        await ctx.send(embed=embed_imperial("⚠️ Proteção Desativada", "*A proteção imperial foi desativada pelo Imperador.*", 0xFF6600))

    @commands.command(name="confianca")
    async def cmd_confianca(self, ctx, member: discord.Member):
        """Adiciona usuário à lista de confiança."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "usuarios_confianca" not in config:
            config["usuarios_confianca"] = []

        if member.id in config["usuarios_confianca"]:
            await ctx.send(embed=embed_imperial("ℹ️ Já na Lista", f"*{member.display_name} já está na lista de confiança.*", 0x6B0000))
            return

        config["usuarios_confianca"].append(member.id)
        _salvar_protecao(config)

        await ctx.send(embed=embed_imperial("✅ Adicionado à Confiança", f"*{member.display_name} foi adicionado à lista de confiança imperial.*", 0x2B0A3D))

    @commands.command(name="remover-confianca")
    async def cmd_remover_confianca(self, ctx, member: discord.Member):
        """Remove usuário da lista de confiança."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "usuarios_confianca" not in config:
            config["usuarios_confianca"] = []

        if member.id not in config["usuarios_confianca"]:
            await ctx.send(embed=embed_imperial("ℹ️ Não na Lista", f"*{member.display_name} não está na lista de confiança.*", 0x6B0000))
            return

        config["usuarios_confianca"].remove(member.id)
        _salvar_protecao(config)

        await ctx.send(embed=embed_imperial("✅ Removido da Confiança", f"*{member.display_name} foi removido da lista de confiança imperial.*", 0x2B0A3D))

    @commands.command(name="bloquear-servidor")
    async def cmd_bloquear_servidor(self, ctx, guild_id: int):
        """Bloqueia um servidor específico."""
        if ctx.author.id != IMPERADOR_ID:
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas o Imperador pode bloquear servidores.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "servidores_bloqueados" not in config:
            config["servidores_bloqueados"] = []

        if guild_id in config["servidores_bloqueados"]:
            await ctx.send(embed=embed_imperial("ℹ️ Já Bloqueado", f"*O servidor {guild_id} já está bloqueado.*", 0x6B0000))
            return

        config["servidores_bloqueados"].append(guild_id)
        _salvar_protecao(config)

        await ctx.send(embed=embed_imperial("✅ Servidor Bloqueado", f"*O servidor {guild_id} foi bloqueado pelo Imperador.*", 0x2B0A3D))

    @commands.command(name="desbloquear-servidor")
    async def cmd_desbloquear_servidor(self, ctx, guild_id: int):
        """Desbloqueia um servidor específico."""
        if ctx.author.id != IMPERADOR_ID:
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas o Imperador pode desbloquear servidores.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "servidores_bloqueados" not in config:
            config["servidores_bloqueados"] = []

        if guild_id not in config["servidores_bloqueados"]:
            await ctx.send(embed=embed_imperial("ℹ️ Não Bloqueado", f"*O servidor {guild_id} não está bloqueado.*", 0x6B0000))
            return

        config["servidores_bloqueados"].remove(guild_id)
        _salvar_protecao(config)

        await ctx.send(embed=embed_imperial("✅ Servidor Desbloqueado", f"*O servidor {guild_id} foi desbloqueado pelo Imperador.*", 0x2B0A3D))

    @commands.command(name="atividade-suspeita")
    async def cmd_atividade_suspeita(self, ctx, member: Optional[discord.Member] = None):
        """Verifica atividade suspeita de um usuário."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        target = member or ctx.author
        config = _carregar_protecao()
        atividades = config.get("atividade_suspeita", {}).get(target.id, [])

        if not atividades:
            await ctx.send(embed=embed_imperial("✅ Nenhuma Atividade", f"*{target.display_name} não possui atividades suspeitas registradas.*", 0x2B0A3D))
            return

        embed = discord.Embed(
            title=f"🔍 Atividade Suspeita - {target.display_name}",
            description=f"Últimas {len(atividades)} atividades registradas:\n\n{SEP}",
            color=0xFF6600
        )

        for idx, atividade in enumerate(atividades[-10:], 1):
            timestamp = atividade.get("timestamp", "Desconhecido")
            desc = atividade.get("atividade", "Não especificado")
            embed.add_field(
                name=f"📌 Atividade {idx}",
                value=f"**{desc}**\n🕐 {timestamp}",
                inline=False
            )

        embed.set_footer(text=RODAPE_IMPERIAL)
        await ctx.send(embed=embed)

    @commands.command(name="parceria")
    async def cmd_parceria(self, ctx, invite_link: str):
        """Gera embed de parceria a partir de link de convite."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem criar propostas de parceria.*", 0x6B0000))
            return

        await ctx.send("🔍 Analisando servidor do link de convite...")

        info_servidor = await self._extrair_info_servidor(invite_link)
        if not info_servidor:
            await ctx.send(embed=embed_imperial("❌ Link Inválido", "*Não foi possível obter informações do servidor. Verifique o link de convite.*", 0x6B0000))
            return

        await ctx.send("✨ Gerando proposta de parceria com IA...")

        embed = await self._gerar_embed_parceria(info_servidor)

        # Salvar no histórico
        parcerias = _carregar_parcerias()
        parcerias["historico"].append({
            "servidor": info_servidor["nome"],
            "servidor_id": info_servidor["id"],
            "codigo": info_servidor["codigo"],
            "criado_por": ctx.author.id,
            "timestamp": datetime.now(UTC).isoformat()
        })
        _salvar_parcerias(parcerias)

        await ctx.send(embed=embed)

    @commands.command(name="historico-parcerias")
    async def cmd_historico_parcerias(self, ctx):
        """Mostra histórico de parcerias."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        parcerias = _carregar_parcerias()
        historico = parcerias.get("historico", [])

        if not historico:
            await ctx.send(embed=embed_imperial("📭 Histórico Vazio", "*Nenhuma parceria foi registrada até o momento.*", 0x2B0A3D))
            return

        embed = discord.Embed(
            title="📜 Histórico de Parcerias",
            description=f"Total de {len(historico)} parcerias registradas.\n\n{SEP}",
            color=0x2B0A3D
        )

        for idx, parceria in enumerate(historico[-15:], 1):
            servidor = parceria.get("servidor", "Desconhecido")
            codigo = parceria.get("codigo", "N/A")
            timestamp = parceria.get("timestamp", "Desconhecido")
            embed.add_field(
                name=f"🤝 Parceria {idx}",
                value=f"**Servidor:** {servidor}\n**Código:** {codigo}\n**Data:** {timestamp[:10]}",
                inline=False
            )

        embed.set_footer(text=RODAPE_IMPERIAL)
        await ctx.send(embed=embed)

    @commands.CogListener()
    async def on_member_join(self, member: discord.Member):
        """Verifica novos membros ao entrarem no servidor."""
        config = _carregar_protecao()
        if not config["configuracoes"].get("protecao_ativa", True):
            return

        # Verificar se é conta fantasma - BAN AUTOMÁTICO
        if await self._eh_conta_fantasma(member):
            await self._registrar_atividade_suspeita(
                member.id,
                f"Conta fantasma detectada - Ban automático"
            )
            
            try:
                await member.ban(reason="Conta fantasma detectada pelo sistema de proteção imperial - Finalização UPP")
                await self._alertar_imperador(
                    "🚨 Ban Automático - Conta Fantasma",
                    f"O usuário **{member.display_name}** ({member.id}) foi banido automaticamente por ser uma conta fantasma.\n\n"
                    f"**Conta criada em:** {member.created_at}\n"
                    f"**Entrou em:** {member.joined_at}\n"
                    f"**Avatar:** {'Sim' if member.avatar else 'Não'}\n\n"
                    f"Esta ação foi executada automaticamente pelo sistema de proteção imperial."
                )
                return
            except discord.Forbidden:
                await self._alertar_imperador(
                    "⚠️ Falha ao Banir Conta Fantasma",
                    f"O usuário **{member.display_name}** ({member.id}) é uma conta fantasma, mas o bot não tem permissão para banir.\n\n"
                    f"**Conta criada em:** {member.created_at}\n"
                    f"**Entrou em:** {member.joined_at}\n\n"
                    f"Por favor, banir manualmente."
                )
                return
            except Exception as e:
                print(f"Erro ao banir conta fantasma: {e}")
                return

        # Verificar comportamento suspeito
        if await self._verificar_comportamento_suspeito(member):
            await self._alertar_imperador(
                "Novo Membro Suspeito",
                f"O usuário **{member.display_name}** ({member.id}) entrou no servidor e apresenta comportamento suspeito.\n\n"
                f"**Conta criada em:** {member.created_at}\n"
                f"**Entrou em:** {member.joined_at}"
            )

    @commands.CogListener()
    async def on_guild_join(self, guild: discord.Guild):
        """Verifica se o servidor está bloqueado quando o bot entra."""
        config = _carregar_protecao()
        if guild.id in config.get("servidores_bloqueados", []):
            await self._alertar_imperador(
                "Bot em Servidor Bloqueado",
                f"O bot foi adicionado ao servidor **{guild.name}** ({guild.id}), que está na lista de servidores bloqueados.\n\n"
                f"**Membros:** {guild.member_count}\n"
                f"**Dono:** {guild.owner}"
            )
            # Sair do servidor bloqueado
            try:
                await guild.leave()
            except Exception as e:
                print(f"Erro ao sair do servidor bloqueado: {e}")


async def setup(bot):
    await bot.add_cog(ProtecaoParcerias(bot))
