"""Interações temáticas por canal, cassino, zoológico e concursos públicos."""

import asyncio
import random
import unicodedata
from datetime import UTC, datetime

import discord

from cogs.parentesco import garantir_cargo_grupo
from database import get_user, save_user
from ia_router import ia_rapida
from utils import IMPERADOR_ID, RODAPE_IMPERIAL


ANIMAIS_ZOO = (
    "Leão", "Tigre", "Onça-pintada", "Elefante", "Girafa", "Zebra", "Rinoceronte", "Hipopótamo",
    "Gorila", "Chimpanzé", "Urso-polar", "Panda-gigante", "Lobo", "Raposa", "Capivara", "Tamanduá-bandeira",
    "Arara-azul", "Tucano", "Flamingo", "Pinguim", "Águia", "Crocodilo", "Tartaruga-gigante", "Cobra-real",
)

ACOES_LOCAIS = {
    "cafeteria": [("Café Imperial", "☕", 12), ("Capuccino Arcano", "🥛", 18), ("Chá Real", "🫖", 10), ("Bolo da Casa", "🍰", 22), ("Brunch Tenshi", "🥐", 35)],
    "sorveteria": [("Taça de Chocolate", "🍫", 16), ("Sundae Imperial", "🍨", 24), ("Sorvete de Frutas", "🍓", 15), ("Milk-shake", "🥤", 22), ("Festival de Sabores", "🌈", 30)],
    "laboratorio": [("Analisar amostra", "🔬", 20), ("Criar poção", "⚗️", 45), ("Testar artefato", "🧪", 35), ("Pesquisa arcana", "🔮", 30), ("Experimento secreto", "🧬", 60)],
    "tenshi-enterprise": [("Reunião executiva", "📊", 0), ("Apresentar projeto", "📈", 10), ("Negociar contrato", "🤝", 15), ("Visitar diretoria", "🏢", 0), ("Planejar startup", "💡", 25)],
    "pet-shop": [("Adotar companheiro", "🐾", 80), ("Comprar ração", "🦴", 15), ("Banho e tosa", "🛁", 25), ("Consulta veterinária", "🩺", 35), ("Brinquedo encantado", "🎾", 20)],
    "lojinha": [("Lembrança Tenshi", "🎁", 20), ("Roupa temática", "👕", 45), ("Acessório", "💍", 35), ("Livro raro", "📕", 40), ("Caixa surpresa", "📦", 50)],
    "casamento": [("Consultar cerimônia", "💒", 0), ("Provar trajes", "👗", 25), ("Escolher decoração", "💐", 30), ("Degustar buffet", "🍽️", 20), ("Ensaiar votos", "💌", 0)],
    "cinema": [("Sessão de aventura", "🎬", 18), ("Terror imperial", "👻", 18), ("Romance", "💞", 18), ("Documentário", "📽️", 15), ("Camarote VIP", "🍿", 35)],
    "banco": [("Consultar gerente", "🏦", 0), ("Planejar investimento", "📈", 10), ("Avaliar patrimônio", "💎", 10), ("Solicitar cartão", "💳", 20), ("Visitar cofre", "🔐", 25)],
    "praca": [("Passear", "🚶", 0), ("Ouvir artista", "🎻", 5), ("Alimentar aves", "🕊️", 3), ("Fazer piquenique", "🧺", 15), ("Conhecer pessoas", "🗣️", 0)],
    "lavanderia": [("Lavagem comum", "🧺", 12), ("Lavagem delicada", "🫧", 18), ("Limpeza de armadura", "🛡️", 30), ("Perfume imperial", "🌸", 15), ("Entrega expressa", "⚡", 25)],
    "parque-de-diversoes": [("Montanha-russa", "🎢", 20), ("Roda-gigante", "🎡", 15), ("Casa assombrada", "🏚️", 18), ("Carrinho de bate-bate", "🚗", 12), ("Jogo de prêmio", "🎯", 10)],
    "psicologo": [("Sessão individual", "🛋️", 30), ("Meditação guiada", "🧘", 15), ("Avaliação emocional", "🧠", 20), ("Terapia de grupo", "👥", 12), ("Diário terapêutico", "📔", 8)],
    "departamento-policial": [("Registrar ocorrência", "📋", 0), ("Consultar investigação", "🔎", 0), ("Prestar depoimento", "🗣️", 0), ("Visitar delegacia", "🚓", 0), ("Solicitar proteção", "🛡️", 0)],
    "bar": [("Cerveja Imperial", "🍺", 25), ("Vinho Sombrio", "🍷", 50), ("Coquetel Tenshi", "🍸", 40), ("Petisco", "🥨", 18), ("Mesa reservada", "🎶", 30)],
    "beco": [("Buscar informante", "🕵️", 20), ("Ouvir rumores", "👂", 10), ("Negociar nas sombras", "🕶️", 35), ("Explorar passagem", "🚪", 15), ("Missão clandestina", "🌑", 40)],
}

JOGOS_CASSINO = {
    "roleta": ("Roleta", "🎡", 0.45, 2.0),
    "slots": ("Caça-níqueis", "🎰", 0.16, 5.0),
    "cara_coroa": ("Cara ou Coroa", "🪙", 0.48, 2.0),
    "dados": ("Dados da Fortuna", "🎲", 0.44, 2.1),
    "blackjack": ("Blackjack", "🃏", 0.42, 2.2),
    "baccarat": ("Bacará", "♠️", 0.43, 2.1),
    "crash": ("Crash Imperial", "🚀", 0.32, 3.0),
    "corrida": ("Corrida de Cavalos", "🏇", 0.24, 4.0),
    "loteria": ("Loteria Tenshi", "🎟️", 0.06, 15.0),
    "roda": ("Roda da Fortuna", "☸️", 0.30, 3.2),
}

CONCURSOS = {
    "policial": ("Policial Imperial", "👮"), "investigador": ("Investigador", "🕵️"),
    "delegado": ("Delegado Imperial", "🚓"), "perito": ("Perito Criminal", "🔬"),
    "escrivao": ("Escrivão Policial", "📋"), "promotor": ("Promotor de Justiça", "⚖️"),
    "defensor": ("Defensor Público", "📚"), "juiz": ("Juiz Imperial", "👨‍⚖️"),
    "oficial": ("Oficial de Justiça", "📜"), "penitenciario": ("Agente Penitenciário", "🔐"),
}

QUESTOES = (
    ("Qual princípio exige tratamento igual perante a lei?", ("Legalidade", "Isonomia", "Publicidade", "Eficiência"), 1),
    ("Uma prova obtida por meio ilícito deve ser:", ("Premiada", "Ignorada pela defesa", "Considerada sempre", "Rejeitada"), 3),
    ("Ao preservar uma cena de crime, a primeira medida é:", ("Isolar o local", "Mover objetos", "Publicar fotos", "Liberar curiosos"), 0),
    ("O contraditório garante às partes o direito de:", ("Ocultar provas", "Participar e responder", "Escolher a sentença", "Ignorar intimações"), 1),
    ("A presunção de inocência permanece até:", ("A denúncia", "A prisão", "Decisão definitiva", "O interrogatório"), 2),
    ("A cadeia de custódia serve para:", ("Aumentar penas", "Preservar a integridade da prova", "Substituir testemunhas", "Evitar perícia"), 1),
    ("O agente público deve agir principalmente conforme:", ("Interesse pessoal", "Rumores", "Lei e interesse público", "Ordem informal ilegal"), 2),
)


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(char for char in texto if not unicodedata.combining(char))


def _local_canal(nome: str) -> str | None:
    normalizado = _normalizar(nome).replace("_", "-")
    for local in [*ACOES_LOCAIS, "zoologico", "cassino"]:
        if local in normalizado:
            return local
    return None


def _embed(titulo: str, descricao: str, cor: int = 0x6D28D9) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


async def _criar_topico(interaction: discord.Interaction, tipo: str, titulo: str):
    user = get_user(interaction.user.id)
    if user.get("interacao_ativa"):
        return None, "Você já possui uma interação ativa. Use `tenshi terminar-interacao`."
    canal = interaction.channel
    topico = None
    if isinstance(canal, discord.TextChannel):
        for tipo_thread in (discord.ChannelType.private_thread, discord.ChannelType.public_thread):
            try:
                topico = await canal.create_thread(
                    name=f"{titulo} • {interaction.user.display_name}"[:100], type=tipo_thread,
                    auto_archive_duration=1440, reason="Interação temática do Tenshi Bot",
                )
                try:
                    await topico.add_user(interaction.user)
                except (discord.Forbidden, discord.HTTPException):
                    pass
                break
            except (discord.Forbidden, discord.HTTPException):
                continue
    if topico is None:
        return None, "Não consegui criar o tópico. Verifique as permissões de tópicos do bot."
    user["interacao_ativa"] = {
        "tipo": tipo, "titulo": titulo, "topico_id": str(topico.id),
        "canal_id": str(canal.id), "iniciada_em": datetime.now(UTC).isoformat(),
    }
    save_user(interaction.user.id, user)
    return topico, None


class EncerrarInteracaoView(discord.ui.View):
    def __init__(self, cog: "InteracoesLocais", user_id: int):
        super().__init__(timeout=None)
        self.cog, self.user_id = cog, user_id

    @discord.ui.button(label="Terminar interação", emoji="✅", style=discord.ButtonStyle.success)
    async def terminar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Apenas o participante pode encerrar esta interação.", ephemeral=True)
            return
        await interaction.response.send_message("Interação encerrada. Este tópico será removido em instantes.", ephemeral=True)
        await self.cog.finalizar_interacao(interaction.user, interaction.guild, interaction.channel)


class AcaoLocalSelect(discord.ui.Select):
    def __init__(self, cog: "InteracoesLocais", local: str, autor_id: int):
        self.cog, self.local, self.autor_id = cog, local, autor_id
        if local == "zoologico":
            options = [discord.SelectOption(label=animal, value=animal, emoji="🐾", description="Visitar este habitat") for animal in ANIMAIS_ZOO]
        else:
            options = [
                discord.SelectOption(label=nome, value=str(indice), emoji=emoji, description=f"{preco} moedas" if preco else "Grátis")
                for indice, (nome, emoji, preco) in enumerate(ACOES_LOCAIS[local])
            ]
        super().__init__(placeholder="Escolha a interação", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("Abra seu próprio painel com `tenshi interagir-local`.", ephemeral=True)
            return
        if self.local == "zoologico":
            nome, emoji, preco = f"Visita ao habitat: {self.values[0]}", "🐾", 0
        else:
            nome, emoji, preco = ACOES_LOCAIS[self.local][int(self.values[0])]
        user = get_user(interaction.user.id)
        if user.get("moedas", 0) < preco:
            await interaction.response.send_message(f"Você precisa de **{preco} moedas**.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        topico, erro = await _criar_topico(interaction, self.local, f"{emoji} {nome}")
        if erro:
            await interaction.followup.send(erro, ephemeral=True)
            return
        if preco:
            user = get_user(interaction.user.id)
            user["moedas"] = max(0, user.get("moedas", 0) - preco)
            user.setdefault("inventario", []).append(nome)
            save_user(interaction.user.id, user)
        prompt = (
            f"Crie uma cena curta de RPG em português para {interaction.user.display_name} realizando '{nome}' "
            f"no local '{self.local}'. Seja elegante, divertido e coerente. Máximo 700 caracteres."
        )
        narrativa = await ia_rapida("Você narra interações locais do Império de Tenshi.", prompt, max_tokens=300)
        await topico.send(
            content=interaction.user.mention,
            embed=_embed(f"{emoji} {nome}", f"{narrativa}\n\n**Custo:** {preco} moedas\nUse o botão ou `tenshi terminar-interacao`."),
            view=EncerrarInteracaoView(self.cog, interaction.user.id),
        )
        await interaction.followup.send(f"Interação iniciada em {topico.mention}.", ephemeral=True)


class AcaoLocalView(discord.ui.View):
    def __init__(self, cog: "InteracoesLocais", local: str, autor_id: int):
        super().__init__(timeout=180)
        self.add_item(AcaoLocalSelect(cog, local, autor_id))


def resolver_aposta(jogo: str, valor: int, sorteio: float | None = None) -> tuple[int, bool]:
    _, _, chance, multiplicador = JOGOS_CASSINO[jogo]
    venceu = (random.random() if sorteio is None else sorteio) < chance
    return (int(valor * multiplicador) if venceu else 0), venceu


class ApostaModal(discord.ui.Modal, title="Confirmar aposta"):
    valor = discord.ui.TextInput(label="Valor da aposta", placeholder="Digite a quantidade de moedas", max_length=10)

    def __init__(self, cog: "InteracoesLocais", jogo: str, autor_id: int):
        super().__init__()
        self.cog, self.jogo, self.autor_id = cog, jogo, autor_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("Esta aposta pertence a outro jogador.", ephemeral=True)
            return
        try:
            valor = int(self.valor.value)
        except ValueError:
            await interaction.response.send_message("Informe um valor inteiro.", ephemeral=True)
            return
        user = get_user(interaction.user.id)
        if valor < 10 or valor > 100_000 or user.get("moedas", 0) < valor:
            await interaction.response.send_message("A aposta deve ser de 10 a 100.000 moedas e caber no seu saldo.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        nome, emoji, _, _ = JOGOS_CASSINO[self.jogo]
        topico, erro = await _criar_topico(interaction, "cassino", f"{emoji} {nome}")
        if erro:
            await interaction.followup.send(erro, ephemeral=True)
            return
        premio, venceu = resolver_aposta(self.jogo, valor)
        user = get_user(interaction.user.id)
        user["moedas"] = user.get("moedas", 0) - valor + premio
        user.setdefault("historico_apostas", []).append({
            "jogo": self.jogo, "aposta": valor, "premio": premio, "venceu": venceu,
            "data": datetime.now(UTC).isoformat(),
        })
        save_user(interaction.user.id, user)
        if venceu:
            narrativa = f"As luzes do salão explodem em dourado: **{interaction.user.display_name} venceu {premio} moedas!**"
            cor = 0x1A5C2E
        else:
            narrativa = await ia_rapida(
                "Narre uma derrota de cassino fictícia, sem incentivar recuperar perdas ou apostar mais.",
                f"{interaction.user.display_name} perdeu {valor} moedas jogando {nome}. Máximo 500 caracteres.",
                max_tokens=220,
            )
            cor = 0x7B1F1F
        await topico.send(
            content=interaction.user.mention,
            embed=_embed(
                f"{emoji} {nome} — {'Vitória' if venceu else 'Derrota'}",
                f"{narrativa}\n\n**Aposta:** {valor}\n**Prêmio creditado:** {premio}\n**Saldo:** {user['moedas']}", cor,
            ),
            view=EncerrarInteracaoView(self.cog, interaction.user.id),
        )
        await interaction.followup.send(f"Mesa aberta em {topico.mention}.", ephemeral=True)


class CassinoSelect(discord.ui.Select):
    def __init__(self, cog: "InteracoesLocais", autor_id: int):
        self.cog, self.autor_id = cog, autor_id
        options = [
            discord.SelectOption(label=nome, value=chave, emoji=emoji, description=f"Prêmio até {multiplicador:.1f}x")
            for chave, (nome, emoji, _, multiplicador) in JOGOS_CASSINO.items()
        ]
        super().__init__(placeholder="Escolha o jogo de aposta", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("Abra sua própria mesa com `tenshi cassino`.", ephemeral=True)
            return
        await interaction.response.send_modal(ApostaModal(self.cog, self.values[0], self.autor_id))


class CassinoView(discord.ui.View):
    def __init__(self, cog: "InteracoesLocais", autor_id: int):
        super().__init__(timeout=180)
        self.add_item(CassinoSelect(cog, autor_id))


class QuestaoSelect(discord.ui.Select):
    def __init__(self, prova: "ProvaView"):
        self.prova = prova
        pergunta, respostas, _ = prova.questoes[prova.indice]
        options = [discord.SelectOption(label=resposta[:100], value=str(indice)) for indice, resposta in enumerate(respostas)]
        super().__init__(placeholder=pergunta[:150], options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.prova.autor_id:
            await interaction.response.send_message("Esta prova pertence a outro candidato.", ephemeral=True)
            return
        _, _, correta = self.prova.questoes[self.prova.indice]
        self.prova.acertos += int(self.values[0]) == correta
        self.prova.indice += 1
        if self.prova.indice < len(self.prova.questoes):
            nova = ProvaView(self.prova.cargo_key, self.prova.autor_id, self.prova.questoes, self.prova.indice, self.prova.acertos)
            await interaction.response.edit_message(embed=nova.embed_questao(), view=nova)
            return
        await interaction.response.defer(ephemeral=True)
        nome, emoji = CONCURSOS[self.prova.cargo_key]
        aprovado = self.prova.acertos >= 4
        cargo_aplicado = False
        if aprovado:
            user = get_user(interaction.user.id)
            aprovados = user.setdefault("concursos_aprovados", [])
            if self.prova.cargo_key not in aprovados:
                aprovados.append(self.prova.cargo_key)
            save_user(interaction.user.id, user)
            try:
                cargo = await garantir_cargo_grupo(interaction.guild, nome, emoji, "concurso_publico")
                if cargo not in interaction.user.roles:
                    await interaction.user.add_roles(cargo, reason=f"Aprovação em concurso: {nome}")
                cargo_aplicado = True
            except (discord.Forbidden, discord.HTTPException):
                cargo_aplicado = False
        embed = _embed(
            f"{'✅ Aprovado' if aprovado else '❌ Não aprovado'} — {nome}",
            f"**Nota:** {self.prova.acertos}/5\n**Mínimo:** 4/5\n\n"
            + (
                f"Cargo {emoji} **{nome}** concedido seguindo a estética do servidor."
                if cargo_aplicado else
                "Aprovação salva; a equipe precisa ajustar a hierarquia do bot para aplicar o cargo."
                if aprovado else
                "Revise o conteúdo e tente novamente em outra oportunidade."
            ),
            0x1A5C2E if aprovado else 0x7B1F1F,
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.followup.send("Resultado registrado.", ephemeral=True)


class ProvaView(discord.ui.View):
    def __init__(self, cargo_key: str, autor_id: int, questoes=None, indice: int = 0, acertos: int = 0):
        super().__init__(timeout=600)
        self.cargo_key, self.autor_id = cargo_key, autor_id
        self.questoes = questoes or random.sample(list(QUESTOES), 5)
        self.indice, self.acertos = indice, acertos
        self.add_item(QuestaoSelect(self))

    def embed_questao(self) -> discord.Embed:
        nome, emoji = CONCURSOS[self.cargo_key]
        pergunta, _, _ = self.questoes[self.indice]
        return _embed(
            f"{emoji} Concurso — {nome}",
            f"**Questão {self.indice + 1}/5**\n\n{pergunta}\n\nEscolha a resposta no menu. Nota mínima: **4/5**.",
            0x1D4ED8,
        )


class ConcursoSelect(discord.ui.Select):
    def __init__(self, autor_id: int):
        self.autor_id = autor_id
        options = [discord.SelectOption(label=nome, value=chave, emoji=emoji, description="Iniciar prova para este cargo") for chave, (nome, emoji) in CONCURSOS.items()]
        super().__init__(placeholder="Escolha a carreira pública", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("Abra sua própria inscrição com `tenshi concurso-publico`.", ephemeral=True)
            return
        prova = ProvaView(self.values[0], self.autor_id)
        await interaction.response.edit_message(embed=prova.embed_questao(), view=prova)


class ConcursoView(discord.ui.View):
    def __init__(self, autor_id: int):
        super().__init__(timeout=180)
        self.add_item(ConcursoSelect(autor_id))


class InteracoesLocais:
    def __init__(self, bot):
        self.bot = bot

    async def handle_interagir_local(self, message, args):
        local = _local_canal(message.channel.name)
        if not local:
            await message.channel.send(embed=_embed("🗺️ Local sem painel", "Use este comando dentro de um canal temático compatível."))
            return
        if local == "cassino":
            await self.handle_cassino(message, args)
            return
        titulo = "🐾 Zoológico Imperial" if local == "zoologico" else f"📍 Interações — {local.replace('-', ' ').title()}"
        descricao = (
            f"Escolha um dos **{len(ANIMAIS_ZOO)} animais** para visitar."
            if local == "zoologico" else
            "Escolha uma atividade. Compras são debitadas da carteira e registradas no inventário."
        )
        await message.channel.send(embed=_embed(titulo, descricao), view=AcaoLocalView(self, local, message.author.id))

    async def handle_cassino(self, message, args):
        await message.channel.send(embed=_embed(
            "🎰 Cassino Imperial — Jogos",
            "Escolha uma mesa e depois informe a aposta. Cada partida abre um tópico próprio.\n\n"
            "⚠️ As chances favorecem a casa. Se perder, as moedas são descontadas; não existe recuperação automática.",
            0x8B6914,
        ), view=CassinoView(self, message.author.id))

    async def handle_zoologico(self, message, args):
        await message.channel.send(embed=_embed(
            "🦜 Zoológico Imperial",
            f"Explore **{len(ANIMAIS_ZOO)} espécies** em habitats narrativos assistidos por IA.",
            0x1A5C2E,
        ), view=AcaoLocalView(self, "zoologico", message.author.id))

    async def handle_concurso(self, message, args):
        await message.channel.send(embed=_embed(
            "⚖️ Concursos Jurídicos e Policiais",
            "Escolha a carreira, responda cinco questões e obtenha pelo menos **4/5**. "
            "A aprovação cria e concede o cargo com a estética do servidor.",
            0x1D4ED8,
        ), view=ConcursoView(message.author.id))

    async def handle_terminar_interacao(self, message, args):
        await self.finalizar_interacao(message.author, message.guild, message.channel)

    async def finalizar_interacao(self, member, guild, canal_atual):
        user = get_user(member.id)
        registro = user.get("interacao_ativa")
        if not registro:
            await canal_atual.send(embed=_embed("ℹ️ Sem interação ativa", "Use `tenshi interagir-local`, `tenshi cassino` ou `tenshi zoologico`."))
            return
        topico = guild.get_thread(int(registro["topico_id"])) if guild and registro.get("topico_id") else None
        log = await self._canal_logs(guild)
        if log:
            await log.send(embed=_embed(
                "🗃️ Interação arquivada",
                f"**Participante:** {member.mention}\n**Tipo:** {registro['tipo']}\n**Atividade:** {registro['titulo']}\n"
                f"**Início:** {registro['iniciada_em'][:16].replace('T', ' ')} UTC\n**Encerramento:** {datetime.now(UTC).strftime('%d/%m/%Y %H:%M UTC')}",
                0x374151,
            ))
        user["ultima_interacao"] = registro
        user["interacao_ativa"] = None
        save_user(member.id, user)
        if canal_atual != topico:
            await canal_atual.send(embed=_embed("✅ Interação encerrada", "O tópico será removido e o resumo ficará no arquivo da equipe.", 0x1A5C2E))
        if topico:
            try:
                await topico.send("✅ Interação encerrada. Este tópico será apagado em 5 segundos.")
                await asyncio.sleep(5)
                await topico.delete(reason="Interação concluída e registrada para a equipe")
            except (discord.Forbidden, discord.HTTPException):
                try:
                    await topico.edit(archived=True, locked=True)
                except (discord.Forbidden, discord.HTTPException):
                    pass

    async def _canal_logs(self, guild):
        if not guild:
            return None
        existente = discord.utils.find(lambda canal: "logs-interacoes" in canal.name.casefold(), guild.text_channels)
        if existente:
            return existente
        bot_member = guild.me
        if not bot_member or not bot_member.guild_permissions.manage_channels:
            return None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        for role in guild.roles:
            nome = _normalizar(role.name)
            if any(termo in nome for termo in ("admin", "staff", "moder", "policial", "imperador")):
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, read_message_history=True)
        try:
            return await guild.create_text_channel(
                "🔒・logs-interacoes", overwrites=overwrites,
                reason="Arquivo privado de interações do Tenshi Bot",
            )
        except (discord.Forbidden, discord.HTTPException):
            return None
