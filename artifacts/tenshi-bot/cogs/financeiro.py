import discord
from database import (get_user, save_user, transferir, depositar_banco,
                      sacar_banco, pedir_emprestimo, pagar_emprestimo)
from utils import embed_imperial
from datetime import datetime


class Financeiro:
    def __init__(self, bot):
        self.bot = bot

    async def handle_banco(self, message):
        user = get_user(message.author.id)
        moedas = user.get("moedas", 0)
        banco = user.get("conta_banco", 0)
        emprestimos = user.get("emprestimos", [])
        divida = sum(e["valor_restante"] for e in emprestimos)
        patrimonio = moedas + banco - divida

        embed = discord.Embed(
            title="🏦 BANCO IMPERIAL DE TENSHI",
            description=f"*Extrato completo de {message.author.display_name}*",
            color=0x1E3A5F
        )
        embed.add_field(name="👜 Moedas em Mãos", value=f"**{moedas}** moedas", inline=True)
        embed.add_field(name="🏦 Conta Bancária", value=f"**{banco}** moedas", inline=True)
        embed.add_field(name="💸 Dívidas Ativas", value=f"**{divida}** moedas", inline=True)
        embed.add_field(name="💎 Patrimônio Líquido", value=f"**{patrimonio}** moedas", inline=False)
        if emprestimos:
            lista = "\n".join([f"• {e['valor_restante']} moedas (orig: {e['valor_original']})" for e in emprestimos])
            embed.add_field(name="📋 Empréstimos Ativos", value=lista, inline=False)
        embed.add_field(name="⚡ Comandos Rápidos", value=(
            "`depositar [v]` · `sacar [v]` · `transferir @user [v]`\n"
            "`emprestimo [v]` · `pagar-divida [v]` · `historico`"
        ), inline=False)
        embed.set_footer(text="🏦 Banco Imperial de Tenshi • Seus bens protegidos pelo Império")
        embed.set_thumbnail(url=message.author.display_avatar.url)
        await message.channel.send(embed=embed)

    async def handle_depositar(self, message, args):
        valor = self._extrair_valor(args)
        if valor is None:
            await message.channel.send(embed=embed_imperial("❓", "Informe o valor: `Tenshi, depositar [valor]`", 0x8B0000))
            return
        ok, msg = depositar_banco(message.author.id, valor)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Erro", msg, 0x8B0000))
            return
        user = get_user(message.author.id)
        await message.channel.send(embed=embed_imperial(
            "🏦 Depósito Realizado",
            f"**+{valor}** moedas depositadas no Banco Imperial.\n"
            f"💼 Em mãos: **{user['moedas']}** | 🏦 Banco: **{user['conta_banco']}**",
            0x006400
        ))

    async def handle_sacar(self, message, args):
        valor = self._extrair_valor(args)
        if valor is None:
            await message.channel.send(embed=embed_imperial("❓", "Informe o valor: `Tenshi, sacar [valor]`", 0x8B0000))
            return
        ok, msg = sacar_banco(message.author.id, valor)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Erro", msg, 0x8B0000))
            return
        user = get_user(message.author.id)
        await message.channel.send(embed=embed_imperial(
            "💰 Saque Realizado",
            f"**{valor}** moedas sacadas do Banco Imperial.\n"
            f"💼 Em mãos: **{user['moedas']}** | 🏦 Banco: **{user['conta_banco']}**",
            0x006400
        ))

    async def handle_transferir(self, message, args):
        if not message.mentions:
            await message.channel.send(embed=embed_imperial("❓", "Use: `Tenshi, transferir @user [valor]`", 0x8B0000))
            return
        alvo = message.mentions[0]
        if alvo.id == message.author.id:
            await message.channel.send(embed=embed_imperial("❌", "Você não pode transferir para si mesmo.", 0x8B0000))
            return
        valor = self._extrair_valor(args)
        if valor is None or valor <= 0:
            await message.channel.send(embed=embed_imperial("❓", "Informe um valor válido.", 0x8B0000))
            return
        ok, msg = transferir(message.author.id, alvo.id, valor)
        if not ok:
            await message.channel.send(embed=embed_imperial("❌ Erro", msg, 0x8B0000))
            return
        embed = discord.Embed(
            title="💸 TRANSFERÊNCIA IMPERIAL",
            description=f"*Os selos do Tesouro Imperial foram apostos...*",
            color=0x006400
        )
        embed.add_field(name="📤 De", value=message.author.display_name, inline=True)
        embed.add_field(name="💰 Valor", value=f"**{valor}** moedas", inline=True)
        embed.add_field(name="📥 Para", value=alvo.display_name, inline=True)
        embed.set_footer(text="🏦 Banco Imperial de Tenshi • Transação registrada")
        await message.channel.send(embed=embed)

    async def handle_emprestimo(self, message, args):
        valor = self._extrair_valor(args)
        if valor is None or valor <= 0:
            user = get_user(message.author.id)
            divida = sum(e["valor_restante"] for e in user.get("emprestimos", []))
            await message.channel.send(embed=embed_imperial(
                "🏦 Crédito Imperial",
                f"Informe o valor: `Tenshi, emprestimo [valor]`\n\n"
                f"• Limite: **1000 moedas**\n"
                f"• Juros: **20%**\n"
                f"• Sua dívida atual: **{divida}** moedas",
                0x1E3A5F
            ))
            return
        ok, msg = pedir_emprestimo(message.author.id, valor)
        cor = 0x006400 if ok else 0x8B0000
        titulo = "💳 Crédito Aprovado!" if ok else "❌ Crédito Negado"
        await message.channel.send(embed=embed_imperial(titulo, msg, cor))

    async def handle_pagar_divida(self, message, args):
        valor = self._extrair_valor(args)
        if valor is None or valor <= 0:
            user = get_user(message.author.id)
            divida = sum(e["valor_restante"] for e in user.get("emprestimos", []))
            await message.channel.send(embed=embed_imperial(
                "💸 Pagamento de Dívida",
                f"Informe o valor: `Tenshi, pagar-divida [valor]`\n\nDívida atual: **{divida}** moedas",
                0x1E3A5F
            ))
            return
        ok, msg = pagar_emprestimo(message.author.id, valor)
        cor = 0x006400 if ok else 0x8B0000
        await message.channel.send(embed=embed_imperial("💳 Pagamento", msg, cor))

    async def handle_historico(self, message):
        user = get_user(message.author.id)
        historico = user.get("historico_financeiro", [])
        if not historico:
            await message.channel.send(embed=embed_imperial("📋 Histórico", "Nenhuma transação registrada ainda.", 0x2C2F33))
            return
        ultimos = historico[-10:][::-1]
        embed = discord.Embed(
            title="📋 EXTRATO IMPERIAL",
            description=f"*Últimas {len(ultimos)} transações de {message.author.display_name}*",
            color=0x1E3A5F
        )
        tipo_emoji = {
            "deposito": "🏦⬆️",
            "saque": "🏦⬇️",
            "transferencia_saida": "📤",
            "transferencia_entrada": "📥",
            "emprestimo": "💳",
            "pagamento_emprestimo": "💸",
            "salario": "💼",
        }
        for reg in ultimos:
            emoji = tipo_emoji.get(reg["tipo"], "💰")
            data = reg.get("data", "")[:10]
            valor = reg.get("valor", 0)
            sinal = "+" if reg["tipo"] in ("transferencia_entrada", "emprestimo", "salario", "saque") else "-"
            embed.add_field(
                name=f"{emoji} {reg['tipo'].replace('_', ' ').title()} — {data}",
                value=f"**{sinal}{valor}** moedas",
                inline=False
            )
        embed.set_footer(text="🏦 Banco Imperial de Tenshi • Histórico protegido pelo Império")
        await message.channel.send(embed=embed)

    def _extrair_valor(self, args) -> int | None:
        for a in args:
            cleaned = a.replace(",", "").replace(".", "")
            if cleaned.isdigit():
                return int(cleaned)
        return None
