import discord

from database import get_casamentos, get_user
from ia_router import ia_soberana
from lei_imperial import buscar_artigos, prompt_lei_imperial
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, SEP


COR_DOURADO = 0x9E7815
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


class GovernancaIA:
    def __init__(self, bot):
        self.bot = bot

    def _is_admin_imperial(self, member: discord.Member) -> bool:
        if member.id == IMPERADOR_ID:
            return True
        try:
            if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
                return True
        except Exception:
            pass
        return bool(get_user(member.id).get("co_soberano"))

    async def handle_consultar_lei(self, message, args):
        consulta = " ".join(args).strip()
        artigos = buscar_artigos(consulta)
        descricao = "\n\n".join(
            f"**{a['ref']} - {a['tema'].title()}**\n{a['texto']}" for a in artigos[:6]
        )
        await message.channel.send(embed=_embed(
            "Consulta ao Codigo Imperial Tenshi",
            f"{descricao}\n\n{SEP}\n*Consulta:* `{consulta or 'principios gerais'}`",
            COR_DOURADO,
        ))

    async def handle_parecer_ia(self, message, args):
        if not self._is_admin_imperial(message.author):
            await message.channel.send(embed=_embed(
                "Acesso Restrito",
                "Pareceres administrativos sao restritos ao Imperador, co-soberania e administradores.",
                COR_PERIGO,
            ))
            return
        caso = " ".join(args).strip()
        if not caso:
            await message.channel.send(embed=_embed(
                "Parametro Invalido",
                "Use: `Tenshi, parecer-ia [caso administrativo ou juridico]`",
                COR_NEUTRO,
            ))
            return

        casamentos = get_casamentos()
        contexto = (
            f"Servidor: {message.guild.name if message.guild else 'DM'}\n"
            f"Autoridade solicitante: {message.author.display_name} ({message.author.id})\n"
            f"Casamentos registrados: {len(casamentos)}\n"
            f"Caso: {caso}"
        )
        resposta = await ia_soberana(
            prompt_lei_imperial()
            + "\n\nFormato obrigatorio: Fundamento, Risco, Decisao recomendada, Comando sugerido, Observacao final.",
            contexto,
            max_tokens=1100,
        )
        await message.channel.send(embed=_embed("Parecer Administrativo da IA", resposta, COR_DOURADO))

    async def handle_plano_admin(self, message, args):
        if not self._is_admin_imperial(message.author):
            await message.channel.send(embed=_embed("Acesso Restrito", "Somente administracao imperial.", COR_PERIGO))
            return
        objetivo = " ".join(args).strip()
        if not objetivo:
            await message.channel.send(embed=_embed(
                "Parametro Invalido",
                "Use: `Tenshi, plano-admin [objetivo]`",
                COR_NEUTRO,
            ))
            return
        contexto = (
            f"Objetivo administrativo: {objetivo}\n"
            f"Autor: {message.author.display_name}\n"
            f"Restricoes: nao executar punicoes sem comando explicito; respeitar proporcionalidade."
        )
        resposta = await ia_soberana(
            prompt_lei_imperial()
            + "\n\nCrie um plano pratico em ate 6 passos, com comandos Tenshi quando existirem.",
            contexto,
            max_tokens=900,
        )
        await message.channel.send(embed=_embed("Plano de Administracao Imperial", resposta, COR_DOURADO))
