"""
Módulo Geopolítica — Módulo 13 A-B
A. Territórios, Domínio, Imposto, Rebelião
B. Imigração, Visto, Cidadania, Exílio
"""
import discord
import asyncio
import uuid
from datetime import datetime, timedelta
from database import get_user, save_user, get_all_users, registrar_infracao
from utils import SEP, RODAPE_IMPERIAL, IMPERADOR_ID
from design import (embed_doc, embed_soberano_decreto, embed_judicial,
                    embed_sucesso, embed_perigo_doc, embed_admin_doc,
                    embed_crime_doc, fmt_moedas,
                    COR_GERAL, COR_DECRETO, COR_JUDICIAL, COR_CRIME,
                    COR_ADMIN, COR_SUCESSO, COR_PERIGO, COR_NEUTRO, rodape_padrao)

# ─── TERRITÓRIOS ─────────────────────────────────────────────────────────────
_dominios: dict = {}          # {canal_id: {"faccao": str, "atividade": int, "expira": str}}
_atividade_canal: dict = {}   # {f"{uid}_{canal_id}": int}  contagem de msgs

IMPOSTO_TERRITORIO = 0.02     # 2% de toda Moeda gasta no canal
CUSTO_REBELIAO     = 200
DURACAO_DOMINIO    = 7 * 24 * 3600  # 7 dias


def registrar_atividade(user_id: int, canal_id: int, faccao: str):
    key = f"{faccao}_{canal_id}"
    _atividade_canal[key] = _atividade_canal.get(key, 0) + 1


def cobrar_imposto_territorio(canal_id: int, valor: int, user_id: int) -> int:
    """Desconta imposto de território se o canal tiver dono. Retorna valor do imposto."""
    dominio = _dominios.get(str(canal_id))
    if not dominio:
        return 0
    expira = datetime.fromisoformat(dominio["expira"])
    if datetime.utcnow() > expira:
        del _dominios[str(canal_id)]
        return 0
    imposto = int(valor * IMPOSTO_TERRITORIO)
    faccao  = dominio["faccao"]
    todos   = get_all_users()
    for uid, u in todos.items():
        if u.get("faccao") == faccao:
            u["moedas"] = u.get("moedas", 0) + imposto // max(1, len(todos))
            save_user(int(uid), u)
    return imposto


class ConfirmarRebeliaoView(discord.ui.View):
    def __init__(self, canal, faccao_atacante: str, lider: discord.Member):
        super().__init__(timeout=120)
        self.canal          = canal
        self.faccao_atacante = faccao_atacante
        self.lider          = lider
        self.resolvida      = False

    @discord.ui.button(label="Iniciar Rebelião", style=discord.ButtonStyle.danger)
    async def iniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.lider.id:
            await interaction.response.send_message("Painel restrito.", ephemeral=True); return
        if self.resolvida: return
        self.resolvida = True; self.clear_items()
        import random
        sucesso = random.random() < 0.55
        cid_str = str(self.canal.id)
        if sucesso:
            _dominios[cid_str] = {
                "faccao": self.faccao_atacante,
                "expira": (datetime.utcnow() + timedelta(seconds=DURACAO_DOMINIO)).isoformat(),
                "atividade": 0
            }
            await interaction.response.edit_message(
                embed=embed_crime_doc(
                    "Rebelião — Território Conquistado",
                    f"• **Facção vitoriosa:** {self.faccao_atacante}\n"
                    f"• **Canal dominado:** {self.canal.mention}\n"
                    f"• **Imposto de 2%** agora revertido para a facção."
                ), view=self)
        else:
            await interaction.response.edit_message(
                embed=embed_crime_doc(
                    "Rebelião — Fracassada",
                    f"• A contraofensiva foi eficaz. O território permanece com a facção anterior.\n"
                    f"• Custo já descontado: {fmt_moedas(CUSTO_REBELIAO)}"
                ), view=self)


# ─── IMIGRAÇÃO / CIDADANIA ───────────────────────────────────────────────────
_entrevistas_visto: dict = {}


class EntrevistaVistoModal(discord.ui.Modal, title="Protocolo de Visto Imperial"):
    intencoes = discord.ui.TextInput(
        label="Suas intenções em Tenshi",
        style=discord.TextStyle.paragraph,
        max_length=500,
        placeholder="Descreva quem você é e o que pretende no Império..."
    )
    nome_rp = discord.ui.TextInput(
        label="Nome do seu personagem",
        max_length=50
    )

    def __init__(self, guild, canal_portaria, canal_entrada):
        super().__init__()
        self.guild          = guild
        self.canal_portaria = canal_portaria
        self.canal_entrada  = canal_entrada

    async def on_submit(self, interaction: discord.Interaction):
        texto = self.intencoes.value
        nome  = self.nome_rp.value
        uid   = interaction.user.id

        # Análise simples de texto (sem IA — verifica comprimento e tom)
        aprovado = len(texto) >= 80 and not any(
            t in texto.lower() for t in ["sei lá", "tanto faz", "qualquer coisa"]
        )

        u = get_user(uid)
        if aprovado:
            u["cidadania"]  = True
            u["estrangeiro"] = False
            u["registro_civil"] = str(uuid.uuid4())[:12].upper()
            u["nome_rp"]    = nome
            save_user(uid, u)

            # Liberar cargos de RP
            cargo_cidadao = discord.utils.get(self.guild.roles, name="Cidadão")
            if cargo_cidadao:
                try: await interaction.user.add_roles(cargo_cidadao)
                except Exception: pass

            await interaction.response.send_message(
                embed=embed_sucesso(
                    "Visto Aprovado — Cidadania Concedida",
                    f"• **Registro Civil:** `{u['registro_civil']}`\n"
                    f"• Bem-vindo(a) ao Império, **{nome}**.\n"
                    f"• Canais de RP liberados."
                ), ephemeral=True)

            if self.canal_portaria:
                await self.canal_portaria.send(embed=embed_doc(
                    f"Novo Cidadão Registrado",
                    f"• **Membro:** {interaction.user.mention}\n"
                    f"• **Nome RP:** {nome}\n"
                    f"• **Registro:** `{u['registro_civil']}`",
                    COR_GERAL
                ))
        else:
            await interaction.response.send_message(
                embed=embed_perigo_doc(
                    "Visto Recusado",
                    "• Suas intenções não foram consideradas suficientemente detalhadas.\n"
                    "• Acesso aos canais de RP permanece bloqueado. Tente novamente com mais detalhes."
                ), ephemeral=True)


class VistoView(discord.ui.View):
    def __init__(self, guild, canal_portaria, canal_entrada):
        super().__init__(timeout=None)
        self.guild = guild; self.cp = canal_portaria; self.ce = canal_entrada

    @discord.ui.button(label="Solicitar Visto de Entrada", style=discord.ButtonStyle.primary,
                       custom_id="solicitar_visto")
    async def solicitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        u = get_user(interaction.user.id)
        if u.get("cidadania"):
            await interaction.response.send_message("Você já possui cidadania registrada.", ephemeral=True)
            return
        modal = EntrevistaVistoModal(self.guild, self.cp, self.ce)
        await interaction.response.send_modal(modal)


class Geopolitica:
    def __init__(self, bot):
        self.bot = bot

    # ── A) DOMINAR TERRITÓRIO ─────────────────────────────────────────────────

    async def handle_dominar(self, message, args):
        u = get_user(message.author.id)
        faccao = u.get("faccao")
        if not faccao:
            await message.channel.send(embed_perigo_doc("Sem Facção",
                "Você precisa pertencer a uma facção para dominar territórios."))
            return
        canal_alvo = message.channel
        canais_neutros = ["parque", "cassino", "praça", "praca", "cafeteria"]
        if not any(c in canal_alvo.name.lower() for c in canais_neutros):
            await message.channel.send(
                f"> ⚠️ **Operação Recusada.** Apenas canais neutros podem ser dominados ({', '.join(canais_neutros)}).")
            return
        cid_str = str(canal_alvo.id)
        dono_atual = _dominios.get(cid_str, {}).get("faccao", "nenhuma")
        atividade_faccao = _atividade_canal.get(f"{faccao}_{canal_alvo.id}", 0)
        if atividade_faccao < 10:
            await message.channel.send(
                f"> ⚠️ **Operação Recusada.** Atividade insuficiente neste canal — {atividade_faccao}/10 mensagens.")
            return
        _dominios[cid_str] = {
            "faccao": faccao,
            "expira": (datetime.utcnow() + timedelta(seconds=DURACAO_DOMINIO)).isoformat(),
            "atividade": atividade_faccao
        }
        await message.channel.send(embed=embed_crime_doc(
            "Domínio de Território Estabelecido",
            f"• **Facção:** {faccao}\n"
            f"• **Canal:** {canal_alvo.mention}\n"
            f"• **Duração:** 7 dias\n"
            f"• **Imposto:** 2% de toda moeda gasta neste canal será revertida à facção."
        ))

    async def handle_status_territorio(self, message, args):
        canal = message.channel
        cid   = str(canal.id)
        dominio = _dominios.get(cid)
        if not dominio:
            await message.channel.send(embed=embed_doc(
                "Status de Território",
                f"• {canal.mention} — **Território Neutro**  (Sem facção dominante)",
                COR_NEUTRO
            ))
            return
        expira = datetime.fromisoformat(dominio["expira"])
        if datetime.utcnow() > expira:
            del _dominios[cid]
            await message.channel.send(embed=embed_doc(
                "Status de Território",
                f"• {canal.mention} — **Território Neutro** (Domínio expirado)",
                COR_NEUTRO
            ))
            return
        await message.channel.send(embed=embed_crime_doc(
            "Status de Território",
            f"• **Canal:** {canal.mention}\n"
            f"• **Facção dominante:** {dominio['faccao']}\n"
            f"• **Expira:** {expira.strftime('%d/%m/%Y %H:%M')} UTC\n"
            f"• **Imposto ativo:** 2%"
        ))

    async def handle_rebeliao(self, message, args):
        u = get_user(message.author.id)
        faccao = u.get("faccao")
        if not faccao:
            await message.channel.send("> ⚠️ Você precisa de uma facção."); return
        if u.get("moedas", 0) < CUSTO_REBELIAO:
            await message.channel.send(
                f"> ⚠️ **Operação Recusada.** Custo de rebelião: {fmt_moedas(CUSTO_REBELIAO)}."); return
        canal_alvo = message.channel
        cid_str = str(canal_alvo.id)
        if cid_str not in _dominios:
            await message.channel.send("> ⚠️ Este canal não possui dominação registrada."); return
        u["moedas"] -= CUSTO_REBELIAO; save_user(message.author.id, u)
        e = embed_crime_doc(
            "Protocolo de Rebelião Iniciado",
            f"• **Facção atacante:** {faccao}\n"
            f"• **Canal contestado:** {canal_alvo.mention}\n"
            f"• **Custo descontado:** {fmt_moedas(CUSTO_REBELIAO)}\n\n"
            f"Confirme a operação abaixo."
        )
        view = ConfirmarRebeliaoView(canal_alvo, faccao, message.author)
        await message.channel.send(embed=e, view=view)

    # ── B) IMIGRAÇÃO / CIDADANIA ──────────────────────────────────────────────

    async def handle_painel_visto(self, message):
        canal_portaria = None
        canal_entrada  = None
        if message.guild:
            for ch in message.guild.text_channels:
                if "portaria" in ch.name.lower(): canal_portaria = ch
                if "entrada" in ch.name.lower(): canal_entrada = ch
        e = embed_doc(
            "Protocolo de Imigração — Império de Tenshi",
            "• Novos membros possuem status **Estrangeiro**.\n"
            "• O acesso aos canais de RP é liberado após a aprovação do visto.\n"
            "• Clique abaixo para iniciar a entrevista de imigração.",
            COR_GERAL
        )
        view = VistoView(message.guild, canal_portaria, canal_entrada)
        await message.channel.send(embed=e, view=view)

    async def handle_cidadania(self, message, args):
        alvo = message.mentions[0] if message.mentions else message.author
        u    = get_user(alvo.id)
        if not u.get("cidadania"):
            await message.channel.send(embed=embed_doc(
                "Status de Cidadania",
                f"• **Membro:** {alvo.mention}\n• **Status:** Estrangeiro — sem cidadania registrada.",
                COR_NEUTRO
            ))
            return
        await message.channel.send(embed=embed_doc(
            "Certidão de Cidadania Imperial",
            f"• **Membro:** {alvo.mention}\n"
            f"• **Nome RP:** {u.get('nome_rp', '—')}\n"
            f"• **Registro Civil:** `{u.get('registro_civil', '?')}`\n"
            f"• **Status:** Cidadão ativo",
            COR_GERAL
        ))

    async def handle_exilio_temporario(self, message, args):
        u_data = get_user(message.author.id)
        try: adm = message.author.guild_permissions.administrator
        except: adm = False
        if not adm and message.author.id != IMPERADOR_ID and not u_data.get("co_soberano"):
            await message.channel.send("> ⚠️ Apenas autoridades podem aplicar exílio."); return
        if not message.mentions: await message.channel.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        duracao_h = int(args[1]) if len(args) > 1 and args[1].isdigit() else 24
        u = get_user(alvo.id)
        u["exilado"]      = True
        u["cidadania"]    = False
        u["bloqueado_ate"] = (datetime.utcnow() + timedelta(hours=duracao_h)).isoformat()
        save_user(alvo.id, u)
        cargo_exil = discord.utils.get(message.guild.roles, name="Exilado") if message.guild else None
        if cargo_exil:
            try: await alvo.add_roles(cargo_exil)
            except: pass
        try:
            await message.author.timeout(discord.utils.utcnow() + timedelta(hours=duracao_h))
        except: pass
        await message.channel.send(embed=embed_judicial(
            "Exílio Temporário Aplicado",
            f"• **Alvo:** {alvo.mention}\n"
            f"• **Duração:** {duracao_h} horas\n"
            f"• **Cidadania suspensa** por determinação da autoridade."
        ))

COR_NEUTRO = 0x3D3D3D
