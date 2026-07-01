import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


BOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

from cogs import soberano  # noqa: E402
from cogs.academia import FUNCOES_DOCENTES, FuncaoDocenteView, MateriaDocenteView  # noqa: E402
from cogs.soberano import ATRIBUTOS_FICHA, PRESTIGIOS, STATUS_LIMITES  # noqa: E402
from utils import IMPERADOR_ID  # noqa: E402


class FakeMember:
    def __init__(self, member_id=123):
        self.id = member_id


class FakeChannel:
    def __init__(self):
        self.envios = []

    async def send(self, **kwargs):
        self.envios.append(kwargs)


class StatusAcademiaTest(unittest.IsolatedAsyncioTestCase):
    def test_perfil_do_imperador_preserva_status_editavel(self):
        usuario = {
            "atributos": {"vida": 321, "inteligencia": 44},
            "prestigio": "Bronze",
            "prestigio_chave": "bronze",
            "poder": 72,
            "fadiga": 35,
        }
        with (
            patch.object(soberano, "get_user", return_value=usuario),
            patch.object(soberano, "save_user") as salvar,
        ):
            resultado = soberano.aplicar_perfil_supremo_imperador()

        self.assertEqual(resultado["prestigio"], "Bronze")
        self.assertEqual(resultado["prestigio_chave"], "bronze")
        self.assertTrue(resultado["acesso_total"])
        self.assertTrue(resultado["diretor_academia"])
        self.assertTrue(resultado["professor"])
        self.assertEqual(resultado["materias_professor"], ["todas"])
        self.assertEqual(resultado["poder"], 72)
        self.assertEqual(resultado["fadiga"], 35)
        self.assertEqual(resultado["atributos"], {"vida": 321, "inteligencia": 44})
        salvar.assert_called_once_with(IMPERADOR_ID, resultado)

    def test_imperador_tem_bypass_de_administrador(self):
        membro = SimpleNamespace(id=IMPERADOR_ID, guild_permissions=SimpleNamespace(administrator=False))
        self.assertTrue(soberano._administrador(membro))

    async def test_set_status_sem_mencao_edita_o_proprio_usuario(self):
        autor = SimpleNamespace(
            id=IMPERADOR_ID,
            mention="@imperador",
            guild_permissions=SimpleNamespace(administrator=False),
        )
        canal = FakeChannel()
        mensagem = SimpleNamespace(author=autor, mentions=[], channel=canal)
        with patch.object(soberano, "get_user", return_value={"atributos": {}}):
            await soberano.Soberano(None).cmd_set_status(mensagem, [])

        self.assertEqual(len(canal.envios), 1)
        painel = canal.envios[0]["view"]
        self.assertIs(painel.children[0].alvo, autor)

    def test_prestigios_e_funcoes_docentes_estao_disponiveis(self):
        self.assertEqual(set(PRESTIGIOS), {"bronze", "prata", "ouro", "platina", "diamante", "obsidiana", "iridio"})
        self.assertTrue({"professor", "assistente", "coordenador", "diretor"}.issubset(FUNCOES_DOCENTES))
        self.assertLessEqual(len(STATUS_LIMITES), 25)

    async def test_paineis_docentes_expoem_funcoes_e_disciplinas(self):
        membro = FakeMember()
        funcoes = FuncaoDocenteView(membro, 1)
        valores = {opcao.value for opcao in funcoes.children[0].options}
        self.assertTrue({"professor", "assistente", "coordenador", "diretor", "remover"}.issubset(valores))

        materias = MateriaDocenteView(membro, 1, "professor")
        self.assertGreaterEqual(len(materias.children[0].options), 1)
        self.assertLessEqual(materias.children[0].max_values, 10)


if __name__ == "__main__":
    unittest.main()
