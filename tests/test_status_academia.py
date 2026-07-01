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


class StatusAcademiaTest(unittest.IsolatedAsyncioTestCase):
    def test_perfil_do_imperador_e_normalizado_no_teto(self):
        usuario = {"atributos": {}, "prestigio": "Bronze"}
        with (
            patch.object(soberano, "get_user", return_value=usuario),
            patch.object(soberano, "save_user") as salvar,
        ):
            resultado = soberano.aplicar_perfil_supremo_imperador()

        self.assertEqual(resultado["prestigio"], "Irídio")
        self.assertTrue(resultado["acesso_total"])
        self.assertTrue(resultado["diretor_academia"])
        self.assertTrue(resultado["professor"])
        self.assertEqual(resultado["materias_professor"], ["todas"])
        self.assertEqual(resultado["fadiga"], 0)
        for atributo in ATRIBUTOS_FICHA:
            self.assertEqual(resultado["atributos"][atributo], STATUS_LIMITES[atributo][1])
        salvar.assert_called_once_with(IMPERADOR_ID, resultado)

    def test_imperador_tem_bypass_de_administrador(self):
        membro = SimpleNamespace(id=IMPERADOR_ID, guild_permissions=SimpleNamespace(administrator=False))
        self.assertTrue(soberano._administrador(membro))

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
