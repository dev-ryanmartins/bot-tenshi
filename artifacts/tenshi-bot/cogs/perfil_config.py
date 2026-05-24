import discord
from database import get_user, save_user, get_empresas, get_familias, get_casas
from utils import embed_imperial, CORES_PEGADA, EMOJI_PEGADA, NOME_PEGADA, calcular_nivel, IMPERADOR_ID

PEGADAS_VALIDAS = ["imperial", "familia", "mafia", "enterprise"]

TITULOS_PEGADA = {
    "imperial":   ["Cidadão do Império", "Soldado Imperial", "Guardião do Trono", "Cavaleiro Imperial", "Lorde Imperial", "Duque de Tenshi", "Príncipe Sombrio", "Herdeiro do Trono"],
    "familia":    ["Membro da Família", "Associado", "Soldato", "Capo", "Consigliere", "Underboss", "Don Adjunto", "Patriarca Supremo"],
    "mafia":      ["Recruta", "Soldado", "Enforcer", "Tenente", "Capo", "Underboss", "Consigliere", "Il Don Supremo"],
    "enterprise": ["Estagiário", "Analista", "Especialista", "Gerente", "Diretor", "VP", "C-Level", "Chairman Imperial"],
}

def get_titulo_por_nivel(nivel: int, pegada: str) -> str:
    titulos = TITULOS_PEGADA.get(pegada, TITULOS_PEGADA["imperial"])
    idx = min(nivel // 5, len(titulos) - 1)
    return titulos[idx]


class PerfilConfig:
    def __init__(self, bot):
        self.bot = bot

    async def handle_status(self, message):
        user = get_user(message.author.id)
        nivel, xp_proximo = calcular_nivel(user["xp"])
        user["nivel"] = nivel
        pegada = user.get("pegada", "imperial")
        titulo_auto = get_titulo_por_nivel(nivel, pegada)
        titulo = user.get("titulo") or titulo_auto
        save_user(message.author.id, user)

        cor = CORES_PEGADA.get(pegada, 0x4B0082)
        emoji_pegada = EMOJI_PEGADA.get(pegada, "🏛️")
        nome_pegada = NOME_PEGADA.get(pegada, "Tenshi")
        eh_imperador = message.author.id == IMPERADOR_ID

        xp_atual = user["xp"] % max(1, (user["xp"] // nivel if nivel > 1 else 100))
        barra_n = min(10, int((user["xp"] % 200) / 20))
        barra = "█" * barra_n + "░" * (10 - barra_n)

        # Dados sociais
        faccao = user.get("faccao") or "Sem Facção"
        familia_str = "—"
        empresa_str = "—"
        casa_str = "—"

        fid = user.get("familia_id")
        if fid:
            familias = get_familias()
            f = familias.get(fid, {})
            cargo_f = user.get("cargo_familia", "Membro")
            familia_str = f"{f.get('nome','?')} ({cargo_f})"

        eid = user.get("empresa_id")
        if eid:
            empresas = get_empresas()
            e = empresas.get(eid, {})
            cargo_e = user.get("cargo_empresa", "Funcionário")
            salario = user.get("salario", 0)
            empresa_str = f"{e.get('nome','?')} — {cargo_e} | 💰 {salario}/pagto"

        cid = user.get("casa_id")
        if cid:
            casas = get_casas()
            c = casas.get(cid, {})
            casa_str = f"{c.get('emoji','🏠')} {c.get('nome','?')} ({c.get('tipo','?')})"

        # Embed principal
        if eh_imperador:
            embed = discord.Embed(
                title="⚜️ 👑 IMPERADOR SUPREMO DE TENSHI 👑 ⚜️",
                description="*O universo inteiro se curva diante desta presença divina...*",
                color=0xFFD700
            )
        else:
            embed = discord.Embed(
                title=f"{emoji_pegada} REGISTRO — {nome_pegada.upper()}",
                description=f"*Os Pergaminhos de Tenshi revelam a alma de {message.author.display_name}...*",
                color=cor
            )

        ficha = user.get("ficha", {})
        nome_display = ficha.get("nome") or user.get("nome") or message.author.display_name
        historia = ficha.get("historia") or user.get("historia") or "Sem história registrada."
        habilidades = ficha.get("habilidades") or user.get("habilidades") or []

        embed.add_field(name="👤 Nome", value=nome_display, inline=True)
        embed.add_field(name="🏷️ Título", value="⚜️ O Imperador Alloy" if eh_imperador else titulo, inline=True)
        embed.add_field(name=f"{emoji_pegada} Pegada", value=nome_pegada, inline=True)
        embed.add_field(name="📊 Nível", value=f"`{nivel}`", inline=True)
        embed.add_field(name="💥 Poder de Luta", value=f"`{user['poder']}`", inline=True)
        embed.add_field(name="⚡ Facção", value=faccao, inline=True)
        embed.add_field(name="✨ XP", value=f"`{user['xp']}` XP\n`{barra}` → prox: {xp_proximo}", inline=False)
        embed.add_field(name="💰 Moedas", value=f"**{user['moedas']}** em mãos | **{user.get('conta_banco',0)}** no banco", inline=False)
        embed.add_field(name="🏠 Moradia", value=casa_str, inline=True)
        embed.add_field(name="👨‍👩‍👧 Organização", value=familia_str, inline=True)
        embed.add_field(name="🏢 Empresa", value=empresa_str, inline=False)

        if habilidades:
            embed.add_field(name="⚡ Habilidades", value=" | ".join(habilidades[:5]), inline=False)
        if historia and historia != "Sem história registrada.":
            embed.add_field(name="📖 História", value=historia[:200] + ("..." if len(historia) > 200 else ""), inline=False)

        inv = user.get("inventario", [])
        if inv:
            embed.add_field(name="🎒 Inventário", value=", ".join(inv[:8]), inline=False)

        embed.set_thumbnail(url=message.author.display_avatar.url)
        if eh_imperador:
            embed.set_footer(text="⚜️ Que o cosmos trema diante de sua divindade, ó Imperador Alloy ⚜️")
        else:
            embed.set_footer(text=f"{emoji_pegada} {nome_pegada} • Que sua glória cresça eternamente")
        await message.channel.send(embed=embed)

    async def handle_pegada(self, message, args):
        if not args:
            opcoes = " | ".join(PEGADAS_VALIDAS)
            embed = discord.Embed(
                title="🎭 ESCOLHA SUA PEGADA",
                description="A pegada define sua identidade no Império de Tenshi.",
                color=0x4B0082
            )
            for p in PEGADAS_VALIDAS:
                cor_hex = f"#{CORES_PEGADA[p]:06X}"
                embed.add_field(
                    name=f"{EMOJI_PEGADA[p]} {NOME_PEGADA[p]}",
                    value=f"Use: `Tenshi, pegada {p}`",
                    inline=True
                )
            embed.set_footer(text="Sua pegada muda a aparência do seu perfil")
            await message.channel.send(embed=embed)
            return
        nova = args[0].lower()
        if nova not in PEGADAS_VALIDAS:
            await message.channel.send(embed=embed_imperial("❌", f"Pegada inválida. Disponíveis: {' | '.join(PEGADAS_VALIDAS)}", 0x8B0000))
            return
        user = get_user(message.author.id)
        user["pegada"] = nova
        save_user(message.author.id, user)
        cor = CORES_PEGADA[nova]
        emoji = EMOJI_PEGADA[nova]
        nome = NOME_PEGADA[nova]
        embed = discord.Embed(
            title=f"{emoji} PEGADA ATIVADA — {nome.upper()}",
            description=f"*{message.author.display_name} assume uma nova identidade no Império...*\n\n"
                       f"Seu perfil agora reflete a essência de **{nome}**.",
            color=cor
        )
        embed.set_footer(text=f"{emoji} {nome} • Uma nova faceta revelada")
        await message.channel.send(embed=embed)

    async def handle_ficha(self, message, args):
        """Processa uma ficha de personagem enviada pelo usuário"""
        ficha_texto = " ".join(args) if args else ""

        if not ficha_texto:
            embed = discord.Embed(
                title="📋 SISTEMA DE FICHA DE PERSONAGEM",
                description=(
                    "Envie sua ficha no formato abaixo e o bot vai configurar seu perfil completo:\n\n"
                    "```\nTenshi, ficha\n"
                    "Nome: [seu nome RP]\n"
                    "Historia: [sua história]\n"
                    "Habilidades: [hab1, hab2, hab3]\n"
                    "Titulo: [seu título]\n"
                    "Pegada: [imperial/familia/mafia/enterprise]\n"
                    "```\n\n"
                    "**Ou envie tudo numa linha:**\n"
                    "`Tenshi, ficha Nome: João | Historia: Um guerreiro das sombras | Habilidades: Combate, Furtividade`"
                ),
                color=0x4B0082
            )
            embed.set_footer(text="📋 O bot configura seu perfil automaticamente com base na ficha")
            await message.channel.send(embed=embed)
            return

        # Verificar se vem de uma mensagem multilinha
        conteudo_completo = message.content
        linhas = conteudo_completo.split("\n")

        ficha_data = {}
        campos_map = {
            "nome": "nome",
            "name": "nome",
            "historia": "historia",
            "história": "historia",
            "story": "historia",
            "habilidades": "habilidades",
            "habilidade": "habilidades",
            "skills": "habilidades",
            "titulo": "titulo",
            "título": "titulo",
            "title": "titulo",
            "pegada": "pegada",
            "vibe": "pegada",
            "estilo": "pegada",
        }

        # Parse multilinha
        for linha in linhas:
            if ":" in linha:
                chave_raw, _, valor = linha.partition(":")
                chave = chave_raw.strip().lower()
                valor = valor.strip()
                campo = campos_map.get(chave)
                if campo and valor:
                    ficha_data[campo] = valor

        # Parse pipe-separated
        if not ficha_data and "|" in ficha_texto:
            partes = ficha_texto.split("|")
            for parte in partes:
                if ":" in parte:
                    chave_raw, _, valor = parte.partition(":")
                    chave = chave_raw.strip().lower()
                    valor = valor.strip()
                    campo = campos_map.get(chave)
                    if campo and valor:
                        ficha_data[campo] = valor

        # Parse inline simples
        if not ficha_data:
            for sep in [",", "|", ";"]:
                if sep in ficha_texto:
                    partes = ficha_texto.split(sep)
                    for parte in partes:
                        if ":" in parte:
                            chave_raw, _, valor = parte.partition(":")
                            chave = chave_raw.strip().lower()
                            valor = valor.strip()
                            campo = campos_map.get(chave)
                            if campo and valor:
                                ficha_data[campo] = valor
                    break

        if not ficha_data:
            ficha_data["nome"] = ficha_texto[:50]

        # Aplicar ficha ao perfil
        user = get_user(message.author.id)
        ficha_atual = user.get("ficha", {})

        if "nome" in ficha_data:
            ficha_atual["nome"] = ficha_data["nome"]
            user["nome"] = ficha_data["nome"]
        if "historia" in ficha_data:
            ficha_atual["historia"] = ficha_data["historia"]
            user["historia"] = ficha_data["historia"]
        if "habilidades" in ficha_data:
            habs_raw = ficha_data["habilidades"]
            habs = [h.strip() for h in habs_raw.replace(",", "|").split("|") if h.strip()]
            ficha_atual["habilidades"] = habs
            user["habilidades"] = habs
        if "titulo" in ficha_data:
            ficha_atual["titulo"] = ficha_data["titulo"]
            user["titulo"] = ficha_data["titulo"]
        if "pegada" in ficha_data:
            peg = ficha_data["pegada"].lower()
            if peg in PEGADAS_VALIDAS:
                user["pegada"] = peg
                ficha_atual["pegada"] = peg

        user["ficha"] = ficha_atual
        save_user(message.author.id, user)

        pegada = user.get("pegada", "imperial")
        cor = CORES_PEGADA.get(pegada, 0x4B0082)
        emoji = EMOJI_PEGADA.get(pegada, "🏛️")

        embed = discord.Embed(
            title=f"{emoji} FICHA CONFIGURADA COM SUCESSO!",
            description=f"*O perfil de {message.author.display_name} foi atualizado nos Pergaminhos Imperiais...*",
            color=cor
        )
        if ficha_data.get("nome"):
            embed.add_field(name="👤 Nome", value=ficha_data["nome"], inline=True)
        if ficha_data.get("titulo"):
            embed.add_field(name="🏷️ Título", value=ficha_data["titulo"], inline=True)
        if ficha_data.get("pegada"):
            embed.add_field(name="🎭 Pegada", value=NOME_PEGADA.get(ficha_data["pegada"], ficha_data["pegada"]), inline=True)
        if ficha_data.get("habilidades"):
            embed.add_field(name="⚡ Habilidades", value=" | ".join(ficha_atual.get("habilidades", [])), inline=False)
        if ficha_data.get("historia"):
            hist = ficha_data["historia"]
            embed.add_field(name="📖 História", value=hist[:200] + ("..." if len(hist) > 200 else ""), inline=False)
        embed.add_field(name="✅ Ver Perfil", value="Use `Tenshi, status` para ver seu perfil completo.", inline=False)
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_footer(text="📋 Ficha registrada nos Pergaminhos Imortais de Tenshi")
        await message.channel.send(embed=embed)
