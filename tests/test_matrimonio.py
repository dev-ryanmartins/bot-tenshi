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
    ConfiguracaoCerimoniaView,
    MadrinhasCerimoniaView,
    PedidoCasamentoView,
    RitualistaCerimoniaView,
    VotosMatrimonioView,
    _configuracao_completa,
    _corte_completa,
    _ids_reservados,
    _parse_agendamento,
)


class FakeMember:
    def __init__(self, member_id=1):
        self.id = member_id
        self.display_name = f"Membro {member_id}"
        self.mention = f"<@{member_id}>"


class MatrimonioHelpersTest(unittest.IsolatedAsyncioTestCase):

    def test_agendamento_aceita_data_futura(self):
        futuro = datetime.now(FUSO_CERIMONIA) + timedelta(days=2)
        resultado = _parse_agendamento(futuro.strftime("%d/%m/%Y"), futuro.strftime("%H:%M"))
        self.assertEqual(resultado.tzinfo, FUSO_CERIMONIA)

    def test_agendamento_rejeita_formato_e_data_passada(self):
        with self.assertRaisesRegex(ValueError, "DD/MM/AAAA"):
            _parse_agendamento("amanhã", "oito horas")
        with self.assertRaisesRegex(ValueError, "data futura"):
            _parse_agendamento("01/01/2020", "12:00")

    def test_corte_exige_tres_padrinhos_tres_madrinhas_e_ritualista(self):
        registro = {
            "noivo1": "1",
            "noivo2": "2",
            "ritualista": "3",
            "padrinho_honra": "4",
            "segundo_padrinho": "5",
            "terceiro_padrinho": "6",
            "dama_honra": "7",
            "segunda_madrinha": "8",
            "terceira_madrinha": "9",
        }
        self.assertTrue(_corte_completa(registro))
        self.assertTrue(_configuracao_completa(registro))
        self.assertEqual(_ids_reservados(registro), {1, 2, 3, 4, 5, 6, 7, 8, 9})
        registro["dama_honra"] = None
        self.assertFalse(_corte_completa(registro))

    def test_registro_final_preserva_ritualista_e_corte(self):
        registro = {
            "tipo": "comum",
            "ritualista": "3",
            "padrinho_honra": "4",
            "segundo_padrinho": "5",
            "terceiro_padrinho": "6",
            "dama_honra": "7",
            "segunda_madrinha": "8",
            "terceira_madrinha": "9",
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
            matrimonio._registrar_uniao(FakeMember(1), FakeMember(2), registro)

        casamento = casamentos_salvos["1_2"]
        self.assertEqual(casamento["celebrante"], "tenshi_ia")
        self.assertEqual(casamento["ritualista"], "3")
        self.assertEqual(casamento["padrinho_honra"], "4")
        self.assertEqual(casamento["terceiro_padrinho"], "6")
        self.assertEqual(casamento["segunda_madrinha"], "8")
        self.assertEqual(casamento["terceira_madrinha"], "9")
        self.assertEqual(usuarios[1]["conjuge"], "2")
        self.assertEqual(usuarios[1]["parentesco"], "Familiar")
        self.assertEqual(usuarios[2]["parentesco_origem"], "casamento")

    def test_registro_de_casamento_deriva_cunhado(self):
        usuarios = {
            1: {"parentesco": "Irmã", "parentesco_emoji": "👩"},
            2: {"parentesco": "Membro", "parentesco_emoji": "👤"},
        }
        with (
            patch.object(matrimonio, "get_casamentos", return_value={}),
            patch.object(matrimonio, "save_casamentos"),
            patch.object(matrimonio, "get_user", side_effect=lambda uid: usuarios[uid]),
            patch.object(matrimonio, "save_user"),
        ):
            matrimonio._registrar_uniao(FakeMember(1), FakeMember(2), {})
        self.assertEqual(usuarios[1]["parentesco"], "Irmã")
        self.assertEqual(usuarios[2]["parentesco"], "Cunhad@")

    async def test_fluxo_visual_tem_seis_testemunhas_ritualista_e_botoes_de_aceite(self):
        n1, n2 = FakeMember(1), FakeMember(2)
        pedido = PedidoCasamentoView(n1, n2)
        self.assertEqual([item.label for item in pedido.children], ["Sim, aceito", "Não aceito"])

        corte = ConfiguracaoCerimoniaView("1_2", n1, n2)
        self.assertEqual(len(corte.children), 4)
        self.assertTrue(any("terceiro padrinho" in item.placeholder.lower() for item in corte.children))

        madrinhas = MadrinhasCerimoniaView("1_2", n1, n2)
        self.assertEqual(len(madrinhas.children), 4)
        self.assertTrue(any("terceira madrinha" in item.placeholder.lower() for item in madrinhas.children))

        ritualista = RitualistaCerimoniaView("1_2", n1, n2)
        self.assertEqual(len(ritualista.children), 1)
        self.assertIn("Ritualista", ritualista.children[0].placeholder)

        votos = VotosMatrimonioView("1_2", n1, n2, {})
        self.assertEqual([item.label for item in votos.children], ["Sim, aceito", "Não aceito"])


if __name__ == "__main__":
    unittest.main()
