import sys
import unittest
from pathlib import Path


BOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

from cogs.interacoes_locais import (  # noqa: E402
    ACOES_LOCAIS,
    ANIMAIS_ZOO,
    CONCURSOS,
    JOGOS_CASSINO,
    QUESTOES,
    AcaoLocalView,
    CassinoView,
    ConcursoView,
    ProvaView,
    _local_canal,
    resolver_aposta,
)


class InteracoesLocaisTest(unittest.IsolatedAsyncioTestCase):
    def test_canais_reconhecem_as_interacoes_corretas(self):
        self.assertEqual(_local_canal("┇9e・🦜・zoológico"), "zoologico")
        self.assertEqual(_local_canal("┇9e・🎰・cassino"), "cassino")
        self.assertEqual(_local_canal("┇9e・☕・cafeteria"), "cafeteria")
        self.assertIsNone(_local_canal("geral"))

    async def test_zoologico_e_comercios_cabem_no_menu(self):
        self.assertEqual(len(ANIMAIS_ZOO), 24)
        self.assertTrue(all(3 <= len(acoes) <= 25 for acoes in ACOES_LOCAIS.values()))
        view = AcaoLocalView(None, "zoologico", 1)
        self.assertEqual(len(view.children[0].options), len(ANIMAIS_ZOO))

    def test_cassino_possui_varios_jogos_e_debita_derrota(self):
        self.assertEqual(len(JOGOS_CASSINO), 10)
        premio, venceu = resolver_aposta("roleta", 100, sorteio=0.99)
        self.assertFalse(venceu)
        self.assertEqual(premio, 0)
        premio, venceu = resolver_aposta("roleta", 100, sorteio=0.01)
        self.assertTrue(venceu)
        self.assertEqual(premio, 200)

    async def test_paineis_cassino_e_concurso_listam_opcoes(self):
        cassino = CassinoView(None, 1)
        self.assertEqual(len(cassino.children[0].options), len(JOGOS_CASSINO))
        concurso = ConcursoView(1)
        self.assertEqual(len(concurso.children[0].options), len(CONCURSOS))
        prova = ProvaView("policial", 1, list(QUESTOES[:5]))
        self.assertEqual(len(prova.children[0].options), 4)
        self.assertIn("Questão 1/5", prova.embed_questao().description)


if __name__ == "__main__":
    unittest.main()
