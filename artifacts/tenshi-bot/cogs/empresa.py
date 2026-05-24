import discord
from database import (get_user, save_user, get_empresas, save_empresas,
                      criar_empresa, contratar_funcionario, demitir_funcionario,
                      pagar_salarios, depositar_empresa)
from utils import embed_imperial
from datetime import datetime


PERMISSOES_DISPONIVEIS = ["contratar", "demitir", "pagar", "ver_financeiro", "depositar"]


class Empresa:
    def __init__(self, bot):
        self.bot = bot

    async def handle_empresa(self, message, args):
        if not args:
            await self._ajuda(message)
            return
        sub = args[0].lower()
        resto = args[1:]

        if sub == "criar":
            await self._criar(message, resto)
        elif sub == "info":
            await self._info(message)
        elif sub == "contratar":
            await self._contratar(message, resto)
        elif sub == "demitir":
            await self._demitir(message, resto)
        elif sub == "funcionarios":
            await self._funcionarios(message)
        elif sub == "pagar":
            await self._pagar(message)
        elif sub in ("depositar", "investir"):
            await self._depositar(message, resto)
        elif sub == "permissao":
            await self._permissao(message, resto)
        elif sub == "cargo":
            await self._cargo(message, resto)
        elif sub == "dissolucao":
            await self._dissolver(message)
        else:
            await self._ajuda(message)

    async def _ajuda(self, message):
        embed = discord.Embed(
            title="🏢 TENSHI ENTERPRISE — GESTÃO",
            description="Sistema completo de gestão empresarial imperial.",
            color=0x1E3A5F
        )
        embed.add_field(name="📋 Comandos", value=(
            "`empresa criar [nome]` — Fundar empresa (500 moedas)\n"
            "`empresa info` — Ver dados da sua empresa\n"
            "`empresa funcionarios` — Listar funcionários e salários\n"
            "`empresa contratar @user [cargo] [salario]` — Contratar\n"
            "`empresa demitir @user` — Demitir funcionário\n"
            "`empresa pagar` — Pagar salários com caixa da empresa\n"
            "`empresa depositar [v]` — Depositar no caixa\n"
            "`empresa cargo @user [novo cargo]` — Mudar cargo\n"
            "`empresa permissao @user [permissão]` — Dar permissão"
        ), inline=False)
        embed.set_footer(text="🏢 Tenshi Enterprise • Poder nos negócios")
        await message.channel.send(embed=embed)

    async def _criar(self, message, args):
        if not args:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, empresa criar [nome da empresa]`", 0x8B0000))
            return
        nome = " ".join(args)
        ok, resultado = criar_empresa(message.author.id, nome)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Erro", resultado, 0x8B0000))
            return
        embed = discord.Embed(
            title="🏢 EMPRESA FUNDADA!",
            description=f"*Os selos da Tenshi Enterprise foram apostos...*\n\n"
                       f"**{nome}** agora opera oficialmente no Império de Tenshi!\n\n"
                       f"Você é o **CEO** desta organização.",
            color=0x1E3A5F
        )
        embed.add_field(name="🆔 ID da Empresa", value=f"`{resultado}`", inline=True)
        embed.add_field(name="💰 Custo de Abertura", value="500 moedas", inline=True)
        embed.add_field(name="📋 Próximos passos", value=(
            "• `empresa depositar [v]` — Adicionar capital\n"
            "• `empresa contratar @user [cargo] [salario]` — Contratar\n"
            "• `empresa pagar` — Pagar salários"
        ), inline=False)
        embed.set_footer(text="🏢 A Tenshi Enterprise registrou seu empreendimento")
        await message.channel.send(embed=embed)

    async def _info(self, message):
        user = get_user(message.author.id)
        eid = user.get("empresa_id")
        if not eid:
            await message.channel.send(embed=embed_imperial("❌", "Você não faz parte de nenhuma empresa. Use `Tenshi, empresa criar [nome]`.", 0x8B0000))
            return
        empresas = get_empresas()
        empresa = empresas.get(eid)
        if not empresa:
            await message.channel.send(embed=embed_imperial("❌", "Empresa não encontrada.", 0x8B0000))
            return
        total_salarios = sum(f["salario"] for f in empresa["funcionarios"].values())
        fundada = empresa.get("fundada", "")[:10]
        embed = discord.Embed(
            title=f"🏢 {empresa['nome'].upper()}",
            description=f"*Registrada no Cadastro Imperial de Tenshi*",
            color=0x1E3A5F
        )
        embed.add_field(name="🆔 ID", value=f"`{eid}`", inline=True)
        embed.add_field(name="📅 Fundada", value=fundada, inline=True)
        embed.add_field(name="👥 Funcionários", value=str(len(empresa["funcionarios"])), inline=True)
        embed.add_field(name="💰 Caixa", value=f"**{empresa['saldo']}** moedas", inline=True)
        embed.add_field(name="💸 Folha Salarial", value=f"**{total_salarios}** moedas/pagamento", inline=True)
        try:
            dono = await self.bot.fetch_user(int(empresa["dono"]))
            embed.add_field(name="👑 CEO", value=dono.display_name, inline=True)
        except Exception:
            embed.add_field(name="👑 CEO", value="Desconhecido", inline=True)
        embed.set_footer(text="🏢 Tenshi Enterprise • Registrada no Cadastro Imperial")
        await message.channel.send(embed=embed)

    async def _funcionarios(self, message):
        user = get_user(message.author.id)
        eid = user.get("empresa_id")
        if not eid:
            await message.channel.send(embed=embed_imperial("❌", "Você não faz parte de nenhuma empresa.", 0x8B0000))
            return
        empresas = get_empresas()
        empresa = empresas.get(eid)
        if not empresa:
            return
        embed = discord.Embed(
            title=f"👥 QUADRO DE FUNCIONÁRIOS — {empresa['nome']}",
            description="*Registro oficial de colaboradores imperiais*",
            color=0x1E3A5F
        )
        total_folha = 0
        for uid, func in empresa["funcionarios"].items():
            try:
                membro = await self.bot.fetch_user(int(uid))
                nome_display = membro.display_name
            except Exception:
                nome_display = f"ID:{uid}"
            cargo = func["cargo"]
            salario = func["salario"]
            perms = ", ".join(func.get("permissoes", [])) or "Nenhuma"
            data = func.get("data_contratacao", "")[:10]
            total_folha += salario
            embed.add_field(
                name=f"👤 {nome_display} — {cargo}",
                value=f"💰 Salário: **{salario}** moedas | 📅 Desde: {data}\n🔑 Permissões: {perms}",
                inline=False
            )
        embed.add_field(name="💸 Total Folha Salarial", value=f"**{total_folha}** moedas", inline=False)
        embed.add_field(name="💰 Caixa Atual", value=f"**{empresa['saldo']}** moedas", inline=True)
        embed.set_footer(text="Use 'empresa pagar' para pagar todos os salários")
        await message.channel.send(embed=embed)

    async def _contratar(self, message, args):
        user = get_user(message.author.id)
        eid = user.get("empresa_id")
        if not eid:
            await message.channel.send(embed=embed_imperial("❌", "Você não faz parte de nenhuma empresa.", 0x8B0000))
            return
        if not message.mentions or len(args) < 2:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, empresa contratar @user [cargo] [salario]`\nExemplo: `Tenshi, empresa contratar @João Gerente 200`", 0x8B0000))
            return
        alvo = message.mentions[0]
        args_sem_mention = [a for a in args if not a.startswith("<@")]
        if not args_sem_mention:
            await message.channel.send(embed=embed_imperial("❓", "Informe cargo e salário.", 0x8B0000))
            return
        salario = 0
        cargo_parts = []
        for a in args_sem_mention:
            if a.isdigit():
                salario = int(a)
            else:
                cargo_parts.append(a)
        cargo = " ".join(cargo_parts) if cargo_parts else "Funcionário"
        ok, msg = contratar_funcionario(eid, message.author.id, alvo.id, cargo, salario)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Erro", msg, 0x8B0000))
            return
        empresas = get_empresas()
        nome_empresa = empresas[eid]["nome"]
        embed = discord.Embed(
            title="✅ FUNCIONÁRIO CONTRATADO",
            description=f"*Os papéis foram assinados e selados...*\n\n"
                       f"**{alvo.display_name}** foi contratado(a) para **{nome_empresa}**!",
            color=0x006400
        )
        embed.add_field(name="👤 Funcionário", value=alvo.display_name, inline=True)
        embed.add_field(name="💼 Cargo", value=cargo, inline=True)
        embed.add_field(name="💰 Salário", value=f"**{salario}** moedas/pagamento", inline=True)
        await message.channel.send(embed=embed)

    async def _demitir(self, message, args):
        user = get_user(message.author.id)
        eid = user.get("empresa_id")
        if not eid:
            await message.channel.send(embed=embed_imperial("❌", "Você não faz parte de nenhuma empresa.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "Mencione quem demitir: `Tenshi, empresa demitir @user`", 0x8B0000))
            return
        alvo = message.mentions[0]
        ok, msg = demitir_funcionario(eid, message.author.id, alvo.id)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Erro", msg, 0x8B0000))
            return
        await message.channel.send(embed=embed_imperial(
            "📋 Funcionário Demitido",
            f"*{alvo.display_name}* foi desligado(a) da empresa por decisão da diretoria.",
            0x8B0000
        ))

    async def _pagar(self, message):
        user = get_user(message.author.id)
        eid = user.get("empresa_id")
        if not eid:
            await message.channel.send(embed=embed_imperial("❌", "Você não faz parte de nenhuma empresa.", 0x8B0000))
            return
        ok, msg, pagos = pagar_salarios(eid, message.author.id)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Folha de Pagamento", msg, 0x8B0000))
            return
        empresas = get_empresas()
        nome_empresa = empresas[eid]["nome"]
        embed = discord.Embed(
            title="💸 FOLHA DE PAGAMENTO PROCESSADA",
            description=f"*Os cofres de {nome_empresa} foram movimentados...*",
            color=0x006400
        )
        total = 0
        for p in pagos:
            try:
                membro = await self.bot.fetch_user(int(p["uid"]))
                nome = membro.display_name
            except Exception:
                nome = f"ID:{p['uid']}"
            embed.add_field(name=f"✅ {nome}", value=f"{p['cargo']} — **+{p['valor']}** moedas", inline=False)
            total += p["valor"]
        embed.add_field(name="💰 Total Pago", value=f"**{total}** moedas", inline=True)
        embed.set_footer(text="💼 Tenshi Enterprise • Compromisso cumprido com os colaboradores")
        await message.channel.send(embed=embed)

    async def _depositar(self, message, args):
        user = get_user(message.author.id)
        eid = user.get("empresa_id")
        if not eid:
            await message.channel.send(embed=embed_imperial("❌", "Você não faz parte de nenhuma empresa.", 0x8B0000))
            return
        valor = 0
        for a in args:
            if a.isdigit():
                valor = int(a)
                break
        if valor <= 0:
            await message.channel.send(embed=embed_imperial("❓", "Informe o valor: `Tenshi, empresa depositar [valor]`", 0x8B0000))
            return
        ok, msg = depositar_empresa(eid, message.author.id, valor)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌", msg, 0x8B0000))
            return
        empresas = get_empresas()
        await message.channel.send(embed=embed_imperial(
            "🏦 Depósito no Caixa",
            f"**{valor} moedas** foram adicionadas ao caixa de **{empresas[eid]['nome']}**.\n"
            f"Novo saldo: **{empresas[eid]['saldo']}** moedas.",
            0x006400
        ))

    async def _permissao(self, message, args):
        user = get_user(message.author.id)
        eid = user.get("empresa_id")
        if not eid:
            return
        empresas = get_empresas()
        empresa = empresas.get(eid)
        if not empresa or empresa["dono"] != str(message.author.id):
            await message.channel.send(embed=embed_imperial("🚫", "Apenas o CEO pode gerenciar permissões.", 0x8B0000))
            return
        if not message.mentions or len(args) < 2:
            perms = " | ".join(PERMISSOES_DISPONIVEIS)
            await message.channel.send(embed=embed_imperial("❓", f"Use: `Tenshi, empresa permissao @user [permissão]`\nDisponíveis: {perms}", 0x8B0000))
            return
        alvo = message.mentions[0]
        args_sem_mention = [a for a in args if not a.startswith("<@")]
        perm = args_sem_mention[0].lower() if args_sem_mention else ""
        if perm not in PERMISSOES_DISPONIVEIS:
            await message.channel.send(embed=embed_imperial("❌", f"Permissão inválida. Disponíveis: {', '.join(PERMISSOES_DISPONIVEIS)}", 0x8B0000))
            return
        uid = str(alvo.id)
        if uid not in empresa["funcionarios"]:
            await message.channel.send(embed=embed_imperial("❌", "Este usuário não é funcionário.", 0x8B0000))
            return
        perms_atuais = empresa["funcionarios"][uid].get("permissoes", [])
        if perm in perms_atuais:
            perms_atuais.remove(perm)
            acao = "revogada"
        else:
            perms_atuais.append(perm)
            acao = "concedida"
        empresa["funcionarios"][uid]["permissoes"] = perms_atuais
        save_empresas(empresas)
        await message.channel.send(embed=embed_imperial(
            "🔑 Permissão Atualizada",
            f"Permissão **{perm}** foi **{acao}** para {alvo.display_name}.\nPermissões atuais: {', '.join(perms_atuais) or 'Nenhuma'}",
            0x1E3A5F
        ))

    async def _cargo(self, message, args):
        user = get_user(message.author.id)
        eid = user.get("empresa_id")
        if not eid:
            return
        empresas = get_empresas()
        empresa = empresas.get(eid)
        if not empresa or empresa["dono"] != str(message.author.id):
            await message.channel.send(embed=embed_imperial("🚫", "Apenas o CEO pode alterar cargos.", 0x8B0000))
            return
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, empresa cargo @user [novo cargo]`", 0x8B0000))
            return
        alvo = message.mentions[0]
        args_sem_mention = [a for a in args if not a.startswith("<@")]
        if not args_sem_mention:
            await message.channel.send(embed=embed_imperial("❓", "Informe o novo cargo.", 0x8B0000))
            return
        novo_cargo = " ".join(args_sem_mention)
        uid = str(alvo.id)
        if uid not in empresa["funcionarios"]:
            await message.channel.send(embed=embed_imperial("❌", "Usuário não é funcionário.", 0x8B0000))
            return
        cargo_antigo = empresa["funcionarios"][uid]["cargo"]
        empresa["funcionarios"][uid]["cargo"] = novo_cargo
        save_empresas(empresas)
        alvo_user = get_user(alvo.id)
        alvo_user["cargo_empresa"] = novo_cargo
        save_user(alvo.id, alvo_user)
        await message.channel.send(embed=embed_imperial(
            "💼 Cargo Atualizado",
            f"{alvo.display_name}: **{cargo_antigo}** → **{novo_cargo}**",
            0x1E3A5F
        ))

    async def _dissolver(self, message):
        user = get_user(message.author.id)
        eid = user.get("empresa_id")
        if not eid:
            return
        empresas = get_empresas()
        empresa = empresas.get(eid)
        if not empresa or empresa["dono"] != str(message.author.id):
            await message.channel.send(embed=embed_imperial("🚫", "Apenas o CEO pode dissolver a empresa.", 0x8B0000))
            return
        nome = empresa["nome"]
        for uid in list(empresa["funcionarios"].keys()):
            try:
                u = get_user(int(uid))
                u["empresa_id"] = None
                u["cargo_empresa"] = None
                u["salario"] = 0
                save_user(int(uid), u)
            except Exception:
                pass
        del empresas[eid]
        save_empresas(empresas)
        await message.channel.send(embed=embed_imperial(
            "💔 Empresa Dissolvida",
            f"**{nome}** foi encerrada. Todos os funcionários foram desligados.",
            0x8B0000
        ))
