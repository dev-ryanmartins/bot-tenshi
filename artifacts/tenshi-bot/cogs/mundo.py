"""Atlas mundial interativo e viagens em tópicos do Discord."""

import json
import os
from datetime import UTC, datetime, timedelta

import aiohttp
import discord

from database import get_user, save_user
from ia_router import ia_narrativa
from utils import RODAPE_IMPERIAL


CACHE_FILE = "data/paises_mundo.json"
REST_COUNTRIES_URL = "https://restcountries.com/v3.1/all?fields=name,capital,continents,cca2"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
CONTINENTES = {
    "Africa": ("África", "🌍"),
    "Asia": ("Ásia", "🌏"),
    "Europe": ("Europa", "🌍"),
    "North America": ("América do Norte", "🌎"),
    "South America": ("América do Sul", "🌎"),
    "Oceania": ("Oceania", "🌏"),
    "Antarctica": ("Antártida", "🧊"),
}

# Mantém o painel operacional mesmo quando a fonte mundial estiver temporariamente fora do ar.
FALLBACK_PAISES = [
    {"nome": "Brasil", "capital": "Brasília", "continente": "South America", "codigo": "BR"},
    {"nome": "Argentina", "capital": "Buenos Aires", "continente": "South America", "codigo": "AR"},
    {"nome": "Estados Unidos", "capital": "Washington, D.C.", "continente": "North America", "codigo": "US"},
    {"nome": "Canadá", "capital": "Ottawa", "continente": "North America", "codigo": "CA"},
    {"nome": "México", "capital": "Cidade do México", "continente": "North America", "codigo": "MX"},
    {"nome": "Portugal", "capital": "Lisboa", "continente": "Europe", "codigo": "PT"},
    {"nome": "Espanha", "capital": "Madri", "continente": "Europe", "codigo": "ES"},
    {"nome": "França", "capital": "Paris", "continente": "Europe", "codigo": "FR"},
    {"nome": "Itália", "capital": "Roma", "continente": "Europe", "codigo": "IT"},
    {"nome": "Japão", "capital": "Tóquio", "continente": "Asia", "codigo": "JP"},
    {"nome": "China", "capital": "Pequim", "continente": "Asia", "codigo": "CN"},
    {"nome": "Índia", "capital": "Nova Délhi", "continente": "Asia", "codigo": "IN"},
    {"nome": "Egito", "capital": "Cairo", "continente": "Africa", "codigo": "EG"},
    {"nome": "África do Sul", "capital": "Pretória", "continente": "Africa", "codigo": "ZA"},
    {"nome": "Austrália", "capital": "Canberra", "continente": "Oceania", "codigo": "AU"},
    {"nome": "Nova Zelândia", "capital": "Wellington", "continente": "Oceania", "codigo": "NZ"},
]


def _carregar_cache() -> list[dict]:
    try:
        if not os.path.exists(CACHE_FILE):
            return []
        with open(CACHE_FILE, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        atualizado = datetime.fromisoformat(dados.get("atualizado_em", "2000-01-01T00:00:00+00:00"))
        if datetime.now(UTC) - atualizado > timedelta(days=30):
            return []
        return dados.get("paises", [])
    except (OSError, ValueError, json.JSONDecodeError):
        return []


def _salvar_cache(paises: list[dict]) -> None:
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as arquivo:
        json.dump({"atualizado_em": datetime.now(UTC).isoformat(), "paises": paises}, arquivo, ensure_ascii=False, indent=2)


async def carregar_paises() -> list[dict]:
    cache = _carregar_cache()
    if cache:
        return cache
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(REST_COUNTRIES_URL) as resposta:
                resposta.raise_for_status()
                dados = await resposta.json()
        paises = []
        for item in dados:
            nome = item.get("name", {}).get("common")
            continente = (item.get("continents") or [None])[0]
            if not nome or continente not in CONTINENTES:
                continue
            paises.append({
                "nome": nome,
                "capital": (item.get("capital") or ["Capital não informada"])[0],
                "continente": continente,
                "codigo": item.get("cca2", ""),
            })
        paises.sort(key=lambda pais: pais["nome"].casefold())
        if len(paises) >= 150:
            _salvar_cache(paises)
            return paises
    except (aiohttp.ClientError, TimeoutError, ValueError):
        pass
    return list(FALLBACK_PAISES)


def _embed(titulo: str, descricao: str, cor: int = 0x2563EB) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


async def _guia_cidade(pais: dict, cidade: str) -> str:
    sistema = (
        "Você é um guia de viagens factual e conciso. Responda em português do Brasil, sem inventar endereços, preços "
        "ou hotéis específicos caso não tenha certeza. Organize em: pontos turísticos, regiões/hospedagem, gastronomia, "
        "transporte, segurança e roteiro de um dia. Máximo 1800 caracteres."
    )
    resposta = await ia_narrativa(sistema, f"Cidade: {cidade}\nPaís: {pais['nome']}\nCapital do país: {pais['capital']}", max_tokens=700)
    if resposta.startswith("⚠️"):
        return (
            f"Explore o centro histórico e os principais espaços culturais de **{cidade}**. Consulte avaliações recentes "
            "antes de reservar hospedagem, confirme horários oficiais das atrações e utilize transporte autorizado. "
            f"A capital de **{pais['nome']}** é **{pais['capital']}**."
        )
    return resposta[:3500]


async def _validar_cidade(pais: dict, cidade: str) -> bool | None:
    """Confirma a cidade mundialmente; None mantém o sistema disponível se o geocodificador cair."""
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        headers = {"User-Agent": "TenshiBot/2.0 (Discord RPG travel atlas)"}
        params = {
            "q": f"{cidade}, {pais['nome']}", "countrycodes": pais["codigo"].casefold(),
            "format": "jsonv2", "limit": 1, "addressdetails": 1,
        }
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(NOMINATIM_URL, params=params) as resposta:
                resposta.raise_for_status()
                return bool(await resposta.json())
    except (aiohttp.ClientError, TimeoutError, ValueError):
        return None


async def _iniciar_viagem(interaction: discord.Interaction, pais: dict, cidade: str) -> None:
    user = get_user(interaction.user.id)
    if user.get("viagem_mundo"):
        await interaction.response.send_message("Você já está viajando. Use `tenshi terminar-viagem` primeiro.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    cidade_valida = await _validar_cidade(pais, cidade)
    if cidade_valida is False:
        await interaction.followup.send(
            f"Não encontrei **{cidade}** em **{pais['nome']}**. Confira a escrita e tente novamente.",
            ephemeral=True,
        )
        return
    guild = interaction.guild
    canal = discord.utils.find(lambda item: "viajando-pelo-mundo" in item.name.casefold(), guild.text_channels) if guild else None
    canal = canal or interaction.channel
    topico = None
    if isinstance(canal, discord.TextChannel):
        try:
            topico = await canal.create_thread(
                name=f"✈️ {cidade} • {interaction.user.display_name}"[:100],
                type=discord.ChannelType.public_thread,
                auto_archive_duration=1440,
                reason="Viagem mundial iniciada pelo Tenshi Bot",
            )
        except (discord.Forbidden, discord.HTTPException):
            topico = None
    destino = topico or canal
    guia = await _guia_cidade(pais, cidade)
    continente_nome, continente_emoji = CONTINENTES[pais["continente"]]
    embed = _embed(
        f"✈️ Guia de {cidade}, {pais['nome']}",
        f"{continente_emoji} **Continente:** {continente_nome}\n"
        f"🏳️ **País:** {pais['nome']} (`{pais['codigo']}`)\n"
        f"🏛️ **Capital:** {pais['capital']}\n"
        f"📍 **Cidade escolhida:** {cidade}\n\n{guia}\n\n"
        "Quando a jornada acabar, use `tenshi terminar-viagem`.",
    )
    if destino:
        await destino.send(content=interaction.user.mention, embed=embed)
    user["local_antes_viagem"] = user.get("local_atual", "cidadela")
    user["local_atual"] = f"{cidade}, {pais['nome']}"
    user["viagem_mundo"] = {
        "continente": pais["continente"], "pais": pais["nome"], "codigo": pais["codigo"],
        "cidade": cidade, "capital": pais["capital"], "topico_id": str(topico.id) if topico else None,
        "iniciada_em": datetime.now(UTC).isoformat(),
    }
    save_user(interaction.user.id, user)
    local = topico.mention if topico else getattr(canal, "mention", "canal atual")
    await interaction.followup.send(f"Viagem iniciada para **{cidade}, {pais['nome']}**. Guia: {local}", ephemeral=True)


class CidadeModal(discord.ui.Modal, title="Escolher cidade de destino"):
    def __init__(self, pais: dict):
        super().__init__()
        self.pais = pais
        self.cidade = discord.ui.TextInput(
            label=f"Cidade em {pais['nome']}"[:45],
            placeholder=f"Ex.: {pais['capital']}",
            default=pais["capital"] if pais["capital"] != "Capital não informada" else None,
            max_length=80,
        )
        self.add_item(self.cidade)

    async def on_submit(self, interaction: discord.Interaction):
        await _iniciar_viagem(interaction, self.pais, self.cidade.value.strip())


class PaisSelect(discord.ui.Select):
    def __init__(self, view: "PaisesView"):
        self.paises_view = view
        inicio = view.pagina * 25
        pagina = view.paises[inicio:inicio + 25]
        options = [
            discord.SelectOption(label=pais["nome"][:100], value=str(inicio + indice), description=f"Capital: {pais['capital']}"[:100])
            for indice, pais in enumerate(pagina)
        ]
        super().__init__(placeholder="Escolha o país", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        pais = self.paises_view.paises[int(self.values[0])]
        await interaction.response.send_modal(CidadeModal(pais))


class PaisesView(discord.ui.View):
    def __init__(self, autor_id: int, continente: str, paises: list[dict], pagina: int = 0):
        super().__init__(timeout=300)
        self.autor_id, self.continente, self.paises, self.pagina = autor_id, continente, paises, pagina
        self.add_item(PaisSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.autor_id:
            return True
        await interaction.response.send_message("Abra seu próprio atlas com `tenshi mundo`.", ephemeral=True)
        return False

    def _embed_pagina(self) -> discord.Embed:
        nome, emoji = CONTINENTES[self.continente]
        total = max(1, (len(self.paises) + 24) // 25)
        return _embed(
            f"{emoji} Países — {nome}",
            f"Escolha um país e depois pesquise qualquer cidade.\nPágina **{self.pagina + 1}/{total}** • {len(self.paises)} países disponíveis.",
        )

    async def _mudar(self, interaction: discord.Interaction, deslocamento: int):
        total = max(1, (len(self.paises) + 24) // 25)
        self.pagina = (self.pagina + deslocamento) % total
        nova = PaisesView(self.autor_id, self.continente, self.paises, self.pagina)
        await interaction.response.edit_message(embed=nova._embed_pagina(), view=nova)

    @discord.ui.button(label="Anterior", emoji="◀️", style=discord.ButtonStyle.secondary, row=1)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._mudar(interaction, -1)

    @discord.ui.button(label="Próxima", emoji="▶️", style=discord.ButtonStyle.secondary, row=1)
    async def proxima(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._mudar(interaction, 1)


class ContinenteSelect(discord.ui.Select):
    def __init__(self, autor_id: int, paises: list[dict]):
        self.autor_id, self.paises = autor_id, paises
        disponiveis = {pais["continente"] for pais in paises}
        options = [
            discord.SelectOption(label=nome, value=chave, emoji=emoji)
            for chave, (nome, emoji) in CONTINENTES.items() if chave in disponiveis
        ]
        super().__init__(placeholder="Escolha o continente", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("Abra seu próprio atlas com `tenshi mundo`.", ephemeral=True)
            return
        continente = self.values[0]
        filtrados = [pais for pais in self.paises if pais["continente"] == continente]
        view = PaisesView(self.autor_id, continente, filtrados)
        await interaction.response.edit_message(embed=view._embed_pagina(), view=view)


class ContinentesView(discord.ui.View):
    def __init__(self, autor_id: int, paises: list[dict]):
        super().__init__(timeout=300)
        self.add_item(ContinenteSelect(autor_id, paises))


class Mundo:
    def __init__(self, bot):
        self.bot = bot

    async def handle_mundo(self, message, args):
        paises = await carregar_paises()
        fonte = "catálogo mundial" if len(paises) >= 150 else "catálogo de emergência"
        await message.channel.send(
            embed=_embed(
                "🌐 Viajando pelo Mundo",
                f"Escolha o continente, navegue pelas páginas de países e informe a cidade desejada.\n\n"
                f"**Países carregados:** {len(paises)} ({fonte})\n"
                "O guia cria um tópico com atrações, hospedagem, gastronomia, transporte e segurança.",
            ),
            view=ContinentesView(message.author.id, paises),
        )

    async def handle_terminar_viagem(self, message, args):
        user = get_user(message.author.id)
        viagem = user.get("viagem_mundo")
        if not viagem:
            await message.channel.send(embed=_embed("🧳 Nenhuma viagem ativa", "Use `tenshi mundo` para escolher um destino.", 0x6B7280))
            return
        topico = None
        if message.guild and viagem.get("topico_id"):
            topico = message.guild.get_thread(int(viagem["topico_id"]))
        encerramento = _embed(
            f"🛬 Viagem encerrada — {viagem['cidade']}",
            f"{message.author.mention} concluiu a jornada por **{viagem['cidade']}, {viagem['pais']}**.\n"
            "O diário foi arquivado e o viajante retornou ao seu local anterior.",
            0x1A5C2E,
        )
        if topico:
            try:
                await topico.send(embed=encerramento)
                await topico.edit(archived=True, locked=False, reason="Viagem mundial concluída")
            except (discord.Forbidden, discord.HTTPException):
                pass
        user["local_atual"] = user.pop("local_antes_viagem", "cidadela")
        user["ultima_viagem_mundo"] = viagem
        user["viagem_mundo"] = None
        save_user(message.author.id, user)
        await message.channel.send(embed=encerramento)

    async def handle_viagem_atual(self, message, args):
        viagem = get_user(message.author.id).get("viagem_mundo")
        if not viagem:
            await message.channel.send(embed=_embed("📍 Localização", "Você não está em uma viagem mundial."))
            return
        await message.channel.send(embed=_embed(
            "📍 Viagem atual",
            f"**Continente:** {CONTINENTES[viagem['continente']][0]}\n**País:** {viagem['pais']}\n"
            f"**Cidade:** {viagem['cidade']}\n**Iniciada em:** {viagem['iniciada_em'][:16].replace('T', ' ')} UTC",
        ))
