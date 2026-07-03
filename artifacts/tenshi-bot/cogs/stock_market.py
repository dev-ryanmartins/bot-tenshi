"""Stock Market System - Advanced Economy Feature"""

import json
import os
import random
from datetime import UTC, datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands
from database import get_user, save_user
from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial

DATA_FILE = "data/stock_market.json"
COR_DOURADO = 0x9E7815
COR_SUCESSO = 0x1A5C2E
COR_PERIGO = 0x7B1F1F
COR_NEUTRO = 0x3D3D3D


def _load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return _create_default_market()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return _create_default_market()


def _save_data(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _create_default_market() -> dict:
    """Cria mercado de ações padrão."""
    stocks = {
        "TENSHI": {
            "name": "Tenshi Imperial",
            "price": 100.00,
            "change": 0,
            "history": [100.00],
            "volatility": 0.05,
            "trend": "neutral"
        },
        "GOLD": {
            "name": "Ouro Imperial",
            "price": 250.00,
            "change": 0,
            "history": [250.00],
            "volatility": 0.03,
            "trend": "neutral"
        },
        "TECH": {
            "name": "Tenshi Tech",
            "price": 75.00,
            "change": 0,
            "history": [75.00],
            "volatility": 0.08,
            "trend": "neutral"
        },
        "ENERGY": {
            "name": "Energia Imperial",
            "price": 150.00,
            "change": 0,
            "history": [150.00],
            "volatility": 0.06,
            "trend": "neutral"
        },
        "FOOD": {
            "name": "Alimentos Reais",
            "price": 50.00,
            "change": 0,
            "history": [50.00],
            "volatility": 0.04,
            "trend": "neutral"
        }
    }
    
    return {
        "stocks": stocks,
        "last_update": datetime.now(UTC).isoformat(),
        "market_status": "open",
        "portfolio": {}  # user_id -> {stock: quantity}
    }


def _embed(titulo: str, descricao: str, cor: int = COR_DOURADO) -> discord.Embed:
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    embed.set_footer(text=RODAPE_IMPERIAL)
    return embed


def _update_market() -> dict:
    """Atualiza os preços das ações."""
    data = _load_data()
    stocks = data["stocks"]
    
    for symbol, stock in stocks.items():
        volatility = stock["volatility"]
        change_percent = random.uniform(-volatility, volatility)
        
        # Aplicar tendência
        if stock["trend"] == "up":
            change_percent += 0.02
        elif stock["trend"] == "down":
            change_percent -= 0.02
        
        # Calcular novo preço
        old_price = stock["price"]
        new_price = old_price * (1 + change_percent)
        new_price = max(1.00, new_price)  # Preço mínimo de 1
        
        stock["price"] = round(new_price, 2)
        stock["change"] = round(change_percent * 100, 2)
        stock["history"].append(new_price)
        
        # Manter apenas últimos 30 dias de histórico
        if len(stock["history"]) > 30:
            stock["history"] = stock["history"][-30:]
        
        # Atualizar tendência
        if len(stock["history"]) >= 3:
            if stock["history"][-1] > stock["history"][-3]:
                stock["trend"] = "up"
            elif stock["history"][-1] < stock["history"][-3]:
                stock["trend"] = "down"
            else:
                stock["trend"] = "neutral"
    
    data["last_update"] = datetime.now(UTC).isoformat()
    _save_data(data)
    return data


class StockMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_market(self, message, args):
        """Mostra o mercado de ações."""
        data = _update_market()
        stocks = data["stocks"]
        
        linhas = []
        for symbol, stock in stocks.items():
            emoji = "📈" if stock["change"] > 0 else "📉" if stock["change"] < 0 else "➡️"
            change_str = f"+{stock['change']}%" if stock["change"] > 0 else f"{stock['change']}%"
            linhas.append(f"{emoji} **{symbol}** - {stock['name']}")
            linhas.append(f"   Preço: {stock['price']} moedas | Variação: {change_str}")
            linhas.append(f"   Tendência: {stock['trend'].upper()}\n")
        
        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("📊 Mercado de Ações Imperial", descricao, COR_DOURADO))

    async def handle_buy(self, message, args):
        """Compra ações."""
        if len(args) < 2:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi buy [ação] [quantidade]`", COR_NEUTRO))
            return
        
        symbol = args[0].upper()
        try:
            quantity = int(args[1])
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Quantidade deve ser um número.", COR_PERIGO))
            return
        
        data = _load_data()
        stocks = data["stocks"]
        
        if symbol not in stocks:
            await message.channel.send(embed=_embed("❌ Erro", f"Ação '{symbol}' não encontrada.", COR_PERIGO))
            return
        
        stock = stocks[symbol]
        total_cost = stock["price"] * quantity
        
        user = get_user(message.author.id)
        total_balance = user["moedas"] + user.get("conta_banco", 0)
        
        if total_balance < total_cost:
            await message.channel.send(embed=_embed("❌ Saldo Insuficiente", f"Você precisa de {total_cost} moedas. Tem {total_balance}.", COR_PERIGO))
            return
        
        # Deduzir do saldo (prioriza moedas em mãos)
        if user["moedas"] >= total_cost:
            user["moedas"] -= total_cost
        else:
            restante = total_cost - user["moedas"]
            user["moedas"] = 0
            user["conta_banco"] -= restante
        
        # Adicionar ao portfólio
        user_id = str(message.author.id)
        if "portfolio" not in data:
            data["portfolio"] = {}
        
        if user_id not in data["portfolio"]:
            data["portfolio"][user_id] = {}
        
        data["portfolio"][user_id][symbol] = data["portfolio"][user_id].get(symbol, 0) + quantity
        
        save_user(message.author.id, user)
        _save_data(data)
        
        await message.channel.send(embed=_embed("✅ Compra Realizada", f"Você comprou {quantity} ações de {symbol} por {total_cost} moedas!", COR_SUCESSO))

    async def handle_sell(self, message, args):
        """Vende ações."""
        if len(args) < 2:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi sell [ação] [quantidade]`", COR_NEUTRO))
            return
        
        symbol = args[0].upper()
        try:
            quantity = int(args[1])
        except ValueError:
            await message.channel.send(embed=_embed("❌ Erro", "Quantidade deve ser um número.", COR_PERIGO))
            return
        
        data = _load_data()
        user_id = str(message.author.id)
        
        if "portfolio" not in data or user_id not in data["portfolio"]:
            await message.channel.send(embed=_embed("❌ Erro", "Você não possui ações.", COR_PERIGO))
            return
        
        portfolio = data["portfolio"][user_id]
        
        if symbol not in portfolio or portfolio[symbol] < quantity:
            await message.channel.send(embed=_embed("❌ Erro", f"Você não possui {quantity} ações de {symbol}.", COR_PERIGO))
            return
        
        stocks = data["stocks"]
        if symbol not in stocks:
            await message.channel.send(embed=_embed("❌ Erro", f"Ação '{symbol}' não encontrada.", COR_PERIGO))
            return
        
        stock = stocks[symbol]
        total_value = stock["price"] * quantity
        
        # Adicionar ao saldo
        user = get_user(message.author.id)
        user["moedas"] += total_value
        
        # Remover do portfólio
        portfolio[symbol] -= quantity
        if portfolio[symbol] == 0:
            del portfolio[symbol]
        
        if not portfolio:
            del data["portfolio"][user_id]
        
        save_user(message.author.id, user)
        _save_data(data)
        
        await message.channel.send(embed=_embed("✅ Venda Realizada", f"Você vendeu {quantity} ações de {symbol} por {total_value} moedas!", COR_SUCESSO))

    async def handle_portfolio(self, message, args):
        """Mostra o portfólio do usuário."""
        data = _load_data()
        user_id = str(message.author.id)
        
        if "portfolio" not in data or user_id not in data["portfolio"]:
            await message.channel.send(embed=_embed("📋 Portfólio Vazio", "Você não possui ações.", COR_NEUTRO))
            return
        
        portfolio = data["portfolio"][user_id]
        stocks = data["stocks"]
        
        linhas = []
        total_value = 0
        
        for symbol, quantity in portfolio.items():
            if symbol in stocks:
                stock = stocks[symbol]
                value = stock["price"] * quantity
                total_value += value
                emoji = "📈" if stock["change"] > 0 else "📉" if stock["change"] < 0 else "➡️"
                linhas.append(f"{emoji} **{symbol}** - {quantity} ações")
                linhas.append(f"   Valor: {value} moedas | Preço unitário: {stock['price']}\n")
        
        linhas.append(f"**Valor Total do Portfólio: {total_value} moedas**")
        descricao = "\n".join(linhas)
        
        await message.channel.send(embed=_embed(f"📋 Portfólio de {message.author.display_name}", descricao, COR_DOURADO))

    async def handle_stock_info(self, message, args):
        """Mostra informações detalhadas de uma ação."""
        if not args:
            await message.channel.send(embed=_embed("❌ Erro", "Use: `tenshi stock-info [ação]`", COR_NEUTRO))
            return
        
        symbol = args[0].upper()
        data = _load_data()
        stocks = data["stocks"]
        
        if symbol not in stocks:
            await message.channel.send(embed=_embed("❌ Erro", f"Ação '{symbol}' não encontrada.", COR_PERIGO))
            return
        
        stock = stocks[symbol]
        emoji = "📈" if stock["change"] > 0 else "📉" if stock["change"] < 0 else "➡️"
        change_str = f"+{stock['change']}%" if stock["change"] > 0 else f"{stock['change']}%"
        
        # Criar gráfico simples
        history = stock["history"][-7:]  # Últimos 7 dias
        chart = " ".join(["█" if i == len(history)-1 else "▄" for i in range(len(history))])
        
        descricao = (
            f"**Nome:** {stock['name']}\n"
            f"**Preço Atual:** {stock['price']} moedas\n"
            f"**Variação:** {emoji} {change_str}\n"
            f"**Tendência:** {stock['trend'].upper()}\n"
            f"**Volatilidade:** {stock['volatility']*100}%\n\n"
            f"**Histórico (7 dias):**\n{chart}\n"
            f"{' '.join([str(round(p, 1)) for p in history])}"
        )
        
        await message.channel.send(embed=_embed(f"📊 {symbol} - Detalhes", descricao, COR_DOURADO))

    async def handle_top_stocks(self, message, args):
        """Mostra as melhores ações do dia."""
        data = _load_data()
        stocks = data["stocks"]
        
        # Ordenar por variação
        sorted_stocks = sorted(stocks.items(), key=lambda x: x[1]["change"], reverse=True)
        
        linhas = []
        for i, (symbol, stock) in enumerate(sorted_stocks[:5], 1):
            emoji = "📈" if stock["change"] > 0 else "📉"
            change_str = f"+{stock['change']}%" if stock["change"] > 0 else f"{stock['change']}%"
            linhas.append(f"{i}. {emoji} **{symbol}** - {change_str}")
        
        descricao = "\n".join(linhas)
        await message.channel.send(embed=_embed("🏆 Top Ações do Dia", descricao, COR_SUCESSO))
