import sys
import unittest
from pathlib import Path


BOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

from cogs.censura import RevelarConteudoView, detectar_e_camuflar  # noqa: E402


class CensuraMultilingueTest(unittest.IsolatedAsyncioTestCase):
    def test_camufla_portugues_ingles_e_espanhol(self):
        texto, termos, idiomas = detectar_e_camuflar("porra, this is bullshit y mierda")
        self.assertNotIn("porra", texto.lower())
        self.assertNotIn("bullshit", texto.lower())
        self.assertNotIn("mierda", texto.lower())
        self.assertTrue({"pt", "en", "es"}.issubset(idiomas))
        self.assertEqual(len(termos), 3)

    def test_detecta_unicode_e_tentativa_de_disfarce(self):
        texto, termos, idiomas = detectar_e_camuflar("P0RR4 씨발 блять")
        self.assertTrue(termos)
        self.assertTrue({"pt", "ko", "ru"}.issubset(idiomas))
        self.assertNotIn("P0RR4", texto)

    def test_nao_camufla_conversa_normal(self):
        texto_original = "Essa missão foi difícil, mas o grupo trabalhou muito bem."
        texto, termos, idiomas = detectar_e_camuflar(texto_original)
        self.assertEqual(texto, texto_original)
        self.assertEqual(termos, [])
        self.assertEqual(idiomas, set())

    async def test_view_oferece_revelacao_opcional(self):
        view = RevelarConteudoView("conteúdo original")
        self.assertEqual(len(view.children), 1)
        self.assertIn("Ver conteúdo original", view.children[0].label)


if __name__ == "__main__":
    unittest.main()
