"""
Sistema de Proteção Imperial e Parcerias
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
LOGS_FILE = "data/protecao_logs.json"


def _carregar_protecao() -> dict:
    if not os.path.exists(PROTECAO_FILE):
        return {
            "usuarios_confianca": [],
            "servidores_bloqueados": [],
            "atividade_suspeita": {},
            "whitelist_fantasma": [],
            "reputacao_usuarios": {},
            "whitelist_temporaria": {},
            "estatisticas": {
                "bans_automaticos": 0,
                "alertas_enviados": 0,
                "whitelist_adicoes": 0,
                "whitelist_remocoes": 0,
                "backups_criados": 0,
                "backups_restaurados": 0
            },
            "configuracoes": {
                "protecao_ativa": True,
                "max_tentativas": 5,
                "tempo_bloqueio": 3600,
                "alertar_imperador": True,
                "backup_automatico": True,
                "ultimo_backup": None,
                "canal_alertas": None,
                "modo_teste": False,
                "cooldown_alertas": 300,
                "canal_quarentena": None,
                "canal_honeypot": None,
                "relatorio_frequencia": "semanal",
                "ultimo_relatorio": None
            },
            "alertas_cooldown": {}
        }
    try:
        with open(PROTECAO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Migrate old data structure
            if "whitelist_fantasma" not in data:
                data["whitelist_fantasma"] = []
            if "reputacao_usuarios" not in data:
                data["reputacao_usuarios"] = {}
            if "whitelist_temporaria" not in data:
                data["whitelist_temporaria"] = {}
            if "estatisticas" not in data:
                data["estatisticas"] = {
                    "bans_automaticos": 0,
                    "alertas_enviados": 0,
                    "whitelist_adicoes": 0,
                    "whitelist_remocoes": 0,
                    "backups_criados": 0,
                    "backups_restaurados": 0
                }
            if "backup_automatico" not in data["configuracoes"]:
                data["configuracoes"]["backup_automatico"] = True
            if "ultimo_backup" not in data["configuracoes"]:
                data["configuracoes"]["ultimo_backup"] = None
            if "canal_alertas" not in data["configuracoes"]:
                data["configuracoes"]["canal_alertas"] = None
            if "modo_teste" not in data["configuracoes"]:
                data["configuracoes"]["modo_teste"] = False
            if "cooldown_alertas" not in data["configuracoes"]:
                data["configuracoes"]["cooldown_alertas"] = 300
            if "canal_quarentena" not in data["configuracoes"]:
                data["configuracoes"]["canal_quarentena"] = None
            if "canal_honeypot" not in data["configuracoes"]:
                data["configuracoes"]["canal_honeypot"] = None
            if "relatorio_frequencia" not in data["configuracoes"]:
                data["configuracoes"]["relatorio_frequencia"] = "semanal"
            if "ultimo_relatorio" not in data["configuracoes"]:
                data["configuracoes"]["ultimo_relatorio"] = None
            if "alertas_cooldown" not in data:
                data["alertas_cooldown"] = {}
            return data
    except Exception:
        return {
            "usuarios_confianca": [],
            "servidores_bloqueados": [],
            "atividade_suspeita": {},
            "whitelist_fantasma": [],
            "reputacao_usuarios": {},
            "whitelist_temporaria": {},
            "estatisticas": {
                "bans_automaticos": 0,
                "alertas_enviados": 0,
                "whitelist_adicoes": 0,
                "whitelist_remocoes": 0,
                "backups_criados": 0,
                "backups_restaurados": 0
            },
            "configuracoes": {
                "protecao_ativa": True,
                "max_tentativas": 5,
                "tempo_bloqueio": 3600,
                "alertar_imperador": True,
                "backup_automatico": True,
                "ultimo_backup": None,
                "canal_alertas": None,
                "modo_teste": False,
                "cooldown_alertas": 300,
                "canal_quarentena": None,
                "canal_honeypot": None,
                "relatorio_frequencia": "semanal",
                "ultimo_relatorio": None
            },
            "alertas_cooldown": {}
        }


def _salvar_protecao(data: dict):
    os.makedirs(os.path.dirname(PROTECAO_FILE), exist_ok=True)
    with open(PROTECAO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _criar_backup():
    """Cria backup das configurações de proteção."""
    try:
        config = _carregar_protecao()
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_file = f"data/protecao_imperial_backup_{timestamp}.json"
        
        os.makedirs(os.path.dirname(backup_file), exist_ok=True)
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # Atualizar timestamp do último backup
        config["configuracoes"]["ultimo_backup"] = datetime.now(UTC).isoformat()
        _salvar_protecao(config)
        
        # Log e estatísticas
        _incrementar_estatistica("backups_criados")
        _registrar_log("backup", "criar_backup", f"Backup criado: {backup_file}")
        
        print(f"✅ Backup criado: {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return False


def _verificar_e_criar_backup():
    """Verifica se é necessário criar backup diário."""
    try:
        config = _carregar_protecao()
        if not config["configuracoes"].get("backup_automatico", True):
            return False
        
        ultimo_backup = config["configuracoes"].get("ultimo_backup")
        if not ultimo_backup:
            return _criar_backup()
        
        # Verificar se passou 24 horas desde o último backup
        from datetime import timedelta
        ultimo_backup_dt = datetime.fromisoformat(ultimo_backup)
        if datetime.now(UTC) - ultimo_backup_dt > timedelta(hours=24):
            return _criar_backup()
        
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar backup: {e}")
        return False


def _carregar_logs() -> list:
    """Carrega logs do sistema de proteção."""
    if not os.path.exists(LOGS_FILE):
        return []
    try:
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _salvar_log(log: dict):
    """Salva um log no sistema."""
    logs = _carregar_logs()
    logs.append(log)
    
    # Manter apenas os últimos 1000 logs
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    os.makedirs(os.path.dirname(LOGS_FILE), exist_ok=True)
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def _registrar_log(tipo: str, acao: str, detalhes: str, user_id: int = None, target_id: int = None):
    """Registra uma ação no sistema de logs."""
    log = {
        "timestamp": datetime.now(UTC).isoformat(),
        "tipo": tipo,  # "ban", "alert", "whitelist", "backup", "config"
        "acao": acao,
        "detalhes": detalhes,
        "user_id": user_id,
        "target_id": target_id
    }
    _salvar_log(log)


def _incrementar_estatistica(chave: str):
    """Incrementa uma estatística no sistema."""
    config = _carregar_protecao()
    if "estatisticas" not in config:
        config["estatisticas"] = {
            "bans_automaticos": 0,
            "alertas_enviados": 0,
            "whitelist_adicoes": 0,
            "whitelist_remocoes": 0,
            "backups_criados": 0,
            "backups_restaurados": 0
        }
    if chave in config["estatisticas"]:
        config["estatisticas"][chave] += 1
    _salvar_protecao(config)


def _verificar_cooldown(user_id: int) -> bool:
    """Verifica se o usuário está em cooldown para alertas."""
    config = _carregar_protecao()
    cooldown_time = config["configuracoes"].get("cooldown_alertas", 300)
    
    if user_id not in config["alertas_cooldown"]:
        return False
    
    ultimo_alerta = config["alertas_cooldown"][user_id]
    tempo_passado = (datetime.now(UTC) - datetime.fromisoformat(ultimo_alerta)).total_seconds()
    
    if tempo_passado >= cooldown_time:
        del config["alertas_cooldown"][user_id]
        _salvar_protecao(config)
        return False
    
    return True


def _definir_cooldown(user_id: int):
    """Define cooldown para um usuário."""
    config = _carregar_protecao()
    config["alertas_cooldown"][user_id] = datetime.now(UTC).isoformat()
    _salvar_protecao(config)


def _obter_reputacao(user_id: int) -> int:
    """Obtém reputação de um usuário (padrão: 0)."""
    config = _carregar_protecao()
    return config.get("reputacao_usuarios", {}).get(str(user_id), 0)


def _ajustar_reputacao(user_id: int, pontos: int):
    """Ajusta reputação de um usuário."""
    config = _carregar_protecao()
    if "reputacao_usuarios" not in config:
        config["reputacao_usuarios"] = {}
    
    reputacao_atual = config["reputacao_usuarios"].get(str(user_id), 0)
    nova_reputacao = max(-100, min(100, reputacao_atual + pontos))
    config["reputacao_usuarios"][str(user_id)] = nova_reputacao
    _salvar_protecao(config)
    return nova_reputacao


def _verificar_whitelist_temporaria(user_id: int) -> bool:
    """Verifica se usuário está na whitelist temporária e não expirou."""
    config = _carregar_protecao()
    whitelist_temp = config.get("whitelist_temporaria", {})
    
    if str(user_id) not in whitelist_temp:
        return False
    
    expiracao = datetime.fromisoformat(whitelist_temp[str(user_id)])
    if datetime.now(UTC) > expiracao:
        # Remover entrada expirada
        del whitelist_temp[str(user_id)]
        _salvar_protecao(config)
        return False
    
    return True


def _adicionar_whitelist_temporaria(user_id: int, dias: int):
    """Adiciona usuário à whitelist temporária."""
    from datetime import timedelta
    config = _carregar_protecao()
    if "whitelist_temporaria" not in config:
        config["whitelist_temporaria"] = {}
    
    expiracao = datetime.now(UTC) + timedelta(days=dias)
    config["whitelist_temporaria"][str(user_id)] = expiracao.isoformat()
    _salvar_protecao(config)


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
        # Verificar backup diário ao carregar
        _verificar_e_criar_backup()

    async def _verificar_acesso_admin(self, member: discord.Member) -> bool:
        """Verifica se o membro tem acesso administrativo."""
        if member.id == IMPERADOR_ID:
            return True
        if member.guild_permissions.administrator:
            return True
        return False

    async def _alertar_imperador(self, titulo: str, mensagem: str, canal: discord.TextChannel = None):
        """Envia alerta ao Imperador e/ou canal sobre atividade suspeita."""
        config = _carregar_protecao()
        if not config["configuracoes"].get("alertar_imperador", True):
            return

        embed = discord.Embed(
            title=f"🚨 {titulo}",
            description=mensagem,
            color=0xFF0000
        )
        embed.set_footer(text=RODAPE_IMPERIAL)

        # Enviar para o Imperador via DM
        imperador = self.bot.get_user(IMPERADOR_ID)
        if imperador:
            try:
                await imperador.send(embed=embed)
            except Exception as e:
                print(f"Erro ao alertar imperador: {e}")

        # Enviar para canal configurado
        canal_alertas_id = config["configuracoes"].get("canal_alertas")
        if canal_alertas_id:
            canal_alertas = self.bot.get_channel(canal_alertas_id)
            if canal_alertas:
                try:
                    await canal_alertas.send(embed=embed)
                except Exception as e:
                    print(f"Erro ao enviar alerta para canal: {e}")

        # Enviar para canal especificado (se fornecido)
        if canal:
            try:
                await canal.send(embed=embed)
            except Exception as e:
                print(f"Erro ao enviar alerta para canal especificado: {e}")

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

    async def _eh_conta_fantasma(self, member: discord.Member) -> Optional[str]:
        """Verifica se a conta é fantasma e retorna status: 'ban', 'alert', ou None."""
        if not member.created_at:
            return None

        try:
            config = _carregar_protecao()
            
            # Verificar whitelist permanente
            if member.id in config.get("whitelist_fantasma", []):
                return None
            
            # Verificar whitelist temporária
            if _verificar_whitelist_temporaria(member.id):
                return None
            
            dias_conta = (datetime.now(UTC) - member.created_at).days
            
            # Novos critérios para conta fantasma
            if dias_conta < 1:  # Menos de 1 dia = BAN automático
                return "ban"
            
            if dias_conta < 3:  # 1-3 dias = ALERTA
                return "alert"
            
            if dias_conta < 7 and not member.avatar:  # Menos de 7 dias sem avatar = ALERTA
                return "alert"
        except Exception as e:
            print(f"Erro ao verificar conta fantasma: {e}")
        
        return None

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

        embed.set_footer(text=f"{RODAPE_IMPERIAL}")
        embed.timestamp = datetime.now(UTC)

        return embed

    async def cmd_protecao_imperial(self, message):
        """Painel de configuração da proteção imperial."""
        try:
            if not await self._verificar_acesso_admin(message.author):
                await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
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
            
            # Adicionar comandos disponíveis
            embed.add_field(
                name="📋 Comandos Disponíveis",
                value=(
                    "`tenshi ativar-protecao` - Ativa a proteção\n"
                    "`tenshi desativar-protecao` - Desativa a proteção\n"
                    "`tenshi confianca @usuario` - Adiciona usuário confiável\n"
                    "`tenshi remover-confianca @usuario` - Remove usuário confiável\n"
                    "`tenshi whitelist-fantasma @usuario` - Adiciona à whitelist fantasma\n"
                    "`tenshi remover-whitelist-fantasma @usuario` - Remove da whitelist fantasma\n"
                    "`tenshi listar-whitelist-fantasma` - Lista whitelist fantasma\n"
                    "`tenshi whitelist-temp @usuario [dias]` - Whitelist temporária\n"
                    "`tenshi reputacao @usuario` - Ver reputação do usuário\n"
                    "`tenshi ajustar-reputacao @usuario [pontos]` - Ajustar reputação\n"
                    "`tenshi config-quarentena #canal` - Configura canal de quarentena\n"
                    "`tenshi config-honeypot #canal` - Configura canal honeypot\n"
                    "`tenshi config-relatorio [freq]` - Configura relatórios automáticos\n"
                    "`tenshi bloquear-servidor [id]` - Bloqueia servidor\n"
                    "`tenshi desbloquear-servidor [id]` - Desbloqueia servidor\n"
                    "`tenshi atividade-suspeita @usuario` - Verifica atividade\n"
                    "`tenshi teste-protecao @usuario` - Testa detecção de conta fantasma\n"
                    "`tenshi criar-backup` - Cria backup manual das configurações\n"
                    "`tenshi listar-backups` - Lista backups disponíveis\n"
                    "`tenshi restaurar-backup [arquivo]` - Restaura backup\n"
                    "`tenshi logs-protecao [filtro]` - Ver logs do sistema\n"
                    "`tenshi estatisticas-protecao` - Ver estatísticas\n"
                    "`tenshi config-canal-alertas #canal` - Configura canal de alertas\n"
                    "`tenshi limpar-logs [dias]` - Limpa logs antigos\n"
                    "`tenshi relatorio-protecao` - Gera relatório detalhado\n"
                    "`tenshi resetar-estatisticas` - Zera estatísticas\n"
                    "`tenshi modo-teste` - Ativa/desativa modo de teste"
                ),
                inline=False
            )

            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌ Erro", f"*Ocorreu um erro ao carregar o painel: {e}*", 0x6B0000))
            print(f"Erro no cmd_protecao_imperial: {e}")

    async def cmd_ativar_protecao(self, message):
        """Ativa a proteção imperial."""
        try:
            if not await self._verificar_acesso_admin(message.author):
                await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
                return

            config = _carregar_protecao()
            config["configuracoes"]["protecao_ativa"] = True
            _salvar_protecao(config)

            embed = discord.Embed(
                title="✅ Proteção Imperial Ativada",
                description=(
                    "*A proteção imperial foi ativada com sucesso.*\n\n"
                    f"{SEP}\n\n"
                    "**🔒 Configurações Atuais:**\n"
                    f"• Máx tentativas: {config['configuracoes'].get('max_tentativas', 5)}\n"
                    f"• Tempo de bloqueio: {config['configuracoes'].get('tempo_bloqueio', 3600)}s\n"
                    f"• Alertar Imperador: {'✅ Sim' if config['configuracoes'].get('alertar_imperador', True) else '❌ Não'}\n\n"
                    "**🛡️ Sistema Ativo:**\n"
                    "• Detecção de contas fantasma\n"
                    "• Bloqueio de servidores suspeitos\n"
                    "• Monitoramento de atividade\n"
                    "• Alertas automáticos ao Imperador"
                ),
                color=0x2B0A3D
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌ Erro", f"*Ocorreu um erro ao ativar a proteção: {e}*", 0x6B0000))
            print(f"Erro no cmd_ativar_protecao: {e}")

    async def cmd_desativar_protecao(self, message):
        """Desativa a proteção imperial."""
        try:
            if message.author.id != IMPERADOR_ID:
                await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas o Imperador pode desativar a proteção.*", 0x6B0000))
                return

            config = _carregar_protecao()
            config["configuracoes"]["protecao_ativa"] = False
            _salvar_protecao(config)

            embed = discord.Embed(
                title="⚠️ Proteção Imperial Desativada",
                description=(
                    "*A proteção imperial foi desativada pelo Imperador.*\n\n"
                    f"{SEP}\n\n"
                    "**⚠️ Aviso:**\n"
                    "O servidor não está mais protegido contra:\n"
                    "• Contas fantasma\n"
                    "• Servidores suspeitos\n"
                    "• Atividades anômalas\n\n"
                    "Reative a proteção com `tenshi ativar-protecao`"
                ),
                color=0xFF6600
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌ Erro", f"*Ocorreu um erro ao desativar a proteção: {e}*", 0x6B0000))
            print(f"Erro no cmd_desativar_protecao: {e}")

    async def cmd_confianca(self, message, member: discord.Member):
        """Adiciona usuário à lista de confiança."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "usuarios_confianca" not in config:
            config["usuarios_confianca"] = []

        if member.id in config["usuarios_confianca"]:
            await message.channel.send(embed=embed_imperial("ℹ️ Já na Lista", f"*{member.display_name} já está na lista de confiança.*", 0x6B0000))
            return

        config["usuarios_confianca"].append(member.id)
        _salvar_protecao(config)

        await message.channel.send(embed=embed_imperial("✅ Adicionado à Confiança", f"*{member.display_name} foi adicionado à lista de confiança imperial.*", 0x2B0A3D))

    async def cmd_remover_confianca(self, message, member: discord.Member):
        """Remove usuário da lista de confiança."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "usuarios_confianca" not in config:
            config["usuarios_confianca"] = []

        if member.id not in config["usuarios_confianca"]:
            await message.channel.send(embed=embed_imperial("ℹ️ Não na Lista", f"*{member.display_name} não está na lista de confiança.*", 0x6B0000))
            return

        config["usuarios_confianca"].remove(member.id)
        _salvar_protecao(config)

        await message.channel.send(embed=embed_imperial("✅ Removido da Confiança", f"*{member.display_name} foi removido da lista de confiança imperial.*", 0x2B0A3D))

    async def cmd_whitelist_fantasma(self, message, member: discord.Member):
        """Adiciona usuário à whitelist de contas fantasma."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "whitelist_fantasma" not in config:
            config["whitelist_fantasma"] = []

        if member.id in config["whitelist_fantasma"]:
            await message.channel.send(embed=embed_imperial("ℹ️ Já na Whitelist", f"*{member.display_name} já está na whitelist de contas fantasma.*", 0x6B0000))
            return

        config["whitelist_fantasma"].append(member.id)
        _salvar_protecao(config)

        # Log e estatísticas
        _incrementar_estatistica("whitelist_adicoes")
        _registrar_log("whitelist", "adicionar", f"Usuário {member.display_name} adicionado à whitelist fantasma", message.author.id, member.id)

        await message.channel.send(embed=embed_imperial("✅ Adicionado à Whitelist", f"*{member.display_name} foi adicionado à whitelist de contas fantasma e não será analisado.*", 0x2B0A3D))

    async def cmd_remover_whitelist_fantasma(self, message, member: discord.Member):
        """Remove usuário da whitelist de contas fantasma."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "whitelist_fantasma" not in config:
            config["whitelist_fantasma"] = []

        if member.id not in config["whitelist_fantasma"]:
            await message.channel.send(embed=embed_imperial("ℹ️ Não na Whitelist", f"*{member.display_name} não está na whitelist de contas fantasma.*", 0x6B0000))
            return

        config["whitelist_fantasma"].remove(member.id)
        _salvar_protecao(config)

        # Log e estatísticas
        _incrementar_estatistica("whitelist_remocoes")
        _registrar_log("whitelist", "remover", f"Usuário {member.display_name} removido da whitelist fantasma", message.author.id, member.id)

        await message.channel.send(embed=embed_imperial("✅ Removido da Whitelist", f"*{member.display_name} foi removido da whitelist de contas fantasma.*", 0x2B0A3D))

    async def cmd_listar_whitelist_fantasma(self, message):
        """Lista todos os usuários na whitelist de contas fantasma."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        whitelist = config.get("whitelist_fantasma", [])

        if not whitelist:
            await message.channel.send(embed=embed_imperial("📭 Whitelist Vazia", "*Nenhum usuário na whitelist de contas fantasma.*", 0x2B0A3D))
            return

        embed = discord.Embed(
            title="📋 Whitelist de Contas Fantasma",
            description=f"Total de {len(whitelist)} usuários na whitelist.\n\n{SEP}",
            color=0x2B0A3D
        )

        for idx, user_id in enumerate(whitelist, 1):
            user = self.bot.get_user(user_id)
            username = user.display_name if user else f"ID: {user_id} (Não encontrado)"
            embed.add_field(
                name=f"👤 Usuário {idx}",
                value=f"**{username}**\nID: {user_id}",
                inline=False
            )

        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def cmd_criar_backup(self, message):
        """Cria backup manual das configurações de proteção."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        await message.channel.send("💾 Criando backup das configurações de proteção...")

        if _criar_backup():
            config = _carregar_protecao()
            ultimo_backup = config["configuracoes"].get("ultimo_backup", "N/A")
            _registrar_log("backup", "criar_backup_manual", f"Backup manual criado por {message.author.display_name}", message.author.id)
            await message.channel.send(embed=embed_imperial(
                "✅ Backup Criado",
                f"*Backup das configurações de proteção criado com sucesso.*\n\n"
                f"{SEP}\n\n"
                f"**📅 Último Backup:** {ultimo_backup[:19] if ultimo_backup != 'N/A' else 'N/A'}\n"
                f"**💾 Local:** data/protecao_imperial_backup_*.json\n\n"
                f"O backup automático diário está ativo.",
                0x2B0A3D
            ))
        else:
            await message.channel.send(embed=embed_imperial("❌ Erro no Backup", "*Ocorreu um erro ao criar o backup das configurações.*", 0x6B0000))

    async def cmd_listar_backups(self, message):
        """Lista todos os backups disponíveis."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        try:
            backup_dir = os.path.dirname("data/protecao_imperial_backup_*.json")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            # Listar arquivos de backup
            import glob
            backup_files = glob.glob("data/protecao_imperial_backup_*.json")
            backup_files.sort(reverse=True)  # Mais recentes primeiro

            if not backup_files:
                await message.channel.send(embed=embed_imperial("📭 Sem Backups", "*Nenhum backup encontrado.*", 0x2B0A3D))
                return

            embed = discord.Embed(
                title="💾 Backups Disponíveis",
                description=f"Total de {len(backup_files)} backups encontrados.\n\n{SEP}",
                color=0x2B0A3D
            )

            for idx, backup_file in enumerate(backup_files[:10], 1):  # Mostrar apenas os 10 mais recentes
                filename = os.path.basename(backup_file)
                # Extrair timestamp do nome do arquivo
                timestamp_str = filename.replace("protecao_imperial_backup_", "").replace(".json", "")
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    formatted_time = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                    file_size = os.path.getsize(backup_file)
                    size_kb = file_size / 1024
                except:
                    formatted_time = timestamp_str
                    size_kb = "N/A"

                embed.add_field(
                    name=f"📁 Backup {idx}",
                    value=f"**Arquivo:** {filename}\n**Data:** {formatted_time}\n**Tamanho:** {size_kb:.2f} KB",
                    inline=False
                )

            if len(backup_files) > 10:
                embed.add_field(
                    name="ℹ️",
                    value=f"E mais {len(backup_files) - 10} backups antigos...",
                    inline=False
                )

            embed.set_footer(text=RODAPE_IMPERIAL)
            await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌ Erro", f"*Ocorreu um erro ao listar backups: {e}*", 0x6B0000))
            print(f"Erro ao listar backups: {e}")

    async def cmd_restaurar_backup(self, message, backup_file: str = None):
        """Restaura configuração de backup."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        if not backup_file:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi restaurar-backup [nome do arquivo]*\n*Exemplo: tenshi restaurar-backup protecao_imperial_backup_20260103_120000.json*", 0x6B0000))
            return

        # Verificar se o arquivo existe
        if not backup_file.startswith("data/"):
            backup_file = f"data/{backup_file}"
        
        if not os.path.exists(backup_file):
            await message.channel.send(embed=embed_imperial("❌ Arquivo Não Encontrado", f"*O arquivo de backup não foi encontrado: {backup_file}*\n\nUse `tenshi listar-backups` para ver os backups disponíveis.", 0x6B0000))
            return

        try:
            # Criar backup atual antes de restaurar
            await message.channel.send("💾 Criando backup de segurança antes de restaurar...")
            _criar_backup()

            # Carregar backup
            with open(backup_file, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            # Restaurar configuração
            _salvar_protecao(backup_data)

            # Log e estatísticas
            _incrementar_estatistica("backups_restaurados")
            _registrar_log("backup", "restaurar_backup", f"Backup restaurado: {backup_file} por {message.author.display_name}", message.author.id)

            await message.channel.send(embed=embed_imperial(
                "✅ Backup Restaurado",
                f"*As configurações foram restauradas com sucesso do backup:* {backup_file}\n\n"
                f"{SEP}\n\n"
                f"**⚠️ Aviso:** Um backup de segurança foi criado automaticamente antes da restauração.",
                0x2B0A3D
            ))
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌ Erro ao Restaurar", f"*Ocorreu um erro ao restaurar o backup: {e}*", 0x6B0000))
            print(f"Erro ao restaurar backup: {e}")

    async def cmd_logs_protecao(self, message, filtro: str = None):
        """Mostra logs do sistema de proteção."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        logs = _carregar_logs()

        if not logs:
            await message.channel.send(embed=embed_imperial("📭 Sem Logs", "*Nenhum log registrado até o momento.*", 0x2B0A3D))
            return

        # Filtrar logs se especificado
        if filtro:
            filtro = filtro.lower()
            logs = [log for log in logs if filtro in log.get("tipo", "").lower() or filtro in log.get("acao", "").lower()]

        # Mostrar apenas os últimos 20 logs
        logs_recentes = logs[-20:]

        embed = discord.Embed(
            title="📜 Logs do Sistema de Proteção",
            description=f"Total de {len(logs)} logs registrados. Mostrando os 20 mais recentes.\n\n{SEP}",
            color=0x2B0A3D
        )

        for idx, log in enumerate(logs_recentes, 1):
            timestamp = log.get("timestamp", "Desconhecido")[:19]
            tipo = log.get("tipo", "N/A").upper()
            acao = log.get("acao", "N/A")
            detalhes = log.get("detalhes", "N/A")
            
            # Emoji baseado no tipo
            emoji = {
                "ban": "🚨",
                "alert": "⚠️",
                "whitelist": "👥",
                "backup": "💾",
                "config": "⚙️"
            }.get(tipo.lower(), "📌")

            embed.add_field(
                name=f"{emoji} Log {idx} - {tipo}",
                value=f"**Ação:** {acao}\n**Data:** {timestamp}\n**Detalhes:** {detalhes}",
                inline=False
            )

        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def cmd_estatisticas_protecao(self, message):
        """Mostra estatísticas do sistema de proteção."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        stats = config.get("estatisticas", {})
        logs = _carregar_logs()

        # Calcular taxa de falsos positivos (aproximada)
        total_acoes = stats.get("bans_automaticos", 0) + stats.get("alertas_enviados", 0)
        taxa_falsos_positivos = "N/A"
        if total_acoes > 0:
            # Assumindo que whitelist remocões podem indicar falsos positivos
            falsos_positivos = stats.get("whitelist_remocoes", 0)
            taxa = (falsos_positivos / total_acoes) * 100
            taxa_falsos_positivos = f"{taxa:.2f}%"

        embed = discord.Embed(
            title="📊 Estatísticas do Sistema de Proteção",
            description=f"Estatísticas de uso e performance do sistema.\n\n{SEP}",
            color=0x2B0A3D
        )

        embed.add_field(
            name="🚨 Ações de Segurança",
            value=(
                f"**Bans Automáticos:** {stats.get('bans_automaticos', 0)}\n"
                f"**Alertas Enviados:** {stats.get('alertas_enviados', 0)}\n"
                f"**Total de Ações:** {total_acoes}"
            ),
            inline=True
        )

        embed.add_field(
            name="👥 Whitelist",
            value=(
                f"**Adições:** {stats.get('whitelist_adicoes', 0)}\n"
                f"**Remoções:** {stats.get('whitelist_remocoes', 0)}\n"
                f"**Usuários na Whitelist:** {len(config.get('whitelist_fantasma', []))}"
            ),
            inline=True
        )

        embed.add_field(
            name="💾 Backups",
            value=(
                f"**Criados:** {stats.get('backups_criados', 0)}\n"
                f"**Restaurados:** {stats.get('backups_restaurados', 0)}"
            ),
            inline=True
        )

        embed.add_field(
            name="📈 Performance",
            value=(
                f"**Taxa de Falsos Positivos:** {taxa_falsos_positivos}\n"
                f"**Total de Logs:** {len(logs)}"
            ),
            inline=True
        )

        embed.add_field(
            name="⚙️ Configuração",
            value=(
                f"**Proteção Ativa:** {'✅ Sim' if config['configuracoes'].get('protecao_ativa', True) else '❌ Não'}\n"
                f"**Backup Automático:** {'✅ Sim' if config['configuracoes'].get('backup_automatico', True) else '❌ Não'}\n"
                f"**Modo Teste:** {'✅ Sim' if config['configuracoes'].get('modo_teste', False) else '❌ Não'}\n"
                f"**Cooldown Alertas:** {config['configuracoes'].get('cooldown_alertas', 300)}s"
            ),
            inline=True
        )

        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def cmd_config_canal_alertas(self, message, canal: discord.TextChannel = None):
        """Configura canal para alertas do sistema."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()

        if canal:
            config["configuracoes"]["canal_alertas"] = canal.id
            _salvar_protecao(config)
            _registrar_log("config", "config_canal_alertas", f"Canal de alertas configurado: {canal.name}", message.author.id)
            await message.channel.send(embed=embed_imperial(
                "✅ Canal Configurado",
                f"*O canal {canal.mention} foi configurado para receber alertas do sistema de proteção.*\n\n"
                f"{SEP}\n\n"
                f"Os alertas serão enviados para este canal além do DM ao Imperador.",
                0x2B0A3D
            ))
        else:
            # Remover configuração
            config["configuracoes"]["canal_alertas"] = None
            _salvar_protecao(config)
            _registrar_log("config", "remover_canal_alertas", "Canal de alertas removido", message.author.id)
            await message.channel.send(embed=embed_imperial(
                "✅ Canal Removido",
                f"*A configuração de canal de alertas foi removida.*\n\n"
                f"{SEP}\n\n"
                f"Os alertas serão enviados apenas via DM ao Imperador.",
                0x2B0A3D
            ))

    async def cmd_limpar_logs(self, message, dias: int = None):
        """Limpa logs antigos do sistema."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        if dias is None:
            await message.channel.send(embed=embed_imperial("❌ Uso Incorreto", "*Use: tenshi limpar-logs [dias]*\n*Exemplo: tenshi limpar-logs 7 (remove logs com mais de 7 dias)*", 0x6B0000))
            return

        logs = _carregar_logs()
        if not logs:
            await message.channel.send(embed=embed_imperial("📭 Sem Logs", "*Nenhum log para limpar.*", 0x2B0A3D))
            return

        from datetime import timedelta
        cutoff_date = datetime.now(UTC) - timedelta(days=dias)
        
        logs_filtrados = [
            log for log in logs 
            if datetime.fromisoformat(log["timestamp"]) >= cutoff_date
        ]

        logs_removidos = len(logs) - len(logs_filtrados)
        
        # Salvar logs filtrados
        os.makedirs(os.path.dirname(LOGS_FILE), exist_ok=True)
        with open(LOGS_FILE, "w", encoding="utf-8") as f:
            json.dump(logs_filtrados, f, ensure_ascii=False, indent=2)

        _registrar_log("config", "limpar_logs", f"Logs com mais de {dias} dias removidos ({logs_removidos} logs)", message.author.id)

        await message.channel.send(embed=embed_imperial(
            "✅ Logs Limpos",
            f"*{logs_removidos} logs com mais de {dias} dias foram removidos.*\n\n"
            f"{SEP}\n\n"
            f"**Logs restantes:** {len(logs_filtrados)}",
            0x2B0A3D
        ))

    async def cmd_relatorio_protecao(self, message):
        """Gera relatório detalhado do sistema de proteção."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        stats = config.get("estatisticas", {})
        logs = _carregar_logs()

        relatorio = f"""
═══════════════════════════════════════════════════════════
📊 RELATÓRIO DO SISTEMA DE PROTEÇÃO IMPERIAL
═══════════════════════════════════════════════════════════
📅 Data: {datetime.now(UTC).strftime('%d/%m/%Y %H:%M:%S')} UTC

═══════════════════════════════════════════════════════════
📈 ESTATÍSTICAS
═══════════════════════════════════════════════════════════
🚨 Bans Automáticos: {stats.get('bans_automaticos', 0)}
⚠️ Alertas Enviados: {stats.get('alertas_enviados', 0)}
👥 Whitelist Adições: {stats.get('whitelist_adicoes', 0)}
👥 Whitelist Remoções: {stats.get('whitelist_remocoes', 0)}
💾 Backups Criados: {stats.get('backups_criados', 0)}
💾 Backups Restaurados: {stats.get('backups_restaurados', 0)}

═══════════════════════════════════════════════════════════
⚙️ CONFIGURAÇÕES
═══════════════════════════════════════════════════════════
🛡️ Proteção Ativa: {'✅ SIM' if config['configuracoes'].get('protecao_ativa', True) else '❌ NÃO'}
📢 Alertar Imperador: {'✅ SIM' if config['configuracoes'].get('alertar_imperador', True) else '❌ NÃO'}
💾 Backup Automático: {'✅ SIM' if config['configuracoes'].get('backup_automatico', True) else '❌ NÃO'}
🧪 Modo Teste: {'✅ SIM' if config['configuracoes'].get('modo_teste', False) else '❌ NÃO'}
⏱️ Cooldown Alertas: {config['configuracoes'].get('cooldown_alertas', 300)} segundos
📺 Canal Alertas: {config['configuracoes'].get('canal_alertas') or 'Não configurado'}

═══════════════════════════════════════════════════════════
👥 LISTAS
═══════════════════════════════════════════════════════════
📋 Usuários Confiança: {len(config.get('usuarios_confianca', []))}
👻 Whitelist Fantasma: {len(config.get('whitelist_fantasma', []))}
🚫 Servidores Bloqueados: {len(config.get('servidores_bloqueados', []))}

═══════════════════════════════════════════════════════════
📜 LOGS
═══════════════════════════════════════════════════════════
Total de Logs: {len(logs)}
Último Backup: {config['configuracoes'].get('ultimo_backup', 'N/A')[:19] if config['configuracoes'].get('ultimo_backup') else 'N/A'}

═══════════════════════════════════════════════════════════
"""

        # Enviar como arquivo
        try:
            with open("data/relatorio_protecao.txt", "w", encoding="utf-8") as f:
                f.write(relatorio)
            
            await message.channel.send(
                "📊 Relatório gerado com sucesso!",
                file=discord.File("data/relatorio_protecao.txt", "relatorio_protecao.txt")
            )
            
            _registrar_log("config", "gerar_relatorio", "Relatório de proteção gerado", message.author.id)
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌ Erro", f"*Ocorreu um erro ao gerar o relatório: {e}*", 0x6B0000))

    async def cmd_resetar_estatisticas(self, message):
        """Reseta todas as estatísticas do sistema."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        config["estatisticas"] = {
            "bans_automaticos": 0,
            "alertas_enviados": 0,
            "whitelist_adicoes": 0,
            "whitelist_remocoes": 0,
            "backups_criados": 0,
            "backups_restaurados": 0
        }
        _salvar_protecao(config)

        _registrar_log("config", "resetar_estatisticas", "Estatísticas resetadas", message.author.id)

        await message.channel.send(embed=embed_imperial(
            "✅ Estatísticas Resetadas",
            f"*Todas as estatísticas do sistema foram zeradas.*\n\n"
            f"{SEP}\n\n"
            f"Isso é útil para começar um novo período de análise.",
            0x2B0A3D
        ))

    async def cmd_modo_teste(self, message):
        """Ativa ou desativa o modo de teste."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()
        modo_atual = config["configuracoes"].get("modo_teste", False)
        novo_modo = not modo_atual
        
        config["configuracoes"]["modo_teste"] = novo_modo
        _salvar_protecao(config)

        _registrar_log("config", "modo_teste", f"Modo teste {'ativado' if novo_modo else 'desativado'}", message.author.id)

        if novo_modo:
            await message.channel.send(embed=embed_imperial(
                "🧪 Modo Teste Ativado",
                f"*O modo de teste foi ativado.*\n\n"
                f"{SEP}\n\n"
                f"**⚠️ Avisos:**\n"
                f"• Bans automáticos serão SIMULADOS (não executados)\n"
                f"• Alertas serão enviados indicando simulação\n"
                f"• Útil para testar o sistema sem riscos\n\n"
                f"Use `tenshi modo-teste` novamente para desativar.",
                0xFF6600
            ))
        else:
            await message.channel.send(embed=embed_imperial(
                "✅ Modo Teste Desativado",
                f"*O modo de teste foi desativado.*\n\n"
                f"{SEP}\n\n"
                f"**🛡️ Sistema Normal:**\n"
                f"• Bans automáticos serão executados normalmente\n"
                f"• O sistema está operando em modo de produção.",
                0x2B0A3D
            ))

    async def cmd_reputacao(self, message, member: discord.Member = None):
        """Mostra reputação de um usuário."""
        target = member or message.author
        
        reputacao = _obter_reputacao(target.id)
        
        # Determinar nível baseado na reputação
        if reputacao >= 50:
            nivel = "🌟 Excelente"
            cor = 0x00FF00
        elif reputacao >= 20:
            nivel = "✅ Boa"
            cor = 0x00AA00
        elif reputacao >= 0:
            nivel = "😐 Neutra"
            cor = 0xFFFF00
        elif reputacao >= -30:
            nivel = "⚠️ Baixa"
            cor = 0xFF6600
        else:
            nivel = "🚨 Muito Baixa"
            cor = 0xFF0000
        
        embed = discord.Embed(
            title=f"⭐ Reputação - {target.display_name}",
            description=f"{SEP}\n\n"
            f"**Pontuação:** {reputacao}/100\n"
            f"**Nível:** {nivel}\n\n"
            f"{SEP}\n\n"
            f"**📊 Impacto:**\n"
            f"• Usuários com reputação baixa são mais monitorados\n"
            f"• Reputação alta indica confiança no sistema\n"
            f"• Ajuste manual disponível para administradores",
            color=cor
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=RODAPE_IMPERIAL)
        await message.channel.send(embed=embed)

    async def cmd_ajustar_reputacao(self, message, member: discord.Member, pontos: int):
        """Ajusta reputação de um usuário manualmente."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        if pontos < -50 or pontos > 50:
            await message.channel.send(embed=embed_imperial("❌ Valor Inválido", "*Pontos devem estar entre -50 e +50*", 0x6B0000))
            return

        nova_reputacao = _ajustar_reputacao(member.id, pontos)
        
        _registrar_log("config", "ajustar_reputacao", f"Reputação de {member.display_name} ajustada em {pontos} pontos (nova: {nova_reputacao})", message.author.id, member.id)

        await message.channel.send(embed=embed_imperial(
            "✅ Reputação Ajustada",
            f"*A reputação de {member.display_name} foi ajustada em {pontos} pontos.*\n\n"
            f"{SEP}\n\n"
            f"**Nova Reputação:** {nova_reputacao}/100",
            0x2B0A3D
        ))

    async def cmd_whitelist_temp(self, message, member: discord.Member, dias: int):
        """Adiciona usuário à whitelist temporária."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        if dias < 1 or dias > 365:
            await message.channel.send(embed=embed_imperial("❌ Valor Inválido", "*Dias devem estar entre 1 e 365*", 0x6B0000))
            return

        _adicionar_whitelist_temporaria(member.id, dias)
        
        _registrar_log("whitelist", "whitelist_temporaria", f"{member.display_name} adicionado à whitelist temporária por {dias} dias", message.author.id, member.id)

        await message.channel.send(embed=embed_imperial(
            "✅ Whitelist Temporária Adicionada",
            f"*{member.display_name} foi adicionado à whitelist temporária por {dias} dias.*\n\n"
            f"{SEP}\n\n"
            f"**⏰ Expira em:** {dias} dias\n"
            f"**Após expirar:** O usuário voltará a ser analisado normalmente",
            0x2B0A3D
        ))

    async def cmd_config_quarentena(self, message, canal: discord.TextChannel = None):
        """Configura canal de quarentena para usuários suspeitos."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()

        if canal:
            config["configuracoes"]["canal_quarentena"] = canal.id
            _salvar_protecao(config)
            _registrar_log("config", "config_quarentena", f"Canal de quarentena configurado: {canal.name}", message.author.id)
            await message.channel.send(embed=embed_imperial(
                "✅ Canal de Quarentena Configurado",
                f"*O canal {canal.mention} foi configurado como quarentena.*\n\n"
                f"{SEP}\n\n"
                f"**⚠️ Funcionalidade:**\n"
                f"• Usuários suspeitos podem ser movidos para este canal\n"
                f"• Sistema de verificação pode ser implementado\n"
                f"• Útil para triagem de novos membros",
                0x2B0A3D
            ))
        else:
            config["configuracoes"]["canal_quarentena"] = None
            _salvar_protecao(config)
            _registrar_log("config", "remover_quarentena", "Canal de quarentena removido", message.author.id)
            await message.channel.send(embed=embed_imperial(
                "✅ Canal de Quarentena Removido",
                f"*A configuração de canal de quarentena foi removida.*",
                0x2B0A3D
            ))

    async def cmd_config_honeypot(self, message, canal: discord.TextChannel = None):
        """Configura canal honeypot para atrair bots."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        config = _carregar_protecao()

        if canal:
            config["configuracoes"]["canal_honeypot"] = canal.id
            _salvar_protecao(config)
            _registrar_log("config", "config_honeypot", f"Canal honeypot configurado: {canal.name}", message.author.id)
            await message.channel.send(embed=embed_imperial(
                "✅ Canal Honeypot Configurado",
                f"*O canal {canal.mention} foi configurado como honeypot.*\n\n"
                f"{SEP}\n\n"
                f"**⚠️ Funcionalidade:**\n"
                f"• Usuários que entrarem neste canal serão banidos\n"
                f"• Útil para detectar bots e spam\n"
                f"• Mantenha este canal oculto ou restrito",
                0xFF6600
            ))
        else:
            config["configuracoes"]["canal_honeypot"] = None
            _salvar_protecao(config)
            _registrar_log("config", "remover_honeypot", "Canal honeypot removido", message.author.id)
            await message.channel.send(embed=embed_imperial(
                "✅ Canal Honeypot Removido",
                f"*A configuração de canal honeypot foi removida.*",
                0x2B0A3D
            ))

    async def cmd_config_relatorio(self, message, frequencia: str = None):
        """Configura frequência de relatórios automáticos."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        if frequencia not in ["diario", "semanal", "mensal", "desativar"]:
            await message.channel.send(embed=embed_imperial("❌ Valor Inválido", "*Use: tenshi config-relatorio [diario/semanal/mensal/desativar]*", 0x6B0000))
            return

        config = _carregar_protecao()
        
        if frequencia == "desativar":
            config["configuracoes"]["relatorio_frequencia"] = None
            _registrar_log("config", "desativar_relatorio", "Relatórios automáticos desativados", message.author.id)
            await message.channel.send(embed=embed_imperial(
                "✅ Relatórios Desativados",
                f"*Os relatórios automáticos foram desativados.*",
                0x2B0A3D
            ))
        else:
            config["configuracoes"]["relatorio_frequencia"] = frequencia
            _salvar_protecao(config)
            _registrar_log("config", "config_relatorio", f"Relatórios configurados: {frequencia}", message.author.id)
            await message.channel.send(embed=embed_imperial(
                "✅ Relatórios Configurados",
                f"*Os relatórios automáticos foram configurados para frequência: {frequencia}.*\n\n"
                f"{SEP}\n\n"
                f"**📊 O relatório incluirá:**\n"
                f"• Resumo de bans e alertas\n"
                f"• Estatísticas do sistema\n"
                f"• Performance e métricas",
                0x2B0A3D
            ))

    async def cmd_bloquear_servidor(self, message, guild_id: int):
        """Bloqueia um servidor específico."""
        if message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas o Imperador pode bloquear servidores.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "servidores_bloqueados" not in config:
            config["servidores_bloqueados"] = []

        if guild_id in config["servidores_bloqueados"]:
            await message.channel.send(embed=embed_imperial("ℹ️ Já Bloqueado", f"*O servidor {guild_id} já está bloqueado.*", 0x6B0000))
            return

        config["servidores_bloqueados"].append(guild_id)
        _salvar_protecao(config)

        await message.channel.send(embed=embed_imperial("✅ Servidor Bloqueado", f"*O servidor {guild_id} foi bloqueado pelo Imperador.*", 0x2B0A3D))

    async def cmd_desbloquear_servidor(self, message, guild_id: int):
        """Desbloqueia um servidor específico."""
        if message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas o Imperador pode desbloquear servidores.*", 0x6B0000))
            return

        config = _carregar_protecao()
        if "servidores_bloqueados" not in config:
            config["servidores_bloqueados"] = []

        if guild_id not in config["servidores_bloqueados"]:
            await message.channel.send(embed=embed_imperial("ℹ️ Não Bloqueado", f"*O servidor {guild_id} não está bloqueado.*", 0x6B0000))
            return

        config["servidores_bloqueados"].remove(guild_id)
        _salvar_protecao(config)

        await message.channel.send(embed=embed_imperial("✅ Servidor Desbloqueado", f"*O servidor {guild_id} foi desbloqueado pelo Imperador.*", 0x2B0A3D))

    async def cmd_atividade_suspeita(self, message, member: Optional[discord.Member] = None):
        """Verifica atividade suspeita de um usuário."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        target = member or message.author
        config = _carregar_protecao()
        atividades = config.get("atividade_suspeita", {}).get(target.id, [])

        if not atividades:
            await message.channel.send(embed=embed_imperial("✅ Nenhuma Atividade", f"*{target.display_name} não possui atividades suspeitas registradas.*", 0x2B0A3D))
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
        await message.channel.send(embed=embed)

    async def cmd_teste_protecao(self, message, member: Optional[discord.Member] = None):
        """Testa a detecção de conta fantasma em um usuário."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        target = member or message.author
        
        await message.channel.send("🔍 Analisando perfil para detecção de conta fantasma...")
        
        try:
            status_fantasma = await self._eh_conta_fantasma(target)
            
            # Calcular servidores em comum com tratamento de erro
            try:
                servidores_comum = len([g for g in target.mutual_guilds if g.id != message.guild.id])
            except Exception:
                servidores_comum = 0
            
            # Formatar datas com tratamento de erro
            try:
                data_criacao = target.created_at.strftime('%d/%m/%Y %H:%M') if target.created_at else 'N/A'
            except Exception:
                data_criacao = 'N/A'
            
            try:
                data_entrada = target.joined_at.strftime('%d/%m/%Y %H:%M') if target.joined_at else 'N/A'
            except Exception:
                data_entrada = 'N/A'
            
            # Calcular dias da conta
            try:
                dias_conta = (datetime.now(UTC) - target.created_at).days if target.created_at else 0
            except Exception:
                dias_conta = 0
            
            if status_fantasma == "ban":
                embed = discord.Embed(
                    title="🚨 Conta Fantasma - BAN AUTOMÁTICO",
                    description=(
                        f"**Usuário:** {target.display_name} ({target.id})\n\n"
                        f"{SEP}\n\n"
                        "**🔍 Análise:**\n"
                        f"• Conta criada em: {data_criacao}\n"
                        f"• Idade da conta: {dias_conta} dias\n"
                        f"• Entrou no servidor em: {data_entrada}\n"
                        f"• Avatar: {'✅ Sim' if target.avatar else '❌ Não'}\n"
                        f"• Servidores em comum: {servidores_comum}\n\n"
                        "**⚠️ Resultado:** Esta conta será BANIDA automaticamente (< 1 dia).\n\n"
                        "**🛡️ Ação Recomendada:** Banimento automático se a proteção estiver ativa."
                    ),
                    color=0xFF0000
                )
                embed.set_thumbnail(url=target.display_avatar.url if target.avatar else None)
                embed.set_footer(text=RODAPE_IMPERIAL)
            elif status_fantasma == "alert":
                embed = discord.Embed(
                    title="⚠️ Conta Nova - ALERTA",
                    description=(
                        f"**Usuário:** {target.display_name} ({target.id})\n\n"
                        f"{SEP}\n\n"
                        "**🔍 Análise:**\n"
                        f"• Conta criada em: {data_criacao}\n"
                        f"• Idade da conta: {dias_conta} dias\n"
                        f"• Entrou no servidor em: {data_entrada}\n"
                        f"• Avatar: {'✅ Sim' if target.avatar else '❌ Não'}\n"
                        f"• Servidores em comum: {servidores_comum}\n\n"
                        "**⚠️ Resultado:** Esta conta gerará ALERTA (1-3 dias).\n\n"
                        "**🛡️ Ação Recomendada:** Monitoramento. Use `tenshi whitelist-fantasma @usuario` para adicionar à whitelist se for confiável."
                    ),
                    color=0xFF6600
                )
                embed.set_thumbnail(url=target.display_avatar.url if target.avatar else None)
                embed.set_footer(text=RODAPE_IMPERIAL)
            else:
                embed = discord.Embed(
                    title="✅ Conta Legítima",
                    description=(
                        f"**Usuário:** {target.display_name} ({target.id})\n\n"
                        f"{SEP}\n\n"
                        "**🔍 Análise:**\n"
                        f"• Conta criada em: {data_criacao}\n"
                        f"• Idade da conta: {dias_conta} dias\n"
                        f"• Entrou no servidor em: {data_entrada}\n"
                        f"• Avatar: {'✅ Sim' if target.avatar else '❌ Não'}\n"
                        f"• Servidores em comum: {servidores_comum}\n\n"
                        "**✅ Resultado:** Esta conta foi classificada como LEGÍTIMA pelo sistema.\n\n"
                        "**🛡️ Status:** Sem risco de banimento ou alerta automático."
                    ),
                    color=0x2B0A3D
                )
                embed.set_thumbnail(url=target.display_avatar.url if target.avatar else None)
                embed.set_footer(text=RODAPE_IMPERIAL)
            
            await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(embed=embed_imperial("❌ Erro no Teste", f"*Ocorreu um erro ao analisar o perfil: {e}*", 0x6B0000))
            print(f"Erro no cmd_teste_protecao: {e}")

    async def cmd_parceria(self, message, invite_link: str):
        """Gera embed de parceria a partir de link de convite."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem criar propostas de parceria.*", 0x6B0000))
            return

        await message.channel.send("🔍 Analisando servidor do link de convite...")

        info_servidor = await self._extrair_info_servidor(invite_link)
        if not info_servidor:
            await message.channel.send(embed=embed_imperial("❌ Link Inválido", "*Não foi possível obter informações do servidor. Verifique o link de convite.*", 0x6B0000))
            return

        await message.channel.send("✨ Gerando proposta de parceria com IA...")

        embed = await self._gerar_embed_parceria(info_servidor)

        # Salvar no histórico
        parcerias = _carregar_parcerias()
        parcerias["historico"].append({
            "servidor": info_servidor["nome"],
            "servidor_id": info_servidor["id"],
            "codigo": info_servidor["codigo"],
            "criado_por": message.author.id,
            "timestamp": datetime.now(UTC).isoformat()
        })
        _salvar_parcerias(parcerias)

        await message.channel.send(embed=embed)

    async def cmd_historico_parcerias(self, message):
        """Mostra histórico de parcerias."""
        if not await self._verificar_acesso_admin(message.author):
            await message.channel.send(embed=embed_imperial("🚫 Acesso Negado", "*Apenas administradores podem acessar este comando.*", 0x6B0000))
            return

        parcerias = _carregar_parcerias()
        historico = parcerias.get("historico", [])

        if not historico:
            await message.channel.send(embed=embed_imperial("📭 Histórico Vazio", "*Nenhuma parceria foi registrada até o momento.*", 0x2B0A3D))
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
        await message.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Verifica novos membros ao entrarem no servidor."""
        config = _carregar_protecao()
        if not config["configuracoes"].get("protecao_ativa", True):
            return

        modo_teste = config["configuracoes"].get("modo_teste", False)

        # Verificar se é conta fantasma - BAN ou ALERTA
        status_fantasma = await self._eh_conta_fantasma(member)
        
        if status_fantasma == "ban":
            await self._registrar_atividade_suspeita(
                member.id,
                f"Conta fantasma detectada - Ban automático"
            )
            
            acao_real = "SIMULAÇÃO" if modo_teste else "REAL"
            
            if modo_teste:
                # Modo teste - apenas log e alerta
                _registrar_log("ban", "ban_simulado", f"[MODO TESTE] Usuário {member.display_name} seria banido (conta fantasma)", target_id=member.id)
                await self._alertar_imperador(
                    f"🧪 [MODO TESTE] Ban Simulado - Conta Fantasma",
                    f"O usuário **{member.display_name}** ({member.id}) seria banido automaticamente por ser uma conta fantasma.\n\n"
                    f"**Ação:** {acao_real}\n"
                    f"**Conta criada em:** {member.created_at}\n"
                    f"**Entrou em:** {member.joined_at}\n"
                    f"**Avatar:** {'Sim' if member.avatar else 'Não'}\n\n"
                    f"Esta ação foi SIMULADA pelo sistema de proteção imperial."
                )
                return
            
            try:
                await member.ban(reason="Conta fantasma detectada pelo sistema de proteção imperial")
                
                # Log e estatísticas
                _incrementar_estatistica("bans_automaticos")
                _registrar_log("ban", "ban_automatico", f"Usuário {member.display_name} banido automaticamente (conta fantasma)", target_id=member.id)
                
                await self._alertar_imperador(
                    "🚨 Ban Automático - Conta Fantasma",
                    f"O usuário **{member.display_name}** ({member.id}) foi banido automaticamente por ser uma conta fantasma.\n\n"
                    f"**Ação:** {acao_real}\n"
                    f"**Conta criada em:** {member.created_at}\n"
                    f"**Entrou em:** {member.joined_at}\n"
                    f"**Avatar:** {'Sim' if member.avatar else 'Não'}\n\n"
                    f"Esta ação foi executada automaticamente pelo sistema de proteção imperial."
                )
                return
            except discord.Forbidden:
                _registrar_log("ban", "falha_ban", f"Falha ao banir {member.display_name} - sem permissão", target_id=member.id)
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
        
        elif status_fantasma == "alert":
            # Verificar cooldown
            if _verificar_cooldown(member.id):
                print(f"Alerta para {member.display_name} ignorado por cooldown")
                return
            
            await self._registrar_atividade_suspeita(
                member.id,
                f"Conta nova detectada - Alerta (1-3 dias)"
            )
            
            # Definir cooldown
            _definir_cooldown(member.id)
            
            # Log e estatísticas
            _incrementar_estatistica("alertas_enviados")
            _registrar_log("alert", "alerta_conta_nova", f"Alerta enviado para conta nova: {member.display_name}", target_id=member.id)
            
            await self._alertar_imperador(
                "⚠️ Alerta - Conta Nova",
                f"O usuário **{member.display_name}** ({member.id}) entrou no servidor com uma conta recente (1-3 dias).\n\n"
                f"**Conta criada em:** {member.created_at}\n"
                f"**Entrou em:** {member.joined_at}\n"
                f"**Avatar:** {'Sim' if member.avatar else 'Não'}\n\n"
                f"⚠️ Esta conta não foi banida automaticamente, mas requer atenção.\n"
                f"Use `tenshi whitelist-fantasma @usuario` para adicionar à whitelist se for confiável."
            )

        # Verificar comportamento suspeito
        if await self._verificar_comportamento_suspeito(member):
            _registrar_log("alert", "comportamento_suspeito", f"Comportamento suspeito detectado: {member.display_name}", target_id=member.id)
            await self._alertar_imperador(
                "Novo Membro Suspeito",
                f"O usuário **{member.display_name}** ({member.id}) entrou no servidor e apresenta comportamento suspeito.\n\n"
                f"**Conta criada em:** {member.created_at}\n"
                f"**Entrou em:** {member.joined_at}"
            )

    @commands.Cog.listener()
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
