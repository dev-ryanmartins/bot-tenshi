import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


BOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

import database  # noqa: E402
from database import LOJA_ITEMS  # noqa: E402
from cogs.economia import verificar_requisitos  # noqa: E402
from cogs.soberano import STATUS_LIMITES, StatusPainelView  # noqa: E402
from cogs.vizinhanca import NOMES_CASAS, TOTAL_CASAS, _nome_canal_novo, get_dados_casa  # noqa: E402


class FakeRole:
    def __init__(self, name):
        self.name = name


class FakeMember:
    def __init__(self, roles=()):
        self.roles = [FakeRole(name) for name in roles]


class MercadoHabitacaoStatusTest(unittest.IsolatedAsyncioTestCase):
    def test_mercado_tem_itens_avancados_com_requisitos(self):
        self.assertGreaterEqual(len(LOJA_ITEMS), 30)
        restritos = [item for item in LOJA_ITEMS if item.get("nivel_minimo")]
        self.assertGreaterEqual(len(restritos), 15)
        ids = [item["id"] for item in LOJA_ITEMS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_requisitos_impedem_e_liberam_compra(self):
        item = next(item for item in LOJA_ITEMS if item["id"] == "medalha_guardiao")
        user = {"nivel": 20, "poder": 500, "atributos": {"mana": 200}, "inventario": []}
        permitido, _ = verificar_requisitos(item, user, FakeMember())
        self.assertFalse(permitido)
        permitido, _ = verificar_requisitos(item, user, FakeMember(["Guarda Imperial"]))
        self.assertTrue(permitido)

    def test_condominio_tem_50_casas_unicas_e_mais_caras(self):
        self.assertEqual(TOTAL_CASAS, 50)
        self.assertEqual(len(NOMES_CASAS), 50)
        self.assertEqual(len(set(NOMES_CASAS)), 50)
        precos = [get_dados_casa(numero)["preco"] for numero in range(1, 51)]
        self.assertEqual(precos, sorted(precos))
        self.assertGreaterEqual(precos[0], 1500)

    def test_banco_migra_condominio_para_50_sem_apagar_dados(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            arquivo = str(Path(temp_dir) / "vizinhanca.json")
            with patch.object(database, "VIZINHANCA_FILE", arquivo):
                dados = database.get_vizinhanca()
                dados["1"]["id_dono"] = "123"
                database.save_vizinhanca(dados)
                migrados = database.get_vizinhanca()
        self.assertEqual(len(migrados), 50)
        self.assertEqual(migrados["1"]["id_dono"], "123")

    def test_novo_canal_preserva_prefixo_visual_existente(self):
        guild = SimpleNamespace(text_channels=[SimpleNamespace(name="┋9Ɛ・🏡・casa-18")])
        self.assertEqual(_nome_canal_novo(guild, 19), "┋9Ɛ・🏡・casa-19")

    async def test_painel_status_expoe_atributos_com_limites(self):
        self.assertEqual(set(STATUS_LIMITES), {
            "vida", "mana", "forca", "agilidade", "poder", "xp", "nivel", "fadiga", "moedas", "conta_banco",
            "inteligencia", "sabedoria", "carisma", "resistencia", "destreza", "sorte", "honra", "reputacao",
            "lideranca", "magia", "defesa", "velocidade",
        })
        view = StatusPainelView(FakeMember(), 1)
        self.assertEqual(len(view.children), 5)
        self.assertEqual(len(view.children[1].options), len(STATUS_LIMITES))


if __name__ == "__main__":
    unittest.main()
