"""Painel Administrativo Imperial - Controle Completo do Bot"""

import discord
from discord.ext import commands
from database import get_user, save_user, get_all_users
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial
from cogs.parentesco import aplicar_parentesco, VINCULOS
from datetime import datetime

COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x6B7280
COR_INFO = 0x3498DB


def _tem_autoridade(member):
    """Verifica se o membro tem autoridade administrativa."""
    if member.id == IMPERADOR_ID:
        return True
    try:
        return member.guild_permissions.administrator
    except:
        return False


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO, thumbnail_url: str = None) -> discord.Embed:
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=cor,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=RODAPE_IMPERIAL)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    return embed


class EditarUsuarioModal(discord.ui.Modal, title="Editar Usuário Completo"):
    xp = discord.ui.TextInput(label="XP", placeholder="Ex: 1000", required=False, max_length=10)
    poder = discord.ui.TextInput(label="Poder", placeholder="Ex: 100", required=False, max_length=10)
    nivel_manual = discord.ui.TextInput(label="Nível Manual (deixe vazio para auto)", placeholder="Ex: 10", required=False, max_length=5)
    moedas = discord.ui.TextInput(label="Moedas", placeholder="Ex: 500", required=False, max_length=15)
    banco = discord.ui.TextInput(label="Banco", placeholder="Ex: 1000", required=False, max_length=15)
    titulo = discord.ui.TextInput(label="Título Personalizado", placeholder="Ex: Cavaleiro das Sombras", required=False, max_length=50)
    pegada = discord.ui.TextInput(label="Pegada (imperial/familia/mafia/enterprise)", placeholder="Ex: imperial", required=False, max_length=20)

    def __init__(self, alvo: discord.Member, admin_id: int):
        super().__init__()
        self.alvo = alvo
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            user = get_user(self.alvo.id)
            
            if self.xp.value.strip():
                user["xp"] = int(self.xp.value)
            if self.poder.value.strip():
                user["poder"] = int(self.poder.value)
            if self.nivel_manual.value.strip():
                user["nivel_manual"] = int(self.nivel_manual.value)
            if self.moedas.value.strip():
                user["moedas"] = int(self.moedas.value)
            if self.banco.value.strip():
                user["conta_banco"] = int(self.banco.value)
            if self.titulo.value.strip():
                user["titulo"] = self.titulo.value
            if self.pegada.value.strip() and self.pegada.value.lower() in ["imperial", "familia", "mafia", "enterprise"]:
                user["pegada"] = self.pegada.value.lower()
            
            save_user(self.alvo.id, user)
            
            await interaction.followup.send(
                f"✅ {self.alvo.mention} editado com sucesso!\n"
                f"XP: {user.get('xp', 0)} | Poder: {user.get('poder', 0)} | Nível: {user.get('nivel_manual', 'auto')}",
                ephemeral=True
            )
        except ValueError:
            await interaction.followup.send("❌ Valores inválidos. Use números inteiros.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class GerenciarMembroModal(discord.ui.Modal, title="Gerenciar Membro da Família"):
    nome = discord.ui.TextInput(label="Nome do vínculo", placeholder="Ex: Filho, Irmã, Tio", max_length=50)
    emoji = discord.ui.TextInput(label="Emoji", placeholder="Ex: 👦", required=False, max_length=20)

    def __init__(self, alvo: discord.Member, admin_id: int):
        super().__init__()
        self.alvo = alvo
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            nome = self.nome.value.strip()
            emoji = self.emoji.value.strip() or "👤"
            
            cargo = await aplicar_parentesco(self.alvo, nome, emoji, interaction.user.id, "admin_painel")
            
            await interaction.followup.send(
                f"✅ {self.alvo.mention} agora é **{nome}** {emoji}\nCargo aplicado: {cargo.mention}",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ Não tenho permissão para aplicar cargos.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class CargoPersonalizadoModal(discord.ui.Modal, title="Criar Cargo Personalizado"):
    emoji = discord.ui.TextInput(label="Emoji do Cargo", placeholder="Ex: ⚔️", max_length=10)
    nome = discord.ui.TextInput(label="Nome do Cargo", placeholder="Ex: Cavaleiro das Sombras", max_length=50)

    def __init__(self, alvo: discord.Member, admin_id: int):
        super().__init__()
        self.alvo = alvo
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            emoji = self.emoji.value.strip() or "🏷️"
            nome = self.nome.value.strip()
            
            if not nome:
                await interaction.followup.send("❌ Nome do cargo é obrigatório.", ephemeral=True)
                return
            
            cargo_nome = f" ͎ᵎ  ⊰ {emoji} {nome} ⊰ 最"
            
            try:
                role = await interaction.guild.create_role(
                    name=cargo_nome[:100],
                    color=discord.Color(0x9E7815),
                    mentionable=True,
                    reason=f"Cargo personalizado criado por {interaction.user} via painel admin"
                )
                
                await self.alvo.add_roles(role)
                
                await interaction.followup.send(
                    f"✅ Cargo criado e aplicado!\n**Nome:** {cargo_nome}\n**Aplicado para:** {self.alvo.mention}",
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.followup.send("❌ Não tenho permissão para criar/aplicar cargos.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class SelecionarMembroSelect(discord.ui.UserSelect):
    def __init__(self, admin_id: int):
        super().__init__(placeholder="Selecione um membro para gerenciar")
        self.admin_id = admin_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Este painel pertence a outro administrador.", ephemeral=True)
            return
        
        alvo = self.values[0]
        view = AcoesMembroView(alvo, self.admin_id)
        user = get_user(alvo.id)
        
        embed = _embed(
            f"👤 Gerenciar {alvo.display_name}",
            f"**ID:** {alvo.id}\n"
            f"**XP:** {user.get('xp', 0)} | **Poder:** {user.get('poder', 0)} | **Nível:** {user.get('nivel_manual', 'auto')}\n"
            f"**Moedas:** {user.get('moedas', 0)} | **Banco:** {user.get('conta_banco', 0)}\n"
            f"**Título:** {user.get('titulo', '—')} | **Pegada:** {user.get('pegada', 'imperial')}",
            COR_DOURADO
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


class AcoesMembroView(discord.ui.View):
    def __init__(self, alvo: discord.Member, admin_id: int):
        super().__init__(timeout=600)
        self.alvo = alvo
        self.admin_id = admin_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="✏️ Editar Usuário", style=discord.ButtonStyle.primary, row=1)
    async def editar_usuario(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditarUsuarioModal(self.alvo, self.admin_id))

    @discord.ui.button(label="👨‍👩‍👧 Parentesco", style=discord.ButtonStyle.secondary, row=1)
    async def parentesco(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GerenciarMembroModal(self.alvo, self.admin_id))

    @discord.ui.button(label="🏷️ Cargo Personalizado", style=discord.ButtonStyle.secondary, row=1)
    async def cargo_personalizado(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CargoPersonalizadoModal(self.alvo, self.admin_id))

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class PainelPrincipalView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Abra seu próprio painel com `tenshi painel-admin`.", ephemeral=True)
        return False

    @discord.ui.button(label="👤 Usuários", style=discord.ButtonStyle.primary, emoji="👤", row=1)
    async def gerenciar_usuarios(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = GerenciarUsuariosView(self.admin_id)
        embed = _embed(
            "👤 Gerenciar Usuários",
            "Selecione um usuário para editar suas informações.\n\n"
            "**Funções disponíveis:**\n"
            "• Editar XP, Poder, Nível, Moedas, Banco\n"
            "• Definir Título e Pegada\n"
            "• Configurar Parentesco\n"
            "• Criar Cargos Personalizados",
            COR_DOURADO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="💰 Economia", style=discord.ButtonStyle.success, emoji="💰", row=1)
    async def economia(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = EconomiaView(self.admin_id)
        embed = _embed(
            "💰 Controle Econômico",
            "Gerencie a economia do servidor.\n\n"
            "**Funções disponíveis:**\n"
            "• Dar Moedas para usuários\n"
            "• Adicionar saldo no Banco\n"
            "• Gerenciar transações",
            COR_SUCESSO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="⚔️ RPG", style=discord.ButtonStyle.primary, emoji="⚔️", row=1)
    async def rpg(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RPGView(self.admin_id)
        embed = _embed(
            "⚔️ Sistema RPG",
            "Gerencie o sistema de RPG.\n\n"
            "**Funções disponíveis:**\n"
            "• Dar XP para usuários\n"
            "• Adicionar Poder\n"
            "• Gerenciar progresso",
            COR_DOURADO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🛡️ Moderação", style=discord.ButtonStyle.danger, emoji="🛡️", row=2)
    async def moderacao(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ModeracaoView(self.admin_id)
        embed = _embed(
            "🛡️ Moderação",
            "Ferramentas de moderação do servidor.\n\n"
            "**Funções disponíveis:**\n"
            "• Enviar Decretos Imperiais\n"
            "• Gerenciar punições\n"
            "• Controlar cargos do servidor",
            COR_PERIGO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="👨‍👩‍👧 Família", style=discord.ButtonStyle.secondary, emoji="👨‍👩‍👧", row=2)
    async def familia(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = FamiliaView(self.admin_id)
        embed = _embed(
            "👨‍👩‍👧 Sistema Familiar",
            "Gerencie famílias e parentesco.\n\n"
            "**Funções disponíveis:**\n"
            "• Visualizar Árvore Familiar\n"
            "• Ver Vínculos disponíveis\n"
            "• Gerenciar relações",
            COR_INFO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🎭 Perfil", style=discord.ButtonStyle.secondary, emoji="🎭", row=2)
    async def perfil(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PerfilView(self.admin_id)
        embed = _embed(
            "🎭 Gerenciar Perfis",
            "Gerencie perfis dos usuários.\n\n"
            "**Funções disponíveis:**\n"
            "• Dar Títulos Personalizados\n"
            "• Editar fichas de personagem\n"
            "• Gerenciar conquistas",
            COR_INFO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🎪 Eventos", style=discord.ButtonStyle.success, emoji="🎪", row=3)
    async def eventos(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = EventosView(self.admin_id)
        embed = _embed(
            "🎪 Eventos",
            "Gerencie eventos do servidor.\n\n"
            "**Funções disponíveis:**\n"
            "• Criar Sorteios\n"
            "• Gerenciar Invasões\n"
            "• Controlar eventos especiais",
            COR_SUCESSO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🎵 Música", style=discord.ButtonStyle.secondary, emoji="🎵", row=3)
    async def musica(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = MusicaView(self.admin_id)
        embed = _embed(
            "🎵 Sistema de Música",
            "Controle o sistema de música.\n\n"
            "**Funções disponíveis:**\n"
            "• Parar música atual\n"
            "• Gerenciar fila\n"
            "• Controlar volume",
            COR_INFO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🎮 Jogos", style=discord.ButtonStyle.secondary, emoji="🎮", row=3)
    async def jogos(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = JogosView(self.admin_id)
        embed = _embed(
            "🎮 Jogos",
            "Gerencie mini-jogos.\n\n"
            "**Funções disponíveis:**\n"
            "• Criar Quizzes\n"
            "• Gerenciar recompensas\n"
            "• Controlar jogos ativos",
            COR_INFO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📊 Estatísticas", style=discord.ButtonStyle.primary, emoji="📊", row=4)
    async def estatisticas(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = EstatisticasView(self.admin_id)
        total_users = len(get_all_users())
        embed = _embed(
            "📊 Estatísticas do Servidor",
            f"**Total de Usuários:** {total_users}\n"
            f"**Data:** {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}\n\n"
            "Selecione uma estatística para visualizar detalhes.",
            COR_INFO
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="❌ Fechar", style=discord.ButtonStyle.danger, emoji="❌", row=4)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(
            embed=_embed("📕 Painel Encerrado", "Use `tenshi painel-admin` quando precisar novamente.", COR_NEUTRO),
            view=None
        )


class EstatisticasView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="👥 Usuários Ativos", style=discord.ButtonStyle.primary, row=1)
    async def usuarios_ativos(self, interaction: discord.Interaction, button: discord.ui.Button):
        all_users = get_all_users()
        total = len(all_users)
        
        # Contar usuários com XP > 0
        ativos = sum(1 for u in all_users.values() if u.get('xp', 0) > 0)
        
        embed = _embed(
            "👥 Estatísticas de Usuários",
            f"**Total de Usuários:** {total}\n"
            f"**Usuários Ativos:** {ativos}\n"
            f"**Taxa de Atividade:** {(ativos/total*100):.1f}%\n\n"
            f"Usuários ativos são aqueles com XP > 0.",
            COR_INFO
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="💰 Economia Total", style=discord.ButtonStyle.success, row=1)
    async def economia_total(self, interaction: discord.Interaction, button: discord.ui.Button):
        all_users = get_all_users()
        
        total_moedas = sum(u.get('moedas', 0) for u in all_users.values())
        total_banco = sum(u.get('conta_banco', 0) for u in all_users.values())
        
        embed = _embed(
            "💰 Estatísticas Econômicas",
            f"**Moedas em Circulação:** {total_moedas:,}\n"
            f"**Moedas no Banco:** {total_banco:,}\n"
            f"**Total da Economia:** {total_moedas + total_banco:,}\n\n"
            f"Valores atualizados em tempo real.",
            COR_SUCESSO
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class GerenciarUsuariosView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id
        self.add_item(SelecionarMembroSelect(admin_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="🌳 Árvore Familiar", style=discord.ButtonStyle.secondary, row=1)
    async def arvore_familiar(self, interaction: discord.Interaction, button: discord.ui.Button):
        grupos = {}
        for uid, user in get_all_users().items():
            try:
                member = interaction.guild.get_member(int(uid))
            except (TypeError, ValueError):
                continue
            if not member or member.bot:
                continue
            vinculo = user.get("parentesco") or "Membro"
            emoji = user.get("parentesco_emoji") or "👤"
            grupos.setdefault(f"{emoji} {vinculo}", []).append(member.mention)

        linhas = []
        for vinculo, membros in sorted(grupos.items(), key=lambda x: (x[0] != "👑 Patriarca da Família", x[0])):
            exibidos = ", ".join(membros[:10])
            restante = f" e mais {len(membros) - 10}" if len(membros) > 10 else ""
            linhas.append(f"### {vinculo}\n{exibidos}{restante}")

        descricao = "\n\n".join(linhas) or "Nenhum parentesco registrado."
        embed = _embed("🌳 Árvore da Família Imperial", descricao, COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="📚 Vínculos", style=discord.ButtonStyle.secondary, row=1)
    async def vinculos(self, interaction: discord.Interaction, button: discord.ui.Button):
        linhas = [f"{emoji} **{nome}**" for nome, emoji in VINCULOS.values()]
        descricao = "Vínculos disponíveis:\n\n" + "\n".join(linhas)
        embed = _embed("📚 Vínculos Disponíveis", descricao, COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class EconomiaView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id
        self.add_item(SelecionarMembroSelect(admin_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="💸 Dar Moedas", style=discord.ButtonStyle.primary, row=1)
    async def dar_moedas(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DarMoedasModal(self.admin_id))

    @discord.ui.button(label="🏦 Dar Banco", style=discord.ButtonStyle.primary, row=1)
    async def dar_banco(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DarBancoModal(self.admin_id))

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class DarMoedasModal(discord.ui.Modal, title="Dar Moedas"):
    usuario = discord.ui.TextInput(label="ID do Usuário ou @menção", placeholder="Ex: 123456789 ou @usuario", max_length=50)
    quantidade = discord.ui.TextInput(label="Quantidade", placeholder="Ex: 1000", max_length=15)

    def __init__(self, admin_id: int):
        super().__init__()
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            user_input = self.usuario.value.strip()
            quantidade = int(self.quantidade.value)
            
            if user_input.startswith("<@") and user_input.endswith(">"):
                user_id = int(user_input[2:-1].replace("!", ""))
            else:
                user_id = int(user_input)
            
            user = get_user(user_id)
            user["moedas"] = user.get("moedas", 0) + quantidade
            save_user(user_id, user)
            
            await interaction.followup.send(f"✅ {quantidade} moedas adicionadas para <@{user_id}>!", ephemeral=True)
        except ValueError:
            await interaction.followup.send("❌ Valores inválidos.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class DarBancoModal(discord.ui.Modal, title="Dar Banco"):
    usuario = discord.ui.TextInput(label="ID do Usuário ou @menção", placeholder="Ex: 123456789 ou @usuario", max_length=50)
    quantidade = discord.ui.TextInput(label="Quantidade", placeholder="Ex: 1000", max_length=15)

    def __init__(self, admin_id: int):
        super().__init__()
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            user_input = self.usuario.value.strip()
            quantidade = int(self.quantidade.value)
            
            if user_input.startswith("<@") and user_input.endswith(">"):
                user_id = int(user_input[2:-1].replace("!", ""))
            else:
                user_id = int(user_input)
            
            user = get_user(user_id)
            user["conta_banco"] = user.get("conta_banco", 0) + quantidade
            save_user(user_id, user)
            
            await interaction.followup.send(f"✅ {quantidade} moedas no banco adicionadas para <@{user_id}>!", ephemeral=True)
        except ValueError:
            await interaction.followup.send("❌ Valores inválidos.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class RPGView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id
        self.add_item(SelecionarMembroSelect(admin_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="💪 Dar XP", style=discord.ButtonStyle.primary, row=1)
    async def dar_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DarXPModal(self.admin_id))

    @discord.ui.button(label="⚡ Dar Poder", style=discord.ButtonStyle.primary, row=1)
    async def dar_poder(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DarPoderModal(self.admin_id))

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class DarXPModal(discord.ui.Modal, title="Dar XP"):
    usuario = discord.ui.TextInput(label="ID do Usuário ou @menção", placeholder="Ex: 123456789 ou @usuario", max_length=50)
    quantidade = discord.ui.TextInput(label="Quantidade", placeholder="Ex: 500", max_length=15)

    def __init__(self, admin_id: int):
        super().__init__()
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            user_input = self.usuario.value.strip()
            quantidade = int(self.quantidade.value)
            
            if user_input.startswith("<@") and user_input.endswith(">"):
                user_id = int(user_input[2:-1].replace("!", ""))
            else:
                user_id = int(user_input)
            
            user = get_user(user_id)
            user["xp"] = user.get("xp", 0) + quantidade
            save_user(user_id, user)
            
            await interaction.followup.send(f"✅ {quantidade} XP adicionados para <@{user_id}>!", ephemeral=True)
        except ValueError:
            await interaction.followup.send("❌ Valores inválidos.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class DarPoderModal(discord.ui.Modal, title="Dar Poder"):
    usuario = discord.ui.TextInput(label="ID do Usuário ou @menção", placeholder="Ex: 123456789 ou @usuario", max_length=50)
    quantidade = discord.ui.TextInput(label="Quantidade", placeholder="Ex: 50", max_length=15)

    def __init__(self, admin_id: int):
        super().__init__()
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            user_input = self.usuario.value.strip()
            quantidade = int(self.quantidade.value)
            
            if user_input.startswith("<@") and user_input.endswith(">"):
                user_id = int(user_input[2:-1].replace("!", ""))
            else:
                user_id = int(user_input)
            
            user = get_user(user_id)
            user["poder"] = user.get("poder", 0) + quantidade
            save_user(user_id, user)
            
            await interaction.followup.send(f"✅ {quantidade} Poder adicionados para <@{user_id}>!", ephemeral=True)
        except ValueError:
            await interaction.followup.send("❌ Valores inválidos.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class ModeracaoView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="📜 Decreto", style=discord.ButtonStyle.primary, row=1)
    async def decreto(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DecretoModal(self.admin_id))

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class DecretoModal(discord.ui.Modal, title="Enviar Decreto Imperial"):
    mensagem = discord.ui.TextInput(label="Mensagem do Decreto", style=discord.TextStyle.long, max_length=2000)

    def __init__(self, admin_id: int):
        super().__init__()
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            embed = discord.Embed(
                title="⚜️ DECRETO IMPERIAL ⚜️",
                description=self.mensagem.value,
                color=0xFFD700
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            
            await interaction.channel.send("@everyone", embed=embed)
            await interaction.followup.send("✅ Decreto enviado!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class FamiliaView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id
        self.add_item(SelecionarMembroSelect(admin_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="🌳 Árvore Familiar", style=discord.ButtonStyle.secondary, row=1)
    async def arvore(self, interaction: discord.Interaction, button: discord.ui.Button):
        grupos = {}
        for uid, user in get_all_users().items():
            try:
                member = interaction.guild.get_member(int(uid))
            except (TypeError, ValueError):
                continue
            if not member or member.bot:
                continue
            vinculo = user.get("parentesco") or "Membro"
            emoji = user.get("parentesco_emoji") or "👤"
            grupos.setdefault(f"{emoji} {vinculo}", []).append(member.mention)

        linhas = []
        for vinculo, membros in sorted(grupos.items(), key=lambda x: (x[0] != "👑 Patriarca da Família", x[0])):
            exibidos = ", ".join(membros[:10])
            restante = f" e mais {len(membros) - 10}" if len(membros) > 10 else ""
            linhas.append(f"### {vinculo}\n{exibidos}{restante}")

        descricao = "\n\n".join(linhas) or "Nenhum parentesco registrado."
        embed = _embed("🌳 Árvore da Família Imperial", descricao, COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class PerfilView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id
        self.add_item(SelecionarMembroSelect(admin_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="🏷️ Dar Título", style=discord.ButtonStyle.primary, row=1)
    async def dar_titulo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DarTituloModal(self.admin_id))

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class DarTituloModal(discord.ui.Modal, title="Dar Título"):
    usuario = discord.ui.TextInput(label="ID do Usuário ou @menção", placeholder="Ex: 123456789 ou @usuario", max_length=50)
    titulo = discord.ui.TextInput(label="Título", placeholder="Ex: Cavaleiro das Sombras", max_length=50)

    def __init__(self, admin_id: int):
        super().__init__()
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            user_input = self.usuario.value.strip()
            titulo = self.titulo.value.strip()
            
            if user_input.startswith("<@") and user_input.endswith(">"):
                user_id = int(user_input[2:-1].replace("!", ""))
            else:
                user_id = int(user_input)
            
            user = get_user(user_id)
            user["titulo"] = titulo
            save_user(user_id, user)
            
            await interaction.followup.send(f"✅ Título '{titulo}' dado para <@{user_id}>!", ephemeral=True)
        except ValueError:
            await interaction.followup.send("❌ Valores inválidos.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class EventosView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="🎲 Sorteio", style=discord.ButtonStyle.primary, row=1)
    async def sorteio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SorteioModal(self.admin_id))

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class SorteioModal(discord.ui.Modal, title="Criar Sorteio"):
    premio = discord.ui.TextInput(label="Prêmio", placeholder="Ex: 1000 moedas", max_length=100)

    def __init__(self, admin_id: int):
        super().__init__()
        self.admin_id = admin_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.admin_id or not _tem_autoridade(interaction.user):
            await interaction.response.send_message("Apenas administradores podem usar este painel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        try:
            embed = discord.Embed(
                title="🎲 SORTEIO IMPERIAL 🎲",
                description=f"Prêmio: **{self.premio.value}**\n\nReaja com 🎉 para participar!",
                color=0xFFD700
            )
            embed.set_footer(text=RODAPE_IMPERIAL)
            
            msg = await interaction.channel.send("@everyone", embed=embed)
            await msg.add_reaction("🎉")
            await interaction.followup.send("✅ Sorteio criado!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)


class MusicaView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="⏹️ Parar Música", style=discord.ButtonStyle.danger, row=1)
    async def parar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `tenshi stop` para parar a música.", ephemeral=True)

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class JogosView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Acesso negado.", ephemeral=True)
        return False

    @discord.ui.button(label="🎯 Criar Quiz", style=discord.ButtonStyle.primary, row=1)
    async def quiz(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `tenshi quiz` para criar um quiz.", ephemeral=True)

    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PainelPrincipalView(self.admin_id)
        embed = _embed("🏛️ Painel Administrativo Imperial", "Selecione uma categoria abaixo para gerenciar o bot.", COR_DOURADO)
        await interaction.response.edit_message(embed=embed, view=view)


class PainelAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_painel_admin(self, message, args):
        """Abre o painel administrativo completo."""
        if not _tem_autoridade(message.author):
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem usar este comando.", COR_PERIGO))
            return
        
        if not message.guild.me.guild_permissions.manage_roles:
            await message.channel.send(embed=_embed("🚫 Permissão Insuficiente", "Preciso da permissão **Gerenciar Cargos**.", COR_PERIGO))
            return

        total_users = len(get_all_users())
        
        embed = _embed(
            "🏛️ Painel Administrativo Imperial",
            f"**Administrador:** {message.author.mention}\n"
            f"**Servidor:** {message.guild.name}\n"
            f"**Total de Usuários:** {total_users}\n\n"
            f"Selecione uma categoria abaixo para gerenciar o bot.\n\n"
            f"**Categorias disponíveis:**\n"
            f"👤 **Usuários** - Editar XP, Poder, Nível, Moedas, Título\n"
            f"💰 **Economia** - Dar moedas, banco\n"
            f"⚔️ **RPG** - Dar XP, Poder\n"
            f"🛡️ **Moderação** - Decretos imperiais\n"
            f"👨‍👩‍👧 **Família** - Árvore familiar\n"
            f"🎭 **Perfil** - Títulos personalizados\n"
            f"🎪 **Eventos** - Sorteios\n"
            f"🎵 **Música** - Controle de música\n"
            f"🎮 **Jogos** - Quizzes e jogos\n"
            f"📊 **Estatísticas** - Dados do servidor",
            COR_DOURADO,
            thumbnail_url=message.guild.icon.url if message.guild.icon else None
        )
        
        view = PainelPrincipalView(message.author.id)
        await message.channel.send(embed=embed, view=view)

    async def handle_casar_admin(self, message, args):
        """Comando especial para o Imperador se casar e conceder acesso admin ao cônjuge."""
        if message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas o Imperador pode usar este comando.", COR_PERIGO))
            return
        
        if not message.mentions:
            await message.channel.send(embed=_embed("❌ Erro", "Mencione o cônjuge para o casamento imperial.", COR_PERIGO))
            return
        
        conjuge = message.mentions[0]
        user = get_user(conjuge.id)
        user["admin_access"] = True
        save_user(conjuge.id, user)
        
        await message.channel.send(
            f"⚜️ **CASAMENTO IMPERIAL** ⚜️\n\n"
            f"O Imperador {message.author.mention} oficializou a união com {conjuge.mention}!\n"
            f"{conjuge.mention} agora tem acesso administrativo ao painel."
        )
