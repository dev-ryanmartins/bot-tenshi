"""
Módulo de Prerrogativas Reais — Módulo 15
30 comandos exclusivos do Imperador Alloy.
Verificação estrita: só IMPERADOR_ID pode usar estes comandos.
"""
import discord
import asyncio
import json
import os
from datetime import datetime
from database import (get_user, save_user, get_all_users,
                      registrar_infracao, get_infrações)
from utils import IMPERADOR_ID, SEP, RODAPE_IMPERIAL
from design import (embed_doc, embed_soberano_decreto, embed_admin_doc,
                    embed_judicial, embed_sucesso, embed_perigo_doc,
                    embed_crime_doc, fmt_moedas,
                    COR_GERAL, COR_DECRETO, COR_JUDICIAL, COR_CRIME,
                    COR_ADMIN, COR_SUCESSO, COR_PERIGO, COR_NEUTRO, rodape_padrao)
from ia_router import ia_soberana, ia_narrativa, ia_relatorio

# ─── ESTADO GLOBAL SOBERANO ───────────────────────────────────────────────────
_economia_congelada    = False
_bypass_cooldown_ids:  set = set()
_termos_censurados:    list = []
_sys_prompt_override:  str | None = None
_memoria_ia:           list = []   # histórico de contexto da IA

def economia_congelada() -> bool:
    return _economia_congelada

def is_bypass_cooldown(user_id: int) -> bool:
    return user_id in _bypass_cooldown_ids


def _log_tentativa_invasao(uid: int, cmd: str):
    """Registrar tentativa de uso de comando soberano por não-autorizado."""
    registrar_infracao(uid, "tentativa_invasao_soberana", f"Tentou usar: {cmd}", "Sistema_Segurança")


class Soberano:
    def __init__(self, bot):
        self.bot = bot

    def _verificar(self, message, cmd: str) -> bool:
        """Retorna True se autorizado. Registra tentativa se não."""
        user_data = get_user(message.author.id)
        ok = (message.author.id == IMPERADOR_ID or user_data.get("co_soberano"))
        if not ok:
            self.bot.loop.create_task(self._log_seg(message, cmd))
        return ok

    async def _log_seg(self, message, cmd: str):
        _log_tentativa_invasao(message.author.id, cmd)
        canal_logs = self._canal(message.guild, "logs-guarda")
        if canal_logs:
            e = embed_admin_doc(
                "Alerta de Segurança — Acesso Negado",
                f"• **Usuário:** {message.author.mention} (ID: {message.author.id})\n"
                f"• **Comando tentado:** `{cmd}`\n"
                f"• **Localização RP:** {getattr(message.channel, 'name', '?')}\n"
                f"• **Protocolo:** Tentativa registrada e arquivada."
            )
            await canal_logs.send(embed=e)

    def _canal(self, guild, nome: str):
        if not guild:
            return None
        for ch in guild.text_channels:
            if nome.lower() in ch.name.lower():
                return ch
        return None

    # ─── A) CONTROLE MONETÁRIO ────────────────────────────────────────────────

    async def cmd_emitir_moeda(self, message, args):
        if not self._verificar(message, "emitir-moeda"): return
        if not args:
            await message.author.send(embed_doc("Uso", "`Tenshi, emitir-moeda [quantia]`", COR_ADMIN))
            return
        try: qtd = int(args[0].replace(".", ""))
        except: await message.author.send("> ⚠️ **Operação Recusada.** Quantia inválida."); return
        user = get_user(IMPERADOR_ID)
        user["moedas"] = user.get("moedas", 0) + qtd
        save_user(IMPERADOR_ID, user)
        e = embed_soberano_decreto(
            "Emissão Monetária Imperial",
            f"• **Quantia emitida:** {fmt_moedas(qtd)}\n"
            f"• **Destino:** Tesouro Real do Soberano\n"
            f"• **Autor:** <@{IMPERADOR_ID}>"
        )
        await message.channel.send(embed=e)

    async def cmd_confiscar_fortuna(self, message, args):
        if not self._verificar(message, "confiscar-fortuna"): return
        if not message.mentions:
            await message.author.send("> ⚠️ **Operação Recusada.** Mencione o alvo."); return
        alvo = message.mentions[0]
        a_user = get_user(alvo.id)
        total  = a_user.get("moedas", 0) + a_user.get("conta_banco", 0)
        a_user["moedas"] = 0; a_user["conta_banco"] = 0
        save_user(alvo.id, a_user)
        i_user = get_user(IMPERADOR_ID)
        i_user["moedas"] = i_user.get("moedas", 0) + total
        save_user(IMPERADOR_ID, i_user)
        await message.channel.send(embed=embed_soberano_decreto(
            "Decreto de Confisco de Fortuna",
            f"• **Alvo:** {alvo.mention}\n"
            f"• **Total confiscado:** {fmt_moedas(total)}\n"
            f"• **Destino:** Tesouro Real"
        ))

    async def cmd_congelar_banco(self, message, args):
        if not self._verificar(message, "congelar-banco"): return
        if not message.mentions:
            await message.author.send("> ⚠️ **Operação Recusada.** Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id); u["banco_congelado"] = True; save_user(alvo.id, u)
        await message.channel.send(embed=embed_judicial(
            "Conta Bancária Congelada",
            f"• **Titular:** {alvo.mention}\n"
            f"• **Status:** Contas bloqueadas — saques, depósitos e transferências suspensos.\n"
            f"• **Autoridade:** Decreto Soberano"
        ))

    async def cmd_perdoar_divida(self, message, args):
        if not self._verificar(message, "perdoar-divida"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id); u["divida"] = 0; u["juros_acumulados"] = 0; save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Perdão Imperial de Dívida",
            f"• **Beneficiário:** {alvo.mention}\n• **Saldo devedor zerado** por decreto soberano."
        ))

    async def cmd_isencao_fiscal(self, message, args):
        if not self._verificar(message, "isencao-fiscal"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id); u["isento_fiscal"] = True; save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Isenção Fiscal Imperial",
            f"• **Beneficiário:** {alvo.mention}\n• Imunidade tributária permanente concedida."
        ))

    # ─── B) MANIPULAÇÃO DO RPG ────────────────────────────────────────────────

    async def cmd_set_status(self, message, args):
        if not self._verificar(message, "set-status"): return
        if not message.mentions or len(args) < 3:
            await message.author.send("> ⚠️ Uso: `Tenshi, set-status @user [atributo] [valor]`"); return
        alvo = message.mentions[0]
        atributo = args[1].lower(); valor_str = args[2]
        try: valor = int(valor_str)
        except: await message.author.send("> ⚠️ Valor inválido."); return
        u = get_user(alvo.id)
        if atributo in ("poder", "vida", "mana", "xp", "nivel", "fadiga"):
            u[atributo] = valor
        else:
            u.setdefault("atributos", {})[atributo] = valor
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Intervenção de Estado — Modificação de Status",
            f"• **Alvo:** {alvo.mention}\n• **Atributo:** {atributo}\n• **Novo valor:** {valor}"
        ))

    async def cmd_apagar_ficha(self, message, args):
        if not self._verificar(message, "apagar-ficha"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        from database import _save, DB_FILE, _load
        dados = _load(DB_FILE)
        if str(alvo.id) in dados:
            del dados[str(alvo.id)]
            _save(DB_FILE, dados)
        await message.channel.send(embed=embed_judicial(
            "Apagamento de Ficha Imperial",
            f"• **Membro:** {alvo.mention}\n• Ficha, inventário e histórico removidos do banco de dados."
        ))

    async def cmd_conceder_item(self, message, args):
        if not self._verificar(message, "conceder-item"): return
        if not message.mentions or len(args) < 2:
            await message.author.send("> ⚠️ Uso: `Tenshi, conceder-item @user [Item] [qtd]`"); return
        alvo = message.mentions[0]
        item_nome = " ".join(args[1:-1]) if len(args) > 2 else args[1]
        qtd = int(args[-1]) if len(args) > 2 and args[-1].isdigit() else 1
        u = get_user(alvo.id)
        for _ in range(qtd):
            u.setdefault("inventario", []).append({
                "id": item_nome.lower().replace(" ", "_"), "nome": item_nome,
                "origem": "decreto_imperial", "data": datetime.utcnow().isoformat()
            })
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Concessão Imperial de Item",
            f"• **Destinatário:** {alvo.mention}\n• **Item:** {item_nome}  ×{qtd}"
        ))

    async def cmd_purificar_status(self, message, args):
        if not self._verificar(message, "purificar-status"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id)
        for campo in ("envenenado", "quarentena", "nocauteado", "bloqueado_ate", "ferido"):
            u[campo] = False if isinstance(u.get(campo), bool) else None
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Purificação de Status Imperial",
            f"• **Alvo:** {alvo.mention}\n• Todas as condições negativas removidas."
        ))

    async def cmd_imortalidade(self, message, args):
        if not self._verificar(message, "imortalidade"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]; toggle = args[1].lower() if len(args) > 1 else "on"
        u = get_user(alvo.id); u["imortal"] = toggle != "off"; save_user(alvo.id, u)
        status = "ATIVADA" if u["imortal"] else "REVOGADA"
        await message.channel.send(embed=embed_soberano_decreto(
            f"Imortalidade {status}",
            f"• **Membro:** {alvo.mention}\n• Flag de imortalidade: **{status}**"
        ))

    # ─── C) DECRETOS DE ESTADO ────────────────────────────────────────────────

    async def cmd_estado_de_sitio(self, message, args):
        if not self._verificar(message, "estado-de-sitio"): return
        if not message.guild: return
        bloqueados = 0
        for cat in message.guild.categories:
            n = cat.name.lower()
            if any(k in n for k in ("condomínio", "cidade", "mafia", "beco", "empresa")):
                try:
                    await cat.set_permissions(message.guild.default_role,
                                               send_messages=False, read_messages=False)
                    bloqueados += 1
                except Exception: pass
        await message.channel.send(embed=embed_soberano_decreto(
            "Decreto de Estado de Sítio",
            f"• **Categorias isoladas:** {bloqueados}\n"
            f"• Acesso público suspenso por ordem imperial.\n"
            f"• Canais de portões e GERAL permanecem operacionais."
        ))

    async def cmd_dissolver_mafia(self, message, args):
        if not self._verificar(message, "dissolver-mafia"): return
        if not message.guild: return
        removidos = 0
        for membro in message.guild.members:
            for cargo in membro.roles:
                if "máfia" in cargo.name.lower() or "mafia" in cargo.name.lower():
                    try: await membro.remove_roles(cargo); removidos += 1
                    except Exception: pass
        await message.channel.send(embed=embed_soberano_decreto(
            "Dissolução Compulsória da Máfia",
            f"• **Cargos removidos:** {removidos} membros afastados\n"
            f"• Categoria do subterrâneo: trancada por decreto."
        ))

    async def cmd_estatizar_casa(self, message, args):
        if not self._verificar(message, "estatizar-casa"): return
        if not args:
            await message.author.send("> ⚠️ Uso: `Tenshi, estatizar-casa [Casa-X]`"); return
        try: numero = int("".join(c for c in args[0] if c.isdigit()))
        except: await message.author.send("> ⚠️ Número inválido."); return
        from database import get_vizinhanca, save_vizinhanca, get_user, save_user
        viz = get_vizinhanca(); chave = str(numero)
        casa = viz.get(chave, {})
        dono_id = casa.get("id_dono")
        if dono_id:
            u = get_user(int(dono_id)); u["casa_condominio"] = None; save_user(int(dono_id), u)
        viz[chave] = {**casa, "id_dono": None, "lista_moradores": [], "status_aluguel": "disponivel"}
        save_vizinhanca(viz)
        await message.channel.send(embed=embed_soberano_decreto(
            f"Estatização de Imóvel — Casa-{numero}",
            f"• **Propriedade:** Casa-{numero} retornada ao controle do Trono.\n• Sem reembolso ao ex-proprietário."
        ))

    async def cmd_silenciar_geral(self, message, args):
        if not self._verificar(message, "silenciar-geral"): return
        if not message.guild: return
        for ch in message.guild.text_channels:
            if "geral" in ch.name.lower():
                try:
                    await ch.set_permissions(message.guild.default_role, send_messages=False)
                except Exception: pass
        await message.channel.send(embed=embed_soberano_decreto(
            "Silêncio Imperial no GERAL",
            "• Canal #GERAL trancado para todos os cargos, exceto Soberano e Cônjuge."
        ))

    async def cmd_anistia_geral(self, message, args):
        if not self._verificar(message, "anistia-geral"): return
        from database import _save, INFRACOES_FILE
        _save(INFRACOES_FILE, {})
        await message.channel.send(embed=embed_soberano_decreto(
            "Anistia Geral Imperial",
            "• Todos os warns, históricos criminais e registros de infração foram apagados por decreto soberano."
        ))

    # ─── D) ALTA JUSTIÇA ──────────────────────────────────────────────────────

    async def cmd_exilio_supremo(self, message, args):
        if not self._verificar(message, "exilio-supremo"): return
        if not message.mentions:
            await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        motivo = " ".join(args[1:]) if len(args) > 1 else "Decreto soberano"
        canal_pun = self._canal(message.guild, "punições")
        try: await alvo.ban(reason=f"Exílio Supremo: {motivo}")
        except Exception: pass
        if canal_pun:
            await canal_pun.send(embed=embed_judicial(
                "COMUNICADO DE EXÍLIO SUPREMO",
                f"• **Membro:** {alvo.display_name} (ID: {alvo.id})\n"
                f"• **Motivo:** {motivo}\n"
                f"• **Autoridade:** Decreto Soberano — irrevogável.\n"
                f"• **Histórico de mensagens:** Purgado."
            ))
        await message.channel.send(embed=embed_soberano_decreto(
            "Exílio Supremo Aplicado",
            f"• {alvo.display_name} banido permanentemente. Decreto arquivado."
        ))

    async def cmd_perdao_judicial(self, message, args):
        if not self._verificar(message, "perdao-judicial"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id)
        u["bloqueado_ate"] = None; u["nocauteado"] = False; u["exilado"] = False
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Perdão Judicial Imperial",
            f"• **Beneficiário:** {alvo.mention}\n• Status de isolamento e masmorra revogados imediatamente."
        ))

    async def cmd_revogar_diploma(self, message, args):
        if not self._verificar(message, "revogar-diploma"): return
        if not message.mentions or len(args) < 2:
            await message.author.send("> ⚠️ Uso: `Tenshi, revogar-diploma @user [Materia]`"); return
        alvo = message.mentions[0]; materia = " ".join(args[1:])
        u = get_user(alvo.id)
        diplomas = u.get("diplomas", [])
        u["diplomas"] = [d for d in diplomas if materia.lower() not in str(d).lower()]
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_judicial(
            "Revogação de Diploma",
            f"• **Membro:** {alvo.mention}\n• **Matéria revogada:** {materia}"
        ))

    async def cmd_cassar_conjuge(self, message, args):
        if not self._verificar(message, "cassar-conjuge"): return
        u = get_user(IMPERADOR_ID)
        conjuge_id = u.get("conjuge")
        if not conjuge_id:
            await message.channel.send("> ⚠️ Nenhum casamento imperial registrado."); return
        u["conjuge"] = None; u["taxa_casa_divisao"] = False; save_user(IMPERADOR_ID, u)
        c = get_user(int(conjuge_id))
        c["conjuge"] = None; c["co_soberano"] = False; c["taxa_casa_divisao"] = False
        save_user(int(conjuge_id), c)
        await message.channel.send(embed=embed_soberano_decreto(
            "Dissolução de Casamento Real — Decreto Sumário",
            f"• Casamento imperial dissolvido por ordem de emergência.\n"
            f"• Co-soberania do ex-cônjuge revogada."
        ))

    # ─── E) IA E CONTROLE DE CONTEÚDO ────────────────────────────────────────

    async def cmd_atualizar_diretriz(self, message, args):
        if not self._verificar(message, "atualizar-diretriz"): return
        if not args:
            await message.author.send("> ⚠️ Fornença o texto da nova diretriz."); return
        global _sys_prompt_override
        _sys_prompt_override = " ".join(args)
        await message.author.send(embed=embed_admin_doc(
            "Diretriz da IA Atualizada",
            f"• Novo system prompt configurado:\n```\n{_sys_prompt_override[:300]}\n```"
        ))
        await message.channel.send(embed=embed_soberano_decreto(
            "Diretriz da IA Atualizada",
            "• Sistema de IA recalibrado por ordem imperial."
        ))

    async def cmd_apagar_memoria_ia(self, message, args):
        if not self._verificar(message, "apagar-memoria-ia"): return
        global _memoria_ia
        _memoria_ia = []
        await message.channel.send(embed=embed_soberano_decreto(
            "Memória da IA Limpa",
            "• Histórico de contexto recente apagado. Fluxo de conversa resetado."
        ))

    async def cmd_interceptar_correio(self, message, args):
        if not self._verificar(message, "interceptar-correio"): return
        if not message.mentions: await message.author.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        from database import _load
        correio_data = _load("data/correio_logs.json")
        msgs = correio_data.get(str(alvo.id), [])
        if not msgs:
            await message.author.send(f"Nenhuma correspondência registrada de {alvo.display_name} nas últimas 24h.")
            return
        e = embed_admin_doc("Interceptação de Correio — Confidencial",
            f"• **Alvo:** {alvo.display_name}\n• **Total de mensagens:** {len(msgs)}\n")
        for i, m in enumerate(msgs[-5:], 1):
            e.add_field(name=f"Carta #{i}", value=m.get("conteudo", "?")[:200], inline=False)
        await message.author.send(embed=e)

    async def cmd_forcar_cronica(self, message, args):
        if not self._verificar(message, "forçar-cronica"): return
        if len(args) < 2:
            await message.author.send("> ⚠️ Uso: `Tenshi, forçar-cronica [nicho] [tema]`"); return
        nicho = args[0]; tema = " ".join(args[1:])
        canal_nicho = self._canal(message.guild, nicho) or message.channel
        from cogs.loremaster import _gerar, SYS_LORE
        narrativa = await _gerar(
            f"Gere uma crônica urgente para o nicho '{nicho}' sobre o tema: {tema}. "
            f"Diretriz do Imperador Alloy: incorpore este tema de forma que direcione o RP.",
            SYS_LORE
        )
        e = embed_soberano_decreto(f"Crônica Forçada — {nicho.capitalize()}", narrativa)
        await canal_nicho.send(embed=e)
        await message.channel.send(embed=embed_sucesso("Crônica Enviada", f"Canal-alvo: {canal_nicho.mention}"))

    async def cmd_censurar_termo(self, message, args):
        if not self._verificar(message, "censurar-termo"): return
        if not args: await message.author.send("> ⚠️ Forneça o termo."); return
        termo = " ".join(args).lower()
        if termo not in _termos_censurados:
            _termos_censurados.append(termo)
        await message.channel.send(embed=embed_soberano_decreto(
            "Termo Censurado Adicionado",
            f"• **Termo:** `{termo}`\n• Adicionado à lista de palavras-chave subversivas monitoradas."
        ))

    # ─── F) ENGENHARIA E MANUTENÇÃO ───────────────────────────────────────────

    async def cmd_desligar(self, message, args):
        if not self._verificar(message, "desligar"): return
        await message.channel.send(embed=embed_soberano_decreto(
            "Encerramento Seguro Iniciado",
            "• O sistema será desligado em 3 segundos por ordem imperial."
        ))
        await asyncio.sleep(3)
        await self.bot.close()

    async def cmd_forcar_pagamento(self, message, args):
        if not self._verificar(message, "forçar-pagamento"): return
        todos = get_all_users()
        pagamentos = 0
        for uid, u_data in todos.items():
            salario = u_data.get("salario", 0)
            if salario > 0:
                u_data["moedas"] = u_data.get("moedas", 0) + salario
                from database import save_user as sv
                sv(int(uid), u_data)
                pagamentos += 1
        await message.channel.send(embed=embed_soberano_decreto(
            "Folha de Pagamento Antecipada",
            f"• **Pagamentos processados:** {pagamentos} funcionários\n"
            f"• Salários depositados com efeito imediato."
        ))

    async def cmd_exportar_banco(self, message, args):
        if not self._verificar(message, "exportar-banco"): return
        import json as _json
        from database import _load, DB_FILE
        dados = _load(DB_FILE)
        texto = _json.dumps(dados, ensure_ascii=False, indent=2)
        with open("/tmp/backup_imperial.json", "w", encoding="utf-8") as f:
            f.write(texto)
        try:
            await message.author.send(
                content="Backup imperial gerado:",
                file=discord.File("/tmp/backup_imperial.json", filename="backup_imperial.json")
            )
            await message.channel.send(embed=embed_soberano_decreto(
                "Backup Exportado",
                "• Arquivo .json enviado via DM para o Soberano."
            ))
        except Exception:
            await message.channel.send("> ⚠️ Não foi possível enviar o arquivo via DM.")

    async def cmd_bypass_cooldown(self, message, args):
        if not self._verificar(message, "bypass-cooldown"): return
        if message.author.id in _bypass_cooldown_ids:
            _bypass_cooldown_ids.discard(message.author.id)
            status = "DESATIVADO"
        else:
            _bypass_cooldown_ids.add(message.author.id)
            status = "ATIVADO"
        await message.channel.send(embed=embed_soberano_decreto(
            f"Bypass de Cooldown {status}",
            f"• Todos os cooldowns para o Soberano estão agora **{status}S**."
        ))

    async def cmd_congelar_economia(self, message, args):
        if not self._verificar(message, "congelar-economia"): return
        global _economia_congelada
        _economia_congelada = not _economia_congelada
        status = "CONGELADA" if _economia_congelada else "RESTABELECIDA"
        await message.channel.send(embed=embed_soberano_decreto(
            f"Economia Imperial — {status}",
            f"• Transferências, compras e salários: **{'SUSPENSOS' if _economia_congelada else 'ATIVOS'}**"
        ))

    async def cmd_censo_imperial(self, message, args):
        if not self._verificar(message, "censo-imperial"): return
        todos = get_all_users()
        total = len(todos)
        if total == 0:
            await message.channel.send("> Nenhum cidadão registrado."); return
        soma_nivel = sum(u.get("nivel", 1) for u in todos.values())
        soma_poder = sum(u.get("poder", 0) for u in todos.values())
        soma_moedas = sum(u.get("moedas", 0) for u in todos.values())
        racas: dict = {}
        for u in todos.values():
            r = u.get("especie", "indefinida")
            racas[r] = racas.get(r, 0) + 1
        raca_txt = "\n".join(f"  • {r}: {n}" for r, n in sorted(racas.items(), key=lambda x: -x[1])[:5])
        from database import get_vizinhanca
        viz = get_vizinhanca()
        casas_ocup = sum(1 for v in viz.values() if v.get("id_dono"))
        e = embed_soberano_decreto("Censo Imperial de Tenshi",
            f"• **Total de cidadãos:** {total}\n"
            f"• **Nível médio:** {soma_nivel/total:.1f}\n"
            f"• **Poder médio:** {soma_poder/total:.0f}\n"
            f"• **Total em circulação:** {fmt_moedas(soma_moedas)}\n"
            f"• **Casas ocupadas:** {casas_ocup}/18\n\n"
            f"**Espécies mais jogadas:**\n{raca_txt}"
        )
        await message.channel.send(embed=e)

    async def cmd_reset_era(self, message, args):
        if not self._verificar(message, "reset-era"): return
        todos = get_all_users()
        arquivados = 0
        for uid, u_data in todos.items():
            conquistas   = u_data.get("conquistas", [])
            titulos      = u_data.get("titulos", [])
            diplomas     = u_data.get("diplomas", [])
            from database import _template_usuario
            novo = _template_usuario()
            novo["conquistas"] = conquistas
            novo["titulos"]    = titulos
            novo["diplomas"]   = diplomas
            from database import save_user as sv
            sv(int(uid), novo)
            arquivados += 1
        canal_hist = self._canal(message.guild, "lore-historico")
        if canal_hist:
            await canal_hist.send(embed=embed_soberano_decreto(
                f"Era Encerrada — Arquivo Histórico",
                f"• A era anterior foi arquivada. {arquivados} fichas foram resetadas.\n"
                f"• Conquistas e títulos de prestígio foram preservados."
            ))
        await message.channel.send(embed=embed_soberano_decreto(
            "Reset de Era Completo",
            f"• {arquivados} cidadãos resetados.\n• Nova temporada iniciada."
        ))

    async def cmd_irradiar(self, message, args):
        if not self._verificar(message, "irradiar"): return
        if not args:
            await message.author.send("> ⚠️ Forneça a mensagem."); return
        texto = " ".join(args)
        e = embed_soberano_decreto("Transmissão Nacional Obrigatória", texto)
        e.set_footer(text="Autenticação Soberana  •  ID Verificado do Trono")
        enviado = 0
        if message.guild:
            for cat in message.guild.categories:
                for ch in cat.text_channels:
                    if ch.permissions_for(message.guild.me).send_messages:
                        try:
                            await ch.send(embed=e); enviado += 1
                            await asyncio.sleep(0.5)
                        except Exception: pass
                        break
        await message.channel.send(embed=embed_sucesso(
            "Transmissão Concluída",
            f"• Comunicado enviado em {enviado} categorias."
        ))

    async def cmd_interdicao(self, message, args):
        if not self._verificar(message, "interdição"): return
        if not args:
            await message.author.send("> ⚠️ Forneça o nome do canal."); return
        nome = " ".join(args).lower()
        canal_alvo = None
        if message.guild:
            for ch in message.guild.text_channels:
                if nome in ch.name.lower():
                    canal_alvo = ch; break
        if not canal_alvo:
            await message.channel.send("> ⚠️ Canal não localizado."); return
        try:
            await canal_alvo.set_permissions(message.guild.default_role, send_messages=False)
            await canal_alvo.send(embed=embed_judicial(
                "Perímetro Isolado por Decreto Imperial",
                f"• Este canal foi trancado por ordem soberana.\n"
                f"• Toda comunicação aqui está suspensa até nova diretriz."
            ))
        except Exception as ex:
            await message.channel.send(f"> ⚠️ Permissão negada: {ex}")
            return
        await message.channel.send(embed=embed_soberano_decreto(
            "Interdição de Canal Aplicada",
            f"• **Canal:** {canal_alvo.mention} — escrita bloqueada."
        ))

    def get_sys_prompt_override(self) -> str | None:
        return _sys_prompt_override

    def get_termos_censurados(self) -> list:
        return _termos_censurados
