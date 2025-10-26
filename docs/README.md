# 📚 Documentação do Classifier

Organização clara e simples da documentação do projeto.

---

## 🚀 Comece Aqui (Obrigatório Ler)

### 1. [SETUP.md](SETUP.md)
**Leia PRIMEIRO**
- Como instalar e configurar o projeto
- Pré-requisitos
- Banco de dados
- Como rodar tudo

**Tempo**: 10 minutos

---

### 2. [RULES_VALIDATION.md](RULES_VALIDATION.md)
**Leia quando encontrar produtos errados**
- Como identificar erros
- Como reportar
- Como as correções funcionam
- Template de reporte

**Tempo**: 5 minutos

---

## 📖 Guias Específicos

Pasta: `guides/`

### [guides/RULE_UPDATE_PROCESS.md](guides/RULE_UPDATE_PROCESS.md)
Entender o processo técnico completo de atualizar regras

### [guides/QUICK_RULE_VALIDATION.md](guides/QUICK_RULE_VALIDATION.md)
Referência rápida com checklist e exemplos

### [guides/RULE_ERRORS_CATALOG.md](guides/RULE_ERRORS_CATALOG.md)
Erros já encontrados e como foram corrigidos

---

## 🔍 Referência Técnica

Pasta: `reference/`

### [reference/CURRENT_ARCHITECTURE.md](reference/CURRENT_ARCHITECTURE.md)
- Estrutura do código
- Como funciona internamente
- Fluxo de dados

### [reference/DATABASE_SETUP.md](reference/DATABASE_SETUP.md)
- Schema do banco
- Tabelas e colunas
- Migrations

### [reference/CLAUDE_INSTRUCTIONS.md](reference/CLAUDE_INSTRUCTIONS.md)
Instruções para Claude Code trabalhar no projeto

---

## 📋 Documentos Antigos (Arquivo)

Pasta: `archive/`

Documentos históricos mantidos para referência:
- CHANGELOG.md
- IMPLEMENTATION_LOG.md
- IMPLEMENTATION_STATUS.md
- PROJECT_SUMMARY.md
- etc.

**Não leia a menos que tenha curiosidade sobre a história do projeto.**

---

## 📊 Resumo Rápido

| Pasta | Para | Quando Ler |
|-------|------|-----------|
| `/docs` | Documentação principal | Sempre |
| `/docs/guides` | Aprender processos | Aprendizado |
| `/docs/reference` | Entender tecnicamente | Desenvolvimento |
| `/docs/archive` | Histórico | Nunca (a menos que queira) |

---

## ✅ Arquitetura Documentação

```
classifier_regras/
├── README.md (principal - obrigatório)
├── docs/
│   ├── README.md (este arquivo)
│   ├── SETUP.md (como configurar)
│   ├── RULES_VALIDATION.md (reportar erros)
│   ├── guides/
│   │   ├── RULE_UPDATE_PROCESS.md
│   │   ├── QUICK_RULE_VALIDATION.md
│   │   └── RULE_ERRORS_CATALOG.md
│   ├── reference/
│   │   ├── CURRENT_ARCHITECTURE.md
│   │   ├── DATABASE_SETUP.md
│   │   └── CLAUDE_INSTRUCTIONS.md
│   └── archive/
│       ├── CHANGELOG.md
│       ├── IMPLEMENTATION_LOG.md
│       └── (19 outros documentos históricos)
├── src/
├── tests/
├── migrations/
└── ...
```

---

## 🎯 Fluxo de Trabalho

### Para Usuário Normal:
1. Primeiro setup? → Leia `SETUP.md`
2. Encontrou erro? → Leia `RULES_VALIDATION.md`
3. Quer aprender? → Explore `guides/`

### Para Claude Code:
1. Toda ação começa em `reference/CLAUDE_INSTRUCTIONS.md`
2. Processo técnico? → `guides/RULE_UPDATE_PROCESS.md`
3. Estrutura código? → `reference/CURRENT_ARCHITECTURE.md`

---

## 🚫 Documentos NÃO Leia

Estes estão no `/archive` por razão - são históricos:

- ❌ EXACT_CHANGES.md
- ❌ IMPLEMENTATION_CHECKLIST.md
- ❌ IMPLEMENTATION_LOG.md
- ❌ IMPLEMENTATION_STATUS.md
- ❌ INDEX.md (antigo)
- ❌ NEXT_STEPS.md
- ❌ NO_MATCH_FIX_IMPLEMENTATION.md
- ❌ NO_MATCH_ISSUE.md
- ❌ PHASE_2_IMPLEMENTATION_COMPLETE.md
- ❌ PROJECT_SUMMARY.md
- ❌ TESTING_GUIDE.md

Todos esses estão em `/docs/archive/` - **não leia a menos que queira entender a história**.

---

## ✨ Conclusão

**Leia apenas**:
1. `docs/SETUP.md` - uma vez
2. `docs/RULES_VALIDATION.md` - quando precisar reportar
3. `docs/guides/` - se quiser aprender profundo
4. `docs/reference/` - se estiver desenvolvendo

**Tudo organizado, nada perdido!**

