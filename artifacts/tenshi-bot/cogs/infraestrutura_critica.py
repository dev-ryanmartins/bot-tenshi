"""
Módulos 19, 20, 21 — Infraestrutura Crítica, Macroeconomia e Alta Vigilância
40+40+50 funcionalidades condensadas nos blocos mais mecânicos e sistêmicos.
"""
import discord
import asyncio
import random
import hashlib
from datetime import datetime, timedelta, date
from database import get_user, save_user, get_all_users, _load, _save, registrar_infracao, INFRACOES_FILE
from utils import IMPERADOR_ID
from design import (embed_doc, embed_soberano_decreto, embed_judicial,
                    embed_sucesso, embed_perigo_doc, embed_admin_doc,
                    embed_crime_doc, embed_hospital, fmt_moedas,
                    COR_GERAL, COR_DECRETO, COR_JUDICIAL, COR_CRIME,
                    COR_ADMIN, COR_SUCESSO, COR_PERIGO, COR_HOSPITAL, rodape_padrao)

# ─── ARQUIVOS ─────────────────────────────────────────────────────────────────
ENERGIA_FILE      = "data/energia.json"
INFLACAO_FILE     = "data/inflacao.json"
ACOES_FILE        = "data/acoes.json"
POUPANCA_FILE     = "data/poupanca.json"
CAMERA_LOG_FILE   = "data/camera_logs.json"
DNA_FILE          = "data/dna_biometria.json"
CARGA_FILE        = "data/cargas.json"
PROPRIEDADE_FILE  = "data/propriedades.json"
FIANCA_FILE       = "data/fiancas.json"
CORREIO_LOG_FILE  = "data/correio_logs.json"
VEIC_DESGASTE_FILE = "data/veiculo_desgaste.json"
COMERCIO_FILE     = "data/comercios.json"
SUCATA_FILE       = "data/sucata.json"
ALUGUEL_COM_FILE  = "data/aluguel_comercial.json"
IMUNIDADE_FILE    = "data/imunidade_diplomatica.json"

# ─── ESTADO GLOBAL ────────────────────────────────────────────────────────────
_rede_eletrica_ok = True
_inflacao_nivel   = 0.0      # 0.0 = sem inflação, 1.0 = +20% nos preços
_emissoes_hoje    = 0
_economia_crise   = False
_autoridade_absoluta_ativa = False


def get_fator_preco() -> float:
    """Retorna multiplicador de preço baseado na inflação."""
    return 1.0 + (_inflacao_nivel * 0.20)


def registrar_emissao(qtd: int):
    global _emissoes_hoje, _inflacao_nivel
    _emissoes_hoje += qtd
    if _emissoes_hoje > 10000:
        _inflacao_nivel = min(1.0, _inflacao_nivel + 0.1)


def registrar_atividade_camera(canal_id: int, user_id: int, acao: str):
    logs = _load(CAMERA_LOG_FILE)
    cid = str(canal_id)
    if cid not in logs: logs[cid] = []
    logs[cid].append({
        "uid": str(user_id),
        "acao": acao,
        "ts": datetime.utcnow().isoformat()
    })
    if len(logs[cid]) > 100: logs[cid] = logs[cid][-100:]
    _save(CAMERA_LOG_FILE, logs)


class InfraestruturaCritica:
    def __init__(self, bot):
        self.bot = bot
        self._loops_iniciados = False

    def cog_load(self):
        if not self._loops_iniciados:
            self._loops_iniciados = True
            self.bot.loop.create_task(self._loop_poupanca())
            self.bot.loop.create_task(self._loop_acoes())
            self.bot.loop.create_task(self._loop_desgaste_veiculos())
            self.bot.loop.create_task(self._loop_iluminacao())
            self.bot.loop.create_task(self._loop_reset_emissoes())

    # ── BLOCO 1: INFRAESTRUTURA ENERGÉTICA ───────────────────────────────────

    async def handle_status_energia(self, message, args):
        e = embed_admin_doc(
            "Status da Rede Elétrica Imperial",
            f"• **Status:** {'OPERACIONAL' if _rede_eletrica_ok else 'SOBRECARREGADA — FALHA'}\n"
            f"• **Afetados (falha):** Cassino, máquinas da academia\n"
            f"• **Índice de inflação:** {_inflacao_nivel*100:.1f}%\n"
            f"• **Emissões monetárias hoje:** {fmt_moedas(_emissoes_hoje)}"
        )
        await message.channel.send(embed=e)

    async def handle_sobrecarga_rede(self, guild):
        global _rede_eletrica_ok
        _rede_eletrica_ok = False
        canal = self._canal(guild, "tenshi-enterprise") or self._canal(guild, "geral")
        if canal:
            await canal.send(embed=embed_perigo_doc(
                "Falha na Rede Elétrica Imperial",
                "• Sobrecarga detectada na usina da Tenshi Enterprise.\n"
                "• **Cassino e academia**: operações suspensas por 1 hora."
            ))
        await asyncio.sleep(3600)
        _rede_eletrica_ok = True

    # ── BLOCO 2: MACROECONOMIA ────────────────────────────────────────────────

    async def handle_status_inflacao(self, message, args):
        await message.channel.send(embed=embed_doc(
            "Índice de Inflação Imperial",
            f"• **Inflação atual:** {_inflacao_nivel*100:.1f}%\n"
            f"• **Fator de preço:** ×{get_fator_preco():.2f}\n"
            f"• **Emissões hoje:** {fmt_moedas(_emissoes_hoje)}\n"
            f"• Acima de 10.000 moedas emitidas/dia, preços aumentam automaticamente.", COR_ADMIN
        ))

    async def handle_comprar_acoes(self, message, args):
        if not args:
            await message.channel.send("> ⚠️ Uso: `Tenshi, comprar-acoes [quantidade]`"); return
        try: qtd = int(args[0])
        except: await message.channel.send("> ⚠️ Quantidade inválida."); return
        acoes = _load(ACOES_FILE)
        preco_unitario = acoes.get("preco_atual", 100)
        total = qtd * preco_unitario
        u = get_user(message.author.id)
        if u["moedas"] < total:
            await message.channel.send(f"> ⚠️ Custo total: {fmt_moedas(total)}."); return
        u["moedas"] -= total
        u.setdefault("acoes_empresa", 0)
        u["acoes_empresa"] += qtd
        save_user(message.author.id, u)
        await message.channel.send(embed=embed_sucesso(
            "Cotas Adquiridas — Tenshi Enterprise",
            f"• **Quantidade:** {qtd} cotas\n"
            f"• **Preço unitário:** {fmt_moedas(preco_unitario)}\n"
            f"• **Total:** {fmt_moedas(total)}\n"
            f"• Dividendos flutuam diariamente com a atividade do servidor."
        ))

    async def handle_poupanca(self, message, args):
        if not args:
            u = get_user(message.author.id)
            await message.channel.send(embed=embed_doc(
                "Conta Poupança",
                f"• **Saldo investido:** {fmt_moedas(u.get('poupanca',0))}\n"
                f"• **Rendimento:** 0,5% a cada 7 dias reais\n"
                f"• Use `Tenshi, poupanca depositar [valor]` ou `Tenshi, poupanca sacar [valor]`",
                COR_GERAL))
            return
        sub = args[0].lower()
        try: valor = int(args[1].replace(".", "")) if len(args) > 1 else 0
        except: valor = 0
        u = get_user(message.author.id)
        if sub == "depositar":
            if u["moedas"] < valor: await message.channel.send("> ⚠️ Saldo insuficiente."); return
            u["moedas"] -= valor; u["poupanca"] = u.get("poupanca", 0) + valor
            save_user(message.author.id, u)
            await message.channel.send(embed=embed_sucesso("Depósito em Poupança", f"• {fmt_moedas(valor)} investidos."))
        elif sub == "sacar":
            if u.get("poupanca", 0) < valor: await message.channel.send("> ⚠️ Saldo em poupança insuficiente."); return
            u["poupanca"] -= valor; u["moedas"] += valor
            save_user(message.author.id, u)
            await message.channel.send(embed=embed_sucesso("Saque de Poupança", f"• {fmt_moedas(valor)} transferidos para a carteira."))

    # ── BLOCO 3: VIGILÂNCIA ───────────────────────────────────────────────────

    async def handle_checar_cameras(self, message, args):
        u_data = get_user(message.author.id)
        try: adm = message.author.guild_permissions.administrator
        except: adm = False
        ok = adm or message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: await message.channel.send("> ⚠️ Exclusivo para Polícia e Trono."); return
        canal_alvo = message.channel_mentions[0] if message.channel_mentions else message.channel
        logs = _load(CAMERA_LOG_FILE).get(str(canal_alvo.id), [])
        agora = datetime.utcnow(); tres_horas_atras = agora - timedelta(hours=3)
        recentes = [l for l in logs if datetime.fromisoformat(l["ts"]) > tres_horas_atras][-5:]
        e = embed_admin_doc(
            f"DVR Intelbras — {canal_alvo.name}",
            f"• **Período:** Últimas 3 horas\n• **Registros:** {len(recentes)}/5"
        )
        for i, l in enumerate(recentes, 1):
            ts = datetime.fromisoformat(l["ts"]).strftime("%H:%M:%S")
            e.add_field(name=f"Registro #{i}", value=f"• UID: {l['uid']}\n• Ação: {l['acao']}\n• {ts} UTC", inline=True)
        await message.channel.send(embed=e)

    async def handle_biometria(self, message, args):
        alvo = message.mentions[0] if message.mentions else message.author
        dna = _load(DNA_FILE)
        uid = str(alvo.id)
        if uid not in dna:
            # Gerar registro biométrico
            dna[uid] = {
                "hash_bio": hashlib.sha256(f"{alvo.id}{alvo.name}".encode()).hexdigest()[:16].upper(),
                "data_criacao": datetime.utcnow().isoformat()
            }
            _save(DNA_FILE, dna)
        e = embed_admin_doc(
            "Registro Biométrico Imperial",
            f"• **Cidadão:** {alvo.mention}\n"
            f"• **Hash Biométrico:** `{dna[uid]['hash_bio']}`\n"
            f"• **Criado em:** {dna[uid]['data_criacao'][:10]}"
        )
        await message.channel.send(embed=e)

    async def handle_rastrear_perfil(self, message, args):
        u_data = get_user(message.author.id)
        try: adm = message.author.guild_permissions.administrator
        except: adm = False
        ok = adm or message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        if not message.mentions: await message.channel.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]; a_u = get_user(alvo.id)
        e = embed_admin_doc(
            f"OSINT Imperial — {alvo.display_name}",
            f"• **Local atual:** {a_u.get('local_atual','?')}\n"
            f"• **Nível:** {a_u.get('nivel',1)}\n"
            f"• **Poder:** {a_u.get('poder',0)}\n"
            f"• **Facção:** {a_u.get('faccao','Sem facção')}\n"
            f"• **Moedas:** {fmt_moedas(a_u.get('moedas',0))}\n"
            f"• **Conta banco:** {fmt_moedas(a_u.get('conta_banco',0))}\n"
            f"• **Dívida:** {fmt_moedas(a_u.get('divida',0))}\n"
            f"• **Foragido:** {'Sim' if a_u.get('foragido') else 'Não'}\n"
            f"• **Cidadania:** {'Ativa' if a_u.get('cidadania') else 'Sem registro'}\n"
            f"• **Compras recentes:** {len(a_u.get('historico_financeiro',[]))}\n"
        )
        await message.channel.send(embed=e)

    # ── BLOCO 4: LOGÍSTICA E ALFÂNDEGA ───────────────────────────────────────

    async def handle_enviar_carga(self, message, args):
        if not message.mentions or len(args) < 2:
            await message.channel.send("> ⚠️ Uso: `Tenshi, enviar-carga @user [Item]`"); return
        alvo = message.mentions[0]; item_nome = " ".join(args[1:])
        u = get_user(message.author.id)
        item = next((i for i in u.get("inventario", []) if item_nome.lower() in i.get("nome","").lower()), None)
        if not item: await message.channel.send("> ⚠️ Item não encontrado no inventário."); return
        u["inventario"].remove(item); save_user(message.author.id, u)
        chegada = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        cargas = _load(CARGA_FILE)
        cargas.setdefault(str(alvo.id), []).append({
            "item": item, "remetente": str(message.author.id),
            "chegada": chegada, "rastreio": f"TEN-{message.author.id}-{datetime.utcnow().strftime('%H%M%S')}"
        })
        _save(CARGA_FILE, cargas)
        await message.channel.send(embed=embed_admin_doc(
            "Carga Despachada — Correio Imperial",
            f"• **Destinatário:** {alvo.mention}\n"
            f"• **Item:** {item_nome}\n"
            f"• **Previsão de entrega:** 1 hora\n"
            f"• **Código de rastreio:** `{cargas[str(alvo.id)][-1]['rastreio']}`"
        ))

    async def handle_alfandega(self, message, user_id: int):
        u = get_user(user_id)
        ilegais = [i for i in u.get("inventario", []) if i.get("ilegal")]
        if ilegais and random.random() < 0.05:
            canal = message.channel
            membro = message.author
            await canal.send(embed=embed_judicial(
                "Inspeção Alfandegária — Item Ilegal Detectado",
                f"• **Passageiro:** {membro.mention}\n"
                f"• **Itens interceptados:** {len(ilegais)}\n"
                f"• Itens confiscados e auto-boletim emitido no #jornal-policial."
            ))
            u["inventario"] = [i for i in u["inventario"] if not i.get("ilegal")]
            save_user(user_id, u)
            registrar_infracao(user_id, "contrabando", f"{len(ilegais)} itens ilegais interceptados")

    # ── BLOCO 5: SAÚDE ────────────────────────────────────────────────────────

    async def handle_laudo_medico(self, message, args):
        u = get_user(message.author.id)
        try:
            from cogs.loremaster import _gerar
            from cogs.eras import _PROMPT_PTBR
            e = embed_doc("Laudo", "> ⚙️ Processando diretriz. Aguarde.", COR_HOSPITAL)
            msg = await message.channel.send(embed=e)
            sys_laudo = (
                f"Você é o Médico Legista Imperial. Emita um laudo médico formal e técnico em PT-BR "
                f"sobre o estado clínico do paciente. Base nos dados: fadiga {u.get('fadiga',0)}%, "
                f"vida {u.get('atributos',{}).get('vida',100)}, envenenado: {u.get('envenenado',False)}, "
                f"quarentena: {u.get('quarentena',False)}. Tom clínico, sóbrio, sem emojis. "
                f"Inclua diagnóstico, conduta recomendada e prognóstico.\n\n{_PROMPT_PTBR}"
            )
            laudo = await _gerar("Emita o laudo médico.", sys_laudo, u, 0.82)
            e2 = embed_hospital("Laudo Médico — " + message.author.display_name, laudo)
            e2.add_field(name="Fadiga", value=f"{u.get('fadiga',0)}%", inline=True)
            e2.add_field(name="Pontos de Vida", value=str(u.get("atributos",{}).get("vida",100)), inline=True)
            e2.add_field(name="Status", value="Quarentena" if u.get("quarentena") else "Nominal", inline=True)
            await msg.edit(embed=e2)
        except Exception as ex:
            await message.channel.send(f"> ⚠️ Erro no laudo: {str(ex)[:80]}")

    async def handle_desintoxicacao(self, message, args):
        u = get_user(message.author.id)
        custo = 80
        if u["moedas"] < custo: await message.channel.send(f"> ⚠️ Custo: {fmt_moedas(custo)}."); return
        u["moedas"] -= custo; u["embriaguez"] = 0; u["envenenado"] = False
        save_user(message.author.id, u)
        await message.channel.send(embed=embed_hospital(
            "Desintoxicação Clínica Concluída",
            f"• **Custo:** {fmt_moedas(custo)}\n• Nível de embriaguez e envenenamento zerados."
        ))

    async def handle_doacao_sangue(self, message, args):
        u = get_user(message.author.id)
        vida = u.get("atributos", {}).get("vida", 100)
        if vida < 40: await message.channel.send("> ⚠️ Vida insuficiente para doação segura (mínimo 40)."); return
        u["atributos"]["vida"] = vida - 20
        ganho = 40
        u["moedas"] = u.get("moedas", 0) + ganho
        save_user(message.author.id, u)
        await message.channel.send(embed=embed_hospital(
            "Doação de Sangue Místico",
            f"• **-20 pontos de vida** transferidos ao banco de sangue.\n"
            f"• **Compensação:** {fmt_moedas(ganho)}"
        ))

    # ── BLOCO 6: IMÓVEIS ──────────────────────────────────────────────────────

    async def handle_titulo_propriedade(self, message, args):
        u = get_user(message.author.id)
        casa_n = u.get("casa_condominio")
        if not casa_n: await message.channel.send("> ⚠️ Você não possui imóvel registrado."); return
        h = hashlib.sha256(f"{message.author.id}{casa_n}".encode()).hexdigest()[:16].upper()
        await message.channel.send(embed=embed_doc(
            "Escritura Digital de Imóvel",
            f"• **Proprietário:** {message.author.mention}\n"
            f"• **Imóvel:** Casa-{casa_n}\n"
            f"• **Hash de escritura:** `{h}`\n"
            f"• Registro válido no banco de dados imperial.", COR_GERAL
        ))

    async def handle_historico_imovel(self, message, args):
        if not args:
            await message.channel.send("> ⚠️ Uso: `Tenshi, historico-imovel [numero]`"); return
        try: num = int("".join(c for c in args[0] if c.isdigit()))
        except: await message.channel.send("> ⚠️ Número inválido."); return
        props = _load(PROPRIEDADE_FILE)
        hist = props.get(str(num), {}).get("historico", [])
        e = embed_admin_doc(
            f"Histórico de Ocupação — Casa-{num}",
            f"• **Total de ocupações registradas:** {len(hist)}"
        )
        for h in hist[-5:]:
            e.add_field(name=h.get("data","?"), value=f"• Proprietário: UID {h.get('uid','?')}", inline=True)
        await message.channel.send(embed=e)

    # ── BLOCO 7: ALUGUEL COMERCIAL ────────────────────────────────────────────

    async def handle_alugar_comercio(self, message, args):
        canais_comerciais = ["cafeteria", "sorveteria", "bar"]
        if not args or args[0].lower() not in canais_comerciais:
            await message.channel.send(
                f"> ⚠️ Comércios disponíveis: {', '.join(canais_comerciais)}. Uso: `Tenshi, alugar-comercio [local]`"); return
        local = args[0].lower(); custo = 300
        u = get_user(message.author.id)
        if u["moedas"] < custo: await message.channel.send(f"> ⚠️ Taxa semanal: {fmt_moedas(custo)}."); return
        u["moedas"] -= custo; save_user(message.author.id, u)
        al = _load(ALUGUEL_COM_FILE)
        al[local] = {"uid": str(message.author.id), "expira": (datetime.utcnow() + timedelta(days=7)).isoformat()}
        _save(ALUGUEL_COM_FILE, al)
        await message.channel.send(embed=embed_sucesso(
            f"Espaço Comercial Alugado — #{local}",
            f"• **Locatário:** {message.author.mention}\n"
            f"• **Duração:** 7 dias\n"
            f"• **Bônus:** 5% de toda moeda gasta no estabelecimento."
        ))

    # ── BLOCO 8: FIANÇA ────────────────────────────────────────────────────────

    async def handle_pagar_fianca(self, message, args):
        if not message.mentions: await message.channel.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        fiancas = _load(FIANCA_FILE); uid = str(alvo.id)
        if uid not in fiancas: await message.channel.send("> ⚠️ Nenhuma fiança registrada para este usuário."); return
        valor = fiancas[uid].get("valor", 0)
        u = get_user(message.author.id)
        if u["moedas"] < valor: await message.channel.send(f"> ⚠️ Valor da fiança: {fmt_moedas(valor)}."); return
        u["moedas"] -= valor; save_user(message.author.id, u)
        alvo_u = get_user(alvo.id); alvo_u["bloqueado_ate"] = None; save_user(alvo.id, alvo_u)
        del fiancas[uid]; _save(FIANCA_FILE, fiancas)
        await message.channel.send(embed=embed_sucesso(
            "Fiança Paga — Liberação Imediata",
            f"• **Preso liberado:** {alvo.mention}\n• **Fiança:** {fmt_moedas(valor)}"
        ))

    def definir_fianca(self, user_id: int, valor: int):
        fiancas = _load(FIANCA_FILE)
        fiancas[str(user_id)] = {"valor": valor, "data": datetime.utcnow().isoformat()}
        _save(FIANCA_FILE, fiancas)

    # ── BLOCO: IMUNIDADE DIPLOMÁTICA ─────────────────────────────────────────

    async def handle_imunidade_diplomatica(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        if not message.mentions: await message.channel.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        im = _load(IMUNIDADE_FILE); im[str(alvo.id)] = True; _save(IMUNIDADE_FILE, im)
        u = get_user(alvo.id); u["imunidade_diplomatica"] = True; save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Imunidade Diplomática Concedida",
            f"• **Beneficiário:** {alvo.mention}\n• Imune a prisões, furtos e mandados automáticos."
        ))

    def tem_imunidade(self, user_id: int) -> bool:
        return _load(IMUNIDADE_FILE).get(str(user_id), False)

    # ── COMANDOS DO SOBERANO (Módulos 19-21) ─────────────────────────────────

    async def cmd_auditoria_geral_banco(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        todos = get_all_users()
        linhas = []
        for uid, u in sorted(todos.items(), key=lambda x: x[1].get("moedas",0)+x[1].get("conta_banco",0), reverse=True)[:20]:
            total = u.get("moedas",0) + u.get("conta_banco",0)
            linhas.append(f"• UID {uid}: Carteira {fmt_moedas(u.get('moedas',0))} | Banco {fmt_moedas(u.get('conta_banco',0))}")
        await message.channel.send(embed=embed_admin_doc(
            "Auditoria Geral do Banco — Top 20",
            "\n".join(linhas) or "Nenhum dado."
        ))

    async def cmd_expurgar_fichas_inativas(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        dias = int(args[0]) if args and args[0].isdigit() else 30
        todos = get_all_users()
        removidos = 0
        from database import DB_FILE
        dados = _load(DB_FILE)
        for uid, u in list(todos.items()):
            ult = u.get("ultimo_trabalho") or u.get("ultima_missao") or u.get("ultimo_treino")
            if not ult: continue
            if (datetime.utcnow() - datetime.fromisoformat(ult)).days > dias:
                del dados[uid]; removidos += 1
        _save(DB_FILE, dados)
        await message.channel.send(embed=embed_soberano_decreto(
            "Expurgo de Fichas Inativas",
            f"• **Critério:** {dias} dias sem atividade\n• **Fichas removidas:** {removidos}"
        ))

    async def cmd_reset_parcial_economia(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        todos = get_all_users()
        for uid, u in todos.items():
            u["moedas"] = 0; u["conta_banco"] = 0
            save_user(int(uid), u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Reset Parcial da Economia",
            "• Todas as carteiras e saldos bancários zerados.\n• Casas, itens e conquistas preservados."
        ))

    async def cmd_bans_lista(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        todos = get_all_users()
        exilados = [(uid, u) for uid, u in todos.items() if u.get("exilado")]
        e = embed_judicial("Lista de Exilados — Registro Imperial", f"• Total: {len(exilados)}")
        for uid, u in exilados[:10]:
            e.add_field(name=f"UID {uid}", value=f"• Status: Exilado\n• Bloqueado até: {u.get('bloqueado_ate','indefinido')[:10] if u.get('bloqueado_ate') else 'Permanente'}", inline=True)
        await message.channel.send(embed=e)

    async def cmd_confiscar_veiculo(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        if not message.mentions: await message.channel.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]; a_u = get_user(alvo.id)
        veiculo = a_u.pop("veiculo", None)
        if not veiculo: await message.channel.send("> ⚠️ Alvo sem veículo registrado."); return
        save_user(alvo.id, a_u)
        imp = get_user(IMPERADOR_ID)
        imp.setdefault("frota_real", []).append(veiculo); save_user(IMPERADOR_ID, imp)
        await message.channel.send(embed=embed_soberano_decreto(
            "Confisco de Veículo Imperial",
            f"• **Alvo:** {alvo.mention}\n• **Veículo:** {veiculo.get('nome','?')}\n• Transferido para a frota privada do Trono."
        ))

    async def cmd_decreto_climatico(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        if not args: await message.channel.send("> ⚠️ Forneça o clima."); return
        clima = " ".join(args)
        for guild in self.bot.guilds:
            canal = self._canal(guild, "clima")
            if canal:
                await canal.send(embed=embed_soberano_decreto(
                    "Decreto Climático Imperial",
                    f"• **Condição forçada:** {clima}\n• Modificadores etéreos aplicados por ordem soberana."
                ))
        await message.channel.send(embed=embed_sucesso("Decreto Climático Aplicado", f"• Clima alterado para: {clima}"))

    # ── LOOPS DE BACKGROUND ───────────────────────────────────────────────────

    async def _loop_poupanca(self):
        await self.bot.wait_until_ready()
        ultimo_render = None
        while not self.bot.is_closed():
            agora = date.today()
            if agora.weekday() == 0 and ultimo_render != agora:
                ultimo_render = agora
                todos = get_all_users()
                for uid, u in todos.items():
                    p = u.get("poupanca", 0)
                    if p > 0 and not u.get("warns", 0):
                        rendimento = int(p * 0.005)
                        u["poupanca"] = p + rendimento
                        save_user(int(uid), u)
            await asyncio.sleep(3600)

    async def _loop_acoes(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            acoes = _load(ACOES_FILE)
            todos = get_all_users()
            atividade = sum(1 for _ in todos.values())
            preco = max(50, min(500, 100 + atividade * 2 + random.randint(-20, 20)))
            acoes["preco_atual"] = preco
            _save(ACOES_FILE, acoes)
            # Pagar dividendos diários
            for uid, u in todos.items():
                cotas = u.get("acoes_empresa", 0)
                if cotas > 0:
                    divid = int(cotas * preco * 0.001)
                    if divid > 0:
                        u["moedas"] = u.get("moedas",0) + divid
                        save_user(int(uid), u)
            await asyncio.sleep(86400)

    async def _loop_desgaste_veiculos(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            todos = get_all_users()
            for uid, u in todos.items():
                veiculo = u.get("veiculo")
                if veiculo and veiculo.get("durabilidade", 100) > 0:
                    veiculo["durabilidade"] = max(0, veiculo["durabilidade"] - 1)
                    save_user(int(uid), u)
            await asyncio.sleep(3600)

    async def _loop_iluminacao(self):
        """Altera topics dos canais públicos para modo diurno/noturno às 6h e 18h."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            if agora.hour in (6, 18) and agora.minute < 30:
                modo = "🌞 Modo Diurno — Iluminação Rúnica Desativada" if agora.hour == 6 else "🌙 Modo Noturno — Lâmpadas Rúnicas Ativadas"
                for guild in self.bot.guilds:
                    for ch in guild.text_channels:
                        if any(k in ch.name.lower() for k in ("parque", "praça", "praca", "jardim")):
                            try: await ch.edit(topic=modo)
                            except: pass
            await asyncio.sleep(1800)

    async def _loop_reset_emissoes(self):
        """Reset diário das emissões para controle de inflação."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            agora = datetime.utcnow()
            if agora.hour == 0 and agora.minute < 30:
                global _emissoes_hoje
                _emissoes_hoje = 0
            await asyncio.sleep(1800)

    def _canal(self, guild, nome: str):
        if not guild: return None
        for ch in guild.text_channels:
            if nome.lower() in ch.name.lower(): return ch
        return None
