import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT_DIR = ROOT / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

from cogs.ajuda import AJUDA_CATEGORIAS, PainelAjudaView, embed_categoria, embed_inicio  # noqa: E402
from utils import AJUDA_TEXTO  # noqa: E402


class AjudaInterativaTest(unittest.IsolatedAsyncioTestCase):
    async def test_painel_cabe_nos_limites_do_discord(self):
        self.assertGreater(len(AJUDA_CATEGORIAS), 10)
        self.assertLessEqual(len(AJUDA_CATEGORIAS), 25)
        self.assertLessEqual(len(embed_inicio()), 6000)
        for indice, (_, corpo) in enumerate(AJUDA_CATEGORIAS):
            self.assertLessEqual(len(corpo), 4096)
            self.assertLessEqual(len(embed_categoria(indice)), 6000)
        view = PainelAjudaView(1)
        seletor = next(item for item in view.children if hasattr(item, "options"))
        self.assertEqual(len(seletor.options), len(AJUDA_CATEGORIAS))
        self.assertEqual(len(view.children), 5)

    def test_todas_as_rotas_canonicas_aparecem_na_ajuda(self):
        codigo = (BOT_DIR / "main.py").read_text(encoding="utf-8")
        blocos = re.findall(r"(?:if|elif)\s+cmd\s+in\s+\(([^\r\n]+)\)", codigo)
        rotas = []
        for bloco in blocos:
            encontrado = re.search(r'["\']([^"\']+)["\']', bloco)
            if encontrado:
                rotas.append(encontrado.group(1))
        ausentes = [
            rota for rota in rotas
            if not re.search(rf"`{re.escape(rota)}(?:`|\s|\[|/)", AJUDA_TEXTO, re.IGNORECASE)
        ]
        self.assertEqual(ausentes, [], f"Comandos ausentes da ajuda: {ausentes}")
        self.assertEqual(len(rotas), len(set(rotas)), "Há rotas canônicas duplicadas no roteador")


if __name__ == "__main__":
    unittest.main()
