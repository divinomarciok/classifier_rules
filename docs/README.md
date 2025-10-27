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

### [guides/DATABASE_MIGRATION_GUIDE.md](guides/DATABASE_MIGRATION_GUIDE.md)
Como migrar o banco de dados ou alterar a estrutura da tabela

### [guides/RULE_UPDATE_PROCESS.md](guides/RULE_UPDATE_PROCESS.md)
Processo completo de atualizar/criar regras de classificação

### [guides/RULE_VALIDATION_INDEX.md](guides/RULE_VALIDATION_INDEX.md)
Índice de navegação entre documentos de validação

---

## 🔍 Referência Técnica

Pasta: `reference/`

### [reference/CURRENT_ARCHITECTURE.md](reference/CURRENT_ARCHITECTURE.md)
- Estrutura do código
- Como funciona internamente
- Fluxo de dados
- Acesso ao banco


---

## 📊 Resumo Rápido

| Pasta | Para | Quando Ler |
|-------|------|-----------|
| `/docs` | Documentação principal | Sempre |
| `/docs/guides` | Aprender processos | Aprendizado |
| `/docs/reference` | Entender tecnicamente | Desenvolvimento |

---

## ✅ Arquitetura Documentação

```
classifier_regras/
├── README.md (principal - obrigatório)
├── QUICKSTART.md (setup rápido)
├── SETUP_DOCKER.md (setup para Docker)
├── setup.sh (script automático)
├── docs/
│   ├── README.md (este arquivo)
│   ├── SETUP.md (como configurar)
│   ├── RULES_VALIDATION.md (reportar erros)
│   ├── guides/
│   │   ├── DATABASE_MIGRATION_GUIDE.md
│   │   ├── RULE_UPDATE_PROCESS.md
│   │   └── RULE_VALIDATION_INDEX.md
│   └── reference/
│       └── CURRENT_ARCHITECTURE.md
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
Veja instruções em `.claude/claude.md`


## ✨ Conclusão

**Leia apenas**:
1. `docs/SETUP.md` - uma vez
2. `docs/RULES_VALIDATION.md` - quando precisar reportar
3. `docs/guides/` - se quiser aprender profundo
4. `docs/reference/` - se estiver desenvolvendo

**Tudo organizado, nada perdido!**

