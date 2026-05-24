import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { motion } from "framer-motion";
import { ArrowDown, ExternalLink, Shield, Cpu, Zap, ScrollText, Building, Home, Coins, Crown, Users, Droplets, Swords } from "lucide-react";
import NotFound from "@/pages/not-found";

const queryClient = new QueryClient();

const commands = [
  {
    category: "Identidade & Perfil",
    icon: <Users className="w-6 h-6" />,
    items: [
      { cmd: "status", desc: "Ver sua ficha" },
      { cmd: "ficha @user", desc: "Ver ficha de alguém" },
      { cmd: "pegada [tema]", desc: "Mudar tema (imperial/familia/mafia/enterprise)" },
      { cmd: "inventario", desc: "Ver itens" },
      { cmd: "conquistas", desc: "Ver badges" }
    ]
  },
  {
    category: "Jornada Imperial",
    icon: <ScrollText className="w-6 h-6" />,
    items: [
      { cmd: "treinar [ação]", desc: "Ganhar XP narrando" },
      { cmd: "missao", desc: "Missão narrativa com IA" },
      { cmd: "meditar", desc: "Regenerar energia" },
      { cmd: "descansar", desc: "Recuperar HP" },
      { cmd: "oraculo [pergunta]", desc: "Consultar oráculo" },
      { cmd: "clima", desc: "Ver clima do dia" }
    ]
  },
  {
    category: "Economia & Comércio",
    icon: <Coins className="w-6 h-6" />,
    items: [
      { cmd: "carteira", desc: "Ver saldo" },
      { cmd: "banco", desc: "Extrato" },
      { cmd: "depositar", desc: "Guardar fundos" },
      { cmd: "sacar", desc: "Retirar fundos" },
      { cmd: "transferir @user", desc: "Transferir dinheiro" },
      { cmd: "mercado", desc: "Loja de itens" },
      { cmd: "mercado-negro", desc: "Loja obscura" },
      { cmd: "trabalhar", desc: "Trabalho diário" },
      { cmd: "leilao [item]", desc: "Leiloar item" },
      { cmd: "emprestimo", desc: "Pegar empréstimo" },
      { cmd: "pagar-divida", desc: "Pagar empréstimo" },
      { cmd: "historico", desc: "Histórico financeiro" }
    ]
  },
  {
    category: "Propriedades & Condomínio",
    icon: <Home className="w-6 h-6" />,
    items: [
      { cmd: "casas", desc: "Mercado imobiliário" },
      { cmd: "minha-casa", desc: "Sua residência" },
      { cmd: "vender-casa", desc: "Vender residência" },
      { cmd: "portaria", desc: "Condomínio" },
      { cmd: "residencia", desc: "Acessar residência" },
      { cmd: "convidar @user", desc: "Convidar para casa" },
      { cmd: "expulsar @user", desc: "Expulsar da casa" },
      { cmd: "devolver-casa", desc: "Desistir da casa" },
      { cmd: "moradores", desc: "Ver moradores" },
      { cmd: "relaxar", desc: "Recuperar na casa" },
      { cmd: "fofoca", desc: "Crônica do condomínio" }
    ]
  },
  {
    category: "Tenshi Enterprise",
    icon: <Building className="w-6 h-6" />,
    items: [
      { cmd: "empresa criar", desc: "Fundar empresa" },
      { cmd: "empresa info", desc: "Detalhes da empresa" },
      { cmd: "empresa contratar/demitir", desc: "Gestão de RH" },
      { cmd: "empresa funcionarios", desc: "Ver quadro" },
      { cmd: "empresa pagar", desc: "Pagar salários" }
    ]
  },
  {
    category: "Família & Máfia",
    icon: <Droplets className="w-6 h-6" />,
    items: [
      { cmd: "familia criar", desc: "Fundar família/máfia" },
      { cmd: "familia entrar", desc: "Juntar-se" },
      { cmd: "familia info", desc: "Detalhes" },
      { cmd: "familia membros", desc: "Lista de membros" },
      { cmd: "familia missao", desc: "Missão em grupo" },
      { cmd: "familia depositar", desc: "Cofre da família" }
    ]
  },
  {
    category: "Facções",
    icon: <Shield className="w-6 h-6" />,
    items: [
      { cmd: "entrar [facção]", desc: "Alistar-se" },
      { cmd: "ranking", desc: "Ranking de facções" }
    ]
  },
  {
    category: "Místico",
    icon: <Zap className="w-6 h-6" />,
    items: [
      { cmd: "tarot", desc: "Tirar cartas" },
      { cmd: "runa", desc: "Ler runas" },
      { cmd: "astros", desc: "Horóscopo" },
      { cmd: "destino @user", desc: "Ler destino" },
      { cmd: "sacrificio", desc: "Oferenda mística" },
      { cmd: "ritual-protecao", desc: "Ritual" }
    ]
  },
  {
    category: "Combate Narrativo",
    icon: <Swords className="w-6 h-6" />,
    items: [
      { cmd: "duelo @user", desc: "Duelo com apostas" },
      { cmd: "aceitar-duelo", desc: "Aceitar desafio" },
      { cmd: "invocar-chefe [criatura]", desc: "Admin: Boss" },
      { cmd: "apostar [valor] @user", desc: "Apostar em duelo" },
      { cmd: "dado [d6/d20]", desc: "Rolar dados" }
    ]
  },
  {
    category: "LoreMaster IA",
    icon: <ScrollText className="w-6 h-6" />,
    items: [
      { cmd: "cronica [tipo]", desc: "Gerar crônica (militar/politico/esoterico/mafia/enterprise)" },
      { cmd: "evento-lore", desc: "Profecia" },
      { cmd: "falar [NPC]", desc: "Conversar com NPC via IA" },
      { cmd: "lore-historico", desc: "Crônicas antigas" },
      { cmd: "quadro-avisos", desc: "Missões diárias" }
    ]
  },
  {
    category: "Moderação Imperial",
    icon: <Crown className="w-6 h-6" />,
    items: [
      { cmd: "julgamento @user", desc: "Tribunal" },
      { cmd: "masmorra-prender @user [tempo]", desc: "Prisão" },
      { cmd: "exilar @user", desc: "Banimento narrativo" },
      { cmd: "anistia-real", desc: "Perdão" },
      { cmd: "decreto [msg]", desc: "Anúncio oficial" },
      { cmd: "promover @user [cargo]", desc: "Conceder título" },
      { cmd: "punir-audacia @user", desc: "Punição leve" },
      { cmd: "clear [n]", desc: "Limpar mensagens" },
      { cmd: "ban", desc: "Banir usuário" },
      { cmd: "kick", desc: "Expulsar usuário" },
      { cmd: "mute", desc: "Silenciar usuário" }
    ]
  },
  {
    category: "Utilitários",
    icon: <Cpu className="w-6 h-6" />,
    items: [
      { cmd: "top", desc: "Ranking global" },
      { cmd: "servidor", desc: "Info do servidor" },
      { cmd: "ping", desc: "Latência" },
      { cmd: "backup", desc: "Dados" },
      { cmd: "ajuda", desc: "Ajuda geral" },
      { cmd: "status-ia", desc: "Status dos motores" }
    ]
  }
];

function HomePage() {
  const scrollToCommands = () => {
    document.getElementById('comandos')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-primary selection:text-primary-foreground font-sans">
      <div className="fixed inset-0 pointer-events-none z-0 imperial-gradient opacity-80" />
      <div 
        className="fixed inset-0 pointer-events-none z-0 opacity-40 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/hero-bg.png)' }}
      />
      <div className="fixed inset-0 pointer-events-none z-0 bg-[url('https://www.transparenttextures.com/patterns/black-paper.png')] opacity-20" />
      
      {/* Hero Section */}
      <section className="relative z-10 min-h-[100dvh] flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 overflow-hidden">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="text-center max-w-4xl mx-auto space-y-8"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 1 }}
            className="flex justify-center mb-6"
          >
            <Crown className="w-20 h-20 text-primary opacity-80" />
          </motion.div>
          
          <h1 className="text-5xl md:text-7xl font-black font-serif tracking-wider uppercase drop-shadow-2xl">
            <span className="gold-text-gradient">⚜️ Bot Tenshi</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground font-light max-w-2xl mx-auto tracking-wide leading-relaxed">
            O Bot RPG Oficial do Império de Tenshi. Forje seu destino em um mundo de política, economia, máfia e misticismo.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 pt-8">
            <a
              href="https://discord.com/oauth2/authorize?client_id=1427699671052320931&permissions=8&scope=bot"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative inline-flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground font-bold uppercase tracking-widest text-sm transition-all hover:scale-105 hover:shadow-[0_0_30px_rgba(234,179,8,0.3)] rounded-sm overflow-hidden"
              data-testid="button-invite"
            >
              <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
              <ExternalLink className="w-5 h-5 relative z-10" />
              <span className="relative z-10">Adicionar ao Discord</span>
            </a>
            
            <button
              onClick={scrollToCommands}
              className="group inline-flex items-center gap-2 px-8 py-4 bg-transparent border-2 border-primary/30 text-primary font-bold uppercase tracking-widest text-sm transition-all hover:bg-primary/10 hover:border-primary rounded-sm"
              data-testid="button-commands"
            >
              <ArrowDown className="w-5 h-5 group-hover:translate-y-1 transition-transform" />
              <span>Ver Comandos</span>
            </button>
          </div>
        </motion.div>
      </section>

      {/* AI Features Section */}
      <section className="relative z-10 py-24 bg-card/50 border-y border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-5xl font-serif font-bold text-foreground mb-4">Inteligência Imperial</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">Potencializado por 7 motores de IA via Groq para uma narrativa sem precedentes.</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {['Narrativa', 'Rápida', 'Analítica', 'Relatório', 'Soberana', 'Economia', 'NPCs'].map((ai, i) => (
              <motion.div
                key={ai}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="p-6 bg-background/50 border border-primary/20 rounded-sm hover:border-primary/50 transition-colors"
              >
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Cpu className="w-5 h-5 text-primary" />
                </div>
                <h3 className="text-xl font-bold font-serif mb-2">Motor {ai}</h3>
                <p className="text-sm text-muted-foreground">Sistema especializado em processamento focado para o ambiente de RPG do Império.</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Commands Section */}
      <section id="comandos" className="relative z-10 py-24 scroll-mt-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-6xl font-serif font-bold text-foreground mb-4">Tomo de Comandos</h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">O compêndio sagrado de ações disponíveis para os cidadãos do Império.</p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {commands.map((cat, idx) => (
              <motion.div
                key={cat.category}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ delay: (idx % 3) * 0.1 }}
                className="bg-card/30 border border-border backdrop-blur-sm p-6 rounded-sm hover:bg-card/50 transition-colors"
              >
                <div className="flex items-center gap-3 mb-6 border-b border-border/50 pb-4">
                  <div className="text-primary">{cat.icon}</div>
                  <h3 className="text-xl font-bold font-serif text-foreground/90">{cat.category}</h3>
                </div>
                <ul className="space-y-4">
                  {cat.items.map(item => (
                    <li key={item.cmd} className="flex flex-col gap-1">
                      <code className="text-primary font-mono text-sm font-semibold tracking-wide">/{item.cmd}</code>
                      <span className="text-sm text-muted-foreground leading-snug">{item.desc}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border/50 bg-background py-12 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4 text-muted-foreground text-sm font-mono">
            <span>Prefixo: <code className="text-primary bg-primary/10 px-2 py-1 rounded">/</code></span>
          </div>
          <div className="text-muted-foreground text-sm text-center">
            © 2016–2026 Império de Tenshi
          </div>
          <div className="text-muted-foreground text-sm font-serif italic text-right flex items-center gap-2">
            Desenvolvido por Alloy, Imperador da Tenshi <Crown className="w-4 h-4 text-primary" />
          </div>
        </div>
      </footer>
    </div>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={HomePage} />
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