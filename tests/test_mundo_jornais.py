import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


BOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

from cogs import crime  # noqa: E402
from cogs.cotidiano import CotidianoCog  # noqa: E402
from cogs.mundo import (  # noqa: E402
    CONTINENTES,
    FALLBACK_PAISES,
    ContinentesView,
    PaisesView,
)


class MundoJornaisTest(unittest.IsolatedAsyncioTestCase):
    async def test_atlas_tem_continentes_e_paginacao_de_25_paises(self):
        paises = [
            {"nome": f"País {i:03}", "capital": f"Capital {i}", "continente": "Europe", "codigo": "PT"}
            for i in range(61)
        ]
        continentes = ContinentesView(1, paises)
        self.assertEqual(len(continentes.children[0].options), 1)
        self.assertEqual(continentes.children[0].options[0].value, "Europe")

        pagina = PaisesView(1, "Europe", paises, pagina=1)
        seletor = next(item for item in pagina.children if hasattr(item, "options"))
        self.assertEqual(len(seletor.options), 25)
        self.assertEqual(seletor.options[0].label, "País 025")

    def test_catalogo_emergencial_cobre_continentes_habitados(self):
        presentes = {pais["continente"] for pais in FALLBACK_PAISES}
        self.assertTrue({"Africa", "Asia", "Europe", "North America", "South America", "Oceania"}.issubset(presentes))
        self.assertTrue(presentes.issubset(CONTINENTES))

    def test_jornal_policial_combina_ocorrencias_e_informes(self):
        registros = {
            "10": [{
                "id": "abc123", "tipo": "assalto_beco", "descricao": "Assalto contra outro jogador",
                "data_hora": "2030-01-01T12:00:00",
            }]
        }
        guild = SimpleNamespace(get_member=lambda uid: SimpleNamespace(display_name="Suspeito") if uid == 10 else None)
        with patch.object(crime, "_load", return_value=registros):
            embed = crime.Crime(None)._embed_jornal_policial(guild)
        self.assertGreaterEqual(len(embed.fields), 3)
        self.assertTrue(any("Assalto Beco" in field.name for field in embed.fields))
        self.assertIn("fictícia", embed.footer.text)

    def test_jornal_cotidiano_publica_varias_noticias(self):
        cotidiano = CotidianoCog(None)
        cotidiano.registrar_mensagem_geral("praca", "Uma celebração ocorreu na praça.")
        embed = cotidiano._build_jornal_cotidiano()
        self.assertGreaterEqual(len(embed.fields), 4)
        self.assertTrue(any("Crônica RPG" in field.name for field in embed.fields))


if __name__ == "__main__":
    unittest.main()
