# 🏪 Classifier: Sistema de Classificação de Produtos

Sistema de classificação automática de produtos por categoria usando regras baseadas em banco de dados.

---

## 🚀 Quick Start

```bash
# 1. Setup inicial (primeira vez apenas)
# Leia: docs/SETUP.md

# 2. Testar se funciona
python3 -m classifier.cli.classify_batch --stats

# 3. Classificar produtos
python3 -m classifier.cli.classify_batch --limit 500
```

---

## 📚 Documentação

**Leia APENAS isto:**

1. **[docs/SETUP.md](docs/SETUP.md)** - Configuração inicial
2. **[docs/RULES_VALIDATION.md](docs/RULES_VALIDATION.md)** - Reportar erros
3. **[docs/README.md](docs/README.md)** - Índice completo

**Tudo o resto está em `docs/` e é opcional.**

## 📊 Estrutura

```
classifier_regras/
├── src/classifier/          # Código-fonte
├── tests/                   # Testes
├── migrations/              # Migrations do banco
├── docs/                    # Documentação (LEIA ISTO)
│   ├── SETUP.md            # Setup
│   ├── RULES_VALIDATION.md # Reportar erros
│   ├── guides/             # Guias detalhados
│   ├── reference/          # Referência técnica
│   └── archive/            # Histórico (ignore)
└── README.md               # Este arquivo
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
