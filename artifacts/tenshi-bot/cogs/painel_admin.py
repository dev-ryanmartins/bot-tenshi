"""Painel Administrativo Imperial - Gerenciamento de Família, Parentesco e Cargos"""

import discord
from discord.ext import commands
from database import get_user, save_user, get_all_users
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial
from cogs.parentesco import aplicar_parentesco, VINCULOS

COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


def _tem_autoridade(member: discord.Member) -> bool:
    """Verifica se o usuário tem autoridade administrativa."""
    if member.id == IMPERADOR_ID:
        return True
    # Verificar se é cônjuge do Imperador (co_soberano)
    user = get_user(member.id)
    if user.get("co_soberano") or user.get("acesso_painel_admin"):
        return True
    try:
        return member.guild_permissions.administrator
    except Exception:
        return False


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


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
            
            # Aplicar parentesco
            cargo = await aplicar_parentesco(self.alvo, nome, emoji, interaction.user.id, "admin_painel")
            
            await interaction.followup.send(
                f"✅ {self.alvo.mention} agora é **{nome}** {emoji}\nCargo aplicado: {cargo.mention}",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ Não tenho permissão para aplicar cargos.", ephemeral=True)
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
        await interaction.response.send_modal(GerenciarMembroModal(alvo, self.admin_id))


class PainelPrincipalView(discord.ui.View):
    def __init__(self, admin_id: int):
        super().__init__(timeout=600)
        self.admin_id = admin_id
        self.add_item(SelecionarMembroSelect(admin_id))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.admin_id:
            return True
        await interaction.response.send_message("Abra seu próprio painel com `tenshi painel-admin`.", ephemeral=True)
        return False

    @discord.ui.button(label="📋 Ver Árvore Familiar", style=discord.ButtonStyle.secondary, row=1)
    async def ver_arvore(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("Acesso negado.", ephemeral=True)
            return
        
        # Gerar árvore familiar
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

    @discord.ui.button(label="👥 Lista de Vínculos", style=discord.ButtonStyle.secondary, row=1)
    async def lista_vinculos(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("Acesso negado.", ephemeral=True)
            return
        
        linhas = [f"{emoji} **{nome}**" for nome, emoji in VINCULOS.values()]
        descricao = "Vínculos disponíveis:\n\n" + "\n".join(linhas)
        embed = _embed("📚 Vínculos Disponíveis", descricao, COR_DOURADO)
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Atualizar Painel", style=discord.ButtonStyle.primary, row=1)
    async def atualizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("Acesso negado.", ephemeral=True)
            return
        
        embed = _embed(
            "🏛️ Painel Administrativo Imperial",
            f"**Administrador:** {interaction.user.mention}\n\n"
            f"Selecione um membro acima para gerenciar seu vínculo familiar e cargo.\n\n"
            f"**Funções disponíveis:**\n"
            f"• Definir parentesco personalizado\n"
            f"• Aplicar cargos automaticamente\n"
            f"• Visualizar árvore familiar\n"
            f"• Listar vínculos disponíveis",
            COR_DOURADO
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Fechar", style=discord.ButtonStyle.danger, row=1)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("Acesso negado.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(
            embed=_embed("📕 Painel Encerrado", "Use `tenshi painel-admin` quando precisar novamente.", COR_NEUTRO),
            view=None
        )


class PainelAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_painel_admin(self, message, args):
        """Abre o painel administrativo para gerenciar família e parentesco."""
        if not _tem_autoridade(message.author):
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas administradores podem usar este comando.", COR_PERIGO))
            return
        
        if not message.guild.me.guild_permissions.manage_roles:
            await message.channel.send(embed=_embed("🚫 Permissão Insuficiente", "Preciso da permissão **Gerenciar Cargos**.", COR_PERIGO))
            return

        embed = _embed(
            "🏛️ Painel Administrativo Imperial",
            f"**Administrador:** {message.author.mention}\n\n"
            f"Selecione um membro acima para gerenciar seu vínculo familiar e cargo.\n\n"
            f"**Funções disponíveis:**\n"
            f"• Definir parentesco personalizado\n"
            f"• Aplicar cargos automaticamente\n"
            f"• Visualizar árvore familiar\n"
            f"• Listar vínculos disponíveis",
            COR_DOURADO
        )
        
        view = PainelPrincipalView(message.author.id)
        await message.channel.send(embed=embed, view=view)

    async def handle_casar_admin(self, message, args):
        """Comando especial para o Imperador se casar e conceder acesso admin ao cônjuge."""
        if message.author.id != IMPERADOR_ID:
            await message.channel.send(embed=_embed("🚫 Acesso Negado", "Apenas o Imperador pode usar este comando.", COR_PERIGO))
            return
        
        if not message.mentions:
            await message.channel.send(embed=_embed("❌ Parâmetro Inválido", "Use: `tenshi casar-admin @usuario`", COR_NEUTRO))
            return
        
        alvo = message.mentions[0]
        if alvo.bot:
            await message.channel.send(embed=_embed("❌ Inválido", "Não pode casar com bots.", COR_PERIGO))
            return
        
        # Verificar se já está casado
        imperador = get_user(IMPERADOR_ID)
        if imperador.get("conjuge"):
            await message.channel.send(embed=_embed("❌ Já Casado", "Você já está casado.", COR_PERIGO))
            return
        
        # Definir casamento
        imperador["conjuge"] = str(alvo.id)
        conjuge = get_user(alvo.id)
        conjuge["conjuge"] = str(IMPERADOR_ID)
        
        # Conceder co_soberano ao cônjuge
        conjuge["co_soberano"] = True
        conjuge["acesso_painel_admin"] = True  # Concede acesso ao painel admin
        
        # Aplicar parentesco de Consorte
        from cogs.parentesco import aplicar_parentesco
        try:
            await aplicar_parentesco(alvo, "Consorte Imperial", "👑", IMPERADOR_ID, "casamento_imperial")
        except Exception as e:
            print(f"[AVISO] Não foi possível aplicar cargo: {e}")
        
        save_user(IMPERADOR_ID, imperador)
        save_user(alvo.id, conjuge)
        
        embed = _embed(
            "💍 União Imperial Realizada",
            f"**Imperador:** {message.author.mention}\n"
            f"**Consorte:** {alvo.mention}\n\n"
            f"O cônjuge agora tem:\n"
            f"• Acesso ao Painel Administrativo\n"
            f"• Título de Co-Soberano\n"
            f"• Cargo de Consorte Imperial\n"
            f"• Permissões de gerenciamento familiar",
            COR_SUCESSO
        )
        
        await message.channel.send(embed=embed)
