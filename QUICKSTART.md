# ⚡ Quick Start - Classifier Project

**Forma mais rápida de começar!**

---

## 🚀 Setup em 5 Minutos

### 1️⃣ Execute o script de setup (automático)

```bash
cd /path/to/classifier_regras
bash setup.sh
```

O script faz tudo automaticamente:
- ✅ Cria ambiente virtual
- ✅ Instala dependências
- ✅ Configura .env
- ✅ Roda migrations
- ✅ Testa a conexão

---

## 📝 Ou Faça Manualmente (5 passos)

### 1. Ativar ambiente virtual

```bash
source venv/bin/activate
```

### 2. Instalar dependências

```bash
python3 -m pip install -r requirements.txt
```

### 3. Configurar banco (uma vez)

```bash
sudo -u postgres psql
CREATE DATABASE market_v1;
\q
```

### 4. Configurar .env

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

### 5. Rodar migrations

```bash
python3 << 'EOF'
from src.classifier.utils import init_database
init_database()
EOF
```

---

## 🎯 Primeiros Comandos

### Ver estatísticas

```bash
python3 -m classifier.cli.classify_batch --stats
```

### Classificar 100 produtos

```bash
python3 -m classifier.cli.classify_batch --limit 100
```

### Testar sem atualizar banco

```bash
python3 -m classifier.cli.classify_batch --limit 100 --dry-run
```

### Rodar testes

```bash
pytest tests/unit/ -v
```

---

## 📚 Próximos Passos

1. Leia **[docs/GUIA_COMPLETO.md](docs/GUIA_COMPLETO.md)** para entender tudo em detalhes
2. Leia **[docs/SETUP.md](docs/SETUP.md)** para problemas de configuração
3. Leia **[docs/RULES_VALIDATION.md](docs/RULES_VALIDATION.md)** para validar regras

---

## 🆘 Erro? Confira Isso

| Erro | Solução |
|------|---------|
| `psycopg2` not found | `python3 -m pip install psycopg2-binary` |
| Cannot connect to database | `sudo systemctl start postgresql` |
| Database doesn't exist | `sudo -u postgres createdb market_v1` |
| venv not found | `python3 -m venv venv && source venv/bin/activate` |

---

## ⭐ Dicas

- Sempre ative o venv: `source venv/bin/activate`
- Use `--dry-run` antes de atualizar o banco
- Use `--limit 100` para testes rápidos
- PostgreSQL deve estar rodando antes de usar

---

**Mais informações?** → Leia [docs/GUIA_COMPLETO.md](docs/GUIA_COMPLETO.md)
