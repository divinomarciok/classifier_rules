# 🏪 Classifier: Sistema de Classificação de Produtos

Sistema de classificação automática de produtos por categoria usando regras baseadas em banco de dados.

---

## 🚀 Quick Start

```bash
# 1. Setup inicial (primeira vez)
# Rápido: docs/QUICKSTART.md
# Detalhado: docs/SETUP.md
# Com Docker: docs/SETUP_DOCKER.md

# 2. Testar se funciona
python3 -m classifier.cli.classify_batch --stats

# 3. Classificar produtos
python3 -m classifier.cli.classify_batch --limit 500
```

---

## 📚 Documentação

**Comece aqui:**

1. **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Setup rápido (5 min)
2. **[docs/SETUP.md](docs/SETUP.md)** - Setup detalhado
3. **[docs/SETUP_DOCKER.md](docs/SETUP_DOCKER.md)** - Se usar Docker

**Depois:**

4. **[docs/RULES_VALIDATION.md](docs/RULES_VALIDATION.md)** - Reportar erros de classificação
5. **[docs/README.md](docs/README.md)** - Índice de documentação
6. **[docs/guides/](docs/guides/)** - Guias técnicos
7. **[docs/reference/](docs/reference/)** - Referência técnica

## 📊 Estrutura

```
classifier_regras/
├── src/classifier/          # Código-fonte
├── tests/                   # Testes
├── migrations/              # Migrations do banco
├── docs/                    # Documentação
│   ├── QUICKSTART.md        # Setup rápido (comece aqui!)
│   ├── SETUP.md             # Setup detalhado
│   ├── SETUP_DOCKER.md      # Setup com Docker
│   ├── RULES_VALIDATION.md  # Reportar erros
│   ├── README.md            # Índice de docs
│   ├── guides/              # Guias técnicos
│   └── reference/           # Referência técnica
├── README.md                # Este arquivo
└── .env.example             # Configuração exemplo
```

---

## 🎯 O Que Fazer

### Primeira Vez?
→ Leia `docs/SETUP.md`

### Encontrou Produto Errado?
→ Leia `docs/RULES_VALIDATION.md`

### Quer Aprender Profundo?
→ Leia `docs/README.md` e explore `docs/guides/`

---

## ✅ Testes

```bash
pytest tests/ -v
```
