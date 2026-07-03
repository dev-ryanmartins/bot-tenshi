"""
Sistema de Moderação de Conteúdo - Finalização UPP
Análise de imagens, links suspeitos e filtro de segurança
"""
import re
import json
import os
import aiohttp
from typing import Optional, List
from urllib.parse import urlparse

import discord
from discord.ext import commands

from ia_router import ia_analitica
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, SEP, embed_imperial
from database_infractions import register_infraction

MODERACAO_FILE = "data/moderacao_conteudo.json"


def _carregar_config_moderacao() -> dict:
    if not os.path.exists(MODERACAO_FILE):
        return {
            "configuracoes": {
                "analise_imagens": True,
                "analise_links": True,
                "filtro_spam": True,
                "bloquear_violencia": True,
                "bloquear_pornografia": True,
                "bloquear_conteudo_infantil": True
            },
            "links_bloqueados": [],
            "dominios_confianca": [],
            "estatisticas": {
                "imagens_analisadas": 0,
                "links_analisados": 0,
                "violacoes_detectadas": 0
            }
        }
    try:
        with open(MODERACAO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "configuracoes": {
                "analise_imagens": True,
                "analise_links": True,
                "filtro_spam": True,
                "bloquear_violencia": True,
                "bloquear_pornografia": True,
                "bloquear_conteudo_infantil": True
            },
            "links_bloqueados": [],
            "dominios_confianca": [],
            "estatisticas": {
                "imagens_analisadas": 0,
                "links_analisados": 0,
                "violacoes_detectadas": 0
            }
        }


def _salvar_config_moderacao(data: dict):
    os.makedirs(os.path.dirname(MODERACAO_FILE), exist_ok=True)
    with open(MODERACAO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ModeracaoConteudo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._spam_tracker: dict[int, List[float]] = {}
        self._links_analisados: dict[str, dict] = {}

    def cog_load(self):
        """Inicializa o cog quando carregado."""
        print("✅ Sistema de Moderação de Conteúdo carregado.")

    async def _verificar_acesso_admin(self, member: discord.Member) -> bool:
        """Verifica se o membro tem acesso administrativo."""
        if member.id == IMPERADOR_ID:
            return True
        if member.guild_permissions.administrator:
            return True
        return False

    async def _alertar_imperador(self, titulo: str, mensagem: str, severity: str = "warning"):
        """Envia alerta ao Imperador sobre violação de conteúdo."""
        imperador = self.bot.get_user(IMPERADOR_ID)
        if imperador:
            try:
                cor = 0xFF0000 if severity == "critical" else (0xFF6600 if severity == "warning" else 0x2B0A3D)
                embed = discord.Embed(
                    title=f"🚨 {titulo}",
                    description=mensagem,
                    color=cor
                )
                embed.set_footer(text=RODAPE_IMPERIAL)
                await imperador.send(embed=embed)
            except Exception as e:
                print(f"Erro ao alertar imperador: {e}")

    def _extrair_links(self, texto: str) -> List[str]:
        """Extrai todos os links de um texto."""
        padrao_url = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .-]*/?'
        return re.findall(padrao_url, texto)

    def _eh_link_suspeito(self, url: str) -> tuple[bool, str]:
        """Verifica se um link é suspeito."""
        config = _carregar_config_moderacao()
        
        # Verificar se está na lista de bloqueados
        if url in config.get("links_bloqueados", []):
            return True, "Link na lista de bloqueados"
        
        try:
            parsed = urlparse(url)
            dominio = parsed.netloc.lower()
            
            # Domínios de confiança
            dominios_confianca = [d.lower() for d in config.get("dominios_confianca", [])]
            if any(d in dominio for d in dominios_confianca):
                return False, ""
            
            # Padrões suspeitos
            padroes_suspeitos = [
                r'\.tk$', r'\.ml$', r'\.ga$', r'\.cf$',  # Domínios gratuitos suspeitos
                r'bit\.ly', r'tinyurl\.com', r'short\.link',  # Encurtadores (podem ser usados para spam)
                r'free\.', r'xxx\.', r'porn\.', r'adult\.',  # Domínios de conteúdo adulto
                r'warez', r'pirata', r'crack', r'hack',  # Termos associados a conteúdo ilegal
            ]
            
            for padrao in padroes_suspeitos:
                if re.search(padrao, dominio):
                    return True, f"Domínio com padrão suspeito: {padrao}"
            
            # Links muito longos (possivelmente disfarçados)
            if len(url) > 200:
                return True, "Link excessivamente longo"
            
            # Links com muitos parâmetros (possível tracking/phishing)
            if url.count('&') > 5 or url.count('?') > 1:
                return True, "Link com muitos parâmetros"
                
        except Exception as e:
            print(f"Erro ao analisar link: {e}")
        
        return False, ""

    async def _analisar_link_com_ia(self, url: str) -> tuple[bool, str]:
        """Analisa um link usando IA para detectar conteúdo suspeito."""
        prompt_sistema = (
            "Você é um especialista em segurança digital. Analise o URL fornecido e determine se ele é suspeito ou perigoso. "
            "Considere: phishing, malware, conteúdo ilegal, spam, scams, sites de phishing, etc. "
            "Responda apenas com 'SIM' se for suspeito ou 'NAO' se for seguro, seguido de uma breve explicação em português."
        )
        
        try:
            resposta = await ia_analitica(prompt_sistema, f"Analise este URL: {url}", max_tokens=200)
            
            if "SIM" in resposta.upper():
                return True, resposta
            return False, ""
        except Exception as e:
            print(f"Erro ao analisar link com IA: {e}")
            return False, ""

    async def _analisar_imagem_com_ia(self, image_url: str) -> tuple[bool, str]:
        """Analisa uma imagem usando IA para detectar conteúdo impróprio."""
        # Nota: Para análise real de imagens, seria necessário usar uma API de visão computacional
        # como Google Vision API, AWS Rekognition, ou similar. Aqui implementamos a estrutura
        # e usamos análise baseada em contexto por enquanto.
        
        config = _carregar_config_moderacao()
        if not config["configuracoes"].get("analise_imagens", True):
            return False, ""
        
        # Por enquanto, vamos usar uma abordagem baseada em análise de contexto
        # Em produção, integrar com API de moderação de conteúdo
        prompt_sistema = (
            "Você é um moderador de conteúdo especializado. Analise o contexto de uma imagem que foi enviada. "
            "Se o contexto ou URL sugerir conteúdo impróprio (violência, pornografia, conteúdo infantil, etc), "
            "responda com 'SIM' e uma breve explicação. Caso contrário, responda 'NAO'."
        )
        
        try:
            resposta = await ia_analitica(prompt_sistema, f"URL da imagem: {image_url}", max_tokens=200)
            
            if "SIM" in resposta.upper():
                return True, resposta
            return False, ""
        except Exception as e:
            print(f"Erro ao analisar imagem com IA: {e}")
            return False, ""

    async def _detectar_spam(self, message: discord.Message) -> tuple[bool, str]:
        """Detecta padrões de spam na mensagem."""
        config = _carregar_config_moderacao()
        if not config["configuracoes"].get("filtro_spam", True):
            return False, ""
        
        user_id = message.author.id
        agora = message.created_at.timestamp()
        
        # Inicializar tracker se necessário
        if user_id not in self._spam_tracker:
            self._spam_tracker[user_id] = []
        
        # Remover mensagens antigas (mais de 10 segundos)
        self._spam_tracker[user_id] = [t for t in self._spam_tracker[user_id] if agora - t < 10]
        
        # Adicionar mensagem atual
        self._spam_tracker[user_id].append(agora)
        
        # Verificar frequência (mais de 5 mensagens em 10 segundos)
        if len(self._spam_tracker[user_id]) > 5:
            return True, "Alta frequência de mensagens (possível spam)"
        
        # Verificar mensagens duplicadas
        if len(self._spam_tracker[user_id]) > 2:
            # Verificar se as últimas 3 mensagens são muito similares
            canal_mensagens = [msg async for msg in message.channel.history(limit=10)]
            mensagens_usuario = [msg for msg in canal_mensagens if msg.author.id == user_id]
            
            if len(mensagens_usuario) >= 3:
                ultimas = mensagens_usuario[-3:]
                conteudos = [msg.content.lower().strip() for msg in ultimas]
                if len(set(conteudos)) == 1 and conteudos[0]:
                    return True, "Mensagens duplicadas (spam)"
        
        # Verificar caracteres repetidos excessivos
        if any(char * 5 in message.content for char in message.content):
            return True, "Caracteres repetidos excessivamente"
        
        # Verificar MENÇÕES em massa
        if message.content.count('@') > 5:
            return True, "Muitas menções em uma mensagem"
        
        return False, ""

    async def _processar_violacao(self, message: discord.Message, tipo: str, motivo: str, severity: str = "warning"):
        """Processa uma violação detectada."""
        config = _carregar_config_moderacao()
        
        # Atualizar estatísticas
        config["estatisticas"]["violacoes_detectadas"] = config["estatisticas"].get("violacoes_detectadas", 0) + 1
        _salvar_config_moderacao(config)
        
        # Registrar infração
        try:
            await register_infraction(
                user_id=message.author.id,
                infraction_type="aviso" if severity == "warning" else "ban",
                reason=f"[Moderação Automática] {tipo}: {motivo}",
                moderator_id=self.bot.user.id if self.bot.user else None,
            )
        except Exception as e:
            print(f"Erro ao registrar infração: {e}")
        
        # Alertar Imperador
        await self._alertar_imperador(
            f"Violação de Conteúdo Detectada - {tipo}",
            f"**Usuário:** {message.author.display_name} ({message.author.id})\n"
            f"**Canal:** {message.channel.name}\n"
            f"**Motivo:** {motivo}\n"
            f"**Mensagem:** {message.content[:200]}...\n\n"
            f"Severidade: {severity.upper()}",
            severity
        )
        
        # Ações baseadas na severidade
        if severity == "critical":
            try:
                await message.delete()
                await message.channel.send(
                    f"🚨 {message.author.mention} Conteúdo removido por violar as regras de segurança do servidor.",
                    delete_after=10
                )
            except Exception:
                pass
        else:
            try:
                await message.author.send(
                    embed=embed_imperial(
                        "⚠️ Aviso de Moderação",
                        f"Sua mensagem foi marcada como **{tipo}**.\n\n"
                        f"**Motivo:** {motivo}\n\n"
                        f"Por favor, evite este tipo de conteúdo. Violações recorrentes resultarão em punições mais severas.",
                        0xFF6600
                    )
                )
            except Exception:
                pass

    async def verificar_mensagem(self, message: discord.Message) -> bool:
        """Verifica uma mensagem por conteúdo impróprio."""
        if message.author.bot:
            return False
        
        if message.author.id == IMPERADOR_ID:
            return False
        
        config = _carregar_config_moderacao()
        
        # 1. Detectar spam
        eh_spam, motivo_spam = await self._detectar_spam(message)
        if eh_spam:
            await self._processar_violacao(message, "Spam", motivo_spam, "warning")
            return True
        
        # 2. Analisar links
        links = self._extrair_links(message.content)
        if links and config["configuracoes"].get("analise_links", True):
            for link in links:
                config["estatisticas"]["links_analisados"] = config["estatisticas"].get("links_analisados", 0) + 1
                
                # Verificação rápida local
                eh_suspeito, motivo_suspeito = self._eh_link_suspeito(link)
                if eh_suspeito:
                    await self._processar_violacao(message, "Link Suspeito", motivo_suspeito, "critical")
                    _salvar_config_moderacao(config)
                    return True
                
                # Análise com IA para links desconhecidos
                if link not in self._links_analisados:
                    eh_perigoso, motivo_ia = await self._analisar_link_com_ia(link)
                    self._links_analisados[link] = {"suspeito": eh_perigoso, "motivo": motivo_ia}
                    
                    if eh_perigoso:
                        await self._processar_violacao(message, "Link Perigoso", motivo_ia, "critical")
                        _salvar_config_moderacao(config)
                        return True
            
            _salvar_config_moderacao(config)
        
        # 3. Analisar imagens
        if message.attachments and config["configuracoes"].get("analise_imagens", True):
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    config["estatisticas"]["imagens_analisadas"] = config["estatisticas"].get("imagens_analisadas", 0) + 1
                    
                    eh_impropria, motivo_imagem = await self._analisar_imagem_com_ia(attachment.url)
                    if eh_impropria:
                        await self._processar_violacao(message, "Imagem Imprópria", motivo_imagem, "critical")
                        _salvar_config_moderacao(config)
                        return True
            
            _salvar_config_moderacao(config)
        
        return False

    @commands.command(name="config-moderacao")
    async def cmd_config_moderacao(self, ctx):
        """Painel de configuração da moderação de conteúdo."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_config_moderacao()
        cfg = config["configuracoes"]
        stats = config["estatisticas"]

        embed = discord.Embed(
            title="🔒 Painel de Moderação de Conteúdo",
            description=f"Configurações e estatísticas do sistema de moderação.\n\n{SEP}",
            color=0x2B0A3D
        )

        embed.add_field(name="📊 Estatísticas", value=(
            f"**Imagens analisadas:** {stats.get('imagens_analisadas', 0)}\n"
            f"**Links analisados:** {stats.get('links_analisados', 0)}\n"
            f"**Violações detectadas:** {stats.get('violacoes_detectadas', 0)}"
        ), inline=False)

        embed.add_field(name="⚙️ Configurações", value=(
            f"**Análise de imagens:** {'✅' if cfg.get('analise_imagens') else '❌'}\n"
            f"**Análise de links:** {'✅' if cfg.get('analise_links') else '❌'}\n"
            f"**Filtro de spam:** {'✅' if cfg.get('filtro_spam') else '❌'}\n"
            f"**Bloquear violência:** {'✅' if cfg.get('bloquear_violencia') else '❌'}\n"
            f"**Bloquear pornografia:** {'✅' if cfg.get('bloquear_pornografia') else '❌'}\n"
            f"**Bloquear conteúdo infantil:** {'✅' if cfg.get('bloquear_conteudo_infantil') else '❌'}"
        ), inline=False)

        embed.add_field(name="🔗 Links Bloqueados", value=str(len(config.get("links_bloqueados", []))), inline=True)
        embed.add_field(name="✅ Domínios Confiança", value=str(len(config.get("dominios_confianca", []))), inline=True)

        embed.set_footer(text=RODAPE_IMPERIAL)
        await ctx.send(embed=embed)

    @commands.command(name="bloquear-link")
    async def cmd_bloquear_link(self, ctx, url: str):
        """Bloqueia um link específico."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_config_moderacao()
        if "links_bloqueados" not in config:
            config["links_bloqueados"] = []

        if url in config["links_bloqueados"]:
            await ctx.send(embed=embed_imperial("ℹ️ Já Bloqueado", f"*O link já está na lista de bloqueados.*", 0x6B0000))
            return

        config["links_bloqueados"].append(url)
        _salvar_config_moderacao(config)

        await ctx.send(embed=embed_imperial("✅ Link Bloqueado", f"*O link foi adicionado à lista de bloqueados.*", 0x2B0A3D))

    @commands.command(name="desbloquear-link")
    async def cmd_desbloquear_link(self, ctx, url: str):
        """Desbloqueia um link específico."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_config_moderacao()
        if "links_bloqueados" not in config:
            config["links_bloqueados"] = []

        if url not in config["links_bloqueados"]:
            await ctx.send(embed=embed_imperial("ℹ️ Não Bloqueado", f"*O link não está na lista de bloqueados.*", 0x6B0000))
            return

        config["links_bloqueados"].remove(url)
        _salvar_config_moderacao(config)

        await ctx.send(embed=embed_imperial("✅ Link Desbloqueado", f"*O link foi removido da lista de bloqueados.*", 0x2B0A3D))

    @commands.command(name="adicionar-dominio-confianca")
    async def cmd_adicionar_dominio_confianca(self, ctx, dominio: str):
        """Adiciona um domínio à lista de confiança."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_config_moderacao()
        if "dominios_confianca" not in config:
            config["dominios_confianca"] = []

        if dominio in config["dominios_confianca"]:
            await ctx.send(embed=embed_imperial("ℹ️ Já na Lista", f"*O domínio já está na lista de confiança.*", 0x6B0000))
            return

        config["dominios_confianca"].append(dominio)
        _salvar_config_moderacao(config)

        await ctx.send(embed=embed_imperial("✅ Domínio Adicionado", f"*O domínio foi adicionado à lista de confiança.*", 0x2B0A3D))

    @commands.command(name="remover-dominio-confianca")
    async def cmd_remover_dominio_confianca(self, ctx, dominio: str):
        """Remove um domínio da lista de confiança."""
        if not await self._verificar_acesso_admin(ctx.author):
            await ctx.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_config_moderacao()
        if "dominios_confianca" not in config:
            config["dominios_confianca"] = []

        if dominio not in config["dominios_confianca"]:
            await ctx.send(embed=embed_imperial("ℹ️ Não na Lista", f"*O domínio não está na lista de confiança.*", 0x6B0000))
            return

        config["dominios_confianca"].remove(dominio)
        _salvar_config_moderacao(config)

        await ctx.send(embed=embed_imperial("✅ Domínio Removido", f"*O domínio foi removido da lista de confiança.*", 0x2B0A3D))


async def setup(bot):
    await bot.add_cog(ModeracaoConteudo(bot))
