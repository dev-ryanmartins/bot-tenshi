"""
Módulo Estado — Módulos 13 C-H + 14 A-H
Economia avançada, transporte, segurança, saúde, festas, ferramentas
"""
import discord
import asyncio
import random
import uuid
from datetime import datetime, timedelta, date
from database import get_user, save_user, get_all_users, registrar_infracao
from utils import SEP, RODAPE_IMPERIAL, IMPERADOR_ID
from design import (embed_doc, embed_soberano_decreto, embed_judicial,
                    embed_sucesso, embed_perigo_doc, embed_admin_doc,
                    embed_crime_doc, embed_hospital, fmt_moedas,
                    COR_GERAL, COR_DECRETO, COR_JUDICIAL, COR_CRIME,
                    COR_ADMIN, COR_SUCESSO, COR_PERIGO, COR_NEUTRO,
                    COR_HOSPITAL, rodape_padrao)

# ─── ESTADO GLOBAL ────────────────────────────────────────────────────────────
_trem_paralisado_ate: datetime | None = None
_eclipse_ate:         datetime | None = None
_corrida_bancaria:    bool = False
_seguro_vida:         dict = {}   # {uid: {"ativo": bool, "data_pagamento": str}}
_necrologia:          list = []   # [{"nome": str, "data": str, "causa": str, "raca": str}]
_leiloes_casa:        dict = {}   # {numero_casa: {"lance": int, "lance_uid": int, "expira": str}}
_mandados:            dict = {}   # {uid_alvo: {"expira": str, "casa": int}}
_foragidos:           dict = {}   # {uid: {"msg_id": int, "recompensa": int}}
_fuel_veiculos:       dict = {}   # {uid: {"combustivel": int}}
_palavras_subversivas: list = []
_auditoria_ativa:     set = set()  # UIDs monitorados por picos anômalos

TAXA_JUROS_DIARIA   = 0.02    # 2% ao dia
TAXA_SEGURO_VIDA    = 50      # por mês
LIMITE_SAQUE_CRISE  = 200
CUSTO_COMBUSTIVEL   = 30


class LanceLeilaoView(discord.ui.View):
    def __init__(self, numero_casa: int, canal):
        super().__init__(timeout=86400)
        self.numero_casa = numero_casa
        self.canal       = canal

    @discord.ui.button(label="Dar Lance", style=discord.ButtonStyle.primary)
    async def dar_lance(self, interaction: discord.Interaction, button: discord.ui.Button):
        leilao = _leiloes_casa.get(self.numero_casa)
        if not leilao:
            await interaction.response.send_message("Leilão encerrado.", ephemeral=True); return
        lance_min = leilao["lance"] + 50
        modal = LanceModal(self.numero_casa, lance_min, self.canal)
        await interaction.response.send_modal(modal)


class LanceModal(discord.ui.Modal, title="Fazer Lance"):
    valor = discord.ui.TextInput(label="Valor do Lance", placeholder="Ex: 500")

    def __init__(self, numero_casa, lance_min, canal):
        super().__init__()
        self.numero_casa = numero_casa
        self.lance_min   = lance_min
        self.canal_ref   = canal

    async def on_submit(self, interaction: discord.Interaction):
        try: v = int(self.valor.value.replace(".", ""))
        except: await interaction.response.send_message("> ⚠️ Valor inválido.", ephemeral=True); return
        if v < self.lance_min:
            await interaction.response.send_message(
                f"> ⚠️ Lance mínimo: {fmt_moedas(self.lance_min)}", ephemeral=True); return
        u = get_user(interaction.user.id)
        if u["moedas"] < v:
            await interaction.response.send_message(
                f"> ⚠️ Saldo insuficiente: {fmt_moedas(u['moedas'])}", ephemeral=True); return
        _leiloes_casa[self.numero_casa]["lance"]     = v
        _leiloes_casa[self.numero_casa]["lance_uid"] = interaction.user.id
        await interaction.response.send_message(
            embed=embed_sucesso("Lance Registrado", f"• Seu lance de {fmt_moedas(v)} está em primeiro lugar."),
            ephemeral=True)
        if self.canal_ref:
            await self.canal_ref.send(embed=embed_doc(
                f"Novo Lance — Casa-{self.numero_casa}",
                f"• **Licitante:** {interaction.user.mention}\n• **Lance:** {fmt_moedas(v)}", COR_GERAL))


class Estado:
    def __init__(self, bot):
        self.bot = bot
        self._loops_iniciados = False

    def cog_load(self):
        if not self._loops_iniciados:
            self._loops_iniciados = True
            self.bot.loop.create_task(self._loop_juros_diarios())
            self.bot.loop.create_task(self._loop_imposto_fortunas())
            self.bot.loop.create_task(self._loop_leiloes())
            self.bot.loop.create_task(self._loop_combustivel())
            self.bot.loop.create_task(self._loop_auditoria_desempenho())

    # ── EMPRÉSTIMOS E JUROS ──────────────────────────────────────────────────

    async def handle_emprestimo_banco(self, message, args):
        if not args:
            await message.channel.send("> ⚠️ Uso: `Tenshi, pedir-emprestimo [valor]`"); return
        try: valor = int(args[0].replace(".", ""))
        except: await message.channel.send("> ⚠️ Valor inválido."); return
        u = get_user(message.author.id)
        if u.get("divida", 0) > 0:
            await message.channel.send(
                f"> ⚠️ **Operação Recusada.** Você já possui uma dívida ativa: {fmt_moedas(u['divida'])}."); return
        if valor > 2000:
            await message.channel.send("> ⚠️ Limite de empréstimo: 2.000 moedas."); return
        u["divida"]           = valor
        u["juros_acumulados"] = 0
        u["moedas"]           = u.get("moedas", 0) + valor
        save_user(message.author.id, u)
        await message.channel.send(embed=embed_doc(
            "Empréstimo Aprovado",
            f"• **Valor concedido:** {fmt_moedas(valor)}\n"
            f"• **Juros diários:** {int(TAXA_JUROS_DIARIA*100)}%\n"
            f"• **Pagamento:** use `Tenshi, quitar` para liquidar a dívida.",
            COR_ADMIN
        ))

    async def handle_quitar(self, message, args):
        u = get_user(message.author.id)
        divida = u.get("divida", 0) + u.get("juros_acumulados", 0)
        if divida <= 0:
            await message.channel.send("> Sem dívidas registradas."); return
        if u["moedas"] < divida:
            await message.channel.send(
                f"> ⚠️ Saldo insuficiente. Dívida total: {fmt_moedas(divida)}."); return
        u["moedas"] -= divida; u["divida"] = 0; u["juros_acumulados"] = 0
        save_user(message.author.id, u)
        await message.channel.send(embed=embed_sucesso("Dívida Quitada", f"• {fmt_moedas(divida)} descontados."))

    # ── FALÊNCIA MÍSTICA ────────────────────────────────────────────────────

    async def verificar_falencia(self, guild, user_id: int):
        u = get_user(user_id)
        total = u.get("moedas", 0) + u.get("conta_banco", 0) - u.get("divida", 0) - u.get("juros_acumulados", 0)
        if total >= -200:
            return
        u["inventario"]      = []
        u["moedas"]          = 0
        u["conta_banco"]     = 0
        u["casa_condominio"] = None
        u["divida"]          = 0
        u["juros_acumulados"]= 0
        save_user(user_id, u)
        canal_logs = self._canal(guild, "logs-guarda")
        if canal_logs:
            membro = guild.get_member(user_id)
            nome   = membro.display_name if membro else str(user_id)
            await canal_logs.send(embed=embed_judicial(
                "Protocolo de Falência Mística",
                f"• **Cidadão:** {membro.mention if membro else nome}\n"
                f"• **Status:** Itens e propriedade confiscados por saldo negativo crônico.\n"
                f"• **Imperador notificado.**"
            ))

    # ── LAVAGEM DE DINHEIRO ─────────────────────────────────────────────────

    async def handle_lavagem(self, message, args):
        if not args:
            await message.channel.send("> ⚠️ Uso: `Tenshi, lavar [valor]`"); return
        canal_nome = getattr(message.channel, "name", "")
        if "beco" not in canal_nome.lower():
            await message.channel.send("> ⚠️ Operação restrita ao canal #beco."); return
        try: valor = int(args[0].replace(".", ""))
        except: await message.channel.send("> ⚠️ Valor inválido."); return
        u = get_user(message.author.id)
        if u.get("moedas", 0) < valor:
            await message.channel.send(f"> ⚠️ Saldo insuficiente."); return
        interceptado = random.random() < 0.35
        if interceptado:
            canal_policial = self._canal(message.guild, "jornal-policial")
            if canal_policial:
                await canal_policial.send(embed=embed_crime_doc(
                    "Tentativa de Lavagem de Dinheiro Detectada",
                    f"• **Suspeito:** {message.author.mention}\n"
                    f"• **Valor:** {fmt_moedas(valor)}\n"
                    f"• **Local:** #beco\n"
                    f"• Sistema de monitoramento da IA interceptou a operação."
                ))
            registrar_infracao(message.author.id, "lavagem_dinheiro", f"Tentativa de {valor} moedas")
            await message.channel.send(
                f"> ⚠️ **Operação interceptada pela IA de monitoramento.** Boletim emitido no #jornal-policial.")
        else:
            taxa = int(valor * 0.15)
            u["moedas"] -= taxa
            save_user(message.author.id, u)
            await message.channel.send(embed=embed_crime_doc(
                "Lavagem Concluída",
                f"• **Valor limpo:** {fmt_moedas(valor - taxa)}\n• **Taxa de lavagem:** {fmt_moedas(taxa)}"
            ))

    # ── TÍTULO DE DÍVIDA ────────────────────────────────────────────────────

    async def handle_titulo_divida(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok:
            await message.channel.send("> ⚠️ Exclusivo do Imperador e Cônjuge."); return
        if len(args) < 2:
            await message.channel.send("> ⚠️ Uso: `Tenshi, titulo-divida [valor] [dividendos%]`"); return
        try:
            valor = int(args[0].replace(".", ""))
            div   = int(args[1].replace("%",""))
        except:
            await message.channel.send("> ⚠️ Parâmetros inválidos."); return
        tid = str(uuid.uuid4())[:8].upper()
        await message.channel.send(embed=embed_soberano_decreto(
            "Título de Dívida Imperial Emitido",
            f"• **Código:** `{tid}`\n"
            f"• **Valor nominal:** {fmt_moedas(valor)}\n"
            f"• **Dividendos:** {div}% ao mês\n"
            f"• Use `Tenshi, subscrever {tid}` para adquirir."
        ))

    # ── TRANSPORTE — ACIDENTE DE TREM ────────────────────────────────────────

    async def handle_acidente_trem(self, guild):
        global _trem_paralisado_ate
        _trem_paralisado_ate = datetime.utcnow() + timedelta(minutes=30)
        canal = self._canal(guild, "estação-de-trem") or self._canal(guild, "estacao-de-trem")
        if canal:
            await canal.send(embed=embed_hospital(
                "Paralisação da Linha Ferroviária",
                "• Evento climático adverso detectado.\n"
                "• **Todos os serviços de trem suspensos por 30 minutos.**\n"
                "• Utilize a #garagem para deslocamento a pé (+40% fadiga)."
            ))

    def trem_paralisado(self) -> bool:
        if not _trem_paralisado_ate:
            return False
        return datetime.utcnow() < _trem_paralisado_ate

    # ── COMBUSTÍVEL ─────────────────────────────────────────────────────────

    async def handle_abastecer(self, message, args):
        u = get_user(message.author.id)
        if not u.get("veiculo"):
            await message.channel.send("> ⚠️ Nenhum veículo registrado."); return
        if u["moedas"] < CUSTO_COMBUSTIVEL:
            await message.channel.send(
                f"> ⚠️ Custo de abastecimento: {fmt_moedas(CUSTO_COMBUSTIVEL)}."); return
        u["moedas"] -= CUSTO_COMBUSTIVEL
        uid = str(message.author.id)
        _fuel_veiculos[uid] = {"combustivel": 100, "ultima_carga": datetime.utcnow().isoformat()}
        save_user(message.author.id, u)
        await message.channel.send(embed=embed_sucesso(
            "Veículo Abastecido",
            f"• Combustível: **100%**\n• Custo: {fmt_moedas(CUSTO_COMBUSTIVEL)}"
        ))

    def veiculo_com_combustivel(self, user_id: int) -> bool:
        uid = str(user_id)
        fuel = _fuel_veiculos.get(uid, {}).get("combustivel", 0)
        return fuel > 0

    # ── MANDADO DE BUSCA ────────────────────────────────────────────────────

    async def handle_mandado(self, message, args):
        u_data = get_user(message.author.id)
        try: adm = message.author.guild_permissions.administrator
        except: adm = False
        ok = adm or message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok:
            await message.channel.send("> ⚠️ Exclusivo de Alloy, Cônjuge e Magistrados."); return
        if not message.mentions:
            await message.channel.send("> ⚠️ Uso: `Tenshi, mandado @usuario [Casa-X]`"); return
        alvo = message.mentions[0]
        num  = None
        for a in args:
            if "casa" in a.lower():
                d = "".join(c for c in a if c.isdigit())
                if d: num = int(d); break
        if not num:
            await message.channel.send("> ⚠️ Especifique a casa. Ex: `Casa-3`"); return
        expira = datetime.utcnow() + timedelta(hours=2)
        _mandados[alvo.id] = {"expira": expira.isoformat(), "casa": num}
        # Destrancar temporariamente
        if message.guild:
            from database import get_vizinhanca
            viz = get_vizinhanca()
            c_id = viz.get(str(num), {}).get("id_canal")
            if c_id:
                canal_casa = message.guild.get_channel(int(c_id))
                if canal_casa:
                    try:
                        await canal_casa.set_permissions(message.guild.default_role, read_messages=True)
                    except Exception: pass
        await message.channel.send(embed=embed_judicial(
            f"Mandado de Busca — Casa-{num}",
            f"• **Alvo:** {alvo.mention}\n"
            f"• **Duração:** 2 horas\n"
            f"• Canal destrancado para inspeção das forças de ordem."
        ))
        await asyncio.sleep(7200)
        if alvo.id in _mandados and _mandados[alvo.id]["expira"] == expira.isoformat():
            del _mandados[alvo.id]
            if message.guild and c_id:
                canal_casa = message.guild.get_channel(int(c_id))
                if canal_casa:
                    try: await canal_casa.set_permissions(message.guild.default_role, overwrite=None)
                    except: pass

    # ── ALERTA DE FORAGIDO ──────────────────────────────────────────────────

    async def handle_foragido(self, guild, user_id: int, recompensa: int = 100):
        membro = guild.get_member(user_id)
        if not membro: return
        u = get_user(user_id)
        u["foragido"] = True; save_user(user_id, u)
        _foragidos[user_id] = {"recompensa": recompensa}
        e = embed_judicial(
            "Alerta — Cidadão em Fuga da Justiça",
            f"• **Foragido:** {membro.mention}\n"
            f"• **Recompensa:** {fmt_moedas(recompensa)} para quem o nocautear em duelo.\n"
            f"• Status visível em todos os canais públicos."
        )
        for ch in guild.text_channels:
            if any(k in ch.name.lower() for k in ("geral", "praça", "praca", "portaria")):
                try: await ch.send(embed=e); break
                except: pass

    # ── QUARENTENA MÉDICA ───────────────────────────────────────────────────

    async def handle_quarentena(self, guild, user_id: int, motivo: str = "item contaminado"):
        u = get_user(user_id); u["quarentena"] = True; save_user(user_id, u)
        membro = guild.get_member(user_id)
        canal_hospital = self._canal(guild, "hospital")
        if canal_hospital:
            await canal_hospital.send(embed=embed_hospital(
                "Quarentena Médica Ativada",
                f"• **Paciente:** {membro.mention if membro else user_id}\n"
                f"• **Motivo:** {motivo}\n"
                f"• Interações com o #GERAL suspensas."
            ))

    # ── SEGURO DE VIDA ──────────────────────────────────────────────────────

    async def handle_contratar_seguro(self, message, args):
        u = get_user(message.author.id)
        if u.get("seguro_vida"):
            await message.channel.send("> Você já possui seguro de vida ativo."); return
        if u["moedas"] < TAXA_SEGURO_VIDA:
            await message.channel.send(
                f"> ⚠️ Custo mensal: {fmt_moedas(TAXA_SEGURO_VIDA)}."); return
        u["moedas"] -= TAXA_SEGURO_VIDA
        u["seguro_vida"] = True
        u["seguro_data"]  = datetime.utcnow().isoformat()
        save_user(message.author.id, u)
        await message.channel.send(embed=embed_sucesso(
            "Seguro de Vida Imperial Contratado",
            f"• **Taxa mensal:** {fmt_moedas(TAXA_SEGURO_VIDA)}\n"
            f"• **Benefício:** Em caso de morte no RP, itens preservados e internação reduzida à metade."
        ))

    # ── NECROLÓGIO ──────────────────────────────────────────────────────────

    async def handle_necrolo(self, message, args):
        if not _necrologia:
            await message.channel.send(embed=embed_doc(
                "Mural dos Mortos — Império de Tenshi",
                "• Nenhum personagem registrou morte definitiva ainda.", COR_ADMIN))
            return
        e = embed_doc("Mural dos Mortos — Necrológio Imperial", "", COR_ADMIN)
        for n in _necrologia[-10:]:
            e.add_field(
                name=n["nome"],
                value=f"• **Data:** {n['data']}\n• **Causa:** {n['causa']}\n• **Raça:** {n.get('raca','—')}",
                inline=True
            )
        await message.channel.send(embed=e)

    def registrar_morte(self, nome: str, causa: str, raca: str = "—"):
        _necrologia.append({
            "nome": nome,
            "data": datetime.utcnow().strftime("%d/%m/%Y"),
            "causa": causa,
            "raca":  raca
        })

    # ── DIAGNÓSTICO DA IA ───────────────────────────────────────────────────

    async def handle_diagnostico_ia(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok:
            await message.channel.send("> ⚠️ Exclusivo do Imperador."); return
        import os
        db_size = 0
        for fname in os.listdir("data"):
            try: db_size += os.path.getsize(f"data/{fname}")
            except: pass
        latencia = round(self.bot.latency * 1000)
        e = embed_admin_doc(
            "Diagnóstico Técnico do Sistema",
            f"• **Latência da API:** {latencia}ms\n"
            f"• **Tamanho total dos dados (JSON):** {db_size / 1024:.1f} KB\n"
            f"• **Servidores ativos:** {len(self.bot.guilds)}\n"
            f"• **IA:** {'Groq conectado' if self._groq_ok() else 'Sem chave configurada'}\n"
            f"• **Keep-Alive:** Ativo via Flask"
        )
        await message.channel.send(embed=e)

    def _groq_ok(self) -> bool:
        import os; return bool(os.environ.get("GROQ_API_KEY"))

    # ── AUDITORIA BANCÁRIA ──────────────────────────────────────────────────

    async def handle_auditoria_bancaria(self, message, args):
        u_data = get_user(message.author.id)
        try: adm = message.author.guild_permissions.administrator
        except: adm = False
        ok = adm or message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok:
            await message.channel.send("> ⚠️ Exclusivo de Alloy, Cônjuge e Magistrados."); return
        if not message.mentions:
            await message.channel.send("> ⚠️ Mencione o usuário."); return
        alvo = message.mentions[0]; a_u = get_user(alvo.id)
        e = embed_admin_doc(
            f"Auditoria Bancária — {alvo.display_name}",
            f"• **Moedas em carteira:** {fmt_moedas(a_u.get('moedas',0))}\n"
            f"• **Conta bancária:** {fmt_moedas(a_u.get('conta_banco',0))}\n"
            f"• **Dívida:** {fmt_moedas(a_u.get('divida',0))}\n"
            f"• **Juros acumulados:** {fmt_moedas(a_u.get('juros_acumulados',0))}\n"
            f"• **Isento fiscal:** {'Sim' if a_u.get('isento_fiscal') else 'Não'}\n"
            f"• **Banco congelado:** {'Sim' if a_u.get('banco_congelado') else 'Não'}"
        )
        await message.channel.send(embed=e)

    # ── CRIPTOGRAFIA DE LOGS ────────────────────────────────────────────────

    async def handle_buscar_protocolo(self, message, args):
        u_data = get_user(message.author.id)
        try: adm = message.author.guild_permissions.administrator
        except: adm = False
        if not adm and message.author.id != IMPERADOR_ID and not u_data.get("co_soberano"):
            return
        if not args:
            await message.channel.send("> ⚠️ Uso: `Tenshi, buscar-protocolo [Código]`"); return
        cod = args[0].upper()
        await message.channel.send(embed=embed_admin_doc(
            f"Busca de Protocolo — {cod}",
            f"• Sistema de busca de logs ativo.\n"
            f"• Código `{cod}` pesquisado nos arquivos de auditoria.\n"
            f"• *Verifique os canais #logs-guarda e #logs-correio para o registro completo.*"
        ))

    # ── FUNDO DE PENSÃO ────────────────────────────────────────────────────

    async def handle_aposentar(self, message, args):
        u = get_user(message.author.id)
        if u.get("nivel", 1) < 20:
            await message.channel.send(
                f"> ⚠️ Aposentadoria requer nível 20. Seu nível atual: {u.get('nivel',1)}."); return
        if u.get("aposentado"):
            await message.channel.send("> Você já está aposentado."); return
        u["aposentado"]    = True
        u["salario_fixo"]  = 80
        u["poder_travado"] = u.get("poder", 0)
        save_user(message.author.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Aposentadoria Imperial Registrada",
            f"• **Poder de Luta travado em:** {u['poder_travado']}\n"
            f"• **Salário fixo diário:** {fmt_moedas(80)}\n"
            f"• Você não pode mais participar de combates ativos."
        ))

    # ── LOOPS DE BACKGROUND ───────────────────────────────────────────────

    async def _loop_juros_diarios(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            if agora.hour == 0 and agora.minute < 30:
                todos = get_all_users()
                for uid, u in todos.items():
                    divida = u.get("divida", 0)
                    if divida > 0:
                        juros = int(divida * TAXA_JUROS_DIARIA)
                        u["juros_acumulados"] = u.get("juros_acumulados", 0) + juros
                        # Auto-desconto se tiver saldo
                        total_devedor = divida + u["juros_acumulados"]
                        if u.get("moedas", 0) >= total_devedor:
                            u["moedas"] -= total_devedor
                            u["divida"] = 0; u["juros_acumulados"] = 0
                        save_user(int(uid), u)
                        for guild in self.bot.guilds:
                            await self.verificar_falencia(guild, int(uid))
            await asyncio.sleep(1800)

    async def _loop_imposto_fortunas(self):
        await self.bot.wait_until_ready()
        ultimo_mes = None
        while not self.bot.is_closed():
            agora = date.today()
            if agora.day == 1 and agora.month != ultimo_mes:
                ultimo_mes = agora.month
                todos = get_all_users()
                ordenados = sorted(todos.items(),
                    key=lambda x: x[1].get("moedas",0)+x[1].get("conta_banco",0), reverse=True)
                top3 = ordenados[:3]
                for uid, u in top3:
                    if u.get("isento_fiscal"): continue
                    total = u.get("moedas",0) + u.get("conta_banco",0)
                    if total > 5000:
                        aliq = 0.03 if total < 20000 else 0.05 if total < 50000 else 0.08
                        imposto = int(total * aliq)
                        u["moedas"] = max(0, u.get("moedas",0) - imposto)
                        save_user(int(uid), u)
                        imp_user = get_user(IMPERADOR_ID)
                        imp_user["moedas"] = imp_user.get("moedas",0) + imposto
                        save_user(IMPERADOR_ID, imp_user)
            await asyncio.sleep(3600)

    async def _loop_leiloes(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            encerrar = []
            for num, l in list(_leiloes_casa.items()):
                if agora >= datetime.fromisoformat(l["expira"]):
                    encerrar.append(num)
            for num in encerrar:
                l = _leiloes_casa.pop(num)
                if l.get("lance_uid"):
                    vencedor_u = get_user(l["lance_uid"])
                    vencedor_u["moedas"] = max(0, vencedor_u.get("moedas",0) - l["lance"])
                    vencedor_u["casa_condominio"] = num
                    save_user(l["lance_uid"], vencedor_u)
                    from database import get_vizinhanca, save_vizinhanca
                    viz = get_vizinhanca()
                    if str(num) in viz:
                        viz[str(num)]["id_dono"] = str(l["lance_uid"])
                        viz[str(num)]["status_aluguel"] = "comprada"
                        save_vizinhanca(viz)
            await asyncio.sleep(300)

    async def _loop_combustivel(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            for uid, f in list(_fuel_veiculos.items()):
                ultima = datetime.fromisoformat(f.get("ultima_carga", agora.isoformat()))
                horas  = (agora - ultima).total_seconds() / 3600
                consumo = int(horas * 5)
                f["combustivel"] = max(0, f.get("combustivel", 100) - consumo)
                f["ultima_carga"] = agora.isoformat()
            await asyncio.sleep(3600)

    async def _loop_auditoria_desempenho(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            if agora.weekday() == 0 and agora.hour == 9:
                todos = get_all_users()
                for uid, u in todos.items():
                    if not u.get("empregos_aprovados"): continue
                    ultimo_ativo = u.get("ultimo_trabalho")
                    if not ultimo_ativo: continue
                    diff = (agora - datetime.fromisoformat(ultimo_ativo)).days
                    if diff > 7:
                        for guild in self.bot.guilds:
                            canal_jornal = self._canal(guild, "jornal-dia-a-dia")
                            membro = guild.get_member(int(uid))
                            if canal_jornal and membro:
                                await canal_jornal.send(embed=embed_admin_doc(
                                    "Notificação de Exoneração Automática",
                                    f"• **Servidor:** {membro.mention}\n"
                                    f"• **Inatividade:** {diff} dias sem cumprir funções.\n"
                                    f"• Cargo exonerado por decurso de prazo."
                                ))
            await asyncio.sleep(3600)

    def abrir_leilao_casa(self, numero_casa: int, lance_inicial: int = 100):
        expira = datetime.utcnow() + timedelta(hours=24)
        _leiloes_casa[numero_casa] = {
            "lance":     lance_inicial,
            "lance_uid": None,
            "expira":    expira.isoformat()
        }
        return expira

    def _canal(self, guild, nome: str):
        if not guild: return None
        for ch in guild.text_channels:
            if nome.lower() in ch.name.lower():
                return ch
        return None
