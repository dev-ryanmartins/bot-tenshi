"""
Módulo de Gestão Acadêmica Avançada — Módulo 22
Tenshi Academy: matérias, aulas, provas, diplomas, clubes
"""
import discord
import asyncio
from datetime import datetime, timedelta
from database import get_user, save_user, get_all_users, _load, _save
from utils import IMPERADOR_ID
from design import (embed_doc, embed_soberano_decreto, embed_judicial,
                    embed_sucesso, embed_perigo_doc, embed_admin_doc,
                    fmt_moedas, COR_GERAL, COR_DECRETO, COR_JUDICIAL,
                    COR_ADMIN, COR_SUCESSO, COR_PERIGO, rodape_padrao)
from ia_router import ia_analitica, ia_rapida

ACADEMIA_FILE = "data/academia.json"
CLUBES_FILE   = "data/clubes.json"

# ─── GRADE CURRICULAR ─────────────────────────────────────────────────────────
MATERIAS = {
    "tatica_militar": {
        "nome": "Tática Militar", "emoji": "⚔️",
        "cargo_destino": "Recruta da Guarda",
        "prompt": (
            "Você é o Professor Imperial de Tática Militar. Ministra aulas formais e sérias "
            "sobre estratégias de defesa de perímetro, cadeia de comando imperial, formações de batalha "
            "e protocolos de resposta a invasões. Tom austero, preciso e militarista. PT-BR formal."
        ),
    },
    "historia_lore": {
        "nome": "História e Lore de Tenshi", "emoji": "📜",
        "cargo_destino": "Escriba Real",
        "prompt": (
            "Você é a Professora de História Imperial. Ensina a cronologia das Eras de Tenshi, "
            "a soberania do Imperador Alloy, os tratados entre facções e os eventos fundadores do Império. "
            "Tom erudito, reverencial ao Imperador. PT-BR formal."
        ),
    },
    "ciencias_esotéricas": {
        "nome": "Ciências Esotéricas", "emoji": "🔮",
        "cargo_destino": "Alquimista da Corte",
        "prompt": (
            "Você é o Mestre Alquimista da Tenshi Academy. Leciona sobre propriedades de runas, "
            "manipulação de éter, alquimia de reagentes e síntese de poções. Tom arcano e preciso. PT-BR formal."
        ),
    },
    "direito_imperial": {
        "nome": "Direito Imperial", "emoji": "⚖️",
        "cargo_destino": "Magistrado",
        "prompt": (
            "Você é o Professor Catedrático de Direito Imperial. Ensina os artigos do Código de Conduta, "
            "hermenêutica jurídica, processos judiciais e jurisprudência do Trono. Tom formal, técnico e imperioso. PT-BR."
        ),
    },
    "logística_engenharia": {
        "nome": "Logística e Engenharia", "emoji": "🔧",
        "cargo_destino": "Engenheiro Imperial",
        "prompt": (
            "Você é o Engenheiro-Chefe da Tenshi Enterprise. Ministra aulas sobre manutenção de "
            "DVRs, switches de rede, malha ferroviária rúnica e infraestrutura urbana. PT-BR técnico-formal."
        ),
    },
}

# ─── CLUBES ───────────────────────────────────────────────────────────────────
CLUBES = {
    "ocultismo":    {"nome": "Clube de Ocultismo",    "emoji": "🔮", "cofre": 0, "membros": []},
    "programacao":  {"nome": "Clube de Programação",  "emoji": "💻", "cofre": 0, "membros": []},
    "ciencias":     {"nome": "Clube de Ciências",     "emoji": "⚗️",  "cofre": 0, "membros": []},
    "artes":        {"nome": "Clube de Artes",         "emoji": "🎨", "cofre": 0, "membros": []},
}

NOTA_MINIMA = 7.0
COOLDOWN_RECUPERACAO_H = 24
TAXA_TRANCAMENTO = 50
TAXA_SEGUNDA_VIA  = 30


def _load_academia() -> dict:
    return _load(ACADEMIA_FILE)

def _save_academia(data: dict):
    _save(ACADEMIA_FILE, data)

def _load_clubes() -> dict:
    d = _load(CLUBES_FILE)
    if not d:
        d = {k: dict(v) for k, v in CLUBES.items()}
        _save(CLUBES_FILE, d)
    return d

def _save_clubes(data: dict):
    _save(CLUBES_FILE, data)


# ─── VIEW DE PROVA ────────────────────────────────────────────────────────────
class ProvaView(discord.ui.View):
    def __init__(self, questoes: list, user_id: int, materia: str):
        super().__init__(timeout=300)
        self.questoes    = questoes
        self.user_id     = user_id
        self.materia     = materia
        self.atual       = 0
        self.acertos     = 0
        self.respondidas = set()
        self._add_botoes()

    def _add_botoes(self):
        self.clear_items()
        if self.atual >= len(self.questoes):
            return
        q = self.questoes[self.atual]
        for i, alt in enumerate(q["alternativas"]):
            btn = discord.ui.Button(
                label=f"{'ABC'[i]}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"alt_{i}"
            )
            btn.callback = self._make_cb(i, q["correta"])
            self.add_item(btn)

    def _make_cb(self, idx: int, correta: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("Prova restrita.", ephemeral=True); return
            if self.atual in self.respondidas:
                await interaction.response.send_message("Questão já respondida.", ephemeral=True); return
            self.respondidas.add(self.atual)
            if idx == correta: self.acertos += 1
            self.atual += 1
            if self.atual >= len(self.questoes):
                self.clear_items()
                nota = (self.acertos / len(self.questoes)) * 10
                aprovado = nota >= NOTA_MINIMA
                await self._finalizar(interaction, nota, aprovado)
            else:
                self._add_botoes()
                q = self.questoes[self.atual]
                e = embed_doc(
                    f"Exame — {self.materia} | Questão {self.atual+1}/{len(self.questoes)}",
                    f"---\n**{q['enunciado']}**\n\n"
                    + "\n".join(f"• **{'ABC'[i]}** — {a}" for i, a in enumerate(q["alternativas"])),
                    COR_GERAL
                )
                await interaction.response.edit_message(embed=e, view=self)
        return callback

    async def _finalizar(self, interaction, nota: float, aprovado: bool):
        ac = _load_academia()
        uid = str(self.user_id)
        ac.setdefault(uid, {})
        tentativa = {"nota": nota, "data": datetime.utcnow().isoformat(), "aprovado": aprovado}
        ac[uid].setdefault("historico_provas", []).append(tentativa)
        if aprovado:
            u = get_user(self.user_id)
            diploma = {"materia": self.materia, "nota": nota, "data": datetime.utcnow().isoformat(),
                       "hash": f"DIP-{self.user_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"}
            u.setdefault("diplomas", []).append(diploma)
            ac[uid]["nota_media"] = nota
            _save_academia(ac)
            save_user(self.user_id, u)
            e = embed_sucesso(
                "Aprovação — Diploma Emitido",
                f"• **Matéria:** {self.materia}\n"
                f"• **Nota:** {nota:.1f}/10\n"
                f"• **Hash de autenticidade:** `{diploma['hash']}`\n"
                f"• Diploma registrado com êxito."
            )
        else:
            ac[uid]["cooldown_recuperacao"] = (datetime.utcnow() + timedelta(hours=COOLDOWN_RECUPERACAO_H)).isoformat()
            _save_academia(ac)
            e = embed_perigo_doc(
                "Reprovação — Período de Recuperação",
                f"• **Matéria:** {self.materia}\n"
                f"• **Nota:** {nota:.1f}/10 (mínimo: {NOTA_MINIMA})\n"
                f"• Próxima tentativa disponível em {COOLDOWN_RECUPERACAO_H} horas."
            )
        await interaction.response.edit_message(embed=e, view=self)


class Academia:
    def __init__(self, bot):
        self.bot = bot

    # ─── MATRÍCULA ────────────────────────────────────────────────────────────

    async def handle_matricular(self, message, args):
        if not args:
            lista = "\n".join(f"• `{k}` — {v['nome']} {v['emoji']}" for k, v in MATERIAS.items())
            await message.channel.send(embed=embed_doc(
                "Grade Curricular — Tenshi Academy",
                f"---\nEscolha sua linha de estudo:\n{lista}\n\n"
                f"Uso: `Tenshi, matricular [materia]`", COR_GERAL))
            return
        materia = args[0].lower()
        if materia not in MATERIAS:
            await message.channel.send(
                f"> ⚠️ **Operação Recusada.** Matéria não encontrada. Use `Tenshi, matricular` para ver a grade."); return
        u = get_user(message.author.id)
        if u.get("matricula_ativa") == materia:
            await message.channel.send("> Você já está matriculado nesta matéria."); return
        ac = _load_academia()
        uid = str(message.author.id)
        ac.setdefault(uid, {})["matricula"] = materia
        ac[uid]["presencas"] = 0
        _save_academia(ac)
        u["matricula_ativa"] = materia
        save_user(message.author.id, u)
        m = MATERIAS[materia]
        await message.channel.send(embed=embed_sucesso(
            f"Matrícula Confirmada — {m['emoji']} {m['nome']}",
            f"• **Aluno:** {message.author.mention}\n"
            f"• **Matéria:** {m['nome']}\n"
            f"• **Cargo de destino:** {m['cargo_destino']}\n"
            f"• Registre presença em 3 aulas para liberar o exame."
        ))

    async def handle_trancar_matricula(self, message, args):
        u = get_user(message.author.id)
        if not u.get("matricula_ativa"):
            await message.channel.send("> Nenhuma matrícula ativa."); return
        if u.get("moedas", 0) < TAXA_TRANCAMENTO:
            await message.channel.send(f"> ⚠️ Taxa de trancamento: {fmt_moedas(TAXA_TRANCAMENTO)}."); return
        u["moedas"] -= TAXA_TRANCAMENTO
        materia_ant = u["matricula_ativa"]
        u["matricula_ativa"] = None
        save_user(message.author.id, u)
        ac = _load_academia(); ac.setdefault(str(message.author.id), {})["matricula"] = None; _save_academia(ac)
        await message.channel.send(embed=embed_admin_doc(
            "Trancamento de Matrícula",
            f"• **Matéria trancada:** {materia_ant}\n"
            f"• **Taxa descontada:** {fmt_moedas(TAXA_TRANCAMENTO)}\n"
            f"• Progresso da matéria zerado."
        ))

    # ─── PRESENÇA ─────────────────────────────────────────────────────────────

    async def handle_presenca(self, message, args):
        u = get_user(message.author.id)
        materia = u.get("matricula_ativa")
        if not materia:
            await message.channel.send("> ⚠️ Você não está matriculado em nenhuma matéria."); return
        canal_nome = getattr(message.channel, "name", "")
        if "sala" not in canal_nome.lower() and "aula" not in canal_nome.lower():
            await message.channel.send("> ⚠️ **Operação Recusada.** Presença deve ser registrada dentro de uma sala de aula."); return
        ac = _load_academia(); uid = str(message.author.id); ac.setdefault(uid, {})
        ultima = ac[uid].get("ultima_presenca")
        if ultima:
            diff = (datetime.utcnow() - datetime.fromisoformat(ultima)).total_seconds() / 3600
            if diff < 4:
                await message.channel.send(f"> ⏱️ **Protocolo de Recuperação.** Próxima presença em {4-diff:.0f}h."); return
        ac[uid]["presencas"] = ac[uid].get("presencas", 0) + 1
        ac[uid]["ultima_presenca"] = datetime.utcnow().isoformat()
        _save_academia(ac)
        presencas = ac[uid]["presencas"]
        await message.channel.send(embed=embed_doc(
            "Presença Registrada",
            f"• **Matéria:** {MATERIAS[materia]['nome']}\n"
            f"• **Presenças acumuladas:** {presencas}/3\n"
            f"{'• Exame liberado! Use `Tenshi, prestar-exame`.' if presencas >= 3 else f'• Aguarde: {3-presencas} presenças restantes.'}",
            COR_SUCESSO if presencas >= 3 else COR_GERAL
        ))

    # ─── AULA DA IA ───────────────────────────────────────────────────────────

    async def handle_iniciar_aula(self, message, args):
        u = get_user(message.author.id)
        materia = u.get("matricula_ativa")
        if not materia:
            await message.channel.send("> ⚠️ Você não está matriculado."); return
        m = MATERIAS[materia]
        await message.channel.send(embed=embed_doc(
            f"{m['emoji']} Aula Iniciada — {m['nome']}",
            f"---\n> ⚙️ Processando diretriz. Aguarde.",
            COR_GERAL
        ))
        try:
            from cogs.loremaster import _gerar, DIRETRIZ_ORIGINALIDADE
            from cogs.eras import _PROMPT_PTBR
            u_data = get_user(message.author.id)
            sys = f"{m['prompt']}\n\n{_PROMPT_PTBR}\n\n{DIRETRIZ_ORIGINALIDADE}"
            parte1 = await _gerar("Gere a Parte 1 de 3 da aula de hoje: introdução ao tema principal.", sys, u_data, 0.82)
            await asyncio.sleep(1)
            e = embed_doc(f"{m['emoji']} {m['nome']} — Parte 1/3", part=None,
                          descricao=parte1, cor=COR_GERAL)
            e.description = f"---\n{parte1}"
            await message.channel.send(embed=e)
            await asyncio.sleep(60)
            parte2 = await _gerar("Gere a Parte 2 de 3 da aula: aprofundamento prático e exemplos históricos.", sys, u_data, 0.82)
            e2 = discord.Embed(description=f"---\n{parte2}", color=COR_GERAL)
            e2.set_author(name=f"{m['nome']} — Parte 2/3")
            e2.set_footer(text=rodape_padrao("Tenshi Academy"))
            await message.channel.send(embed=e2)
            await asyncio.sleep(60)
            parte3 = await _gerar("Gere a Parte 3 de 3 da aula: revisão, conclusões e tarefa para o próximo encontro.", sys, u_data, 0.82)
            e3 = discord.Embed(description=f"---\n{parte3}", color=COR_GERAL)
            e3.set_author(name=f"{m['nome']} — Parte 3/3 (Conclusão)")
            e3.set_footer(text=rodape_padrao("Tenshi Academy"))
            await message.channel.send(embed=e3)
        except Exception as ex:
            await message.channel.send(f"> ⚠️ Aula interrompida: {str(ex)[:80]}")

    async def handle_ler_apostila(self, message, args):
        u = get_user(message.author.id)
        materia = u.get("matricula_ativa")
        if not materia:
            await message.channel.send("> ⚠️ Você não está matriculado."); return
        m = MATERIAS[materia]
        await message.channel.send(embed_doc("Apostila", "> ⚙️ Processando diretriz. Aguarde.", COR_GERAL))
        try:
            from cogs.loremaster import _gerar
            from cogs.eras import _PROMPT_PTBR
            sumario = await _gerar(
                f"Gere um sumário executivo compacto e técnico de 5-7 pontos principais sobre "
                f"a disciplina {m['nome']} para estudo individual. Formato de bullet points com rótulos em negrito.",
                f"{m['prompt']}\n\n{_PROMPT_PTBR}", temperatura=0.80
            )
            e = embed_doc(f"📚 Apostila — {m['nome']}", sumario, COR_GERAL)
            await message.channel.send(embed=e)
        except Exception as ex:
            await message.channel.send(f"> ⚠️ Erro ao carregar apostila: {str(ex)[:80]}")

    # ─── EXAME ────────────────────────────────────────────────────────────────

    async def handle_prestar_exame(self, message, args):
        u = get_user(message.author.id)
        materia = u.get("matricula_ativa")
        if not materia:
            await message.channel.send("> ⚠️ Você não está matriculado."); return
        ac = _load_academia(); uid = str(message.author.id); ac.setdefault(uid, {})
        if ac[uid].get("presencas", 0) < 3:
            await message.channel.send(
                f"> ⚠️ **Operação Recusada.** São necessárias 3 presenças. Atual: {ac[uid].get('presencas',0)}."); return
        cooldown = ac[uid].get("cooldown_recuperacao")
        if cooldown and datetime.utcnow() < datetime.fromisoformat(cooldown):
            diff = datetime.fromisoformat(cooldown) - datetime.utcnow()
            h = int(diff.total_seconds() // 3600)
            await message.channel.send(f"> ⏱️ **Protocolo de Recuperação.** Aguarde {h}h."); return
        await message.author.send("> ⚙️ Processando diretriz. Aguarde — sua prova está sendo formulada.")
        try:
            from cogs.loremaster import _gerar
            from cogs.eras import _PROMPT_PTBR
            m = MATERIAS[materia]
            raw = await _gerar(
                f"Formule 5 questões de múltipla escolha (3 alternativas cada) sobre {m['nome']}. "
                f"Retorne no formato JSON puro: "
                f'[{{"enunciado":"...", "alternativas":["A","B","C"], "correta":0}}, ...]',
                f"{m['prompt']}\n\n{_PROMPT_PTBR}", temperatura=0.75
            )
            import json, re
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if not match: raise ValueError("JSON não encontrado")
            questoes = json.loads(match.group())[:5]
        except Exception:
            questoes = [
                {"enunciado": f"Qual é o fundamento central de {MATERIAS[materia]['nome']}?",
                 "alternativas": ["Disciplina e hierarquia", "Caos e improviso", "Isolamento total"],
                 "correta": 0}
            ] * 3

        e = embed_doc(
            f"📝 Exame Oficial — {MATERIAS[materia]['nome']} | Questão 1/{len(questoes)}",
            f"---\n**{questoes[0]['enunciado']}**\n\n"
            + "\n".join(f"• **{'ABC'[i]}** — {a}" for i, a in enumerate(questoes[0]["alternativas"])),
            COR_GERAL
        )
        view = ProvaView(questoes, message.author.id, materia)
        await message.author.send(embed=e, view=view)
        await message.channel.send(embed=embed_admin_doc("Exame Iniciado", f"• Prova enviada via mensagem privada para {message.author.mention}."))

    # ─── HISTÓRICO ESCOLAR ────────────────────────────────────────────────────

    async def handle_historico_escolar(self, message, args):
        alvo = message.mentions[0] if message.mentions else message.author
        u = get_user(alvo.id)
        diplomas = u.get("diplomas", [])
        e = embed_doc(
            f"Histórico Escolar — {alvo.display_name}",
            f"• **Matrícula ativa:** {u.get('matricula_ativa','Nenhuma')}\n"
            f"• **Diplomas emitidos:** {len(diplomas)}", COR_GERAL
        )
        for d in diplomas[:8]:
            e.add_field(
                name=d.get("materia", "?"),
                value=f"• Nota: {d.get('nota',0):.1f}/10\n• `{d.get('hash','?')}`",
                inline=True
            )
        await message.channel.send(embed=e)

    async def handle_segunda_via_diploma(self, message, args):
        u = get_user(message.author.id)
        if u.get("moedas", 0) < TAXA_SEGUNDA_VIA:
            await message.channel.send(f"> ⚠️ Taxa: {fmt_moedas(TAXA_SEGUNDA_VIA)}."); return
        u["moedas"] -= TAXA_SEGUNDA_VIA; save_user(message.author.id, u)
        await message.channel.send(embed=embed_admin_doc(
            "Segunda Via de Diploma",
            f"• Taxa: {fmt_moedas(TAXA_SEGUNDA_VIA)} descontada.\n"
            f"• Use `Tenshi, historico-escolar` para verificar seus diplomas."
        ))

    # ─── CLUBES ───────────────────────────────────────────────────────────────

    async def handle_entrar_clube(self, message, args):
        if not args:
            clubes = _load_clubes()
            lista = "\n".join(f"• `{k}` — {v['nome']} {v['emoji']} (membros: {len(v.get('membros',[]))})" for k, v in clubes.items())
            await message.channel.send(embed=embed_doc("Clubes da Tenshi Academy", f"---\n{lista}", COR_GERAL))
            return
        clube_id = args[0].lower()
        clubes = _load_clubes()
        if clube_id not in clubes:
            await message.channel.send("> ⚠️ Clube não encontrado."); return
        uid = str(message.author.id)
        if uid in clubes[clube_id].get("membros", []):
            await message.channel.send("> Você já é membro deste clube."); return
        clubes[clube_id].setdefault("membros", []).append(uid)
        _save_clubes(clubes)
        u = get_user(message.author.id); u.setdefault("clubes", []).append(clube_id); save_user(message.author.id, u)
        c = clubes[clube_id]
        await message.channel.send(embed=embed_sucesso(
            f"Filiação ao {c['nome']} {c['emoji']}",
            f"• **Membro:** {message.author.mention}\n• Bem-vindo ao {c['nome']}."
        ))

    async def handle_cofre_clube(self, message, args):
        clubes = _load_clubes()
        e = embed_doc("Balanço dos Cofres de Clubes", "", COR_ADMIN)
        for kid, c in clubes.items():
            e.add_field(name=f"{c['emoji']} {c['nome']}", value=fmt_moedas(c.get("cofre", 0)), inline=True)
        await message.channel.send(embed=e)

    # ─── COMANDOS DO SOBERANO ────────────────────────────────────────────────

    async def cmd_interditar_escola(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        if message.guild:
            for cat in message.guild.categories:
                if "academy" in cat.name.lower() or "escola" in cat.name.lower():
                    try: await cat.set_permissions(message.guild.default_role, send_messages=False)
                    except: pass
        await message.channel.send(embed=embed_soberano_decreto(
            "Academia Interditada",
            "• Todas as salas de aula e clubes trancados por decreto imperial."
        ))

    async def cmd_aprovacao_forcada(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        if not message.mentions or len(args) < 2:
            await message.channel.send("> ⚠️ Uso: `Tenshi, aprovação-forçada @user [materia]`"); return
        alvo = message.mentions[0]; materia = args[1].lower()
        if materia not in MATERIAS: await message.channel.send("> ⚠️ Matéria inválida."); return
        u = get_user(alvo.id)
        diploma = {"materia": materia, "nota": 10.0,
                   "data": datetime.utcnow().isoformat(),
                   "hash": f"DIP-FORCE-{alvo.id}-{datetime.utcnow().strftime('%Y%m%d')}"}
        u.setdefault("diplomas", []).append(diploma)
        save_user(alvo.id, u)
        await message.channel.send(embed=embed_soberano_decreto(
            "Aprovação Forçada — Decreto Imperial",
            f"• **Aluno:** {alvo.mention}\n• **Matéria:** {MATERIAS[materia]['nome']}\n"
            f"• **Hash:** `{diploma['hash']}`"
        ))

    async def cmd_estatizar_cofre_clube(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        if not args: await message.channel.send("> ⚠️ Especifique o clube."); return
        clube_id = args[0].lower(); clubes = _load_clubes()
        if clube_id not in clubes: await message.channel.send("> ⚠️ Clube não encontrado."); return
        valor = clubes[clube_id].get("cofre", 0)
        clubes[clube_id]["cofre"] = 0; _save_clubes(clubes)
        imp = get_user(IMPERADOR_ID); imp["moedas"] = imp.get("moedas",0) + valor; save_user(IMPERADOR_ID, imp)
        await message.channel.send(embed=embed_soberano_decreto(
            "Estatização de Cofre de Clube",
            f"• **Clube:** {clubes[clube_id]['nome']}\n• **Valor transferido:** {fmt_moedas(valor)}\n• Tesouro Real atualizado."
        ))

    async def cmd_zerar_historico_academico(self, message, args):
        u_data = get_user(message.author.id)
        ok = message.author.id == IMPERADOR_ID or u_data.get("co_soberano")
        if not ok: return
        if not message.mentions: await message.channel.send("> ⚠️ Mencione o alvo."); return
        alvo = message.mentions[0]
        u = get_user(alvo.id); u["diplomas"] = []; u["matricula_ativa"] = None; save_user(alvo.id, u)
        ac = _load_academia(); ac[str(alvo.id)] = {}; _save_academia(ac)
        await message.channel.send(embed=embed_judicial(
            "Histórico Acadêmico Zerado",
            f"• **Aluno:** {alvo.mention}\n• Todos os registros acadêmicos removidos."
        ))

    # ─── helpers ──────────────────────────────────────────────────────────────
    def embed_doc(self, titulo, descricao, cor=COR_GERAL):
        return embed_doc(titulo, descricao, cor)
