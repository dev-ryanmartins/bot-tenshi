import { useState, useEffect, useCallback } from "react";
import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowDown, ExternalLink, Cpu, Crown, ChevronRight,
  Lock, LogOut, RefreshCw, WifiOff, Server, Activity,
  Eye, EyeOff, AlertTriangle, CheckCircle2, Settings,
  ArrowLeft, Wifi, Bot, Zap, Shield,
} from "lucide-react";
import NotFound from "@/pages/not-found";

const queryClient = new QueryClient();
const PREFIX = "tenshi,";

// ── Automações Imperiais ──────────────────────────────────────────────────────
const automacoes = [
  {
    icon: "🧠", name: "Triagem Jurídica",
    desc: "Monitora canais públicos (geral, beco, cassino) com IA e aplica advertências automáticas. Detecta toxicidade, spam e comportamentos proibidos sem intervenção humana.",
  },
  {
    icon: "📜", name: "LoreMaster Natural",
    desc: "Responde mensagens no canal geral e praça com lore narrativo do Império gerado por IA, mantendo a ambientação RPG ativa mesmo sem comandos.",
  },
  {
    icon: "🌊", name: "Embriaguez Dinâmica",
    desc: "Após usar `tenshi, beber`, o usuário fica bêbado: suas mensagens no geral são distorcidas automaticamente pela IA por tempo determinado.",
  },
  {
    icon: "🧬", name: "Psicologia Estratégica",
    desc: "Em canais de nome `psicologia-estrategia`, o bot responde automaticamente a todas as mensagens com análise de conselheiro imperial via IA.",
  },
  {
    icon: "⚔️", name: "Invasões & Boss Events",
    desc: "Eventos de invasão que geram criaturas atacando o servidor. Membros colaboram para derrotar o boss com ações narrativas em tempo real.",
  },
  {
    icon: "🌤️", name: "Clima Dinâmico Diário",
    desc: "Gera um clima narrativo diário para o Império, com efeitos reais em mecânicas de RPG como energia, HP e produtividade.",
  },
  {
    icon: "📰", name: "Crônicas do Cotidiano",
    desc: "Registra atividades dos canais públicos e gera crônicas épicas periódicas narrando o que aconteceu no servidor como se fosse um pergaminho histórico.",
  },
  {
    icon: "👑", name: "Saudação ao Imperador",
    desc: "Reconhece a chegada de Alloy em qualquer canal com uma fanfarra imperial automática — uma mensagem solene a cada nova sessão.",
  },
];

// ── Motores de IA ─────────────────────────────────────────────────────────────
const aiMotors = [
  { name: "Narrativa", model: "LLaMA 4 Maverick", use: "Crônicas épicas, roleplay imersivo, missões" },
  { name: "Rápida", model: "LLaMA 4 Scout", use: "Respostas instantâneas, triagem, moderação" },
  { name: "Analítica", model: "LLaMA 3.3 70B", use: "Jurídico, estratégia, análise profunda" },
  { name: "Relatório", model: "Mixtral 8x7B", use: "Auditorias, RH, relatórios econômicos" },
  { name: "Soberana", model: "GPT-120B → Maverick", use: "Geopolítica, decretos, soberania" },
  { name: "Economia", model: "GPT-20B → Scout", use: "Transações, cálculos, finanças" },
  { name: "NPCs", model: "Gemma 2 9B", use: "Personagens, clima, respostas curtas" },
];

// ── Comandos Completos ────────────────────────────────────────────────────────
const commands = [
  {
    category: "Identidade & Perfil", emoji: "🎭",
    color: "from-purple-900/30 to-purple-800/10", border: "border-purple-700/30",
    items: [
      { cmd: "status", desc: "Exibe sua ficha completa — nível, XP, HP, energia, moedas e facção.", usage: "tenshi, status" },
      { cmd: "ficha @user", desc: "Vê e edita sua ficha de personagem RP com nome, história e habilidades.", usage: "tenshi, ficha Nome: Alloy | Historia: Guerreiro..." },
      { cmd: "criar-ficha", desc: "Cria seu personagem pela primeira vez no Império.", usage: "tenshi, criar-ficha" },
      { cmd: "pegada [tema]", desc: "Muda seu tema visual. Opções: imperial, familia, mafia, enterprise.", usage: "tenshi, pegada imperial" },
      { cmd: "inventario", desc: "Lista todos os itens e equipamentos no seu inventário.", usage: "tenshi, inventario" },
      { cmd: "conquistas", desc: "Exibe seus badges e marcos conquistados no Império.", usage: "tenshi, conquistas" },
      { cmd: "especies", desc: "Lista as espécies e raças disponíveis para personagens.", usage: "tenshi, especies" },
      { cmd: "viajar [local]", desc: "Move seu personagem para outro local do mapa imperial.", usage: "tenshi, viajar Floresta das Sombras" },
      { cmd: "local", desc: "Mostra onde seu personagem está no mapa do Império.", usage: "tenshi, local" },
    ],
  },
  {
    category: "Jornada Imperial", emoji: "⚡",
    color: "from-yellow-900/30 to-yellow-800/10", border: "border-yellow-700/30",
    items: [
      { cmd: "treinar [ação]", desc: "Ganha XP narrando uma ação de treino. A IA avalia e recompensa.", usage: "tenshi, treinar medito na cachoeira ao amanhecer" },
      { cmd: "missao", desc: "Inicia uma missão narrativa gerada por IA. Cooldown de 1h.", usage: "tenshi, missao" },
      { cmd: "meditar", desc: "Recupera energia espiritual. Essencial antes de missões longas.", usage: "tenshi, meditar" },
      { cmd: "descansar", desc: "Recupera HP. Funciona em casa ou área segura.", usage: "tenshi, descansar" },
      { cmd: "interagir [ação]", desc: "Realiza uma ação de roleplay expressa em texto narrativo.", usage: "tenshi, interagir saca sua espada e avança" },
      { cmd: "dado [tipo]", desc: "Rola dados para ações de RPG. Tipos: d4, d6, d10, d20, d100.", usage: "tenshi, dado d20" },
      { cmd: "profissao [classe]", desc: "Define ou muda sua profissão: Ferreiro, Alquimista, etc.", usage: "tenshi, profissao Ferreiro" },
      { cmd: "clima", desc: "Exibe o clima do dia no Império com efeitos narrativos no RPG.", usage: "tenshi, clima" },
      { cmd: "clima-atual", desc: "Versão detalhada do clima com forecast meteorológico via IA.", usage: "tenshi, clima-atual" },
    ],
  },
  {
    category: "Poderes de RP", emoji: "✨",
    color: "from-violet-900/30 to-violet-800/10", border: "border-violet-700/30",
    items: [
      { cmd: "poderes", desc: "Abre a árvore de poderes disponíveis para sua espécie e nível.", usage: "tenshi, poderes" },
      { cmd: "meus-poderes", desc: "Lista os poderes que você já desbloqueou.", usage: "tenshi, meus-poderes" },
    ],
  },
  {
    category: "LoreMaster IA", emoji: "📖",
    color: "from-teal-900/30 to-teal-800/10", border: "border-teal-700/30",
    items: [
      { cmd: "cronica [tipo]", desc: "Gera uma crônica épica via IA. Tipos: militar, politico, esoterico, mafia, enterprise.", usage: "tenshi, cronica militar" },
      { cmd: "evento-lore", desc: "Gera uma profecia ou evento lendário para o Império.", usage: "tenshi, evento-lore" },
      { cmd: "oraculo [pergunta]", desc: "Consulta o Oráculo Imperial com uma pergunta livre via IA.", usage: "tenshi, oraculo Qual será o fim do Império?" },
      { cmd: "falar [NPC]", desc: "Conversa em tempo real com um NPC do Império via IA.", usage: "tenshi, falar Guardião da Porta" },
      { cmd: "lore-historico", desc: "Exibe as crônicas e registros históricos do Império.", usage: "tenshi, lore-historico" },
      { cmd: "quadro-avisos", desc: "Mostra as missões diárias e avisos do Império.", usage: "tenshi, quadro-avisos" },
    ],
  },
  {
    category: "Místico", emoji: "🔮",
    color: "from-indigo-900/30 to-indigo-800/10", border: "border-indigo-700/30",
    items: [
      { cmd: "tarot", desc: "O Oráculo tira cartas de tarô e interpreta seu futuro via IA.", usage: "tenshi, tarot" },
      { cmd: "runa", desc: "Consulta as runas ancestrais para guia espiritual.", usage: "tenshi, runa" },
      { cmd: "astros", desc: "Lê as constelações e gera seu horóscopo imperial via IA.", usage: "tenshi, astros" },
      { cmd: "destino @user", desc: "Lê o destino de outro cidadão via IA mística.", usage: "tenshi, destino @Alloy" },
      { cmd: "sacrificio [item]", desc: "Oferenda mística em troca de bênçãos ou maldições.", usage: "tenshi, sacrificio Poção Velha" },
      { cmd: "ritual-protecao", desc: "Realiza ritual de proteção — imunidade narrativa temporária.", usage: "tenshi, ritual-protecao" },
    ],
  },
  {
    category: "Combate Narrativo", emoji: "⚔️",
    color: "from-rose-900/30 to-rose-800/10", border: "border-rose-700/30",
    items: [
      { cmd: "duelo @user", desc: "Desafia outro cidadão para um duelo com apostas opcionais.", usage: "tenshi, duelo @Alloy" },
      { cmd: "aceitar-duelo", desc: "Aceita um desafio de duelo pendente direcionado a você.", usage: "tenshi, aceitar-duelo" },
      { cmd: "basquete @user", desc: "Desafia alguém para uma partida de basquete narrativo.", usage: "tenshi, basquete @Alloy" },
      { cmd: "futebol @user", desc: "Desafia alguém para uma partida de futebol narrativo.", usage: "tenshi, futebol @Alloy" },
      { cmd: "invocar-chefe [criatura]", desc: "Admin: Invoca um boss para o servidor enfrentar coletivamente.", usage: "tenshi, invocar-chefe Dragão das Sombras" },
      { cmd: "invasao", desc: "Admin: Inicia uma invasão de criaturas no servidor.", usage: "tenshi, invasao" },
    ],
  },
  {
    category: "Economia & Comércio", emoji: "💰",
    color: "from-amber-900/30 to-amber-800/10", border: "border-amber-700/30",
    items: [
      { cmd: "carteira", desc: "Exibe seu saldo de Moedas Imperiais em circulação.", usage: "tenshi, carteira" },
      { cmd: "mercado", desc: "Abre a loja oficial do Império com itens e equipamentos.", usage: "tenshi, mercado" },
      { cmd: "mercado-negro", desc: "Acessa o mercado clandestino com itens raros e ilegais.", usage: "tenshi, mercado-negro" },
      { cmd: "comprar [item]", desc: "Compra um item disponível no mercado ativo.", usage: "tenshi, comprar Espada de Ferro" },
      { cmd: "leilao [item]", desc: "Lança um item em leilão para outros jogadores comprarem.", usage: "tenshi, leilao Poção Rara" },
      { cmd: "sorteio-real", desc: "Participa do sorteio imperial com prêmios em moedas.", usage: "tenshi, sorteio-real" },
      { cmd: "trabalhar", desc: "Executa trabalho diário em seu emprego para ganhar moedas.", usage: "tenshi, trabalhar" },
      { cmd: "emprego", desc: "Lista empregos disponíveis e mostra seu emprego atual.", usage: "tenshi, emprego" },
    ],
  },
  {
    category: "Banco & Finanças", emoji: "🏦",
    color: "from-green-900/30 to-green-800/10", border: "border-green-700/30",
    items: [
      { cmd: "banco", desc: "Acessa seu extrato bancário e histórico de transações.", usage: "tenshi, banco" },
      { cmd: "depositar [valor]", desc: "Deposita moedas no banco imperial para guardar com segurança.", usage: "tenshi, depositar 500" },
      { cmd: "sacar [valor]", desc: "Saca moedas do banco para sua carteira.", usage: "tenshi, sacar 200" },
      { cmd: "transferir @user [valor]", desc: "Transfere moedas para outro cidadão via PIX Imperial.", usage: "tenshi, transferir @Alloy 100" },
      { cmd: "emprestimo [valor]", desc: "Solicita empréstimo ao Banco Imperial com juros.", usage: "tenshi, emprestimo 1000" },
      { cmd: "pagar-divida", desc: "Quita seu empréstimo ativo com o Banco Imperial.", usage: "tenshi, pagar-divida" },
      { cmd: "historico", desc: "Exibe seu histórico financeiro completo.", usage: "tenshi, historico" },
      { cmd: "poupanca [valor]", desc: "Investe moedas em conta poupança com rendimentos.", usage: "tenshi, poupanca 500" },
      { cmd: "comprar-acoes [valor]", desc: "Compra ações no mercado imperial de capitais.", usage: "tenshi, comprar-acoes 200" },
      { cmd: "titulo-divida", desc: "Emite título de dívida pública imperial.", usage: "tenshi, titulo-divida" },
      { cmd: "seguro-vida", desc: "Contrata seguro de vida no sistema estatal.", usage: "tenshi, seguro-vida" },
      { cmd: "aposentar", desc: "Solicita aposentadoria e acesso ao fundo de pensão.", usage: "tenshi, aposentar" },
      { cmd: "lavar [valor]", desc: "Lavagem de dinheiro no beco — risco alto, lucro alto.", usage: "tenshi, lavar 1000" },
    ],
  },
  {
    category: "Propriedades & Casas", emoji: "🏠",
    color: "from-lime-900/30 to-lime-800/10", border: "border-lime-700/30",
    items: [
      { cmd: "casas", desc: "Exibe o mercado imobiliário com casas disponíveis para compra.", usage: "tenshi, casas" },
      { cmd: "minha-casa", desc: "Mostra detalhes da sua residência atual no Império.", usage: "tenshi, minha-casa" },
      { cmd: "vender-casa", desc: "Coloca sua residência à venda no mercado imobiliário.", usage: "tenshi, vender-casa" },
      { cmd: "portaria", desc: "Acessa o sistema de condomínio e vê residências disponíveis.", usage: "tenshi, portaria" },
      { cmd: "residencia", desc: "Entra em sua residência do condomínio.", usage: "tenshi, residencia" },
      { cmd: "convidar @user", desc: "Convida outro jogador para morar na sua residência.", usage: "tenshi, convidar @Alloy" },
      { cmd: "expulsar @user", desc: "Expulsa um morador da sua residência.", usage: "tenshi, expulsar @Alloy" },
      { cmd: "devolver-casa", desc: "Devolve sua residência e sai do condomínio.", usage: "tenshi, devolver-casa" },
      { cmd: "moradores", desc: "Lista todos os moradores da sua residência.", usage: "tenshi, moradores" },
      { cmd: "relaxar", desc: "Descansa em casa ganhando bônus de regeneração de HP.", usage: "tenshi, relaxar" },
      { cmd: "fofoca", desc: "Gera uma crônica via IA dos acontecimentos do condomínio.", usage: "tenshi, fofoca" },
      { cmd: "trancar-casa", desc: "Tranca sua residência impedindo entrada de visitantes.", usage: "tenshi, trancar-casa" },
      { cmd: "destrancar-casa", desc: "Destranca sua residência permitindo acesso de convidados.", usage: "tenshi, destrancar-casa" },
      { cmd: "titulo-propriedade", desc: "Obtém escritura oficial de sua propriedade.", usage: "tenshi, titulo-propriedade" },
      { cmd: "alugar-comercio", desc: "Aluga um espaço comercial no Império.", usage: "tenshi, alugar-comercio" },
    ],
  },
  {
    category: "Garagem, Esportes & Pets", emoji: "🚗",
    color: "from-sky-900/30 to-sky-800/10", border: "border-sky-700/30",
    items: [
      { cmd: "garagem", desc: "Exibe seus veículos registrados e seus status.", usage: "tenshi, garagem" },
      { cmd: "vender-veiculo", desc: "Coloca seu veículo à venda no mercado.", usage: "tenshi, vender-veiculo" },
      { cmd: "abastecer [valor]", desc: "Abastece seu veículo com combustível imperial.", usage: "tenshi, abastecer 100" },
      { cmd: "pool-party", desc: "Admin: Inicia uma Pool Party com bônus de remuneração para todos.", usage: "tenshi, pool-party" },
      { cmd: "pet-shop", desc: "Abre a loja de pets — adquira seu animal companheiro.", usage: "tenshi, pet-shop" },
      { cmd: "meu-pet", desc: "Exibe informações do seu pet atual.", usage: "tenshi, meu-pet" },
      { cmd: "vender-pet", desc: "Vende seu pet no mercado.", usage: "tenshi, vender-pet" },
    ],
  },
  {
    category: "Social & Cotidiano", emoji: "💑",
    color: "from-pink-900/30 to-pink-800/10", border: "border-pink-700/30",
    items: [
      { cmd: "casar @user", desc: "Propõe casamento a outro cidadão. Requer consentimento.", usage: "tenshi, casar @Alloy" },
      { cmd: "divorcio", desc: "Encerra o casamento atual com processo oficial.", usage: "tenshi, divorcio" },
      { cmd: "lavanderia", desc: "Leva seus itens para lavagem — restaura condição.", usage: "tenshi, lavanderia" },
      { cmd: "sintetizar [item]", desc: "Fabrica um item combinando materiais no laboratório.", usage: "tenshi, sintetizar Poção de Cura" },
      { cmd: "cartaz [filme]", desc: "Agenda ou vê o cartaz do cinema do condomínio.", usage: "tenshi, cartaz Avatar 2" },
      { cmd: "psicologo [texto]", desc: "Desabafa com o psicólogo imperial — resposta via IA.", usage: "tenshi, psicologo estou me sentindo sobrecarregado..." },
      { cmd: "beber [bebida]", desc: "Bebe no bar do Império. Efeito de embriaguez narrativo.", usage: "tenshi, beber whisky" },
      { cmd: "jornal-cotidiano", desc: "Gera o jornal diário do Império com manchetes via IA.", usage: "tenshi, jornal-cotidiano" },
      { cmd: "correio", desc: "Abre o sistema de correio anônimo do Império.", usage: "tenshi, correio" },
      { cmd: "estacoes", desc: "Exibe a estação atual e seus efeitos no RPG.", usage: "tenshi, estacoes" },
      { cmd: "entrevista [cargo]", desc: "Participa de uma entrevista de emprego narrativa.", usage: "tenshi, entrevista Oficial da Guarda" },
      { cmd: "socorrer @user", desc: "Presta socorro médico de emergência a outro cidadão.", usage: "tenshi, socorrer @Alloy" },
      { cmd: "vdd", desc: "Verdade ou Desafio — jogo social via IA com perguntas e desafios.", usage: "tenshi, vdd" },
    ],
  },
  {
    category: "Crime & Inteligência", emoji: "🕵️",
    color: "from-zinc-800/30 to-zinc-700/10", border: "border-zinc-600/30",
    items: [
      { cmd: "assaltar @user", desc: "Tenta assaltar outro cidadão no beco — risco de cadeia.", usage: "tenshi, assaltar @Alloy" },
      { cmd: "mercado-negro-beco", desc: "Mercado clandestino no beco, com itens proibidos raros.", usage: "tenshi, mercado-negro-beco" },
      { cmd: "subornar-porteiro @user", desc: "Suborna o porteiro para espionar uma residência.", usage: "tenshi, subornar-porteiro @Alloy" },
      { cmd: "grampear-call", desc: "Grampo em call ativa — espionagem narrativa via IA.", usage: "tenshi, grampear-call" },
      { cmd: "iniciar-festa [local]", desc: "Organiza uma festa no local indicado com efeitos narrativos.", usage: "tenshi, iniciar-festa condominio" },
      { cmd: "registrar-perola [msg]", desc: "Salva uma pérola (momento memorável) nos registros do Império.", usage: "tenshi, registrar-perola esse momento foi lendário" },
    ],
  },
  {
    category: "Jurídico & Clero", emoji: "⚖️",
    color: "from-orange-900/30 to-orange-800/10", border: "border-orange-700/30",
    items: [
      { cmd: "ficha-criminal @user", desc: "Exibe a ficha criminal completa de um cidadão.", usage: "tenshi, ficha-criminal @Alloy" },
      { cmd: "warn @user", desc: "Emite uma advertência oficial para o cidadão.", usage: "tenshi, warn @Alloy" },
      { cmd: "perdoar-aviso @user", desc: "Remove uma advertência do histórico do cidadão.", usage: "tenshi, perdoar-aviso @Alloy" },
      { cmd: "mandado @user", desc: "Emite mandado de busca e apreensão contra cidadão.", usage: "tenshi, mandado @Alloy" },
      { cmd: "pagar-fianca", desc: "Paga fiança para sair da masmorra judicial.", usage: "tenshi, pagar-fianca" },
      { cmd: "imunidade-diplomatica", desc: "Solicita imunidade diplomática temporária.", usage: "tenshi, imunidade-diplomatica" },
      { cmd: "padre [rito]", desc: "Realiza um rito clerical: batismo, casamento, enterro.", usage: "tenshi, padre batismo" },
      { cmd: "sindicancia @user", desc: "Abre sindicância investigativa sobre um cidadão.", usage: "tenshi, sindicancia @Alloy" },
      { cmd: "laudo-medico", desc: "Emite laudo médico oficial do cidadão.", usage: "tenshi, laudo-medico" },
      { cmd: "desintoxicacao", desc: "Processo de desintoxicação médica de status negativos.", usage: "tenshi, desintoxicacao" },
      { cmd: "doacao-sangue", desc: "Doa sangue — ganha karma e cura parcial.", usage: "tenshi, doacao-sangue" },
      { cmd: "diagnostico-ia", desc: "Diagnóstico médico completo via IA do Império.", usage: "tenshi, diagnostico-ia" },
    ],
  },
  {
    category: "Geopolítica & Estado", emoji: "🌍",
    color: "from-emerald-900/30 to-emerald-800/10", border: "border-emerald-700/30",
    items: [
      { cmd: "dominar [canal]", desc: "Tenta dominar um canal/território para sua facção.", usage: "tenshi, dominar #canal-geral" },
      { cmd: "territorio", desc: "Exibe o mapa de domínio territorial das facções.", usage: "tenshi, territorio" },
      { cmd: "rebeliao", desc: "Inicia uma rebelião contra o poder dominante local.", usage: "tenshi, rebeliao" },
      { cmd: "visto", desc: "Acessa o painel de vistos e imigração do Império.", usage: "tenshi, visto" },
      { cmd: "cidadania", desc: "Solicita ou exibe sua certidão de cidadania imperial.", usage: "tenshi, cidadania" },
      { cmd: "exilio @user", desc: "Exilia temporariamente um cidadão para fora do território.", usage: "tenshi, exilio @Alloy" },
      { cmd: "auditoria-bancaria", desc: "Audita o banco de um cidadão suspeito de irregularidades.", usage: "tenshi, auditoria-bancaria" },
      { cmd: "necrolo", desc: "Acessa o mural dos mortos — obituários narrativos do Império.", usage: "tenshi, necrolo" },
      { cmd: "buscar-protocolo", desc: "Acessa protocolos de segurança de estado.", usage: "tenshi, buscar-protocolo" },
      { cmd: "set-era [nome]", desc: "Define a era histórica atual do Império.", usage: "tenshi, set-era Era das Trevas" },
      { cmd: "era", desc: "Exibe a era histórica atual com efeitos no RPG.", usage: "tenshi, era" },
      { cmd: "decreto-marcial [ação]", desc: "Decreta lei marcial com restrições automáticas.", usage: "tenshi, decreto-marcial silencio total" },
      { cmd: "aconselhar-estrategia [sit.]", desc: "Conselheiro imperial analisa situação via IA e sugere estratégia.", usage: "tenshi, aconselhar-estrategia facção rival dominando" },
    ],
  },
  {
    category: "Infraestrutura Crítica", emoji: "🏗️",
    color: "from-cyan-900/30 to-cyan-800/10", border: "border-cyan-700/30",
    items: [
      { cmd: "status-energia", desc: "Verifica o status da rede elétrica e energética do Império.", usage: "tenshi, status-energia" },
      { cmd: "inflacao", desc: "Exibe o índice de inflação atual da economia imperial.", usage: "tenshi, inflacao" },
      { cmd: "checar-cameras", desc: "Acessa as câmeras de segurança de um local.", usage: "tenshi, checar-cameras" },
      { cmd: "biometria", desc: "Registra ou consulta dados biométricos e DNA.", usage: "tenshi, biometria" },
      { cmd: "rastrear-perfil @user", desc: "OSINT avançado — rastreia perfil e atividades do cidadão.", usage: "tenshi, rastrear-perfil @Alloy" },
      { cmd: "enviar-carga [tipo]", desc: "Despacha uma carga logística no Império.", usage: "tenshi, enviar-carga medicamentos" },
      { cmd: "historico-imovel", desc: "Consulta o histórico de transações de um imóvel.", usage: "tenshi, historico-imovel" },
    ],
  },
  {
    category: "Tenshi Academy", emoji: "🎓",
    color: "from-blue-900/30 to-blue-800/10", border: "border-blue-700/30",
    items: [
      { cmd: "matricular [materia]", desc: "Matricula-se em uma matéria da Tenshi Academy.", usage: "tenshi, matricular Filosofia Imperial" },
      { cmd: "trancar-matricula [mat.]", desc: "Tranca a matrícula em uma matéria.", usage: "tenshi, trancar-matricula Filosofia Imperial" },
      { cmd: "presenca [materia]", desc: "Registra presença em aula ativa.", usage: "tenshi, presenca Filosofia Imperial" },
      { cmd: "iniciar-aula [materia]", desc: "Prof./Admin: Inicia uma aula com conteúdo via IA.", usage: "tenshi, iniciar-aula Filosofia Imperial" },
      { cmd: "ler-apostila [materia]", desc: "Acessa a apostila digital da matéria via IA.", usage: "tenshi, ler-apostila Filosofia Imperial" },
      { cmd: "prestar-exame [materia]", desc: "Faz o exame final da matéria enviado por DM via IA.", usage: "tenshi, prestar-exame Filosofia Imperial" },
      { cmd: "historico-escolar", desc: "Exibe seu histórico acadêmico com notas e aprovações.", usage: "tenshi, historico-escolar" },
      { cmd: "segunda-via-diploma", desc: "Solicita segunda via de diploma já obtido.", usage: "tenshi, segunda-via-diploma" },
      { cmd: "entrar-clube [nome]", desc: "Filia-se a um clube extracurricular da Academia.", usage: "tenshi, entrar-clube Clube de Combate" },
      { cmd: "cofre-clube", desc: "Acessa as finanças do clube que você participa.", usage: "tenshi, cofre-clube" },
    ],
  },
  {
    category: "Empresa", emoji: "🏢",
    color: "from-slate-800/30 to-slate-700/10", border: "border-slate-600/30",
    items: [
      { cmd: "empresa criar [nome]", desc: "Funda uma empresa no Império. Requer capital inicial.", usage: "tenshi, empresa criar Tenshi Corp" },
      { cmd: "empresa info", desc: "Exibe detalhes da sua empresa: capital, funcionários e status.", usage: "tenshi, empresa info" },
      { cmd: "empresa contratar @user", desc: "Contrata um cidadão como funcionário da empresa.", usage: "tenshi, empresa contratar @Alloy" },
      { cmd: "empresa demitir @user", desc: "Demite um funcionário da empresa.", usage: "tenshi, empresa demitir @Alloy" },
      { cmd: "empresa funcionarios", desc: "Lista o quadro de funcionários da empresa.", usage: "tenshi, empresa funcionarios" },
      { cmd: "empresa pagar", desc: "Paga salários a todos os funcionários automaticamente.", usage: "tenshi, empresa pagar" },
    ],
  },
  {
    category: "Família, Máfia & Facções", emoji: "👨‍👩‍👧",
    color: "from-red-900/30 to-red-800/10", border: "border-red-700/30",
    items: [
      { cmd: "familia criar [nome]", desc: "Funda uma família ou clã com você como patriarca.", usage: "tenshi, familia criar Os Tenshi" },
      { cmd: "familia entrar [nome]", desc: "Junta-se a uma família/máfia existente.", usage: "tenshi, familia entrar Os Tenshi" },
      { cmd: "familia info", desc: "Exibe informações detalhadas da sua família.", usage: "tenshi, familia info" },
      { cmd: "familia membros", desc: "Lista todos os membros da família com seus cargos.", usage: "tenshi, familia membros" },
      { cmd: "familia missao", desc: "Inicia uma missão em grupo para a família.", usage: "tenshi, familia missao" },
      { cmd: "familia depositar [v]", desc: "Deposita moedas no cofre compartilhado da família.", usage: "tenshi, familia depositar 500" },
      { cmd: "entrar [facção]", desc: "Alista-se em uma das facções do Império.", usage: "tenshi, entrar Guardiões do Trono" },
      { cmd: "ranking", desc: "Exibe o ranking de poder entre todas as facções ativas.", usage: "tenshi, ranking" },
    ],
  },
  {
    category: "Moderação Imperial", emoji: "🛡️",
    color: "from-gray-800/30 to-gray-700/10", border: "border-gray-600/30",
    admin: true,
    items: [
      { cmd: "decreto [msg]", desc: "Publica um decreto oficial do Império.", usage: "tenshi, decreto Que todos se curvem!", admin: true },
      { cmd: "promover @user [cargo]", desc: "Concede um título ou cargo imperial a um cidadão.", usage: "tenshi, promover @Alloy Cavaleiro", admin: true },
      { cmd: "julgamento @user", desc: "Inicia tribunal para julgamento de um cidadão.", usage: "tenshi, julgamento @Alloy", admin: true },
      { cmd: "masmorra-prender @user [min]", desc: "Prende o cidadão na masmorra por X minutos.", usage: "tenshi, masmorra-prender @Alloy 30", admin: true },
      { cmd: "exilar @user", desc: "Exila o cidadão narrativamente do Império.", usage: "tenshi, exilar @Alloy", admin: true },
      { cmd: "anistia-real", desc: "Concede perdão geral a todos os presos e exilados.", usage: "tenshi, anistia-real", admin: true },
      { cmd: "punir-audacia @user", desc: "Aplica punição leve por comportamento inadequado.", usage: "tenshi, punir-audacia @Alloy", admin: true },
      { cmd: "trancar-portoes", desc: "Ativa lockdown — restringe ações dos cidadãos.", usage: "tenshi, trancar-portoes", admin: true },
      { cmd: "tesouro [valor]", desc: "Adiciona moedas ao tesouro público do Império.", usage: "tenshi, tesouro 1000", admin: true },
      { cmd: "veto [acao]", desc: "Veta uma ação ou evento em andamento.", usage: "tenshi, veto duelo", admin: true },
      { cmd: "ban @user", desc: "Bane o usuário do servidor Discord.", usage: "tenshi, ban @Alloy", admin: true },
      { cmd: "kick @user", desc: "Expulsa o usuário do servidor Discord.", usage: "tenshi, kick @Alloy", admin: true },
      { cmd: "mute @user [min]", desc: "Silencia o usuário por X minutos.", usage: "tenshi, mute @Alloy 10", admin: true },
      { cmd: "clear [n]", desc: "Apaga as últimas N mensagens do canal.", usage: "tenshi, clear 10", admin: true },
      { cmd: "warn @user", desc: "Emite advertência oficial para o cidadão.", usage: "tenshi, warn @Alloy", admin: true },
    ],
  },
  {
    category: "Prerrogativas Soberanas", emoji: "👑",
    color: "from-yellow-950/50 to-yellow-900/10", border: "border-yellow-800/40",
    admin: true,
    items: [
      { cmd: "emitir-moeda [v]", desc: "Emite moedas novas na economia imperial.", usage: "tenshi, emitir-moeda 50000", admin: true },
      { cmd: "confiscar-fortuna @user", desc: "Confisca toda a fortuna de um cidadão.", usage: "tenshi, confiscar-fortuna @Alloy", admin: true },
      { cmd: "congelar-banco @user", desc: "Congela acesso bancário de um cidadão.", usage: "tenshi, congelar-banco @Alloy", admin: true },
      { cmd: "perdoar-divida @user", desc: "Perdoa a dívida bancária de um cidadão.", usage: "tenshi, perdoar-divida @Alloy", admin: true },
      { cmd: "isencao-fiscal @user", desc: "Concede isenção fiscal permanente.", usage: "tenshi, isencao-fiscal @Alloy", admin: true },
      { cmd: "set-status @user [campo:v]", desc: "Define qualquer atributo do personagem diretamente.", usage: "tenshi, set-status @Alloy hp:500", admin: true },
      { cmd: "apagar-ficha @user", desc: "Apaga permanentemente a ficha de personagem.", usage: "tenshi, apagar-ficha @Alloy", admin: true },
      { cmd: "conceder-item @user [item]", desc: "Concede um item direto ao inventário do cidadão.", usage: "tenshi, conceder-item @Alloy Espada Lendária", admin: true },
      { cmd: "imortalidade @user", desc: "Concede ou remove imortalidade narrativa.", usage: "tenshi, imortalidade @Alloy", admin: true },
      { cmd: "estado-de-sitio [dur.]", desc: "Decreta estado de sítio com restrições automáticas.", usage: "tenshi, estado-de-sitio 24h", admin: true },
      { cmd: "dissolver-mafia [nome]", desc: "Dissolve uma família/máfia compulsoriamente.", usage: "tenshi, dissolver-mafia Os Tenshi", admin: true },
      { cmd: "anistia-geral", desc: "Anistia geral — perdoa todos os crimes do servidor.", usage: "tenshi, anistia-geral", admin: true },
      { cmd: "exilio-supremo @user", desc: "Exílio supremo permanente — maior punição narrativa.", usage: "tenshi, exilio-supremo @Alloy", admin: true },
      { cmd: "atualizar-diretriz [texto]", desc: "Atualiza a diretriz comportamental dos NPCs via IA.", usage: "tenshi, atualizar-diretriz sejam mais austeros", admin: true },
      { cmd: "apagar-memoria-ia", desc: "Apaga o histórico de memória da IA narrativa.", usage: "tenshi, apagar-memoria-ia", admin: true },
      { cmd: "forcar-cronica [tipo]", desc: "Força a geração imediata de uma crônica narrativa.", usage: "tenshi, forcar-cronica militar", admin: true },
      { cmd: "censo-imperial", desc: "Gera censo completo de todos os cidadãos cadastrados.", usage: "tenshi, censo-imperial", admin: true },
      { cmd: "reset-era [nome]", desc: "Reseta a era histórica e recalibra o Império.", usage: "tenshi, reset-era Era das Luzes", admin: true },
      { cmd: "irradiar [msg]", desc: "Transmissão nacional — envia mensagem a todos os canais.", usage: "tenshi, irradiar Cidadãos, atenção!", admin: true },
      { cmd: "congelar-economia", desc: "Paralisa todas as transações econômicas do servidor.", usage: "tenshi, congelar-economia", admin: true },
      { cmd: "exportar-banco", desc: "Exporta backup completo do banco de dados imperial.", usage: "tenshi, exportar-banco", admin: true },
      { cmd: "bypass-cooldown @user", desc: "Remove o cooldown de todos os comandos do cidadão.", usage: "tenshi, bypass-cooldown @Alloy", admin: true },
      { cmd: "desligar", desc: "Desliga o bot graciosamente (apenas Imperador).", usage: "tenshi, desligar", admin: true },
    ],
  },
  {
    category: "Utilitários", emoji: "🔧",
    color: "from-stone-800/30 to-stone-700/10", border: "border-stone-600/30",
    items: [
      { cmd: "top", desc: "Ranking global de cidadãos por XP e riqueza.", usage: "tenshi, top" },
      { cmd: "servidor", desc: "Informações detalhadas do servidor Discord.", usage: "tenshi, servidor" },
      { cmd: "ping", desc: "Verifica a latência do bot com o Discord.", usage: "tenshi, ping" },
      { cmd: "backup", desc: "Salva uma cópia dos seus dados no Império.", usage: "tenshi, backup" },
      { cmd: "status-ia", desc: "Verifica o status dos 7 motores de IA ativos.", usage: "tenshi, status-ia" },
      { cmd: "aniversario", desc: "Exibe o aniversário de fundação do Império.", usage: "tenshi, aniversario" },
      { cmd: "ajuda", desc: "Guia completo de todos os comandos do Bot Tenshi.", usage: "tenshi, ajuda" },
    ],
  },
];

// ── Admin types ───────────────────────────────────────────────────────────────
interface BotStatus { online: boolean; guilds: number; latency: number; user: string | null; }
const ADMIN_TOKEN_KEY = "tenshi_admin_token";
const API_BASE = "/api";

// ── HomePage ──────────────────────────────────────────────────────────────────
function HomePage() {
  const [search, setSearch] = useState("");
  const scrollToCommands = () => document.getElementById("comandos")?.scrollIntoView({ behavior: "smooth" });

  const filtered = search.trim()
    ? commands.map(cat => ({
        ...cat,
        items: cat.items.filter(i =>
          i.cmd.toLowerCase().includes(search.toLowerCase()) ||
          i.desc.toLowerCase().includes(search.toLowerCase())
        ),
      })).filter(cat => cat.items.length > 0)
    : commands;

  const totalCmds = commands.reduce((acc, c) => acc + c.items.length, 0);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <div className="fixed inset-0 pointer-events-none z-0 bg-gradient-to-b from-[#0a0208] via-[#0d050f] to-[#080412]" />
      <div className="fixed inset-0 pointer-events-none z-0 opacity-35 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: "url(/hero-bg.png)" }} />
      <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_at_top,rgba(158,120,21,0.08)_0%,transparent_60%)]" />

      {/* Hero */}
      <section className="relative z-10 min-h-[100dvh] flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1.2 }} className="text-center max-w-4xl mx-auto space-y-8">
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
            Prefixo: <span className="text-yellow-500/70">tenshi,</span> &nbsp;•&nbsp; 7 Motores de IA &nbsp;•&nbsp; {totalCmds}+ Comandos
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-5 pt-6">
            <a
              href="https://discord.com/oauth2/authorize?client_id=1427699671052320931&permissions=8&scope=bot"
              target="_blank" rel="noopener noreferrer"
              className="group relative inline-flex items-center gap-3 px-10 py-4 bg-gradient-to-r from-yellow-600 to-yellow-500 text-black font-black uppercase tracking-widest text-sm transition-all hover:scale-105 hover:shadow-[0_0_40px_rgba(234,179,8,0.35)] rounded-sm overflow-hidden"
            >
              <div className="absolute inset-0 bg-white/15 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
              <ExternalLink className="w-4 h-4 relative z-10" />
              <span className="relative z-10">Adicionar ao Discord</span>
            </a>
            <button onClick={scrollToCommands} className="group inline-flex items-center gap-3 px-10 py-4 border border-yellow-700/40 text-yellow-500/80 font-bold uppercase tracking-widest text-sm hover:bg-yellow-900/20 hover:border-yellow-600/60 transition-all rounded-sm">
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
              <motion.div key={ai.name} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.08 }}
                className="p-5 bg-yellow-950/20 border border-yellow-900/30 rounded-sm hover:border-yellow-700/40 transition-colors">
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

      {/* Automações Imperiais */}
      <section className="relative z-10 py-24 bg-black/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-14">
            <div className="inline-flex items-center gap-2 mb-4 px-4 py-1.5 border border-green-800/40 bg-green-950/20 rounded-full">
              <Bot className="w-3.5 h-3.5 text-green-500/70" />
              <span className="text-green-400/70 text-xs font-mono uppercase tracking-widest">Totalmente Automático</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-serif font-bold text-yellow-100/90 mb-3">Automações Imperiais</h2>
            <p className="text-yellow-100/40 max-w-2xl mx-auto">A IA administra o servidor em tempo real — sem precisar digitar comandos. O Império vive mesmo quando ninguém está comandando.</p>
          </motion.div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {automacoes.map((a, i) => (
              <motion.div key={a.name} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.07 }}
                className="p-5 bg-green-950/10 border border-green-900/20 rounded-sm hover:border-green-700/30 transition-colors group">
                <div className="text-2xl mb-3">{a.icon}</div>
                <h3 className="text-green-300/80 font-bold font-serif text-sm uppercase tracking-wide mb-2 group-hover:text-green-300/100 transition-colors">{a.name}</h3>
                <p className="text-yellow-100/40 text-xs leading-relaxed">{a.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Commands */}
      <section id="comandos" className="relative z-10 py-24 scroll-mt-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-10">
            <h2 className="text-4xl md:text-6xl font-serif font-bold text-yellow-100/90 mb-4">Tomo de Comandos</h2>
            <p className="text-yellow-100/40 text-lg max-w-2xl mx-auto mb-6">
              {totalCmds} comandos. Prefixo: <code className="text-yellow-500 bg-yellow-950/40 px-2 py-0.5 rounded text-sm">tenshi,</code>
            </p>
            {/* Search */}
            <div className="max-w-md mx-auto">
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Pesquisar comando..."
                className="w-full bg-yellow-950/20 border border-yellow-900/40 text-yellow-100/80 placeholder-yellow-100/20 px-4 py-2.5 rounded-sm font-mono text-sm focus:outline-none focus:border-yellow-700/60 transition-colors"
              />
            </div>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {filtered.map((cat, idx) => (
              <motion.div key={cat.category} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }} transition={{ delay: (idx % 3) * 0.06 }}
                className={`bg-gradient-to-b ${cat.color} border ${cat.border} backdrop-blur-sm rounded-sm overflow-hidden`}>
                <div className="flex items-center gap-3 px-5 py-3.5 border-b border-white/5">
                  <span className="text-lg">{cat.emoji}</span>
                  <h3 className="text-sm font-bold font-serif text-yellow-100/90">{cat.category}</h3>
                  {(cat as any).admin && <span className="ml-auto text-xs bg-red-900/40 text-red-400 border border-red-800/40 px-2 py-0.5 rounded font-mono">Admin</span>}
                  <span className="ml-auto text-xs text-yellow-100/20 font-mono">{cat.items.length}</span>
                </div>
                <ul className="divide-y divide-white/5">
                  {cat.items.map(item => (
                    <li key={item.cmd} className="px-5 py-2.5 group hover:bg-white/5 transition-colors">
                      <div className="flex items-start gap-2 mb-0.5">
                        <ChevronRight className="w-3 h-3 text-yellow-600/60 mt-1 shrink-0" />
                        <code className="text-yellow-400 font-mono text-xs font-semibold break-all leading-tight">
                          tenshi, {item.cmd}
                          {(item as any).admin && <span className="text-red-400/60 ml-1">🔒</span>}
                        </code>
                      </div>
                      <p className="text-yellow-100/40 text-xs leading-relaxed pl-5">{item.desc}</p>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
          {filtered.length === 0 && (
            <div className="text-center py-20 text-yellow-100/30 font-mono">
              Nenhum comando encontrado para "{search}"
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-yellow-900/20 bg-black/40 py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm">
          <div className="text-yellow-100/30 font-mono">Prefixo: <span className="text-yellow-600">tenshi,</span></div>
          <div className="text-yellow-100/30">© 2016–2026 Império de Tenshi</div>
          <div className="text-yellow-100/30 font-serif italic flex items-center gap-2">
            Desenvolvido por Alloy, Imperador da Tenshi <Crown className="w-3 h-3 text-yellow-600" />
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── Admin Login ───────────────────────────────────────────────────────────────
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
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="relative z-10 w-full max-w-md">
        <div className="border border-yellow-900/40 bg-black/60 backdrop-blur-sm p-8 rounded-sm">
          <div className="text-center mb-8">
            <Lock className="w-10 h-10 text-yellow-600/70 mx-auto mb-4" />
            <h1 className="text-2xl font-black font-serif text-yellow-100/90 uppercase tracking-widest mb-1">Acesso Imperial</h1>
            <p className="text-yellow-100/30 text-sm">Preferências do Criador — Alloy</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-yellow-100/40 font-mono uppercase tracking-widest mb-2">Usuário</label>
              <input type="text" value={username} onChange={e => setUsername(e.target.value)}
                className="w-full bg-yellow-950/20 border border-yellow-900/40 text-yellow-100/90 placeholder-yellow-100/20 px-4 py-3 rounded-sm font-mono text-sm focus:outline-none focus:border-yellow-700/60 transition-colors"
                placeholder="usuário" required />
            </div>
            <div>
              <label className="block text-xs text-yellow-100/40 font-mono uppercase tracking-widest mb-2">Senha</label>
              <div className="relative">
                <input type={showPass ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full bg-yellow-950/20 border border-yellow-900/40 text-yellow-100/90 placeholder-yellow-100/20 px-4 py-3 pr-12 rounded-sm font-mono text-sm focus:outline-none focus:border-yellow-700/60 transition-colors"
                  placeholder="••••••••" required />
                <button type="button" onClick={() => setShowPass(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-yellow-100/30 hover:text-yellow-100/60 transition-colors">
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <AnimatePresence>
              {error && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}
                  className="flex items-center gap-2 text-red-400 text-xs bg-red-950/30 border border-red-900/40 px-3 py-2 rounded-sm">
                  <AlertTriangle className="w-3 h-3 shrink-0" />{error}
                </motion.div>
              )}
            </AnimatePresence>
            <button type="submit" disabled={loading} className="w-full py-3 bg-gradient-to-r from-yellow-700 to-yellow-600 text-black font-black uppercase tracking-widest text-sm rounded-sm hover:opacity-90 disabled:opacity-50 transition-opacity mt-2">
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

// ── Admin Panel ───────────────────────────────────────────────────────────────
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

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  async function handleReconnect() {
    setReconnecting(true);
    setReconnectMsg("");
    try {
      const res = await fetch(`${API_BASE}/admin/bot/reconnect`, { method: "POST", headers: authHeader });
      const data = await res.json();
      setReconnectMsg(data.message ?? data.error ?? "Sinal enviado.");
    } catch { setReconnectMsg("Erro ao enviar sinal de reconexão."); }
    finally {
      setReconnecting(false);
      setTimeout(() => fetchStatus(), 4000);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      <div className="fixed inset-0 bg-gradient-to-b from-[#0a0208] via-[#0d050f] to-[#080412]" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,rgba(158,120,21,0.06)_0%,transparent_60%)]" />
      <div className="relative z-10 max-w-4xl mx-auto px-4 py-12">
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
            <button onClick={onLogout} className="flex items-center gap-2 px-4 py-2 border border-red-900/40 text-red-400/60 hover:text-red-400 hover:border-red-700/60 transition-colors rounded-sm text-xs font-mono uppercase tracking-widest">
              <LogOut className="w-3 h-3" /> Sair
            </button>
          </div>
        </div>

        <div className="border border-yellow-900/30 bg-black/40 rounded-sm overflow-hidden mb-6">
          <div className="flex items-center justify-between px-6 py-4 border-b border-yellow-900/20">
            <div className="flex items-center gap-3">
              <Server className="w-5 h-5 text-yellow-600/60" />
              <h2 className="font-serif font-bold text-yellow-100/80 uppercase tracking-wide text-sm">Status do Bot Tenshi</h2>
            </div>
            <button onClick={fetchStatus} disabled={statusLoading} className="text-yellow-100/30 hover:text-yellow-100/60 transition-colors disabled:opacity-30">
              <RefreshCw className={`w-4 h-4 ${statusLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
          <div className="p-6">
            {statusLoading && !botStatus ? (
              <div className="flex items-center gap-3 text-yellow-100/40"><RefreshCw className="w-4 h-4 animate-spin" /><span className="text-sm">Verificando...</span></div>
            ) : botStatus ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-xs text-yellow-100/30 uppercase tracking-widest font-mono mb-2">Status</p>
                  <div className={`flex items-center gap-2 font-bold text-lg ${botStatus.online ? "text-green-400" : "text-red-400"}`}>
                    {botStatus.online ? <><CheckCircle2 className="w-5 h-5" /> Online</> : <><WifiOff className="w-5 h-5" /> Offline</>}
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
          <div className="px-6 pb-6 flex flex-wrap gap-3">
            {botStatus?.online ? (
              <button onClick={handleReconnect} disabled={reconnecting}
                className="flex items-center gap-2 px-5 py-2.5 border border-yellow-700/40 text-yellow-500/80 hover:bg-yellow-900/20 transition-all rounded-sm text-sm font-bold uppercase tracking-widest disabled:opacity-40">
                <RefreshCw className={`w-4 h-4 ${reconnecting ? "animate-spin" : ""}`} />
                {reconnecting ? "Reconectando..." : "Reconectar Bot"}
              </button>
            ) : (
              <button onClick={handleReconnect} disabled={reconnecting}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-800 to-green-700 text-white font-black uppercase tracking-widest text-sm rounded-sm hover:opacity-90 disabled:opacity-40 transition-opacity">
                <Wifi className={`w-4 h-4 ${reconnecting ? "animate-pulse" : ""}`} />
                {reconnecting ? "Ligando..." : "Ligar Bot"}
              </button>
            )}
            <a href="https://discord.com/developers/applications/1427699671052320931/bot" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 border border-indigo-700/40 text-indigo-400/70 hover:bg-indigo-900/20 transition-colors rounded-sm text-sm font-bold uppercase tracking-widest">
              <ExternalLink className="w-4 h-4" /> Developer Portal
            </a>
          </div>
          <AnimatePresence>
            {reconnectMsg && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}
                className="mx-6 mb-6 flex items-center gap-2 text-yellow-400/80 text-sm bg-yellow-950/30 border border-yellow-900/40 px-4 py-2.5 rounded-sm">
                <Activity className="w-4 h-4 shrink-0" />{reconnectMsg}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="border border-yellow-900/20 bg-black/30 rounded-sm p-6">
          <h3 className="text-xs text-yellow-100/30 uppercase tracking-widest font-mono mb-4">Informações do Sistema</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between"><span className="text-yellow-100/30">Prefixo</span><code className="text-yellow-500 font-mono">tenshi,</code></div>
              <div className="flex justify-between"><span className="text-yellow-100/30">Imperador</span><span className="text-yellow-100/60 font-mono">Alloy Tenshi</span></div>
              <div className="flex justify-between"><span className="text-yellow-100/30">Fundação</span><span className="text-yellow-100/60 font-mono">06/06/2016</span></div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between"><span className="text-yellow-100/30">Motores IA</span><span className="text-yellow-100/60 font-mono">7 (Groq)</span></div>
              <div className="flex justify-between"><span className="text-yellow-100/30">App ID</span><code className="text-yellow-500/60 font-mono text-xs">1427699671052320931</code></div>
              <div className="flex justify-between"><span className="text-yellow-100/30">Total Comandos</span><span className="text-yellow-100/60 font-mono">{commands.reduce((a,c)=>a+c.items.length,0)}+</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminPage() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(ADMIN_TOKEN_KEY));
  if (!token) return <AdminLogin onLogin={t => { setToken(t); }} />;
  return <AdminPanel token={token} onLogout={() => { localStorage.removeItem(ADMIN_TOKEN_KEY); setToken(null); }} />;
}

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
