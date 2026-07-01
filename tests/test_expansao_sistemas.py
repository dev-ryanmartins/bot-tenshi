import sys
import unittest
from pathlib import Path

import discord


BOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

from academia_curriculo import CURRICULO_ACADEMIA  # noqa: E402
from cogs.empregos import (  # noqa: E402
    EMPREGOS_ILEGAIS,
    EMPREGOS_LEGAIS,
    SelectEmpregoView,
    _sincronizar_profissao,
)
from cogs.npcs import NPCS, _detectar_npc  # noqa: E402
from confirmacoes import (  # noqa: E402
    limpar_confirmacoes,
    processar_resposta,
    registrar_confirmacao,
)
from utils import EMBED_PAGE_DESCRIPTION_LIMIT, EmbedContinuacaoView, split_embed  # noqa: E402


class FakeAuthor:
    def __init__(self, user_id):
        self.id = user_id


class FakeChannel:
    def __init__(self):
        self.messages = []

    async def send(self, content=None, **kwargs):
        self.messages.append(content or kwargs)


class FakeMessage:
    def __init__(self, user_id):
        self.author = FakeAuthor(user_id)
        self.channel = FakeChannel()


class FakeRole:
    def __init__(self, name):
        self.name = name


class FakeGuild:
    def __init__(self, roles):
        self.roles = roles

    async def create_role(self, name, **kwargs):
        role = FakeRole(name)
        self.roles.append(role)
        return role


class FakeMember:
    def __init__(self, roles):
        self.roles = roles

    async def add_roles(self, *roles, **kwargs):
        self.roles.extend(role for role in roles if role not in self.roles)

    async def remove_roles(self, *roles, **kwargs):
        self.roles = [role for role in self.roles if role not in roles]


class ExpansaoSistemasTest(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        limpar_confirmacoes()

    async def test_menu_de_empregos_paginaa_todo_catalogo(self):
        user = {
            "nivel": 99,
            "diplomas": [{"materia": materia} for materia in CURRICULO_ACADEMIA],
        }
        view = SelectEmpregoView(10, "legal", user)
        self.assertGreater(view.total_paginas, 1)
        self.assertLessEqual(len(view.children[0].options), 25)
        self.assertEqual(view.total_paginas, (len(EMPREGOS_LEGAIS) + 24) // 25)

    async def test_profissao_e_gravada_no_perfil_sem_guild(self):
        user = {"ficha": {}}
        mensagem = await _sincronizar_profissao(None, None, EMPREGOS_LEGAIS[0], user)
        self.assertEqual(user["emprego_id"], EMPREGOS_LEGAIS[0]["id"])
        self.assertEqual(user["ficha"]["profissao"], EMPREGOS_LEGAIS[0]["nome"])
        self.assertIn("perfil", mensagem)

    async def test_profissao_cria_cargo_e_remove_o_anterior(self):
        antigo = FakeRole("Profissão • Cargo Antigo")
        guild = FakeGuild([antigo])
        member = FakeMember([antigo])
        user = {"ficha": {}}
        await _sincronizar_profissao(guild, member, EMPREGOS_LEGAIS[0], user)
        nomes = {role.name for role in member.roles}
        self.assertNotIn("Profissão • Cargo Antigo", nomes)
        self.assertIn(user["cargo_trabalho"], nomes)

    async def test_confirmacao_por_prefixo_executa_callback(self):
        executado = []

        async def confirmar(message):
            executado.append(message.author.id)

        registrar_confirmacao(42, "ação de teste", confirmar)
        await processar_resposta(FakeMessage(42), confirmar=True)
        self.assertEqual(executado, [42])

    async def test_embeds_longos_viram_continuacao(self):
        embed = discord.Embed(title="Documento", description="parágrafo longo " * 300)
        paginas = split_embed(embed)
        self.assertGreater(len(paginas), 1)
        self.assertTrue(all(len(p.description or "") <= EMBED_PAGE_DESCRIPTION_LIMIT for p in paginas))
        view = EmbedContinuacaoView(paginas)
        self.assertEqual(view.children[-1].label, "Mostrar continuação")

    async def test_catalogos_expandidos_e_coerentes(self):
        ids = {emprego["id"] for emprego in EMPREGOS_LEGAIS + EMPREGOS_ILEGAIS}
        self.assertGreaterEqual(len(NPCS), 18)
        self.assertGreaterEqual(len(CURRICULO_ACADEMIA), 21)
        self.assertGreaterEqual(len(EMPREGOS_LEGAIS), 79)
        for curso in CURRICULO_ACADEMIA.values():
            self.assertTrue(set(curso.get("empregos", [])).issubset(ids))
        self.assertEqual(_detectar_npc("capela-cerimonia")["nome"], "Padre Celestino")


if __name__ == "__main__":
    unittest.main()
