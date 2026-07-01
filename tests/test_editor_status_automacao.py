import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


BOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

from cogs import perfil_config, soberano  # noqa: E402
from cogs.automacao_servidor import CANAIS_SISTEMA, _nome_canal  # noqa: E402
from cogs.soberano import (  # noqa: E402
    CAMPO_TEXTO_PERFIL,
    COLECOES_PERFIL,
    REGISTROS_LIMITES,
    StatusPainelView,
    StatusValorModal,
    _gravar_caminho,
    _ler_caminho,
)


class FakeResponse:
    def __init__(self):
        self.envios = []

    async def send_message(self, *args, **kwargs):
        self.envios.append((args, kwargs))


class EditorStatusAutomacaoTest(unittest.IsolatedAsyncioTestCase):
    def test_caminhos_aninhados_podem_ser_editados_e_limpos(self):
        user = {}
        _gravar_caminho(user, "ficha.nome", "Alloy")
        self.assertEqual(_ler_caminho(user, "ficha.nome"), "Alloy")
        _gravar_caminho(user, "ficha.nome", None)
        self.assertIsNone(_ler_caminho(user, "ficha.nome"))

    async def test_editor_expoe_todas_as_cinco_areas(self):
        alvo = SimpleNamespace(id=2)
        view = StatusPainelView(alvo, 1)
        self.assertEqual(len(view.children), 5)
        self.assertEqual({item.row for item in view.children}, {0, 1, 2, 3, 4})
        self.assertEqual(len(view.children[0].options), len(CAMPO_TEXTO_PERFIL))
        self.assertEqual(len(view.children[2].options), len(REGISTROS_LIMITES))
        self.assertEqual(len(view.children[3].options), len(COLECOES_PERFIL))

    async def test_operacao_somar_atualiza_valor_sem_ultrapassar_modelo(self):
        alvo = SimpleNamespace(id=2, mention="@alvo")
        admin = SimpleNamespace(id=1, mention="@admin", guild_permissions=SimpleNamespace(administrator=True))
        interaction = SimpleNamespace(user=admin, response=FakeResponse())
        user = {"poder": 100, "atributos": {}}
        modal = StatusValorModal(alvo, "poder", 1)
        modal.operacao._value = "somar"
        modal.valor._value = "50"
        with (
            patch.object(soberano, "get_user", return_value=user),
            patch.object(soberano, "save_user") as salvar,
        ):
            await modal.on_submit(interaction)
        self.assertEqual(user["poder"], 150)
        salvar.assert_called_once_with(2, user)

    async def test_perfil_reflete_nomenclaturas_personalizadas(self):
        member = SimpleNamespace(
            id=2,
            display_name="Jogador",
            display_avatar=SimpleNamespace(url="https://example.com/avatar.png"),
        )
        user = {
            "xp": 50,
            "nivel": 1,
            "poder": 136,
            "pegada": "imperial",
            "titulo": "Diretor",
            "ficha": {"nome": "Nome Editado"},
            "cabecalho_perfil": "Cabeçalho Editado",
            "subtitulo_perfil": "Frase Editada",
            "moradia_custom": "Palácio Lunar",
            "organizacao_custom": "Casa Tenshi",
            "empresa_custom": "Tenshi Corp",
            "prestigio": "Ouro",
        }
        with (
            patch.object(perfil_config, "get_user", return_value=user),
            patch.object(perfil_config, "get_familias", return_value={}),
            patch.object(perfil_config, "get_empresas", return_value={}),
            patch.object(perfil_config, "get_casas", return_value={}),
        ):
            embed = await perfil_config._build_perfil_embed(None, member)
        self.assertEqual(embed.title, "Cabeçalho Editado")
        self.assertIn("Frase Editada", embed.description)
        valores = {field.name: field.value for field in embed.fields}
        self.assertEqual(valores["🏠 Moradia"], "Palácio Lunar")
        self.assertEqual(valores["👨‍👩‍👧 Organização"], "Casa Tenshi")
        self.assertEqual(valores["🏢 Empresa"], "Tenshi Corp")

    def test_automacao_tem_canais_tematicos_e_nome_estetico(self):
        self.assertGreaterEqual(len(CANAIS_SISTEMA), 11)
        self.assertEqual(_nome_canal("┇9e", "🎓", "Tenshi Academy"), "┇9e・🎓・tenshi-academy")


if __name__ == "__main__":
    unittest.main()
