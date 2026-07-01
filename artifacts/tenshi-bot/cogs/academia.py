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
from academia_curriculo import (
    CURSOS_VISIVEIS,
    competencias_do_curso,
    curriculo_resumo_prompt,
    diploma_payload,
    formatar_cargo_diploma,
    materias_academicas,
    normalizar_materia,
    permissoes_do_curso,
    resumo_curso,
    tem_diploma,
)

ACADEMIA_FILE = "data/academia.json"
CLUBES_FILE   = "data/clubes.json"

# ─── GRADE CURRICULAR ─────────────────────────────────────────────────────────
MATERIAS = materias_academicas()

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


async def _conceder_cargo_diploma(guild, member, materia: str) -> str:
    if guild is None or member is None:
        return "Cargo de diploma nao atribuido: exame feito por DM."
    nome_cargo = formatar_cargo_diploma(materia)
    role = discord.utils.get(guild.roles, name=nome_cargo)
    bot_member = guild.me
    if not bot_member:
        return "Cargo de diploma nao atribuido: bot nao localizado no servidor."
    try:
        if role is None:
            if not bot_member.guild_permissions.manage_roles:
                return f"Cargo `{nome_cargo}` nao criado: falta permissao Gerenciar cargos."
            role = await guild.create_role(
                name=nome_cargo,
                color=discord.Color(0x9E7815),
                mentionable=True,
                reason="Diploma academico emitido pela Tenshi Academy",
            )
        if role.position >= bot_member.top_role.position:
            return f"Cargo `{nome_cargo}` criado/encontrado, mas esta acima do cargo do bot."
        await member.add_roles(role, reason="Diploma academico emitido pela Tenshi Academy")
        return f"Cargo de diploma atribuido: {role.mention}"
    except discord.Forbidden:
        return f"Cargo `{nome_cargo}` nao atribuido: hierarquia/permissao insuficiente."
    except Exception as exc:
        return f"Cargo `{nome_cargo}` nao atribuido: {str(exc)[:80]}"


# ─── VIEW DE PROVA ────────────────────────────────────────────────────────────
class ProvaView(discord.ui.View):
    def __init__(self, questoes: list, user_id: int, materia: str, guild_id: int | None = None):
        super().__init__(timeout=300)
        self.questoes    = questoes
        self.user_id     = user_id
        self.materia     = normalizar_materia(materia)
        self.guild_id    = guild_id
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
            diploma = diploma_payload(self.user_id, self.materia, nota)
            ja_tinha = tem_diploma(u, self.materia)
            if not ja_tinha:
                u.setdefault("diplomas", []).append(diploma)
            u["matricula_ativa"] = None
            ac[uid]["nota_media"] = nota
            _save_academia(ac)
            save_user(self.user_id, u)
            guild = interaction.client.get_guild(self.guild_id) if self.guild_id else interaction.guild
            member = guild.get_member(self.user_id) if guild else None
            cargo_msg = await _conceder_cargo_diploma(guild, member, self.materia)
            curso_nome = diploma.get("nome", self.materia)
            competencias = ", ".join(diploma.get("competencias", [])[:4]) or "competencias registradas"
            e = embed_sucesso(
                "Aprovação — Diploma Emitido",
                f"• **Matéria:** {curso_nome}\n"
                f"• **Nota:** {nota:.1f}/10\n"
                f"• **Hash de autenticidade:** `{diploma['hash']}`\n"
                f"• **Competências:** {competencias}\n"
                f"• **Registro:** {'diploma ja existia; validação renovada' if ja_tinha else 'diploma registrado com êxito'}\n"
                f"• **Cargo:** {cargo_msg}"
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
            lista = "\n".join(
                f"• `{k}` — {MATERIAS[k]['emoji']} **{MATERIAS[k]['nome']}** "
                f"({MATERIAS[k].get('faculdade','Academia')})"
                for k in CURSOS_VISIVEIS
            )
            await message.channel.send(embed=embed_doc(
                "Grade Curricular — Tenshi Academy",
                f"---\nEscolha sua linha de estudo:\n{lista}\n\n"
                f"Use `Tenshi, certificado [materia]` para ver o que o diploma libera.\n"
                f"Uso: `Tenshi, matricular [materia]`", COR_GERAL))
            return
        materia = normalizar_materia(args[0].lower())
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
        materia_ant = normalizar_materia(u["matricula_ativa"])
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
        materia = normalizar_materia(u.get("matricula_ativa"))
        if not materia or materia not in MATERIAS:
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
        materia = normalizar_materia(u.get("matricula_ativa"))
        if not materia or materia not in MATERIAS:
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
            e = embed_doc(f"{m['emoji']} {m['nome']} — Parte 1/3", parte1, COR_GERAL)
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
        materia = normalizar_materia(u.get("matricula_ativa"))
        if not materia or materia not in MATERIAS:
            await message.channel.send("> ⚠️ Você não está matriculado."); return
        m = MATERIAS[materia]
        await message.channel.send(embed=embed_doc("Apostila", "> ⚙️ Processando diretriz. Aguarde.", COR_GERAL))
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
        materia = normalizar_materia(u.get("matricula_ativa"))
        if not materia or materia not in MATERIAS:
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
                f"Use estas competências oficiais: {', '.join(m.get('competencias', []))}. "
                f"Base curricular:\n{curriculo_resumo_prompt()}\n\n"
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
        view = ProvaView(questoes, message.author.id, materia, message.guild.id if message.guild else None)
        await message.author.send(embed=e, view=view)
        await message.channel.send(embed=embed_admin_doc("Exame Iniciado", f"• Prova enviada via mensagem privada para {message.author.mention}."))

    # ─── HISTÓRICO ESCOLAR ────────────────────────────────────────────────────

    async def handle_historico_escolar(self, message, args):
        alvo = message.mentions[0] if message.mentions else message.author
        u = get_user(alvo.id)
        diplomas = u.get("diplomas", [])
        matricula = normalizar_materia(u.get("matricula_ativa"))
        matricula_nome = MATERIAS.get(matricula, {}).get("nome", "Nenhuma") if matricula else "Nenhuma"
        e = embed_doc(
            f"Histórico Escolar — {alvo.display_name}",
            f"• **Matrícula ativa:** {matricula_nome}\n"
            f"• **Diplomas emitidos:** {len(diplomas)}", COR_GERAL
        )
        for d in diplomas[:8]:
            materia = normalizar_materia(d.get("materia"))
            curso = MATERIAS.get(materia, {})
            competencias = d.get("competencias") or competencias_do_curso(materia)
            competencias_txt = ", ".join(competencias[:3]) if competencias else "competencias em registro antigo"
            e.add_field(
                name=f"{curso.get('emoji','🎓')} {curso.get('nome', d.get('materia', '?'))}",
                value=(
                    f"• Nota: {d.get('nota',0):.1f}/10\n"
                    f"• Faculdade: {curso.get('faculdade', d.get('faculdade','Academia Imperial'))}\n"
                    f"• Competências: {competencias_txt}\n"
                    f"• Cargo: `{d.get('cargo_diploma') or formatar_cargo_diploma(materia)}`\n"
                    f"• `{d.get('hash','?')}`"
                ),
                inline=True
            )
        await message.channel.send(embed=e)

    async def handle_grade_academia(self, message, args):
        por_faculdade: dict[str, list[str]] = {}
        for materia in CURSOS_VISIVEIS:
            curso = MATERIAS[materia]
            por_faculdade.setdefault(curso.get("faculdade", "Academia Imperial Tenshi"), []).append(
                f"{curso['emoji']} `{materia}` — {curso['nome']}"
            )
        e = embed_doc(
            "Academia Imperial Tenshi — Faculdades",
            "Grade baseada no PDF oficial de currículo. Cada curso libera diploma, competências e empregos próprios.",
            COR_GERAL,
        )
        for faculdade, cursos in por_faculdade.items():
            e.add_field(name=faculdade, value="\n".join(cursos), inline=False)
        await message.channel.send(embed=e)

    async def handle_certificado_info(self, message, args):
        if not args:
            await self.handle_grade_academia(message, args)
            return
        materia = normalizar_materia(args[0].lower())
        if materia not in MATERIAS:
            await message.channel.send("> ⚠️ Curso não encontrado. Use `Tenshi, grade-academia`.")
            return
        curso = MATERIAS[materia]
        competencias = "\n".join(f"• {c}" for c in competencias_do_curso(materia))
        permissoes = "\n".join(f"• {p}" for p in permissoes_do_curso(materia))
        empregos = ", ".join(curso.get("empregos", [])) or "empregos em configuracao"
        possui = tem_diploma(get_user(message.author.id), materia)
        e = embed_doc(
            f"{curso['emoji']} Certificado — {curso['nome']}",
            (
                f"• **Faculdade:** {curso.get('faculdade')}\n"
                f"• **Cargo de diploma:** `{formatar_cargo_diploma(materia)}`\n"
                f"• **Status do aluno:** {'Apto/certificado' if possui else 'Ainda nao certificado'}\n\n"
                f"**Competências ensinadas**\n{competencias}\n\n"
                f"**O certificado permite no RPG**\n{permissoes}\n\n"
                f"**Empregos relacionados:** {empregos}\n\n"
                f"Use `Tenshi, matricular {materia}` para estudar este curso."
            ),
            COR_GERAL,
        )
        await message.channel.send(embed=e)

    async def handle_aptidao_academica(self, message, args):
        if not args:
            await message.channel.send(embed=embed_doc(
                "Aptidão Acadêmica",
                "Use `Tenshi, aptidao-academica [curso]` para receber perguntas, ou "
                "`Tenshi, aptidao-academica [curso] [suas respostas]` para a IA julgar sua aptidão.",
                COR_GERAL,
            ))
            return
        materia = normalizar_materia(args[0].lower())
        if materia not in MATERIAS:
            await message.channel.send("> ⚠️ Curso não encontrado. Use `Tenshi, grade-academia`.")
            return
        curso = MATERIAS[materia]
        resposta = " ".join(args[1:]).strip()
        await message.channel.send(embed=embed_doc("Banca Acadêmica", "> ⚙️ Avaliação em preparação.", COR_GERAL))
        sistema = (
            "Voce e a Banca da Academia Imperial Tenshi. Use o curriculo oficial, o Codigo Imperial e os PDFs em memoria. "
            "Avalie com rigor, mas sem humilhar o aluno. Responda em PT-BR."
        )
        if not resposta:
            prompt = (
                f"Crie 4 perguntas de aptidao para o curso {curso['nome']}.\n"
                f"Resumo do curso:\n{resumo_curso(materia)}\n\n"
                "As perguntas devem testar vocacao, entendimento pratico, postura etica e aplicacao no RPG. "
                "Finalize dizendo para o aluno responder com `Tenshi, aptidao-academica "
                f"{materia} [respostas]`."
            )
        else:
            u = get_user(message.author.id)
            diplomas = ", ".join(str(d.get("materia")) for d in u.get("diplomas", [])) or "nenhum"
            prompt = (
                f"Curso avaliado: {curso['nome']}\n"
                f"Resumo do curso:\n{resumo_curso(materia)}\n"
                f"Diplomas atuais do aluno: {diplomas}\n"
                f"Resposta do aluno: {resposta}\n\n"
                "Julgue a aptidao em quatro campos: conhecimento, postura, risco administrativo e recomendacao. "
                "Diga APTO, APTO COM RESSALVAS ou NAO APTO, e recomende proximas aulas ou empregos adequados."
            )
        try:
            texto = await ia_analitica(sistema, prompt, max_tokens=900)
            if texto.startswith("⚠"):
                raise RuntimeError(texto)
        except Exception:
            if resposta and len(resposta) >= 180:
                texto = (
                    f"**APTO COM RESSALVAS** para {curso['nome']}.\n"
                    "A resposta tem desenvolvimento suficiente para avaliação inicial. Recomenda-se concluir as aulas, "
                    "fazer o exame oficial e revisar as competências do certificado antes de assumir cargo sensível."
                )
            elif resposta:
                texto = (
                    f"**NAO APTO AINDA** para {curso['nome']}.\n"
                    "A resposta ficou curta para medir aptidão. Desenvolva exemplos práticos, postura ética e aplicação no RPG."
                )
            else:
                comps = ", ".join(competencias_do_curso(materia)[:4])
                texto = (
                    f"1. Como voce aplicaria {comps} em uma crise do Imperio?\n"
                    "2. Qual erro etico voce evitaria ao exercer esse certificado?\n"
                    "3. Que cargo ou emprego combina com sua vocacao e por que?\n"
                    "4. Como voce provaria obediencia ao Codigo Imperial durante essa funcao?"
                )
        await message.channel.send(embed=embed_doc(f"Aptidão — {curso['nome']}", texto[:3900], COR_GERAL))

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
        alvo = message.mentions[0]; materia = normalizar_materia(args[1].lower())
        if materia not in MATERIAS: await message.channel.send("> ⚠️ Matéria inválida."); return
        u = get_user(alvo.id)
        diploma = diploma_payload(alvo.id, materia, 10.0, origem="decreto")
        diploma["hash"] = f"DIP-FORCE-{alvo.id}-{datetime.utcnow().strftime('%Y%m%d')}"
        if not tem_diploma(u, materia):
            u.setdefault("diplomas", []).append(diploma)
        u["matricula_ativa"] = None
        save_user(alvo.id, u)
        cargo_msg = await _conceder_cargo_diploma(message.guild, alvo, materia)
        await message.channel.send(embed=embed_soberano_decreto(
            "Aprovação Forçada — Decreto Imperial",
            f"• **Aluno:** {alvo.mention}\n• **Matéria:** {MATERIAS[materia]['nome']}\n"
            f"• **Hash:** `{diploma['hash']}`\n"
            f"• **Cargo:** {cargo_msg}"
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
