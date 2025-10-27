# 📚 Índice de Documentação - Classifier Project

Bem-vindo! Este arquivo ajuda você a encontrar o guia certo para sua necessidade.

---

## 🚀 Comecei do Zero - Por Onde Começo?

### Opção 1: Automático (recomendado)
1. Leia: **[QUICKSTART.md](QUICKSTART.md)** (2 min) - Overview rápido
2. Execute: **[setup.sh](setup.sh)** (5 min) - Script que faz tudo automaticamente
3. Pronto! Seu projeto está funcionando

### Opção 2: Manual
1. Leia: **[QUICKSTART.md](QUICKSTART.md)** (2 min) - Entenda o processo
2. Siga: **[docs/GUIA_COMPLETO.md](docs/GUIA_COMPLETO.md)** (20 min) - Instruções passo a passo
3. Use: **[SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)** (10 min) - Verifique tudo

---

## 📖 Documentação por Cenário

### 1️⃣ "Quero rodar rápido!"
→ Leia: **[QUICKSTART.md](QUICKSTART.md)**
- Setup em 5 minutos
- Apenas o essencial
- Próximos comandos

### 2️⃣ "Preciso de instruções detalhadas"
→ Leia: **[docs/GUIA_COMPLETO.md](docs/GUIA_COMPLETO.md)**
- Explica cada passo
- Mostra alternativas
- Inclui troubleshooting
- **⭐ RECOMENDADO para primeira vez**

### 3️⃣ "Vou seguir um checklist"
→ Use: **[SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)**
- Checklist completo
- Comandos de verificação
- Pronto para imprimir/usar offline

### 4️⃣ "Quero automatizar tudo"
→ Execute: **[setup.sh](setup.sh)**
```bash
bash setup.sh
```
- Cria venv
- Instala dependências
- Configura banco
- Roda migrations
- Testa tudo automaticamente

### 5️⃣ "Encontrei um erro"
→ Veja: **[docs/GUIA_COMPLETO.md#-troubleshooting](docs/GUIA_COMPLETO.md)** (seção Troubleshooting)
- Erros comuns
- Soluções prontas
- Como diagnosticar

### 6️⃣ "Já configurei, como uso?"
→ Consulte: **[docs/SETUP.md](docs/SETUP.md)** ou **[QUICKSTART.md](QUICKSTART.md)**
- Comandos principais
- Exemplos de uso
- Flags disponíveis

---

## 📂 Estrutura de Documentação

```
classifier_regras/
├── QUICKSTART.md                 ⭐ Comece aqui (5 min)
├── setup.sh                      ⭐ Execute isto (automático)
├── SETUP_CHECKLIST.md            ✅ Verifique isto
├── DOCUMENTACAO_GUIAS.md         📍 Este arquivo
│
├── docs/
│   ├── GUIA_COMPLETO.md          📖 Tudo em detalhes (RECOMENDADO)
│   ├── SETUP.md                  🔧 Setup inicial
│   ├── RULES_VALIDATION.md       🎯 Validar regras
│   ├── README.md                 📄 Índice geral
│   │
│   ├── guides/                   📚 Guias práticos
│   │   ├── DATABASE_MIGRATION_GUIDE.md
│   │   ├── RULE_UPDATE_PROCESS.md
│   │   ├── RULE_VALIDATION_INDEX.md
│   │   └── QUICK_RULE_VALIDATION.md
│   │
│   └── reference/                📖 Referência técnica
│       ├── CURRENT_ARCHITECTURE.md
│       └── CLAUDE_INSTRUCTIONS.md
│
├── requirements.txt              📦 Dependências Python
├── .env.example                  ⚙️  Variáveis de ambiente
└── README.md                     📋 README principal
```

---

## 📺 Fluxo de Leitura Recomendado

### Para Iniciantes (primeira vez)

```
1. QUICKSTART.md (5 min)
   ↓ Entender o processo geral
2. setup.sh (5 min automático)
   ↓ Ou GUIA_COMPLETO.md se quiser fazer manual
3. SETUP_CHECKLIST.md (5 min)
   ↓ Verificar se tudo funcionou
4. Próximo: docs/SETUP.md (se encontrar problemas)
```

### Para Desenvolvedores

```
1. QUICKSTART.md (entender overview)
   ↓
2. docs/GUIA_COMPLETO.md (detalhes completos)
   ↓
3. docs/reference/CURRENT_ARCHITECTURE.md (como funciona)
   ↓
4. docs/guides/ (conforme necessário)
```

### Para Integração/CI-CD

```
1. setup.sh (script de setup)
   ↓
2. docs/GUIA_COMPLETO.md (para troubleshooting)
   ↓
3. docs/guides/DATABASE_MIGRATION_GUIDE.md
```

---

## 🎯 Matriz de Documentos

| Necessidade | Documento | Tempo | Nível |
|-------------|-----------|-------|-------|
| Começar rápido | QUICKSTART.md | 5 min | Iniciante |
| Setup automático | setup.sh | 5 min | Qualquer |
| Setup manual completo | GUIA_COMPLETO.md | 20 min | Iniciante |
| Verificar setup | SETUP_CHECKLIST.md | 10 min | Qualquer |
| Resolver problemas | GUIA_COMPLETO.md (Troubleshooting) | 10 min | Qualquer |
| Entender arquitetura | reference/CURRENT_ARCHITECTURE.md | 15 min | Desenvolvedor |
| Usar a aplicação | QUICKSTART.md + SETUP.md | 5 min | Qualquer |
| Validar regras | RULES_VALIDATION.md | 10 min | Qualquer |

---

## ✅ Após Completar o Setup

Após instalar e configurar, você pode:

```bash
# 1. Ver estatísticas
python3 -m classifier.cli.classify_batch --stats

# 2. Classificar 100 produtos
python3 -m classifier.cli.classify_batch --limit 100

# 3. Rodar testes
pytest tests/unit/ -v

# 4. Processar CSV
python3 -m classifier.cli.classify_csv arquivo.csv

# Mais? Veja docs/SETUP.md
```

---

## 🆘 Precisa de Ajuda?

### Erro na instalação?
→ **[docs/GUIA_COMPLETO.md#-troubleshooting](docs/GUIA_COMPLETO.md)** (seção Troubleshooting)

### Erro ao rodar?
→ **[docs/SETUP.md](docs/SETUP.md)** (seção de troubleshooting)

### Como validar regras?
→ **[docs/RULES_VALIDATION.md](docs/RULES_VALIDATION.md)**

### Como é a arquitetura?
→ **[docs/reference/CURRENT_ARCHITECTURE.md](docs/reference/CURRENT_ARCHITECTURE.md)**

### Guias práticos?
→ **[docs/guides/](docs/guides/)**

---

## 📱 TL;DR (Tl;Dr)

**Não tem tempo? Faça isto:**

```bash
# 1. Execute o script (5 min)
bash setup.sh

# 2. Ative venv
source venv/bin/activate

# 3. Teste
python3 -m classifier.cli.classify_batch --stats

# Pronto! ✅
```

---

## 📞 Resumo Rápido

| Situação | Ação |
|----------|------|
| Primeira vez | Execute: `bash setup.sh` |
| Quer detalhes | Leia: `docs/GUIA_COMPLETO.md` |
| Encontrou erro | Veja: `docs/GUIA_COMPLETO.md` (Troubleshooting) |
| Quer usar agora | Siga: `QUICKSTART.md` |
| Verificar tudo | Use: `SETUP_CHECKLIST.md` |

---

**Última atualização:** 26/10/2025

**Versão:** 1.0 - Documentação Completa

Qualquer dúvida, comece por **[QUICKSTART.md](QUICKSTART.md)** ou execute **`bash setup.sh`** ⭐
