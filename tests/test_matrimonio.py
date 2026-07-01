import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch


BOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

from cogs import matrimonio  # noqa: E402
from cogs.matrimonio import (  # noqa: E402
    FUSO_CERIMONIA,
    _corte_completa,
    _eh_padre,
    _ids_reservados,
    _parse_agendamento,
)


class FakeRole:
    def __init__(self, name):
        self.name = name


class FakeMember:
    def __init__(self, *roles, member_id=1):
        self.id = member_id
        self.roles = [FakeRole(role) for role in roles]


class MatrimonioHelpersTest(unittest.TestCase):
    def test_celebrante_precisa_de_cargo_clerical(self):
        self.assertTrue(_eh_padre(FakeMember("Padre Imperial")))
        self.assertTrue(_eh_padre(FakeMember("Pároco da Capital")))
        self.assertFalse(_eh_padre(FakeMember("Administrador", "Cerimonialista")))

    def test_agendamento_aceita_data_futura(self):
        futuro = datetime.now(FUSO_CERIMONIA) + timedelta(days=2)
        resultado = _parse_agendamento(futuro.strftime("%d/%m/%Y"), futuro.strftime("%H:%M"))
        self.assertEqual(resultado.tzinfo, FUSO_CERIMONIA)

    def test_agendamento_rejeita_formato_e_data_passada(self):
        with self.assertRaisesRegex(ValueError, "DD/MM/AAAA"):
            _parse_agendamento("amanhã", "oito horas")
        with self.assertRaisesRegex(ValueError, "data futura"):
            _parse_agendamento("01/01/2020", "12:00")

    def test_corte_exige_padre_e_quatro_testemunhas_distintas(self):
        registro = {
            "noivo1": "1",
            "noivo2": "2",
            "padre": "3",
            "padrinho_honra": "4",
            "segundo_padrinho": "5",
            "dama_honra": "6",
            "segunda_madrinha": "7",
        }
        self.assertTrue(_corte_completa(registro))
        self.assertEqual(_ids_reservados(registro), {1, 2, 3, 4, 5, 6, 7})
        registro["dama_honra"] = None
        self.assertFalse(_corte_completa(registro))

    def test_registro_final_preserva_padre_e_corte(self):
        registro = {
            "tipo": "comum",
            "padre": "3",
            "padrinho_honra": "4",
            "segundo_padrinho": "5",
            "dama_honra": "6",
            "segunda_madrinha": "7",
            "agendado_para": "2030-01-01T12:00:00-03:00",
        }
        usuarios = {1: {}, 2: {}}
        casamentos_salvos = {}

        with (
            patch.object(matrimonio, "get_casamentos", return_value={}),
            patch.object(matrimonio, "save_casamentos", side_effect=lambda dados: casamentos_salvos.update(dados)),
            patch.object(matrimonio, "get_user", side_effect=lambda uid: usuarios.setdefault(uid, {})),
            patch.object(matrimonio, "save_user"),
        ):
            matrimonio._registrar_uniao(FakeMember(member_id=1), FakeMember(member_id=2), registro)

        casamento = casamentos_salvos["1_2"]
        self.assertEqual(casamento["padre"], "3")
        self.assertEqual(casamento["padrinho_honra"], "4")
        self.assertEqual(casamento["segunda_madrinha"], "7")
        self.assertEqual(usuarios[1]["conjuge"], "2")


if __name__ == "__main__":
    unittest.main()
