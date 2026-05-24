import { useState, useEffect, useCallback } from "react";
import { Switch, Route, Router as WouterRouter, useLocation } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowDown, ExternalLink, Shield, Cpu, Zap, ScrollText,
  Building, Home, Coins, Crown, Users, Droplets, Swords,
  Lock, LogOut, RefreshCw, Wifi, WifiOff, Server, Activity,
  ChevronRight, Eye, EyeOff, AlertTriangle, CheckCircle2,
  Settings, ArrowLeft
} from "lucide-react";
import NotFound from "@/pages/not-found";

const queryClient = new QueryClient();

const PREFIX = "tenshi,";

const commands = [
  {
    category: "Identidade & Perfil",
    emoji: "🎭",
    color: "from-purple-900/30 to-purple-800/10",
    border: "border-purple-700/30",
    items: [
      { cmd: "status", desc: "Exibe sua ficha completa — nível, XP, HP, energia, moedas e facção atual.", usage: `${PREFIX} status` },
      { cmd: "ficha @user", desc: "Vê a ficha de outro cidadão. Mencione o usuário com @.", usage: `${PREFIX} ficha @Alloy` },
      { cmd: "pegada [tema]", desc: "Muda seu tema visual entre: imperial, familia, mafia ou enterprise.", usage: `${PREFIX} pegada imperial` },
      { cmd: "inventario", desc: "Lista todos os itens e equipamentos no seu inventário.", usage: `${PREFIX} inventario` },
      { cmd: "conquistas", desc: "Exibe seus badges e marcos conquistados no Império.", usage: `${PREFIX} conquistas` },
      { cmd: "criar-ficha", desc: "Cria sua ficha de personagem pela primeira vez no Império.", usage: `${PREFIX} criar-ficha` },
      { cmd: "especies", desc: "Lista as espécies e raças disponíveis para personagens.", usage: `${PREFIX} especies` },
      { cmd: "viajar [local]", desc: "Move seu personagem para outro local do mapa imperial.", usage: `${PREFIX} viajar Floresta das Sombras` },
      { cmd: "local", desc: "Mostra onde seu personagem está no mapa do Império.", usage: `${PREFIX} local` },
    ]
  },
  {
    category: "Jornada Imperial",
    emoji: "⚡",
    color: "from-yellow-900/30 to-yellow-800/10",
    border: "border-yellow-700/30",
    items: [
      { cmd: "treinar [ação]", desc: "Ganha XP narrando uma ação de treino. Use sua criatividade!", usage: `${PREFIX} treinar medito na cachoeira ao amanhecer` },
      { cmd: "missao", desc: "Inicia uma missão narrativa gerada por IA. Cooldown de 1 hora.", usage: `${PREFIX} missao` },
      { cmd: "meditar", desc: "Recupera energia espiritual. Essencial antes de missões longas.", usage: `${PREFIX} meditar` },
      { cmd: "descansar", desc: "Recupera HP. Só funciona em sua residência ou área segura.", usage: `${PREFIX} descansar` },
      { cmd: "oraculo [pergunta]", desc: "O Oráculo Imperial responde sua pergunta via IA mística.", usage: `${PREFIX} oraculo Qual é meu destino?` },
      { cmd: "clima", desc: "Exibe o clima do dia no Império, com efeitos no RPG.", usage: `${PREFIX} clima` },
      { cmd: "dado [tipo]", desc: "Rola dados para ações de RPG. Tipos: d6, d20, d100.", usage: `${PREFIX} dado d20` },
      { cmd: "interagir [ação]", desc: "Realiza uma ação de roleplay expressa em texto narrativo.", usage: `${PREFIX} interagir saca sua espada e avança` },
      { cmd: "profissao [classe]", desc: "Define ou muda sua profissão: Ferreiro, Alquimista, etc.", usage: `${PREFIX} profissao Ferreiro` },
    ]
  },
  {
    category: "Poderes de RP",
    emoji: "✨",
    color: "from-violet-900/30 to-violet-800/10",
    border: "border-violet-700/30",
    items: [
      { cmd: "poderes", desc: "Abre a árvore de poderes disponíveis para sua espécie e nível.", usage: `${PREFIX} poderes` },
      { cmd: "meus-poderes", desc: "Lista os poderes que você já desbloqueou.", usage: `${PREFIX} meus-poderes` },
    ]
  },
  {
    category: "Economia & Comércio",
    emoji: "💰",
    color: "from-amber-900/30 to-amber-800/10",
    border: "border-amber-700/30",
    items: [
      { cmd: "carteira", desc: "Exibe seu saldo de Moedas Imperiais e moedas em circulação.", usage: `${PREFIX} carteira` },
      { cmd: "banco", desc: "Acessa seu extrato bancário e histórico de transações.", usage: `${PREFIX} banco` },
      { cmd: "depositar [valor]", desc: "Deposita moedas no banco imperial para guardar com segurança.", usage: `${PREFIX} depositar 500` },
      { cmd: "sacar [valor]", desc: "Saca moedas do banco para sua carteira.", usage: `${PREFIX} sacar 200` },
      { cmd: "transferir @user [valor]", desc: "Transfere moedas para outro cidadão via PIX Imperial.", usage: `${PREFIX} transferir @Alloy 100` },
      { cmd: "mercado", desc: "Abre a loja oficial do Império com itens e equipamentos.", usage: `${PREFIX} mercado` },
      { cmd: "mercado-negro", desc: "Acessa o mercado clandestino com itens raros e ilegais.", usage: `${PREFIX} mercado-negro` },
      { cmd: "comprar [item]", desc: "Compra um item disponível no mercado ativo.", usage: `${PREFIX} comprar Espada de Ferro` },
      { cmd: "trabalhar", desc: "Executa trabalho diário em seu emprego para ganhar moedas.", usage: `${PREFIX} trabalhar` },
      { cmd: "emprego", desc: "Lista empregos disponíveis e mostra seu emprego atual.", usage: `${PREFIX} emprego` },
      { cmd: "leilao [item]", desc: "Lança um item em leilão para outros jogadores comprarem.", usage: `${PREFIX} leilao Poção Rara` },
      { cmd: "emprestimo [valor]", desc: "Solicita empréstimo ao Banco Imperial com juros.", usage: `${PREFIX} emprestimo 1000` },
      { cmd: "pagar-divida", desc: "Quita seu empréstimo ativo com o Banco Imperial.", usage: `${PREFIX} pagar-divida` },
      { cmd: "historico", desc: "Exibe seu histórico financeiro completo.", usage: `${PREFIX} historico` },
    ]
  },
  {
    category: "Propriedades & Condomínio",
    emoji: "🏠",
    color: "from-green-900/30 to-green-800/10",
    border: "border-green-700/30",
    items: [
      { cmd: "casas", desc: "Exibe o mercado imobiliário com casas disponíveis para compra.", usage: `${PREFIX} casas` },
      { cmd: "minha-casa", desc: "Mostra detalhes da sua residência atual no Império.", usage: `${PREFIX} minha-casa` },
      { cmd: "vender-casa", desc: "Coloca sua residência à venda no mercado imobiliário.", usage: `${PREFIX} vender-casa` },
      { cmd: "portaria", desc: "Acessa o sistema de condomínio e vê residências disponíveis.", usage: `${PREFIX} portaria` },
      { cmd: "residencia", desc: "Entra em sua residência do condomínio.", usage: `${PREFIX} residencia` },
      { cmd: "convidar @user", desc: "Convida outro jogador para morar na sua residência.", usage: `${PREFIX} convidar @Alloy` },
      { cmd: "expulsar @user", desc: "Expulsa um morador da sua residência.", usage: `${PREFIX} expulsar @Alloy` },
      { cmd: "devolver-casa", desc: "Devolve sua residência e sai do condomínio.", usage: `${PREFIX} devolver-casa` },
      { cmd: "moradores", desc: "Lista todos os moradores da sua residência.", usage: `${PREFIX} moradores` },
      { cmd: "relaxar", desc: "Descansa em casa ganhando bônus de regeneração.", usage: `${PREFIX} relaxar` },
      { cmd: "fofoca", desc: "Gera uma crônica dos acontecimentos do condomínio via IA.", usage: `${PREFIX} fofoca` },
    ]
  },
  {
    category: "Tenshi Enterprise",
    emoji: "🏢",
    color: "from-blue-900/30 to-blue-800/10",
    border: "border-blue-700/30",
    items: [
      { cmd: "empresa criar [nome]", desc: "Funda uma empresa no Império. Requer capital inicial.", usage: `${PREFIX} empresa criar Tenshi Corp` },
      { cmd: "empresa info", desc: "Exibe detalhes da sua empresa: capital, funcionários e status.", usage: `${PREFIX} empresa info` },
      { cmd: "empresa contratar @user", desc: "Contrata um cidadão como funcionário da empresa.", usage: `${PREFIX} empresa contratar @Alloy` },
      { cmd: "empresa demitir @user", desc: "Demite um funcionário da empresa.", usage: `${PREFIX} empresa demitir @Alloy` },
      { cmd: "empresa funcionarios", desc: "Lista o quadro de funcionários da empresa.", usage: `${PREFIX} empresa funcionarios` },
      { cmd: "empresa pagar", desc: "Paga salários a todos os funcionários automaticamente.", usage: `${PREFIX} empresa pagar` },
    ]
  },
  {
    category: "Família & Máfia",
    emoji: "👨‍👩‍👧",
    color: "from-red-900/30 to-red-800/10",
    border: "border-red-700/30",
    items: [
      { cmd: "familia criar [nome]", desc: "Funda uma família ou clã com você como patriarca.", usage: `${PREFIX} familia criar Os Tenshi` },
      { cmd: "familia entrar [nome]", desc: "Junta-se a uma família/máfia existente.", usage: `${PREFIX} familia entrar Os Tenshi` },
      { cmd: "familia info", desc: "Exibe informações detalhadas da sua família.", usage: `${PREFIX} familia info` },
      { cmd: "familia membros", desc: "Lista todos os membros da família com seus cargos.", usage: `${PREFIX} familia membros` },
      { cmd: "familia missao", desc: "Inicia uma missão em grupo para a família.", usage: `${PREFIX} familia missao` },
      { cmd: "familia depositar [valor]", desc: "Deposita moedas no cofre compartilhado da família.", usage: `${PREFIX} familia depositar 500` },
    ]
  },
  {
    category: "Facções",
    emoji: "⚔️",
    color: "from-orange-900/30 to-orange-800/10",
    border: "border-orange-700/30",
    items: [
      { cmd: "entrar [facção]", desc: "Alista-se em uma das facções do Império. Escolha com sabedoria.", usage: `${PREFIX} entrar Guardiões do Trono` },
      { cmd: "ranking", desc: "Exibe o ranking de poder entre todas as facções ativas.", usage: `${PREFIX} ranking` },
    ]
  },
  {
    category: "Místico",
    emoji: "🔮",
    color: "from-indigo-900/30 to-indigo-800/10",
    border: "border-indigo-700/30",
    items: [
      { cmd: "tarot", desc: "O Oráculo tira cartas de tarô e interpreta seu futuro via IA.", usage: `${PREFIX} tarot` },
      { cmd: "runa", desc: "Consulta as runas ancestrais para guia espiritual.", usage: `${PREFIX} runa` },
      { cmd: "astros", desc: "Lê as constelações e gera seu horóscopo imperial.", usage: `${PREFIX} astros` },
      { cmd: "destino @user", desc: "Lê o destino de outro cidadão via IA mística.", usage: `${PREFIX} destino @Alloy` },
      { cmd: "sacrificio [item]", desc: "Oferenda mística em troca de bênçãos ou maldições.", usage: `${PREFIX} sacrificio Poção Velha` },
      { cmd: "ritual-protecao", desc: "Realiza ritual de proteção — imunidade temporária.", usage: `${PREFIX} ritual-protecao` },
    ]
  },
  {
    category: "Combate Narrativo",
    emoji: "⚔️",
    color: "from-rose-900/30 to-rose-800/10",
    border: "border-rose-700/30",
    items: [
      { cmd: "duelo @user", desc: "Desafia outro cidadão para um duelo com apostas opcionales.", usage: `${PREFIX} duelo @Alloy` },
      { cmd: "aceitar-duelo", desc: "Aceita um desafio de duelo pendente direcionado a você.", usage: `${PREFIX} aceitar-duelo` },
      { cmd: "apostar [valor] @user", desc: "Aposta moedas em um duelo em andamento.", usage: `${PREFIX} apostar 500 @Alloy` },
      { cmd: "invocar-chefe [criatura]", desc: "Admin: Invoca um boss para o servidor enfrentar.", usage: `${PREFIX} invocar-chefe Dragão das Sombras` },
      { cmd: "invasao", desc: "Admin: Inicia uma invasão de criaturas no servidor.", usage: `${PREFIX} invasao` },
    ]
  },
  {
    category: "LoreMaster IA",
    emoji: "📖",
    color: "from-teal-900/30 to-teal-800/10",
    border: "border-teal-700/30",
    items: [
      { cmd: "cronica [tipo]", desc: "Gera uma crônica épica via IA. Tipos: militar, politico, esoterico, mafia, enterprise.", usage: `${PREFIX} cronica militar` },
      { cmd: "evento-lore", desc: "Gera uma profecia ou evento lendário para o Império.", usage: `${PREFIX} evento-lore` },
      { cmd: "oraculo [pergunta]", desc: "Consulta o Oráculo Imperial com uma pergunta livre.", usage: `${PREFIX} oraculo Qual será o fim do Império?` },
      { cmd: "falar [NPC]", desc: "Conversa em tempo real com um NPC do Império via IA.", usage: `${PREFIX} falar Guardião da Porta` },
      { cmd: "lore-historico", desc: "Exibe as crônicas e registros históricos do Império.", usage: `${PREFIX} lore-historico` },
      { cmd: "quadro-avisos", desc: "Mostra as missões diárias e avisos do Império.", usage: `${PREFIX} quadro-avisos` },
    ]
  },
  {
    category: "Moderação Imperial",
    emoji: "🛡️",
    color: "from-slate-800/30 to-slate-700/10",
    border: "border-slate-600/30",
    admin: true,
    items: [
      { cmd: "decreto [mensagem]", desc: "Publica um decreto oficial do Império em nome do Imperador.", usage: `${PREFIX} decreto Que todos se curvem!`, admin: true },
      { cmd: "promover @user [cargo]", desc: "Concede um título ou cargo imperial a um cidadão.", usage: `${PREFIX} promover @Alloy Cavaleiro`, admin: true },
      { cmd: "julgamento @user", desc: "Inicia um tribunal para julgamento de um cidadão.", usage: `${PREFIX} julgamento @Alloy`, admin: true },
      { cmd: "masmorra-prender @user [tempo]", desc: "Prende o cidadão na masmorra por X minutos.", usage: `${PREFIX} masmorra-prender @Alloy 30`, admin: true },
      { cmd: "exilar @user", desc: "Exila o cidadão narrativamente do Império.", usage: `${PREFIX} exilar @Alloy`, admin: true },
      { cmd: "anistia-real", desc: "Concede perdão geral a todos os presos e exilados.", usage: `${PREFIX} anistia-real`, admin: true },
      { cmd: "punir-audacia @user", desc: "Aplica punição leve por comportamento inadequado.", usage: `${PREFIX} punir-audacia @Alloy`, admin: true },
      { cmd: "trancar-portoes", desc: "Ativa lockdown — restringe ações dos cidadãos.", usage: `${PREFIX} trancar-portoes`, admin: true },
      { cmd: "tesouro [valor]", desc: "Adiciona moedas ao tesouro público do Império.", usage: `${PREFIX} tesouro 1000`, admin: true },
      { cmd: "veto [acao]", desc: "Veta uma ação ou evento em andamento.", usage: `${PREFIX} veto duelo`, admin: true },
      { cmd: "ban @user", desc: "Bane o usuário do servidor Discord.", usage: `${PREFIX} ban @Alloy`, admin: true },
      { cmd: "kick @user", desc: "Expulsa o usuário do servidor Discord.", usage: `${PREFIX} kick @Alloy`, admin: true },
      { cmd: "mute @user [tempo]", desc: "Silencia o usuário por X minutos.", usage: `${PREFIX} mute @Alloy 10`, admin: true },
      { cmd: "clear [quantidade]", desc: "Apaga as últimas N mensagens do canal.", usage: `${PREFIX} clear 10`, admin: true },
    ]
  },
  {
    category: "Utilitários",
    emoji: "🔧",
    color: "from-zinc-800/30 to-zinc-700/10",
    border: "border-zinc-600/30",
    items: [
      { cmd: "top", desc: "Exibe o ranking global de cidadãos por XP e riqueza.", usage: `${PREFIX} top` },
      { cmd: "servidor", desc: "Mostra informações detalhadas do servidor Discord.", usage: `${PREFIX} servidor` },
      { cmd: "ping", desc: "Verifica a latência do bot com o Discord.", usage: `${PREFIX} ping` },
      { cmd: "backup", desc: "Salva uma cópia dos seus dados no Império.", usage: `${PREFIX} backup` },
      { cmd: "ajuda", desc: "Exibe o guia completo de comandos do Bot Tenshi.", usage: `${PREFIX} ajuda` },
      { cmd: "status-ia", desc: "Verifica o status dos 7 motores de IA ativos.", usage: `${PREFIX} status-ia` },
    ]
  }
];

const aiMotors = [
  { name: "Narrativa", model: "LLaMA 4 Maverick", use: "Crônicas épicas, roleplay imersivo, missões" },
  { name: "Rápida", model: "LLaMA 4 Scout", use: "Respostas instantâneas, triagem, moderação" },
  { name: "Analítica", model: "LLaMA 3.3 70B", use: "Jurídico, estratégia, análise profunda" },
  { name: "Relatório", model: "Mixtral 8x7B", use: "Auditorias, RH, relatórios econômicos" },
  { name: "Soberana", model: "GPT-120B → Maverick", use: "Geopolítica, decretos, soberania" },
  { name: "Economia", model: "GPT-20B → Scout", use: "Transações, cálculos, finanças" },
  { name: "NPCs", model: "Gemma 2 9B", use: "Personagens, clima, respostas curtas" },
];

function HomePage() {
  const scrollToCommands = () => {
    document.getElementById("comandos")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <div className="fixed inset-0 pointer-events-none z-0 bg-gradient-to-b from-[#0a0208] via-[#0d050f] to-[#080412]" />
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-35 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url(/hero-bg.png)" }}
      />
      <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_at_top,rgba(158,120,21,0.08)_0%,transparent_60%)]" />

      {/* Hero */}
      <section className="relative z-10 min-h-[100dvh] flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className="text-center max-w-4xl mx-auto space-y-8"
        >
          <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3, duration: 1 }}>
            <Crown className="w-16 h-16 text-primary mx-auto mb-4 opacity-90 drop-shadow-[0_0_24px_rgba(234,179,8,0.4)]" />
          </motion.div>
          <h1 className="text-6xl md:text-8xl font-black font-serif tracking-widest uppercase drop-shadow-2xl">
            <span className="bg-gradient-to-b from-yellow-300 via-yellow-500 to-yellow-800 bg-clip-text text-transparent">⚜️ Bot Tenshi</span>
          </h1>
          <p className="text-xl md:text-2xl text-yellow-100/60 font-light max-w-2xl mx-auto leading-relaxed">
            O Bot RPG Oficial do Império de Tenshi. Forje seu destino em um mundo de política, economia, máfia e misticismo.
          </p>
          <p className="text-sm text-yellow-100/30 font-mono tracking-widest uppercase">
            Prefixo: <span className="text-yellow-500/70">tenshi,</span> &nbsp;•&nbsp; 7 Motores de IA &nbsp;•&nbsp; RPG Narrativo
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-5 pt-6">
            <a
              href="https://discord.com/oauth2/authorize?client_id=1427699671052320931&permissions=8&scope=bot"
              target="_blank"
              rel="noopener noreferrer"
              data-testid="button-invite"
              className="group relative inline-flex items-center gap-3 px-10 py-4 bg-gradient-to-r from-yellow-600 to-yellow-500 text-black font-black uppercase tracking-widest text-sm transition-all hover:scale-105 hover:shadow-[0_0_40px_rgba(234,179,8,0.35)] rounded-sm overflow-hidden"
            >
              <div className="absolute inset-0 bg-white/15 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
              <ExternalLink className="w-4 h-4 relative z-10" />
              <span className="relative z-10">Adicionar ao Discord</span>
            </a>
            <button
              onClick={scrollToCommands}
              data-testid="button-commands"
              className="group inline-flex items-center gap-3 px-10 py-4 border border-yellow-700/40 text-yellow-500/80 font-bold uppercase tracking-widest text-sm hover:bg-yellow-900/20 hover:border-yellow-600/60 transition-all rounded-sm"
            >
              <ArrowDown className="w-4 h-4 group-hover:translate-y-1 transition-transform" />
              <span>Ver Comandos</span>
            </button>
          </div>
        </motion.div>
      </section>

      {/* AI Motors */}
      <section className="relative z-10 py-24 border-y border-yellow-900/20 bg-black/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-serif font-bold text-yellow-100/90 mb-3">Inteligência Imperial</h2>
            <p className="text-yellow-100/40 max-w-xl mx-auto">7 motores de IA via Groq, roteados automaticamente para cada tipo de tarefa.</p>
          </motion.div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {aiMotors.map((ai, i) => (
              <motion.div
                key={ai.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="p-5 bg-yellow-950/20 border border-yellow-900/30 rounded-sm hover:border-yellow-700/40 transition-colors"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Cpu className="w-4 h-4 text-yellow-500/70" />
                  <span className="text-yellow-400/90 font-bold font-serif text-sm uppercase tracking-wide">Motor {ai.name}</span>
                </div>
                <p className="text-yellow-100/30 text-xs font-mono mb-1">{ai.model}</p>
                <p className="text-yellow-100/50 text-xs leading-relaxed">{ai.use}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Commands */}
      <section id="comandos" className="relative z-10 py-24 scroll-mt-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-16">
            <h2 className="text-4xl md:text-6xl font-serif font-bold text-yellow-100/90 mb-4">Tomo de Comandos</h2>
            <p className="text-yellow-100/40 text-lg max-w-2xl mx-auto">Cada comando usa o prefixo <code className="text-yellow-500 bg-yellow-950/40 px-2 py-0.5 rounded text-sm">tenshi,</code> seguido do nome.</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {commands.map((cat, idx) => (
              <motion.div
                key={cat.category}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ delay: (idx % 3) * 0.08 }}
                className={`bg-gradient-to-b ${cat.color} border ${cat.border} backdrop-blur-sm rounded-sm overflow-hidden`}
              >
                <div className="flex items-center gap-3 px-5 py-4 border-b border-white/5">
                  <span className="text-xl">{cat.emoji}</span>
                  <h3 className="text-base font-bold font-serif text-yellow-100/90">{cat.category}</h3>
                  {cat.admin && (
                    <span className="ml-auto text-xs bg-red-900/40 text-red-400 border border-red-800/40 px-2 py-0.5 rounded font-mono">Admin</span>
                  )}
                </div>
                <ul className="divide-y divide-white/5">
                  {cat.items.map(item => (
                    <li key={item.cmd} className="px-5 py-3 group hover:bg-white/5 transition-colors">
                      <div className="flex items-start gap-2 mb-1">
                        <ChevronRight className="w-3 h-3 text-yellow-600/60 mt-1 shrink-0" />
                        <div className="min-w-0">
                          <code className="text-yellow-400 font-mono text-xs font-semibold break-all leading-tight">
                            tenshi, {item.cmd}
                          </code>
                          {(item as any).admin && <span className="ml-2 text-xs text-red-400/60">🔒</span>}
                        </div>
                      </div>
                      <p className="text-yellow-100/45 text-xs leading-relaxed pl-5">{item.desc}</p>
                      <p className="text-yellow-600/40 text-xs font-mono pl-5 mt-0.5 truncate">ex: {item.usage}</p>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-yellow-900/20 bg-black/40 py-10 mt-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm">
          <div className="text-yellow-100/30 font-mono">
            Prefixo: <span className="text-yellow-600">tenshi,</span>
          </div>
          <div className="text-yellow-100/30">© 2016–2026 Império de Tenshi</div>
          <div className="text-yellow-100/30 font-serif italic flex items-center gap-2">
            Desenvolvido por Alloy, Imperador da Tenshi <Crown className="w-3 h-3 text-yellow-600" />
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── Admin Panel ───────────────────────────────────────────────────────────────

interface BotStatus {
  online: boolean;
  guilds: number;
  latency: number;
  user: string | null;
}

const ADMIN_TOKEN_KEY = "tenshi_admin_token";
const API_BASE = "/api";

function AdminLogin({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (res.ok) {
        const { token } = await res.json();
        localStorage.setItem(ADMIN_TOKEN_KEY, token);
        onLogin(token);
      } else {
        setError("Credenciais inválidas. Acesso negado pelo Império.");
      }
    } catch {
      setError("Erro de conexão com o servidor imperial.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="fixed inset-0 bg-gradient-to-b from-[#0a0208] via-[#0d050f] to-[#080412]" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,rgba(158,120,21,0.06)_0%,transparent_60%)]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 w-full max-w-md"
      >
        <div className="border border-yellow-900/40 bg-black/60 backdrop-blur-sm p-8 rounded-sm">
          <div className="text-center mb-8">
            <Lock className="w-10 h-10 text-yellow-600/70 mx-auto mb-4" />
            <h1 className="text-2xl font-black font-serif text-yellow-100/90 uppercase tracking-widest mb-1">Acesso Imperial</h1>
            <p className="text-yellow-100/30 text-sm">Preferências do Criador — Alloy</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-yellow-100/40 font-mono uppercase tracking-widest mb-2">Usuário</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                data-testid="input-username"
                className="w-full bg-yellow-950/20 border border-yellow-900/40 text-yellow-100/90 placeholder-yellow-100/20 px-4 py-3 rounded-sm font-mono text-sm focus:outline-none focus:border-yellow-700/60 transition-colors"
                placeholder="usuário"
                required
              />
            </div>
            <div>
              <label className="block text-xs text-yellow-100/40 font-mono uppercase tracking-widest mb-2">Senha</label>
              <div className="relative">
                <input
                  type={showPass ? "text" : "password"}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  data-testid="input-password"
                  className="w-full bg-yellow-950/20 border border-yellow-900/40 text-yellow-100/90 placeholder-yellow-100/20 px-4 py-3 pr-12 rounded-sm font-mono text-sm focus:outline-none focus:border-yellow-700/60 transition-colors"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-yellow-100/30 hover:text-yellow-100/60 transition-colors"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex items-center gap-2 text-red-400 text-xs bg-red-950/30 border border-red-900/40 px-3 py-2 rounded-sm"
                >
                  <AlertTriangle className="w-3 h-3 shrink-0" />
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            <button
              type="submit"
              data-testid="button-login"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-yellow-700 to-yellow-600 text-black font-black uppercase tracking-widest text-sm rounded-sm hover:opacity-90 disabled:opacity-50 transition-opacity mt-2"
            >
              {loading ? "Verificando..." : "Entrar no Império"}
            </button>
          </form>

          <div className="mt-6 text-center">
            <a href="/" className="text-yellow-100/25 text-xs hover:text-yellow-100/50 transition-colors flex items-center justify-center gap-1">
              <ArrowLeft className="w-3 h-3" /> Voltar ao site
            </a>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function AdminPanel({ token, onLogout }: { token: string; onLogout: () => void }) {
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [reconnecting, setReconnecting] = useState(false);
  const [reconnectMsg, setReconnectMsg] = useState("");

  const authHeader = { Authorization: `Bearer ${token}` };

  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const res = await fetch(`${API_BASE}/admin/bot/status`, { headers: authHeader });
      if (res.ok) setBotStatus(await res.json());
      else setBotStatus({ online: false, guilds: 0, latency: 0, user: null });
    } catch {
      setBotStatus({ online: false, guilds: 0, latency: 0, user: null });
    } finally {
      setStatusLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  async function handleReconnect() {
    setReconnecting(true);
    setReconnectMsg("");
    try {
      const res = await fetch(`${API_BASE}/admin/bot/reconnect`, {
        method: "POST",
        headers: authHeader,
      });
      const data = await res.json();
      setReconnectMsg(data.message ?? data.error ?? "Sinal enviado.");
    } catch {
      setReconnectMsg("Erro ao enviar sinal de reconexão.");
    } finally {
      setReconnecting(false);
      setTimeout(() => fetchStatus(), 4000);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <div className="fixed inset-0 bg-gradient-to-b from-[#0a0208] via-[#0d050f] to-[#080412]" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,rgba(158,120,21,0.06)_0%,transparent_60%)]" />

      <div className="relative z-10 max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <Settings className="w-5 h-5 text-yellow-600/70" />
              <h1 className="text-2xl font-black font-serif text-yellow-100/90 uppercase tracking-widest">Preferências do Criador</h1>
            </div>
            <p className="text-yellow-100/30 text-sm ml-8">Painel privado — Alloy, Imperador da Tenshi</p>
          </div>
          <div className="flex items-center gap-3">
            <a href="/" className="text-yellow-100/30 hover:text-yellow-100/60 transition-colors text-xs flex items-center gap-1">
              <ArrowLeft className="w-3 h-3" /> Site
            </a>
            <button
              onClick={onLogout}
              data-testid="button-logout"
              className="flex items-center gap-2 px-4 py-2 border border-red-900/40 text-red-400/60 hover:text-red-400 hover:border-red-700/60 transition-colors rounded-sm text-xs font-mono uppercase tracking-widest"
            >
              <LogOut className="w-3 h-3" /> Sair
            </button>
          </div>
        </div>

        {/* Bot Status Card */}
        <div className="border border-yellow-900/30 bg-black/40 rounded-sm overflow-hidden mb-6">
          <div className="flex items-center justify-between px-6 py-4 border-b border-yellow-900/20">
            <div className="flex items-center gap-3">
              <Server className="w-5 h-5 text-yellow-600/60" />
              <h2 className="font-serif font-bold text-yellow-100/80 uppercase tracking-wide text-sm">Status do Bot Tenshi</h2>
            </div>
            <button
              onClick={fetchStatus}
              data-testid="button-refresh-status"
              disabled={statusLoading}
              className="text-yellow-100/30 hover:text-yellow-100/60 transition-colors disabled:opacity-30"
            >
              <RefreshCw className={`w-4 h-4 ${statusLoading ? "animate-spin" : ""}`} />
            </button>
          </div>

          <div className="p-6">
            {statusLoading && !botStatus ? (
              <div className="flex items-center gap-3 text-yellow-100/40">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="text-sm">Verificando status...</span>
              </div>
            ) : botStatus ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-xs text-yellow-100/30 uppercase tracking-widest font-mono mb-2">Status</p>
                  <div className={`flex items-center gap-2 font-bold text-lg ${botStatus.online ? "text-green-400" : "text-red-400"}`}>
                    {botStatus.online
                      ? <><CheckCircle2 className="w-5 h-5" /> Online</>
                      : <><WifiOff className="w-5 h-5" /> Offline</>
                    }
                  </div>
                </div>
                <div>
                  <p className="text-xs text-yellow-100/30 uppercase tracking-widest font-mono mb-2">Servidores</p>
                  <p className="text-2xl font-black text-yellow-400">{botStatus.guilds}</p>
                </div>
                <div>
                  <p className="text-xs text-yellow-100/30 uppercase tracking-widest font-mono mb-2">Latência</p>
                  <p className="text-2xl font-black text-yellow-400">{botStatus.latency}<span className="text-sm text-yellow-100/40 ml-1">ms</span></p>
                </div>
                <div>
                  <p className="text-xs text-yellow-100/30 uppercase tracking-widest font-mono mb-2">Usuário</p>
                  <p className="text-sm text-yellow-100/70 font-mono truncate">{botStatus.user ?? "—"}</p>
                </div>
              </div>
            ) : null}
          </div>

          {/* Controls */}
          <div className="px-6 pb-6 flex flex-wrap gap-3">
            {botStatus?.online ? (
              <button
                onClick={handleReconnect}
                data-testid="button-reconnect"
                disabled={reconnecting}
                className="flex items-center gap-2 px-5 py-2.5 border border-yellow-700/40 text-yellow-500/80 hover:bg-yellow-900/20 hover:border-yellow-600/60 transition-all rounded-sm text-sm font-bold uppercase tracking-widest disabled:opacity-40"
              >
                <RefreshCw className={`w-4 h-4 ${reconnecting ? "animate-spin" : ""}`} />
                {reconnecting ? "Reconectando..." : "Reconectar Bot"}
              </button>
            ) : (
              <button
                onClick={handleReconnect}
                data-testid="button-ligar-bot"
                disabled={reconnecting}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-800 to-green-700 text-white font-black uppercase tracking-widest text-sm rounded-sm hover:opacity-90 disabled:opacity-40 transition-opacity"
              >
                <Wifi className={`w-4 h-4 ${reconnecting ? "animate-pulse" : ""}`} />
                {reconnecting ? "Ligando..." : "Ligar Bot"}
              </button>
            )}

            <a
              href="https://discord.com/developers/applications/1427699671052320931/bot"
              target="_blank"
              rel="noopener noreferrer"
              data-testid="link-discord-portal"
              className="flex items-center gap-2 px-5 py-2.5 border border-indigo-700/40 text-indigo-400/70 hover:bg-indigo-900/20 transition-colors rounded-sm text-sm font-bold uppercase tracking-widest"
            >
              <ExternalLink className="w-4 h-4" />
              Developer Portal
            </a>
          </div>

          <AnimatePresence>
            {reconnectMsg && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mx-6 mb-6 flex items-center gap-2 text-yellow-400/80 text-sm bg-yellow-950/30 border border-yellow-900/40 px-4 py-2.5 rounded-sm"
              >
                <Activity className="w-4 h-4 shrink-0" />
                {reconnectMsg}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Info Card */}
        <div className="border border-yellow-900/20 bg-black/30 rounded-sm p-6">
          <h3 className="text-xs text-yellow-100/30 uppercase tracking-widest font-mono mb-4">Informações do Sistema</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-yellow-100/30">Prefixo</span>
                <code className="text-yellow-500 font-mono">tenshi,</code>
              </div>
              <div className="flex justify-between">
                <span className="text-yellow-100/30">Imperador</span>
                <span className="text-yellow-100/60 font-mono">Alloy Tenshi</span>
              </div>
              <div className="flex justify-between">
                <span className="text-yellow-100/30">Fundação</span>
                <span className="text-yellow-100/60 font-mono">06/06/2016</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-yellow-100/30">Motores IA</span>
                <span className="text-yellow-100/60 font-mono">7 (Groq)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-yellow-100/30">App ID</span>
                <code className="text-yellow-500/60 font-mono text-xs">1427699671052320931</code>
              </div>
              <div className="flex justify-between">
                <span className="text-yellow-100/30">Atualização</span>
                <span className="text-yellow-100/60 font-mono">a cada 15s</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminPage() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(ADMIN_TOKEN_KEY));

  function handleLogin(t: string) {
    setToken(t);
  }

  function handleLogout() {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    setToken(null);
  }

  if (!token) return <AdminLogin onLogin={handleLogin} />;
  return <AdminPanel token={token} onLogout={handleLogout} />;
}

// ── Router ────────────────────────────────────────────────────────────────────

function Router() {
  return (
    <Switch>
      <Route path="/" component={HomePage} />
      <Route path="/admin" component={AdminPage} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <Router />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
