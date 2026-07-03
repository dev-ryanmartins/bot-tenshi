"""Sistema de Teste e Diagnóstico - Verifica todas as funcionalidades do bot"""

import discord
from discord.ext import commands
from datetime import datetime
import sys
import traceback


class SistemaTeste(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_teste_sistema(self, message, args):
        """Executa testes completos do sistema e mostra resultados."""
        
        # Criar embed inicial
        embed = discord.Embed(
            title="🧪 Sistema de Teste e Diagnóstico",
            description="Iniciando testes do sistema...",
            color=0x3498DB,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Sistema Imperial Tenshi • Teste Automático")
        
        msg = await message.channel.send(embed=embed)
        
        resultados = []
        
        # Teste 1: Importação de módulos
        try:
            from cogs.design_visual import CoresImperial, EmojisImperial, criar_embed_moderno
            resultados.append(("✅ Design Visual", "Módulo carregado com sucesso", True))
        except ImportError as e:
            resultados.append(("❌ Design Visual", f"Erro ao importar: {str(e)}", False))
        
        # Teste 2: Funções de embed
        try:
            from cogs.design_visual import criar_embed_moderno
            test_embed = criar_embed_moderno("Teste", "Descrição de teste", 0x9E7815)
            resultados.append(("✅ Embed Moderno", "Função de embed funciona", True))
        except Exception as e:
            resultados.append(("❌ Embed Moderno", f"Erro: {str(e)}", False))
        
        # Teste 3: Painel Admin
        try:
            from cogs.painel_admin import PainelAdmin
            resultados.append(("✅ Painel Admin", "Cog carregado com sucesso", True))
        except ImportError as e:
            resultados.append(("❌ Painel Admin", f"Erro ao importar: {str(e)}", False))
        
        # Teste 4: Database
        try:
            from database import get_user, save_user, get_all_users
            test_user = get_user(message.author.id)
            resultados.append(("✅ Database", "Funções de database funcionam", True))
        except Exception as e:
            resultados.append(("❌ Database", f"Erro: {str(e)}", False))
        
        # Teste 5: Utils
        try:
            from utils import IMPERADOR_ID, RODAPE_IMPERIAL, embed_imperial
            resultados.append(("✅ Utils", "Módulo utils carregado", True))
        except Exception as e:
            resultados.append(("❌ Utils", f"Erro: {str(e)}", False))
        
        # Teste 6: Parentesco
        try:
            from cogs.parentesco import aplicar_parentesco, VINCULOS
            resultados.append(("✅ Parentesco", "Módulo parentesco carregado", True))
        except Exception as e:
            resultados.append(("❌ Parentesco", f"Erro: {str(e)}", False))
        
        # Teste 7: Permissões do bot
        try:
            perms = message.guild.me.guild_permissions
            permissoes = []
            if perms.administrator:
                permissoes.append("Administrador")
            if perms.manage_roles:
                permissoes.append("Gerenciar Cargos")
            if perms.manage_messages:
                permissoes.append("Gerenciar Mensagens")
            if perms.ban_members:
                permissoes.append("Banir Membros")
            
            if permissoes:
                resultados.append(("✅ Permissões", f"Bot tem: {', '.join(permissoes)}", True))
            else:
                resultados.append(("⚠️ Permissões", "Bot tem poucas permissões", False))
        except Exception as e:
            resultados.append(("❌ Permissões", f"Erro: {str(e)}", False))
        
        # Teste 8: Sistema de deduplicação
        try:
            from main import _ja_processou, _seen_msg_ids
            resultados.append(("✅ Deduplicação", "Sistema anti-duplicação ativo", True))
        except Exception as e:
            resultados.append(("❌ Deduplicação", f"Erro: {str(e)}", False))
        
        # Teste 9: Cores do Design Visual
        try:
            from cogs.design_visual import CoresImperial
            cores = [CoresImperial.DOURADO, CoresImperial.SUCESSO, CoresImperial.PERIGO, CoresImperial.INFO]
            resultados.append(("✅ Cores", f"Paleta de {len(cores)} cores carregada", True))
        except Exception as e:
            resultados.append(("❌ Cores", f"Erro: {str(e)}", False))
        
        # Teste 10: Emojis do Design Visual
        try:
            from cogs.design_visual import EmojisImperial
            emojis = [EmojisImperial.USUARIO, EmojisImperial.ECONOMIA, EmojisImperial.RPG]
            resultados.append(("✅ Emojis", f"{len(emojis)} emojis temáticos carregados", True))
        except Exception as e:
            resultados.append(("❌ Emojis", f"Erro: {str(e)}", False))
        
        # Contar resultados
        sucesso = sum(1 for _, _, s in resultados if s)
        falha = len(resultados) - sucesso
        
        # Criar embed final com resultados
        campos = []
        for status, nome, detalhe in resultados:
            valor = f"{detalhe}"
            campos.append((nome, valor, False))
        
        embed_final = discord.Embed(
            title="🧪 Resultado dos Testes",
            description=f"**Total de Testes:** {len(resultados)}\n"
                       f"**✅ Sucesso:** {sucesso}\n"
                       f"**❌ Falhas:** {falha}\n"
                       f"**Taxa de Sucesso:** {(sucesso/len(resultados)*100):.1f}%",
            color=0x00FF7F if falha == 0 else 0xFF4500,
            timestamp=datetime.utcnow()
        )
        
        # Adicionar campos (máximo 25 campos por embed)
        for nome, valor, inline in campos[:25]:
            embed_final.add_field(name=nome, value=valor, inline=inline)
        
        embed_final.set_footer(text="Sistema Imperial Tenshi • Diagnóstico Completo")
        
        await msg.edit(embed=embed_final)
        
        # Se houver falhas, enviar detalhes
        if falha > 0:
            detalhes_falhas = "\n".join([f"• {nome}: {detalhe}" for status, nome, detalhe in resultados if not s])
            if detalhes_falhas:
                await message.channel.send(
                    embed=discord.Embed(
                        title="⚠️ Detalhes das Falhas",
                        description=detalhes_falhas,
                        color=0xFF4500
                    )
                )

    async def handle_teste_embed(self, message, args):
        """Testa o sistema de embed visual."""
        try:
            from cogs.design_visual import (
                CoresImperial,
                EmojisImperial,
                criar_embed_moderno,
                criar_embed_categoria,
                criar_embed_sucesso,
                criar_embed_erro,
                criar_embed_aviso,
                formatar_numero_grande,
                criar_lista_decorativa,
                criar_separador
            )
            
            # Testar todos os tipos de embed
            embeds = [
                criar_embed_moderno("Teste Embed Moderno", "Descrição do embed moderno", CoresImperial.DOURADO, "👑"),
                criar_embed_categoria("usuarios", "Teste Categoria", "Descrição da categoria"),
                criar_embed_sucesso("Teste Sucesso", "Mensagem de sucesso"),
                criar_embed_erro("Teste Erro", "Mensagem de erro"),
                criar_embed_aviso("Teste Aviso", "Mensagem de aviso"),
            ]
            
            for i, embed in enumerate(embeds, 1):
                await message.channel.send(embed=embed)
            
            # Testar utilitários
            await message.channel.send(f"**Número formatado:** {formatar_numero_grande(1500000)}")
            await message.channel.send(f"**Lista decorativa:**\n{criar_lista_decorativa(['Item 1', 'Item 2', 'Item 3'])}")
            await message.channel.send(f"**Separador:**\n{criar_separador('Teste')}")
            
            await message.channel.send("✅ Todos os testes de embed visual concluídos com sucesso!")
            
        except Exception as e:
            await message.channel.send(f"❌ Erro ao testar embed visual: {str(e)}\n```\n{traceback.format_exc()}```")

    async def handle_teste_painel(self, message, args):
        """Testa o painel administrativo."""
        try:
            from cogs.painel_admin import PainelAdmin, _tem_autoridade
            
            if not _tem_autoridade(message.author):
                await message.channel.send("❌ Você não tem autoridade para testar o painel admin.")
                return
            
            await message.channel.send("✅ Painel Admin carregado e pronto para uso.")
            await message.channel.send("Use `tenshi painel-admin` para testar o painel completo.")
            
        except Exception as e:
            await message.channel.send(f"❌ Erro ao testar painel: {str(e)}\n```\n{traceback.format_exc()}```")


def setup(bot):
    bot.add_cog(SistemaTeste(bot))
