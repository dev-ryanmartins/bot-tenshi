import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import discord


BOT_DIR = Path(__file__).resolve().parents[1] / "artifacts" / "tenshi-bot"
sys.path.insert(0, str(BOT_DIR))

from cogs import parentesco  # noqa: E402
from cogs.parentesco import (  # noqa: E402
    ParentescoView,
    aplicar_parentesco,
    nome_cargo_estetico,
    resolver_parentescos_casamento,
)
from utils import IMPERADOR_ID  # noqa: E402


class FakeRole:
    def __init__(self, role_id, name, color=None, position=1):
        self.id = role_id
        self.name = name
        self.color = color or discord.Color(0x9E7815)
        self.position = position
        self.managed = False

    def is_default(self):
        return False

    async def edit(self, **kwargs):
        self.position = kwargs.get("position", self.position)
        return self


class FakeGuild:
    def __init__(self):
        self.id = 99
        self.roles = []
        self._next_id = 10

    def get_role(self, role_id):
        return next((role for role in self.roles if role.id == role_id), None)

    async def create_role(self, **kwargs):
        role = FakeRole(self._next_id, kwargs["name"], kwargs["color"])
        self._next_id += 1
        self.roles.append(role)
        return role


class FakeMember:
    def __init__(self, guild, member_id=123):
        self.id = member_id
        self.guild = guild
        self.roles = []
        self.bot = False

    async def add_roles(self, *roles, **kwargs):
        for role in roles:
            if role not in self.roles:
                self.roles.append(role)

    async def remove_roles(self, *roles, **kwargs):
        self.roles = [role for role in self.roles if role not in roles]


class ParentescoTest(unittest.IsolatedAsyncioTestCase):
    def test_nome_segue_estetica_tenshi(self):
        self.assertEqual(nome_cargo_estetico("Filha", "👧"), "” ͎ᵎ  ⊰ 👧  Filha")

    async def test_painel_tem_vinculos_e_personalizado(self):
        view = ParentescoView(FakeMember(FakeGuild()), 1)
        valores = {option.value for option in view.children[0].options}
        self.assertTrue({
            "membro", "patriarca", "filho", "filha", "irmao", "irma", "cunhado",
            "sobrinho", "sobrinha", "neto", "neta", "tio", "tia", "primo", "prima",
            "afilhado", "afilhada", "genro_nora", "consorte", "familiar", "personalizado",
        }.issubset(valores))
        self.assertLessEqual(len(view.children[0].options), 25)

    def test_casamento_com_irmao_gera_cunhado_neutro(self):
        irmao = {"parentesco": "Irmão", "parentesco_emoji": "👨"}
        conjuge = {"parentesco": "Membro", "parentesco_emoji": "👤"}
        vinculo_irmao, vinculo_conjuge = resolver_parentescos_casamento(irmao, conjuge)
        self.assertEqual(vinculo_irmao, ("Irmão", "👨"))
        self.assertEqual(vinculo_conjuge, ("Cunhad@", "🤝"))

    async def test_imperador_permanece_patriarca(self):
        guild = FakeGuild()
        member = FakeMember(guild, IMPERADOR_ID)
        usuarios = {member.id: {}}
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(parentesco, "DATA_FILE", str(Path(temp_dir) / "roles.json")),
                patch.object(parentesco, "get_user", side_effect=lambda uid: usuarios.setdefault(uid, {})),
                patch.object(parentesco, "save_user", side_effect=lambda uid, data: usuarios.__setitem__(uid, data)),
            ):
                await aplicar_parentesco(member, "Membro", "👤", 1)
        self.assertEqual(usuarios[member.id]["parentesco"], "Patriarca da Família")

    async def test_aplicar_parentesco_substitui_apenas_cargo_mapeado(self):
        guild = FakeGuild()
        member = FakeMember(guild)
        usuarios = {member.id: {}}
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(parentesco, "DATA_FILE", str(Path(temp_dir) / "roles.json")),
                patch.object(parentesco, "get_user", side_effect=lambda uid: usuarios.setdefault(uid, {})),
                patch.object(parentesco, "save_user", side_effect=lambda uid, data: usuarios.__setitem__(uid, data)),
            ):
                cargo_filho = await aplicar_parentesco(member, "Filho", "👦", 1)
                cargo_irmao = await aplicar_parentesco(member, "Irmão", "👨", 1)

        self.assertNotIn(cargo_filho, member.roles)
        self.assertIn(cargo_irmao, member.roles)
        self.assertEqual(usuarios[member.id]["parentesco"], "Irmão")
        self.assertEqual(len(guild.roles), 2)


if __name__ == "__main__":
    unittest.main()
