import { useState, useEffect, useCallback, useRef } from "react";
import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { motion, AnimatePresence } from "framer-motion";
import {
  ExternalLink, Search, ChevronRight, Copy, Check,
  Lock, LogOut, RefreshCw, WifiOff, Server, Activity,
  Eye, EyeOff, AlertTriangle, CheckCircle2, Settings,
  ArrowLeft, Wifi, Zap, Shield, Brain, BarChart3,
  Users, MessageSquare, Sparkles, Terminal, Globe,
  Building2, Crown,
} from "lucide-react";
import NotFound from "@/pages/not-found";

const queryClient = new QueryClient();
const PREFIX = "tenshi,";

// ── Data ──────────────────────────────────────────────────────────────────────

const features = [
  { icon: Brain, label: "IA Narrativa", desc: "7 modelos Groq roteados por contexto — desde crônicas épicas até triagem jurídica em tempo real." },
  { icon: BarChart3, label: "Economia Completa", desc: "Banco, mercado, ações, imóveis, empréstimos, lavagem de dinheiro e câmbio imperial." },
  { icon: Shield, label: "Moderação Inteligente", desc: "IA monitora canais públicos e aplica advertências automaticamente, sem intervenção humana." },
  { icon: Users, label: "RPG Social", desc: "Famílias, máfias, facções, casamentos, duelos e eventos coletivos que conectam toda a comunidade." },
  { icon: Building2, label: "Infraestrutura", desc: "Condomínio, garagem, academia, empresa, geopolítica e sistema de eras históricas." },
  { icon: Sparkles, label: "Automações", desc: "O servidor vive sem comandos. Eventos, clima, crônicas e interações geradas automaticamente." },
];

const automacoes = [
  { emoji: "🔍", name: "Triagem Jurídica", desc: "Monitora canais públicos (geral, beco, cassino, praça) com IA e aplica advertências automáticas por toxicidade, spam ou comportamento proibido." },
  { emoji: "📜", name: "LoreMaster Natural", desc: "Responde mensagens no geral e praça com narrativa do Império gerada por IA, mantendo a ambientação RPG ativa 24/7 sem comandos." },
  { emoji: "🍺", name: "Embriaguez Dinâmica", desc: "Após `tenshi, beber`, as mensagens do usuário no geral são distorcidas automaticamente pela IA pelo tempo correspondente à bebida." },
  { emoji: "🧠", name: "Psicologia Estratégica", desc: "Em canais com `psicologia-estrategia` no nome, o bot responde automaticamente a toda mensagem com análise de conselheiro imperial via IA." },
  { emoji: "⚔️", name: "Invasões & Boss Events", desc: "Eventos gerados pela IA onde criaturas atacam o servidor. Membros cooperam para derrotá-las com ações narrativas em tempo real." },
  { emoji: "🌦️", name: "Clima Dinâmico Diário", desc: "Gera clima narrativo diário com efeitos reais em mecânicas de RPG: energia, HP, produtividade e colheitas de recursos." },
  { emoji: "📰", name: "Crônicas do Cotidiano", desc: "Registra atividades dos canais públicos e gera crônicas periódicas narrando os acontecimentos do servidor como pergaminhos históricos." },
  { emoji: "👑", name: "Protocolo Imperial", desc: "Reconhece a chegada do Imperador em qualquer canal com uma saudação solene automática — uma cerimônia discreta a cada nova sessão." },
];

const aiMotors = [
  { name: "Narrativa", model: "LLaMA 4 Maverick", use: "Missões, crônicas épicas, roleplay" },
  { name: "Rápida", model: "LLaMA 4 Scout", use: "Respostas instantâneas, triagem" },
  { name: "Analítica", model: "LLaMA 3.3 70B", use: "Jurídico, estratégia, análise" },
  { name: "Relatório", model: "Mixtral 8x7B", use: "Auditorias, RH, relatórios" },
  { name: "Soberana", model: "LLaMA 4 Maverick", use: "Geopolítica, decretos, soberania" },
  { name: "Economia", model: "LLaMA 4 Scout", use: "Transações, cálculos, finanças" },
  { name: "NPCs", model: "Gemma 2 9B", use: "Personagens, clima, curtos" },
];

const commands = [
  {
    category: "Identidade & Perfil", tag: "perfil",
    items: [
      { cmd: "status", desc: "Ficha completa — nível, XP, HP, energia, moedas e facção." },
      { cmd: "ficha", desc: "Cria ou edita sua ficha de personagem RP." },
      { cmd: "criar-ficha", desc: "Registra seu personagem pela primeira vez." },
      { cmd: "pegada [tema]", desc: "Muda o tema visual: imperial · familia · mafia · enterprise." },
      { cmd: "inventario", desc: "Lista itens e equipamentos no inventário." },
      { cmd: "conquistas", desc: "Badges e marcos conquistados no Império." },
      { cmd: "especies", desc: "Espécies e raças disponíveis para personagens." },
      { cmd: "viajar [local]", desc: "Move seu personagem para outro local do mapa." },
      { cmd: "local", desc: "Localização atual no mapa do Império." },
      { cmd: "poderes", desc: "Árvore de poderes disponíveis para sua espécie." },
      { cmd: "meus-poderes", desc: "Poderes já desbloqueados." },
    ],
  },
  {
    category: "Jornada Imperial", tag: "jornada",
    items: [
      { cmd: "treinar [ação]", desc: "Ganha XP narrando uma ação — a IA avalia e recompensa." },
      { cmd: "missao", desc: "Missão narrativa gerada por IA. Cooldown 1h." },
      { cmd: "meditar", desc: "Recupera energia espiritual." },
      { cmd: "descansar", desc: "Recupera HP em área segura." },
      { cmd: "interagir [ação]", desc: "Ação de roleplay em texto narrativo." },
      { cmd: "dado [tipo]", desc: "Rola dados: d4, d6, d10, d20, d100." },
      { cmd: "profissao [classe]", desc: "Define ou muda sua profissão." },
      { cmd: "clima", desc: "Clima do dia com efeitos nas mecânicas de RPG." },
      { cmd: "oraculo [pergunta]", desc: "O Oráculo Imperial responde via IA." },
    ],
  },
  {
    category: "LoreMaster IA", tag: "lore",
    items: [
      { cmd: "cronica [tipo]", desc: "Crônica épica: militar · politico · esoterico · mafia · enterprise." },
      { cmd: "evento-lore", desc: "Profecia ou evento lendário gerado por IA." },
      { cmd: "falar [NPC]", desc: "Conversa em tempo real com um NPC via IA." },
      { cmd: "lore-historico", desc: "Crônicas e registros históricos do Império." },
      { cmd: "quadro-avisos", desc: "Missões diárias e avisos imperiais." },
    ],
  },
  {
    category: "Místico", tag: "mistico",
    items: [
      { cmd: "tarot", desc: "O Oráculo tira cartas de tarô e interpreta via IA." },
      { cmd: "runa", desc: "Consulta runas ancestrais para guia espiritual." },
      { cmd: "astros", desc: "Horóscopo imperial gerado por IA." },
      { cmd: "destino @user", desc: "Lê o destino de outro cidadão via IA." },
      { cmd: "sacrificio [item]", desc: "Oferenda mística em troca de bênçãos ou maldições." },
      { cmd: "ritual-protecao", desc: "Imunidade narrativa temporária." },
    ],
  },
  {
    category: "Combate Narrativo", tag: "combate",
    items: [
      { cmd: "duelo @user", desc: "Desafia para duelo com apostas opcionais." },
      { cmd: "aceitar-duelo", desc: "Aceita desafio de duelo pendente." },
      { cmd: "basquete @user", desc: "Partida de basquete narrativo." },
      { cmd: "futebol @user", desc: "Partida de futebol narrativo." },
      { cmd: "invocar-chefe [criatura]", desc: "Admin: Invoca boss para o servidor enfrentar.", admin: true },
      { cmd: "invasao", desc: "Admin: Inicia invasão de criaturas.", admin: true },
    ],
  },
  {
    category: "Economia & Comércio", tag: "economia",
    items: [
      { cmd: "carteira", desc: "Saldo de Moedas Imperiais." },
      { cmd: "mercado", desc: "Loja oficial com itens e equipamentos." },
      { cmd: "mercado-negro", desc: "Mercado clandestino com itens raros e ilegais." },
      { cmd: "comprar [item]", desc: "Compra item no mercado ativo." },
      { cmd: "leilao [item]", desc: "Lança item em leilão para outros comprarem." },
      { cmd: "sorteio-real", desc: "Sorteio imperial com prêmios em moedas." },
      { cmd: "trabalhar", desc: "Trabalho diário no emprego para ganhar moedas." },
      { cmd: "emprego", desc: "Empregos disponíveis e emprego atual." },
    ],
  },
  {
    category: "Banco & Finanças", tag: "financas",
    items: [
      { cmd: "banco", desc: "Extrato bancário e histórico de transações." },
      { cmd: "depositar [valor]", desc: "Deposita moedas no banco imperial." },
      { cmd: "sacar [valor]", desc: "Saca moedas do banco." },
      { cmd: "transferir @user [valor]", desc: "Transfere moedas via PIX Imperial." },
      { cmd: "emprestimo [valor]", desc: "Empréstimo bancário com juros." },
      { cmd: "pagar-divida", desc: "Quita empréstimo ativo." },
      { cmd: "historico", desc: "Histórico financeiro completo." },
      { cmd: "poupanca [valor]", desc: "Investe em conta poupança com rendimentos." },
      { cmd: "comprar-acoes [valor]", desc: "Compra ações no mercado de capitais." },
      { cmd: "seguro-vida", desc: "Contrata seguro de vida estatal." },
      { cmd: "aposentar", desc: "Solicita aposentadoria e fundo de pensão." },
      { cmd: "lavar [valor]", desc: "Lavagem de dinheiro no beco — risco elevado." },
    ],
  },
  {
    category: "Propriedades & Condomínio", tag: "casas",
    items: [
      { cmd: "casas", desc: "Mercado imobiliário com casas disponíveis." },
      { cmd: "minha-casa", desc: "Detalhes da sua residência atual." },
      { cmd: "vender-casa", desc: "Coloca residência à venda." },
      { cmd: "portaria", desc: "Sistema de condomínio." },
      { cmd: "residencia", desc: "Entra em sua residência do condomínio." },
      { cmd: "convidar @user", desc: "Convida usuário para morar na residência." },
      { cmd: "expulsar @user", desc: "Expulsa morador da residência." },
      { cmd: "devolver-casa", desc: "Sai do condomínio." },
      { cmd: "moradores", desc: "Lista moradores da residência." },
      { cmd: "relaxar", desc: "Descansa em casa com bônus de regeneração." },
      { cmd: "fofoca", desc: "Crônica dos acontecimentos do condomínio via IA." },
      { cmd: "trancar-casa", desc: "Tranca residência para visitantes." },
      { cmd: "destrancar-casa", desc: "Abre residência para visitantes." },
      { cmd: "titulo-propriedade", desc: "Escritura oficial da propriedade." },
      { cmd: "alugar-comercio", desc: "Aluga espaço comercial no Império." },
    ],
  },
  {
    category: "Garagem, Esportes & Pets", tag: "extras",
    items: [
      { cmd: "garagem", desc: "Veículos registrados e seus status." },
      { cmd: "vender-veiculo", desc: "Coloca veículo à venda." },
      { cmd: "abastecer [valor]", desc: "Abastece veículo com combustível." },
      { cmd: "pool-party", desc: "Admin: Inicia Pool Party com bônus para todos.", admin: true },
      { cmd: "pet-shop", desc: "Loja de pets — adquira seu companheiro." },
      { cmd: "meu-pet", desc: "Informações do pet atual." },
      { cmd: "vender-pet", desc: "Vende pet no mercado." },
    ],
  },
  {
    category: "Social & Cotidiano", tag: "social",
    items: [
      { cmd: "casar @user", desc: "Propõe casamento a outro cidadão." },
      { cmd: "divorcio", desc: "Encerra casamento com processo oficial." },
      { cmd: "lavanderia", desc: "Lava itens restaurando condição." },
      { cmd: "sintetizar [item]", desc: "Fabrica item combinando materiais." },
      { cmd: "cartaz [filme]", desc: "Agenda ou exibe cartaz do cinema do condomínio." },
      { cmd: "psicologo [texto]", desc: "Desabafa com o psicólogo imperial — IA responde." },
      { cmd: "beber [bebida]", desc: "Bebe no bar — efeito de embriaguez narrativo." },
      { cmd: "jornal-cotidiano", desc: "Jornal diário com manchetes geradas por IA." },
      { cmd: "correio", desc: "Sistema de correio anônimo imperial." },
      { cmd: "estacoes", desc: "Estação atual e seus efeitos no RPG." },
      { cmd: "entrevista [cargo]", desc: "Entrevista de emprego narrativa." },
      { cmd: "socorrer @user", desc: "Socorro médico de emergência a outro cidadão." },
      { cmd: "vdd", desc: "Verdade ou Desafio com perguntas e desafios via IA." },
    ],
  },
  {
    category: "Crime & Inteligência", tag: "crime",
    items: [
      { cmd: "assaltar @user", desc: "Tenta assaltar cidadão no beco — risco de cadeia." },
      { cmd: "mercado-negro-beco", desc: "Mercado clandestino do beco com itens proibidos." },
      { cmd: "subornar-porteiro @user", desc: "Suborna porteiro para espionar residência." },
      { cmd: "grampear-call", desc: "Grampo narrativo em call ativa via IA." },
      { cmd: "iniciar-festa [local]", desc: "Organiza festa com efeitos narrativos." },
      { cmd: "registrar-perola [msg]", desc: "Salva momento memorável nos registros." },
    ],
  },
  {
    category: "Jurídico & Clero", tag: "juridico",
    items: [
      { cmd: "ficha-criminal @user", desc: "Ficha criminal completa de um cidadão." },
      { cmd: "warn @user", desc: "Advertência oficial.", admin: true },
      { cmd: "perdoar-aviso @user", desc: "Remove advertência do histórico.", admin: true },
      { cmd: "mandado @user", desc: "Mandado de busca e apreensão.", admin: true },
      { cmd: "pagar-fianca", desc: "Paga fiança para sair da masmorra." },
      { cmd: "imunidade-diplomatica", desc: "Imunidade diplomática temporária." },
      { cmd: "padre [rito]", desc: "Rito clerical: batismo, casamento, enterro." },
      { cmd: "sindicancia @user", desc: "Abre sindicância investigativa." },
      { cmd: "laudo-medico", desc: "Laudo médico oficial." },
      { cmd: "desintoxicacao", desc: "Processo de desintoxicação de status negativos." },
      { cmd: "doacao-sangue", desc: "Doa sangue — karma e cura parcial." },
      { cmd: "diagnostico-ia", desc: "Diagnóstico médico completo via IA." },
    ],
  },
  {
    category: "Geopolítica & Estado", tag: "geopolitica",
    items: [
      { cmd: "dominar [canal]", desc: "Tenta dominar canal para sua facção." },
      { cmd: "territorio", desc: "Mapa de domínio territorial das facções." },
      { cmd: "rebeliao", desc: "Inicia rebelião contra o poder dominante." },
      { cmd: "visto", desc: "Painel de vistos e imigração." },
      { cmd: "cidadania", desc: "Certidão de cidadania imperial." },
      { cmd: "set-era [nome]", desc: "Define a era histórica atual.", admin: true },
      { cmd: "era", desc: "Era histórica atual com efeitos no RPG." },
      { cmd: "decreto-marcial [ação]", desc: "Decreta lei marcial com restrições automáticas.", admin: true },
      { cmd: "aconselhar-estrategia [sit.]", desc: "Conselheiro imperial analisa e sugere estratégia via IA." },
    ],
  },
  {
    category: "Infraestrutura Crítica", tag: "infra",
    items: [
      { cmd: "status-energia", desc: "Status da rede elétrica imperial." },
      { cmd: "inflacao", desc: "Índice de inflação da economia imperial." },
      { cmd: "checar-cameras", desc: "Câmeras de segurança de um local." },
      { cmd: "biometria", desc: "Dados biométricos e DNA." },
      { cmd: "rastrear-perfil @user", desc: "OSINT — rastreia perfil e atividades." },
      { cmd: "enviar-carga [tipo]", desc: "Despacha carga logística." },
      { cmd: "historico-imovel", desc: "Histórico de transações de imóvel." },
      { cmd: "auditoria-bancaria", desc: "Audita banco de cidadão suspeito.", admin: true },
    ],
  },
  {
    category: "Tenshi Academy", tag: "academia",
    items: [
      { cmd: "matricular [materia]", desc: "Matricula em matéria da Tenshi Academy." },
      { cmd: "trancar-matricula [mat.]", desc: "Tranca matrícula em matéria." },
      { cmd: "presenca [materia]", desc: "Registra presença em aula ativa." },
      { cmd: "iniciar-aula [materia]", desc: "Inicia aula com conteúdo via IA.", admin: true },
      { cmd: "ler-apostila [materia]", desc: "Acessa apostila digital da matéria via IA." },
      { cmd: "prestar-exame [materia]", desc: "Exame final enviado por DM via IA." },
      { cmd: "historico-escolar", desc: "Histórico acadêmico com notas e aprovações." },
      { cmd: "segunda-via-diploma", desc: "Segunda via de diploma já obtido." },
      { cmd: "entrar-clube [nome]", desc: "Filia-se a clube extracurricular." },
      { cmd: "cofre-clube", desc: "Finanças do clube que você participa." },
    ],
  },
  {
    category: "Empresa", tag: "empresa",
    items: [
      { cmd: "empresa criar [nome]", desc: "Funda empresa no Império." },
      { cmd: "empresa info", desc: "Capital, funcionários e status da empresa." },
      { cmd: "empresa contratar @user", desc: "Contrata funcionário." },
      { cmd: "empresa demitir @user", desc: "Demite funcionário." },
      { cmd: "empresa funcionarios", desc: "Quadro de funcionários." },
      { cmd: "empresa pagar", desc: "Paga salários automaticamente." },
    ],
  },
  {
    category: "Família, Máfia & Facções", tag: "familia",
    items: [
      { cmd: "familia criar [nome]", desc: "Funda família ou clã." },
      { cmd: "familia entrar [nome]", desc: "Junta-se a família existente." },
      { cmd: "familia info", desc: "Informações da família." },
      { cmd: "familia membros", desc: "Membros com seus cargos." },
      { cmd: "familia missao", desc: "Missão em grupo para a família." },
      { cmd: "familia depositar [v]", desc: "Deposita no cofre da família." },
      { cmd: "entrar [facção]", desc: "Alista-se em uma facção." },
      { cmd: "ranking", desc: "Ranking de poder entre facções." },
    ],
  },
  {
    category: "Moderação Imperial", tag: "moderacao", admin: true,
    items: [
      { cmd: "decreto [msg]", desc: "Decreto oficial do Império.", admin: true },
      { cmd: "promover @user [cargo]", desc: "Título ou cargo imperial.", admin: true },
      { cmd: "julgamento @user", desc: "Tribunal para julgamento.", admin: true },
      { cmd: "masmorra-prender @user [min]", desc: "Prende na masmorra por X minutos.", admin: true },
      { cmd: "exilar @user", desc: "Exila narrativamente do Império.", admin: true },
      { cmd: "anistia-real", desc: "Perdão geral a presos e exilados.", admin: true },
      { cmd: "punir-audacia @user", desc: "Punição leve por comportamento inadequado.", admin: true },
      { cmd: "trancar-portoes", desc: "Lockdown — restringe ações.", admin: true },
      { cmd: "tesouro [valor]", desc: "Adiciona moedas ao tesouro público.", admin: true },
      { cmd: "ban @user", desc: "Bane do servidor Discord.", admin: true },
      { cmd: "kick @user", desc: "Expulsa do servidor Discord.", admin: true },
      { cmd: "mute @user [min]", desc: "Silencia por X minutos.", admin: true },
      { cmd: "clear [n]", desc: "Apaga N mensagens do canal.", admin: true },
    ],
  },
  {
    category: "Prerrogativas Soberanas", tag: "soberano", admin: true,
    items: [
      { cmd: "emitir-moeda [v]", desc: "Emite moedas novas na economia.", admin: true },
      { cmd: "confiscar-fortuna @user", desc: "Confisca toda a fortuna.", admin: true },
      { cmd: "congelar-banco @user", desc: "Congela acesso bancário.", admin: true },
      { cmd: "perdoar-divida @user", desc: "Perdoa dívida bancária.", admin: true },
      { cmd: "set-status @user", desc: "Define qualquer atributo diretamente.", admin: true },
      { cmd: "apagar-ficha @user", desc: "Apaga permanentemente ficha.", admin: true },
      { cmd: "conceder-item @user [item]", desc: "Concede item ao inventário.", admin: true },
      { cmd: "imortalidade @user", desc: "Concede ou remove imortalidade narrativa.", admin: true },
      { cmd: "estado-de-sitio [dur.]", desc: "Decreta estado de sítio.", admin: true },
      { cmd: "dissolver-mafia [nome]", desc: "Dissolve família compulsoriamente.", admin: true },
      { cmd: "anistia-geral", desc: "Perdoa todos os crimes do servidor.", admin: true },
      { cmd: "exilio-supremo @user", desc: "Exílio supremo permanente.", admin: true },
      { cmd: "atualizar-diretriz [texto]", desc: "Atualiza diretriz dos NPCs via IA.", admin: true },
      { cmd: "apagar-memoria-ia", desc: "Apaga histórico de memória da IA.", admin: true },
      { cmd: "forcar-cronica [tipo]", desc: "Força geração imediata de crônica.", admin: true },
      { cmd: "censo-imperial", desc: "Censo completo de cidadãos.", admin: true },
      { cmd: "reset-era [nome]", desc: "Reseta era histórica.", admin: true },
      { cmd: "irradiar [msg]", desc: "Transmissão nacional para todos os canais.", admin: true },
      { cmd: "congelar-economia", desc: "Paralisa transações econômicas.", admin: true },
      { cmd: "exportar-banco", desc: "Backup completo do banco de dados.", admin: true },
      { cmd: "desligar", desc: "Desliga o bot graciosamente.", admin: true },
    ],
  },
  {
    category: "Utilitários", tag: "util",
    items: [
      { cmd: "top", desc: "Ranking global por XP e riqueza." },
      { cmd: "servidor", desc: "Informações do servidor Discord." },
      { cmd: "ping", desc: "Latência do bot com o Discord." },
      { cmd: "backup", desc: "Cópia dos seus dados." },
      { cmd: "status-ia", desc: "Status dos 7 motores de IA." },
      { cmd: "aniversario", desc: "Aniversário de fundação do Império." },
      { cmd: "ajuda", desc: "Guia completo de todos os comandos." },
    ],
  },
];

const totalCmds = commands.reduce((a, c) => a + c.items.length, 0);

// ── Shared styles ─────────────────────────────────────────────────────────────
const S = {
  bg: "bg-[#08090a]",
  card: "bg-[#0e0f11] border border-[#1c1d21]",
  cardHover: "hover:border-[#2d2f36] hover:bg-[#111315]",
  text: "text-[#f0f0f2]",
  muted: "text-[#71717a]",
  accent: "text-violet-400",
  accentBg: "bg-violet-600",
  border: "border-[#1c1d21]",
};

// ── CopyButton ────────────────────────────────────────────────────────────────
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded text-[#4a4b52] hover:text-[#a0a0a8]"
    >
      {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
    </button>
  );
}

// ── HomePage ──────────────────────────────────────────────────────────────────
function HomePage() {
  const [search, setSearch] = useState("");
  const [activeTag, setActiveTag] = useState("all");
  const searchRef = useRef<HTMLInputElement>(null);

  const tags = [{ id: "all", label: "Todos" }, ...commands.map(c => ({ id: c.tag, label: c.category }))];

  const filtered = commands
    .filter(cat => activeTag === "all" || cat.tag === activeTag)
    .map(cat => ({
      ...cat,
      items: cat.items.filter(i =>
        !search.trim() ||
        i.cmd.toLowerCase().includes(search.toLowerCase()) ||
        i.desc.toLowerCase().includes(search.toLowerCase())
      ),
    }))
    .filter(cat => cat.items.length > 0);

  return (
    <div className={`min-h-screen ${S.bg} ${S.text} font-sans antialiased`}>

      {/* ── Nav ── */}
      <nav className={`sticky top-0 z-50 border-b ${S.border} bg-[#08090a]/90 backdrop-blur-md`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <img src="/tenshi-logo.png" alt="Tenshi" className="w-8 h-8 rounded object-cover opacity-90" />
            <span className="font-semibold text-sm tracking-tight">Bot Tenshi</span>
            <span className="text-[#3a3b42] text-xs font-mono hidden sm:block">v2.0</span>
          </div>
          <div className="flex items-center gap-3">
            <a href="/admin" className={`text-xs ${S.muted} hover:text-[#a0a0a8] transition-colors`}>Admin</a>
            <a
              href="https://discord.com/oauth2/authorize?client_id=1427699671052320931&permissions=8&scope=bot"
              target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold rounded-md transition-colors"
            >
              <ExternalLink className="w-3 h-3" /> Adicionar ao Discord
            </a>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-violet-950/20 via-transparent to-transparent pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-20%,rgba(109,40,217,0.15),transparent)] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-20 text-center relative z-10">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <img
              src="/tenshi-logo.png"
              alt="Império de Tenshi"
              className="w-24 h-24 mx-auto mb-8 object-contain opacity-95 drop-shadow-[0_0_40px_rgba(139,92,246,0.25)]"
            />
            <div className="inline-flex items-center gap-2 px-3 py-1 mb-8 text-xs font-medium text-violet-300 bg-violet-950/50 border border-violet-800/40 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
              Bot RPG para Discord · Império de Tenshi
            </div>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-none">
              <span className="text-[#f0f0f2]">Bot </span>
              <span className="bg-gradient-to-r from-violet-400 to-violet-300 bg-clip-text text-transparent">Tenshi</span>
            </h1>
            <p className="text-lg text-[#71717a] max-w-2xl mx-auto leading-relaxed mb-10">
              Sistema completo de RPG, economia, moderação e narração via IA para Discord.
              Gerencie um Império inteiro com mais de {totalCmds} comandos e 7 modelos de linguagem.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <a
                href="https://discord.com/oauth2/authorize?client_id=1427699671052320931&permissions=8&scope=bot"
                target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-500 text-white font-semibold rounded-lg transition-colors text-sm"
              >
                <ExternalLink className="w-4 h-4" /> Adicionar ao Discord
              </a>
              <a href="#comandos" className="inline-flex items-center gap-2 px-5 py-2.5 border border-[#2a2b31] hover:border-[#3a3b42] text-[#a0a0a8] font-semibold rounded-lg transition-colors text-sm">
                Ver Comandos
              </a>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.6 }}
            className="mt-16 grid grid-cols-3 gap-px max-w-lg mx-auto border border-[#1c1d21] rounded-xl overflow-hidden">
            {[
              { n: `${totalCmds}+`, label: "Comandos" },
              { n: "7", label: "Modelos de IA" },
              { n: "∞", label: "Automações" },
            ].map((s) => (
              <div key={s.label} className="bg-[#0e0f11] px-6 py-4">
                <div className="text-2xl font-bold text-violet-400">{s.n}</div>
                <div className="text-xs text-[#71717a] mt-0.5">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className={`border-t ${S.border} py-20`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-12">
            <h2 className="text-2xl font-bold tracking-tight mb-2">Funcionalidades</h2>
            <p className={S.muted + " text-sm"}>Um ecossistema completo para sua comunidade.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((f, i) => (
              <motion.div key={f.label} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }}
                className={`${S.card} ${S.cardHover} rounded-xl p-5 transition-colors`}>
                <f.icon className="w-5 h-5 text-violet-400 mb-3" />
                <h3 className="font-semibold text-sm mb-1.5">{f.label}</h3>
                <p className={`${S.muted} text-sm leading-relaxed`}>{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Automações ── */}
      <section className={`border-t ${S.border} py-20 bg-[#0a0b0d]`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-12">
            <div className="inline-flex items-center gap-2 text-xs font-medium text-green-400 bg-green-950/40 border border-green-900/40 px-3 py-1 rounded-full mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              Totalmente automático — sem comandos
            </div>
            <h2 className="text-2xl font-bold tracking-tight mb-2">IA gerencia sua comunidade</h2>
            <p className={S.muted + " text-sm max-w-xl"}>O servidor vive sozinho. Moderação, narração, clima e eventos acontecem sem nenhum comando dos usuários.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {automacoes.map((a, i) => (
              <motion.div key={a.name} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }}
                className={`${S.card} ${S.cardHover} rounded-xl p-5 transition-colors`}>
                <div className="text-xl mb-3">{a.emoji}</div>
                <h3 className="font-semibold text-sm mb-1.5 text-green-300">{a.name}</h3>
                <p className={`${S.muted} text-xs leading-relaxed`}>{a.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── AI Models ── */}
      <section className={`border-t ${S.border} py-20`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-12">
            <h2 className="text-2xl font-bold tracking-tight mb-2">7 Modelos de IA via Groq</h2>
            <p className={S.muted + " text-sm"}>Cada tarefa é roteada automaticamente para o modelo mais adequado.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {aiMotors.map((ai, i) => (
              <motion.div key={ai.name} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.04 }}
                className={`${S.card} rounded-xl p-4`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-violet-400 uppercase tracking-widest">{ai.name}</span>
                  <Brain className="w-3.5 h-3.5 text-[#3a3b42]" />
                </div>
                <p className="text-xs font-mono text-[#a0a0a8] mb-1">{ai.model}</p>
                <p className={`${S.muted} text-xs`}>{ai.use}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Commands ── */}
      <section id="comandos" className={`border-t ${S.border} py-20 bg-[#0a0b0d] scroll-mt-14`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h2 className="text-2xl font-bold tracking-tight mb-2">Referência de Comandos</h2>
            <p className={S.muted + " text-sm"}>
              {totalCmds} comandos · prefixo <code className="text-violet-400 bg-violet-950/40 px-1.5 py-0.5 rounded text-xs font-mono">tenshi,</code>
            </p>
          </div>

          {/* Search */}
          <div className="flex flex-col sm:flex-row gap-3 mb-8">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#3a3b42]" />
              <input
                ref={searchRef}
                type="text"
                value={search}
                onChange={e => { setSearch(e.target.value); setActiveTag("all"); }}
                placeholder="Pesquisar comando..."
                className="w-full pl-9 pr-4 py-2 bg-[#0e0f11] border border-[#1c1d21] focus:border-violet-600/60 rounded-lg text-sm text-[#f0f0f2] placeholder-[#3a3b42] outline-none transition-colors"
              />
            </div>
            {search && (
              <button onClick={() => setSearch("")} className={`text-xs ${S.muted} hover:text-[#a0a0a8] transition-colors`}>Limpar</button>
            )}
          </div>

          {/* Category pills */}
          {!search && (
            <div className="flex gap-2 flex-wrap mb-6">
              {tags.map(t => (
                <button key={t.id} onClick={() => setActiveTag(t.id)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors border ${
                    activeTag === t.id
                      ? "bg-violet-600 border-violet-500 text-white"
                      : "border-[#1c1d21] text-[#71717a] hover:border-[#2d2f36] hover:text-[#a0a0a8]"
                  }`}>
                  {t.label}
                </button>
              ))}
            </div>
          )}

          {/* Command grid */}
          <div className="space-y-6">
            {filtered.map((cat) => (
              <motion.div key={cat.category} initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true, margin: "-20px" }}>
                <div className="flex items-center gap-3 mb-3">
                  <h3 className="text-sm font-semibold text-[#c0c0c8]">{cat.category}</h3>
                  {(cat as any).admin && <span className="text-xs px-2 py-0.5 bg-amber-950/40 text-amber-500 border border-amber-900/40 rounded font-mono">admin</span>}
                  <span className="text-xs text-[#3a3b42]">{cat.items.length}</span>
                </div>
                <div className={`${S.card} rounded-xl overflow-hidden divide-y divide-[#1c1d21]`}>
                  {cat.items.map((item) => (
                    <div key={item.cmd} className="flex items-center justify-between px-4 py-3 group hover:bg-[#111315] transition-colors">
                      <div className="flex items-center gap-3 min-w-0">
                        <code className="text-violet-400 font-mono text-xs shrink-0">tenshi, {item.cmd}</code>
                        {(item as any).admin && <span className="text-xs text-amber-600/60 shrink-0">🔒</span>}
                        <span className="text-[#71717a] text-xs truncate hidden sm:block">{item.desc}</span>
                      </div>
                      <CopyButton text={`tenshi, ${item.cmd}`} />
                    </div>
                  ))}
                </div>
                {/* mobile desc */}
                <div className="sm:hidden mt-1 space-y-1 pl-1">
                  {cat.items.map(item => (
                    <p key={item.cmd + "-d"} className="text-xs text-[#4a4b52] leading-relaxed">
                      <span className="text-violet-500/60 font-mono">{item.cmd}</span> — {item.desc}
                    </p>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>

          {filtered.length === 0 && (
            <div className="text-center py-24">
              <p className="text-[#3a3b42] text-sm">Nenhum comando encontrado para "{search}"</p>
            </div>
          )}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className={`border-t ${S.border} py-10`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <img src="/tenshi-logo.png" alt="Tenshi" className="w-6 h-6 object-contain opacity-80" />
            <span className="text-sm font-semibold">Bot Tenshi</span>
          </div>
          <p className="text-xs text-[#3a3b42]">© 2016–2026 Império de Tenshi · Desenvolvido por Alloy Tenshi</p>
          <div className="flex items-center gap-4">
            <span className="text-xs text-[#3a3b42]">Prefixo: <code className="text-violet-500/60">tenshi,</code></span>
            <a href="/admin" className="text-xs text-[#3a3b42] hover:text-[#71717a] transition-colors">Admin</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── Admin Login ───────────────────────────────────────────────────────────────
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
        setError("Credenciais inválidas.");
      }
    } catch {
      setError("Erro de conexão com o servidor.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`min-h-screen ${S.bg} ${S.text} font-sans antialiased flex items-center justify-center px-4`}>
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 mb-8">
          <img src="/tenshi-logo.png" alt="Tenshi" className="w-7 h-7 object-contain opacity-90" />
          <span className="font-semibold text-sm">Bot Tenshi</span>
        </div>
        <h1 className="text-xl font-bold mb-1">Painel do Criador</h1>
        <p className={`${S.muted} text-sm mb-8`}>Acesso restrito — Alloy, Imperador de Tenshi</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-[#71717a] mb-1.5">Usuário</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)}
              className={`w-full px-3 py-2 ${S.card} rounded-lg text-sm outline-none focus:border-violet-600/60 transition-colors`}
              placeholder="usuário" required />
          </div>
          <div>
            <label className="block text-xs text-[#71717a] mb-1.5">Senha</label>
            <div className="relative">
              <input type={showPass ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)}
                className={`w-full px-3 py-2 pr-10 ${S.card} rounded-lg text-sm outline-none focus:border-violet-600/60 transition-colors`}
                placeholder="••••••••" required />
              <button type="button" onClick={() => setShowPass(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#3a3b42] hover:text-[#71717a]">
                {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <AnimatePresence>
            {error && (
              <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}
                className="flex items-center gap-2 text-red-400 text-xs">
                <AlertTriangle className="w-3 h-3" />{error}
              </motion.p>
            )}
          </AnimatePresence>
          <button type="submit" disabled={loading}
            className="w-full py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition-colors">
            {loading ? "Verificando..." : "Entrar"}
          </button>
        </form>
        <div className="mt-6 text-center">
          <a href="/" className="text-xs text-[#3a3b42] hover:text-[#71717a] transition-colors flex items-center justify-center gap-1">
            <ArrowLeft className="w-3 h-3" /> Voltar ao site
          </a>
        </div>
      </div>
    </div>
  );
}

// ── Admin Panel ───────────────────────────────────────────────────────────────
interface BotStatus { online: boolean; guilds: number; latency: number; user: string | null; }

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
    } catch { setBotStatus({ online: false, guilds: 0, latency: 0, user: null }); }
    finally { setStatusLoading(false); }
  }, [token]);

  useEffect(() => { fetchStatus(); const t = setInterval(fetchStatus, 15000); return () => clearInterval(t); }, [fetchStatus]);

  async function handleReconnect() {
    setReconnecting(true);
    setReconnectMsg("");
    try {
      const res = await fetch(`${API_BASE}/admin/bot/reconnect`, { method: "POST", headers: authHeader });
      const data = await res.json();
      setReconnectMsg(data.message ?? data.error ?? "Sinal enviado.");
    } catch { setReconnectMsg("Erro ao enviar sinal."); }
    finally { setReconnecting(false); setTimeout(fetchStatus, 4000); }
  }

  return (
    <div className={`min-h-screen ${S.bg} ${S.text} font-sans antialiased`}>
      {/* Nav */}
      <nav className={`border-b ${S.border} h-14 flex items-center px-6`}>
        <div className="flex items-center gap-2">
          <img src="/tenshi-logo.png" alt="Tenshi" className="w-6 h-6 object-contain opacity-90" />
          <span className="font-semibold text-sm">Bot Tenshi</span>
          <span className="text-[#3a3b42] text-xs">/ admin</span>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <a href="/" className="text-xs text-[#71717a] hover:text-[#a0a0a8] flex items-center gap-1 transition-colors">
            <ArrowLeft className="w-3 h-3" /> Site
          </a>
          <button onClick={onLogout} className="flex items-center gap-1.5 text-xs text-[#71717a] hover:text-red-400 transition-colors">
            <LogOut className="w-3 h-3" /> Sair
          </button>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-4 py-10 space-y-4">
        <div className="mb-6">
          <h1 className="text-xl font-bold">Painel do Criador</h1>
          <p className={`${S.muted} text-sm`}>Alloy — Imperador de Tenshi</p>
        </div>

        {/* Bot Status */}
        <div className={`${S.card} rounded-xl overflow-hidden`}>
          <div className={`flex items-center justify-between px-5 py-3.5 border-b ${S.border}`}>
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-[#71717a]" />
              <span className="text-sm font-semibold">Status do Bot</span>
            </div>
            <button onClick={fetchStatus} disabled={statusLoading} className="text-[#3a3b42] hover:text-[#71717a] disabled:opacity-30 transition-colors">
              <RefreshCw className={`w-3.5 h-3.5 ${statusLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
          <div className="p-5">
            {botStatus && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {[
                  {
                    label: "Status",
                    value: (
                      <span className={`flex items-center gap-1.5 text-sm font-semibold ${botStatus.online ? "text-green-400" : "text-red-400"}`}>
                        {botStatus.online ? <CheckCircle2 className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                        {botStatus.online ? "Online" : "Offline"}
                      </span>
                    )
                  },
                  { label: "Servidores", value: <span className="text-lg font-bold text-violet-400">{botStatus.guilds}</span> },
                  { label: "Latência", value: <span className="text-lg font-bold text-violet-400">{botStatus.latency}<span className="text-xs text-[#71717a] ml-1">ms</span></span> },
                  { label: "Usuário", value: <span className="text-xs font-mono text-[#a0a0a8] truncate">{botStatus.user ?? "—"}</span> },
                ].map(s => (
                  <div key={s.label}>
                    <p className="text-xs text-[#3a3b42] uppercase tracking-widest mb-1">{s.label}</p>
                    <div>{s.value}</div>
                  </div>
                ))}
              </div>
            )}
            {statusLoading && !botStatus && (
              <div className="flex items-center gap-2 text-[#71717a] text-sm">
                <RefreshCw className="w-4 h-4 animate-spin" /> Verificando...
              </div>
            )}
          </div>
          <div className={`flex flex-wrap gap-2 px-5 pb-5 border-t ${S.border} pt-4`}>
            {botStatus?.online ? (
              <button onClick={handleReconnect} disabled={reconnecting}
                className="inline-flex items-center gap-1.5 px-4 py-2 border border-[#2a2b31] hover:border-[#3a3b42] text-sm text-[#a0a0a8] rounded-lg transition-colors disabled:opacity-40">
                <RefreshCw className={`w-3.5 h-3.5 ${reconnecting ? "animate-spin" : ""}`} />
                {reconnecting ? "Reconectando..." : "Reconectar"}
              </button>
            ) : (
              <button onClick={handleReconnect} disabled={reconnecting}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-green-700 hover:bg-green-600 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-40">
                <Wifi className="w-3.5 h-3.5" />
                {reconnecting ? "Ligando..." : "Ligar Bot"}
              </button>
            )}
            <a href="https://discord.com/developers/applications/1427699671052320931/bot" target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-2 border border-[#2a2b31] hover:border-[#3a3b42] text-sm text-[#71717a] rounded-lg transition-colors">
              <ExternalLink className="w-3.5 h-3.5" /> Developer Portal
            </a>
          </div>
          <AnimatePresence>
            {reconnectMsg && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}
                className={`mx-5 mb-5 flex items-center gap-2 text-xs text-[#a0a0a8] bg-[#111315] border ${S.border} px-3 py-2 rounded-lg`}>
                <Activity className="w-3 h-3 shrink-0" />{reconnectMsg}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Info */}
        <div className={`${S.card} rounded-xl p-5`}>
          <p className="text-xs text-[#3a3b42] uppercase tracking-widest mb-4">Informações do Sistema</p>
          <div className="grid grid-cols-2 gap-y-3 text-sm">
            {[
              ["Prefixo", <code className="text-violet-400 font-mono text-xs">tenshi,</code>],
              ["Imperador", <span className="text-[#a0a0a8] text-xs">Alloy Tenshi</span>],
              ["Fundação", <span className="text-[#a0a0a8] text-xs font-mono">06/06/2016</span>],
              ["Motores IA", <span className="text-[#a0a0a8] text-xs">7 via Groq</span>],
              ["Comandos", <span className="text-violet-400 text-xs font-mono">{totalCmds}+</span>],
              ["App ID", <code className="text-[#4a4b52] text-xs font-mono">1427699671052320931</code>],
            ].map(([k, v]) => (
              <div key={String(k)} className="flex items-center justify-between col-span-1">
                <span className="text-[#3a3b42] text-xs">{k}</span>
                <span>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminPage() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(ADMIN_TOKEN_KEY));
  if (!token) return <AdminLogin onLogin={t => setToken(t)} />;
  return <AdminPanel token={token} onLogout={() => { localStorage.removeItem(ADMIN_TOKEN_KEY); setToken(null); }} />;
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
