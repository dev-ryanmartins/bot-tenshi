"""
Sistema de Design Imperial — Tenshi Bot
Módulos 16 e 17: Manual Estrito de UI, Embeds, Botões e Estética
"""
import discord
from datetime import datetime, timezone

# ─── PALETA DE CORES ──────────────────────────────────────────────────────────
COR_GERAL       = 0x2C3E50   # Cinza Azulado Imperial — fichas, status, academia
COR_DECRETO     = 0x9E7815   # Dourado Opaco — decretos de Alloy, casamentos, clero
COR_CRIME       = 0x1E1E1E   # Preto Carvão — Máfia, execuções, Mercado Negro
COR_ADMIN       = 0x7F8C8D   # Cinza Administrativo — logs, auditoria, trem
COR_HOSPITAL    = 0xD35400   # Abóbora Escuro — alertas hospitalares, quarentena, acidentes
COR_JUDICIAL    = 0xC0392B   # Vermelho Sangue — infrações, exílios, Código de Conduta
COR_SUCESSO     = 0x1A5C2E   # Verde Escuro — confirmações, aprovações
COR_NEUTRO      = 0x3D3D3D   # Cinza Neutro — cancelamentos, info neutra
COR_PERIGO      = 0x7B1F1F   # Vermelho Escuro — erros, bloqueios

# ─── FORMATO DE RODAPÉ ────────────────────────────────────────────────────────
_PROTOCOLO_COUNTER = 0

def _protocolo() -> str:
    global _PROTOCOLO_COUNTER
    _PROTOCOLO_COUNTER += 1
    return f"S-{_PROTOCOLO_COUNTER:04d}"

def rodape_padrao(autor: str = "Terminal Central de Tenshi") -> str:
    now = datetime.now(timezone.utc)
    return f"{autor}  •  {now.strftime('%d/%m/%Y %H:%M')} UTC  •  Protocolo {_protocolo()}"

# ─── EMBED FACTORY PRINCIPAL ──────────────────────────────────────────────────
def embed_doc(titulo: str, descricao: str = "", cor: int = COR_GERAL, *, autor: str = "Terminal Central de Tenshi") -> discord.Embed:
    """Embed padrão documental: título curto, --- divider, rodapé com data/protocolo."""
    desc = f"---\n{descricao}" if descricao and not descricao.startswith("---") else descricao
    e = discord.Embed(title=titulo, description=desc, color=cor)
    e.set_footer(text=rodape_padrao(autor))
    return e

def embed_erro(mensagem: str) -> str:
    """Mensagem de erro para envio como blockquote efêmero."""
    return f"> ⚠️ **Operação Recusada.** {mensagem}"

def embed_cooldown(minutos: int, segundos: int = 0) -> str:
    """Mensagem de cooldown para envio como blockquote efêmero."""
    if minutos > 0 and segundos > 0:
        return f"> ⏱️ **Protocolo de Recuperação.** Aguarde {minutos}m {segundos}s antes de prosseguir."
    elif minutos > 0:
        return f"> ⏱️ **Protocolo de Recuperação.** Aguarde {minutos}m antes de prosseguir."
    else:
        return f"> ⏱️ **Protocolo de Recuperação.** Aguarde {segundos}s antes de prosseguir."

def embed_processando() -> str:
    return "> ⚙️ Processando diretriz. Aguarde."

def embed_soberano_decreto(titulo: str, descricao: str) -> discord.Embed:
    """Embed exclusivo para decretos imperiais."""
    e = embed_doc(titulo, descricao, COR_DECRETO, autor="Trono Imperial de Tenshi")
    return e

def embed_judicial(titulo: str, descricao: str) -> discord.Embed:
    return embed_doc(titulo, descricao, COR_JUDICIAL)

def embed_hospital(titulo: str, descricao: str) -> discord.Embed:
    return embed_doc(titulo, descricao, COR_HOSPITAL)

def embed_crime_doc(titulo: str, descricao: str) -> discord.Embed:
    return embed_doc(titulo, descricao, COR_CRIME)

def embed_admin_doc(titulo: str, descricao: str) -> discord.Embed:
    return embed_doc(titulo, descricao, COR_ADMIN)

def embed_sucesso(titulo: str, descricao: str) -> discord.Embed:
    return embed_doc(titulo, descricao, COR_SUCESSO)

def embed_perigo_doc(titulo: str, descricao: str) -> discord.Embed:
    return embed_doc(titulo, descricao, COR_PERIGO)

# ─── FORMATAR MOEDAS ─────────────────────────────────────────────────────────
def fmt_moedas(valor: int) -> str:
    return f"⌕ {valor:,} Moedas Imperiais".replace(",", ".")

# ─── PAGINAÇÃO ────────────────────────────────────────────────────────────────
class PaginacaoView(discord.ui.View):
    """View de paginação padrão [ ◀ ] [ Página X/Y ] [ ▶ ]"""
    def __init__(self, paginas: list[discord.Embed], user_id: int):
        super().__init__(timeout=60)
        self.paginas  = paginas
        self.user_id  = user_id
        self.atual    = 0
        self._update_btn()

    def _update_btn(self):
        for item in self.children:
            if hasattr(item, "custom_id"):
                if item.custom_id == "pag_info":
                    item.label = f"Página {self.atual+1}/{len(self.paginas)}"
                    item.disabled = True
                elif item.custom_id == "pag_prev":
                    item.disabled = self.atual == 0
                elif item.custom_id == "pag_next":
                    item.disabled = self.atual >= len(self.paginas) - 1

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary, custom_id="pag_prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Painel restrito.", ephemeral=True); return
        self.atual -= 1
        self._update_btn()
        await interaction.response.edit_message(embed=self.paginas[self.atual], view=self)

    @discord.ui.button(label="Página 1/1", style=discord.ButtonStyle.secondary, custom_id="pag_info", disabled=True)
    async def info_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary, custom_id="pag_next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Painel restrito.", ephemeral=True); return
        self.atual += 1
        self._update_btn()
        await interaction.response.edit_message(embed=self.paginas[self.atual], view=self)
