import random

import discord

from ia_router import ia_narrativa, ia_relatorio
from memoria_documental import buscar_memoria, listar_documentos, obter_documento, prompt_memoria_documental
from utils import RODAPE_IMPERIAL, SEP


COR_DOURADO = 0x9E7815
COR_IMPERIAL = 0x2C3E50
COR_NEUTRO = 0x3D3D3D
COR_SUCESSO = 0x1A5C2E


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


class BibliotecaImperial:
    def __init__(self, bot):
        self.bot = bot

    async def handle_biblioteca(self, message, args):
        docs = listar_documentos()
        embed = _embed(
            "Biblioteca Imperial Tenshi",
            f"*Todos os PDFs oficiais contabilizados na memoria do bot.*\n{SEP}",
            COR_DOURADO,
        )
        for doc in docs:
            embed.add_field(
                name=f"{doc['id']} - {doc['titulo']}",
                value=f"`{doc['arquivo']}`\n**{doc['paginas']} paginas**\n{doc['resumo'][:420]}",
                inline=False,
            )
        await message.channel.send(embed=embed)

    async def handle_documento(self, message, args):
        if not args:
            await message.channel.send(embed=_embed(
                "Documento Imperial",
                "Use: `Tenshi, documento codigo|rito|bases|academia`",
                COR_NEUTRO,
            ))
            return
        key, doc = obter_documento(" ".join(args))
        if not doc:
            await message.channel.send(embed=_embed("Documento Nao Encontrado", "Use `Tenshi, biblioteca-imperial` para ver a lista.", COR_NEUTRO))
            return
        embed = _embed(
            doc["titulo"],
            f"**Arquivo:** `{doc['arquivo']}`\n**Paginas:** {doc['paginas']}\n\n{doc['resumo']}",
            COR_DOURADO,
        )
        for idx, topico in enumerate(doc["topicos"][:5], start=1):
            embed.add_field(name=f"Topico {idx}", value=topico[:900], inline=False)
        await message.channel.send(embed=embed)

    async def handle_memoria(self, message, args):
        consulta = " ".join(args).strip()
        resultados = buscar_memoria(consulta)
        if not resultados:
            await message.channel.send(embed=_embed("Memoria Imperial", "Nada encontrado nessa consulta.", COR_NEUTRO))
            return
        embed = _embed(
            "Consulta a Memoria Imperial",
            f"**Busca:** `{consulta or 'todos os documentos'}`\n{SEP}",
            COR_DOURADO,
        )
        for key, doc, topicos in resultados[:4]:
            embed.add_field(
                name=f"{doc['titulo']}",
                value=("\n".join(f"- {t}" for t in topicos[:3]))[:1000],
                inline=False,
            )
        await message.channel.send(embed=embed)

    async def handle_aula_imperial(self, message, args):
        tema = " ".join(args).strip() or "formacao imperial"
        contexto = prompt_memoria_documental()
        resposta = await ia_relatorio(
            "Voce e professor da Academia Imperial Tenshi. Crie uma aula curta, clara e elegante para RPG.",
            f"{contexto}\n\nTema da aula: {tema}\nFormato: objetivo, 4 topicos, 1 exercicio pratico e 1 frase final.",
            max_tokens=900,
        )
        await message.channel.send(embed=_embed("Aula Imperial", resposta[:3900], COR_IMPERIAL))

    async def handle_missao_historica(self, message, args):
        tema = " ".join(args).strip() or random.choice(["Primeira Alianca", "Brasao Tenshi", "Guardioes", "Academia Imperial"])
        resposta = await ia_narrativa(
            "Voce e narrador oficial do RPG Tenshi. Gere missao historica usando apenas a memoria documental resumida.",
            f"{prompt_memoria_documental()}\n\nCrie uma missao de RPG de texto para {message.author.display_name}. Tema: {tema}. "
            "Inclua objetivo, cena inicial, conflito, 3 escolhas e recompensa narrativa.",
            max_tokens=1000,
        )
        await message.channel.send(embed=_embed("Missao Historica", resposta[:3900], COR_DOURADO))

    async def handle_juramento_tenshi(self, message, args):
        tema = " ".join(args).strip() or "honra e lealdade"
        resposta = await ia_narrativa(
            "Voce escreve juramentos cerimoniais do Imperio Tenshi, solenes e curtos.",
            f"{prompt_memoria_documental()}\n\nCrie um juramento Tenshi sobre: {tema}. Maximo 8 linhas. Sem explicar.",
            max_tokens=450,
        )
        await message.channel.send(embed=_embed("Juramento Tenshi", f"*{resposta[:1800]}*", COR_DOURADO))

    async def handle_protocolo_imperial(self, message, args):
        tema = " ".join(args).strip()
        if not tema:
            await message.channel.send(embed=_embed(
                "Protocolo Imperial",
                "Use: `Tenshi, protocolo-imperial [situação]`",
                COR_NEUTRO,
            ))
            return
        resposta = await ia_relatorio(
            "Voce e Chancelaria Imperial. Crie protocolo pratico de RPG baseado na memoria documental Tenshi.",
            f"{prompt_memoria_documental()}\n\nSituacao: {tema}\nFormato: finalidade, autoridade, passos, limite legal, registro final.",
            max_tokens=1000,
        )
        await message.channel.send(embed=_embed("Protocolo Imperial", resposta[:3900], COR_IMPERIAL))

    async def handle_quiz_imperial(self, message, args):
        perguntas = [
            ("O Sangue Angelical representa poder sobrenatural?", "Nao. Representa heranca moral, disciplina, coragem e dever."),
            ("Quais ideias o Brasao Tenshi transmite?", "Protecao, honra, justica, continuidade e esperanca."),
            ("Por que existe Conselho Imperial?", "Para orientar o soberano e impedir decisoes movidas por ira, orgulho ou ambicao."),
            ("O que a Academia Imperial forma?", "Liderancas, herdeiros, administradores, diplomatas, guardioes, tecnologos e especialistas da Casa."),
            ("No casamento, a historia deve ser lida inteira?", "Nao. Apenas um resumo essencial deve ser lembrado no rito."),
        ]
        pergunta, resposta = random.choice(perguntas)
        embed = _embed(
            "Quiz Imperial",
            f"**Pergunta:** {pergunta}\n\n||**Resposta:** {resposta}||",
            COR_SUCESSO,
        )
        await message.channel.send(embed=embed)
