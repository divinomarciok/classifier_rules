# ⚙️ Setup Inicial do Projeto

**Leia isto PRIMEIRO se está começando do zero.**

---

## 1️⃣ Pré-requisitos

```bash
# PostgreSQL rodando
sudo systemctl start postgresql  # Linux
brew services start postgresql  # Mac

# Criar banco de dados
createdb -U postgres market_v1

# Python 3.8+
python3 --version

# Instalar dependências
python3 -m pip install psycopg2-binary pytest pytest-cov
```

---

## 2️⃣ Configurar Banco de Dados

```bash
# Variáveis de ambiente
export DB_HOST=localhost
export DB_NAME=market_v1
export DB_USER=postgres
export DB_PASSWORD=sua_senha

# Testar conexão
psql -U postgres -h localhost -d market_v1 -c "SELECT 1;"
```

---

## 3️⃣ Rodar Migrations

```bash
# Executar todas as migrations
python3 << 'EOF'
from src.classifier.utils import init_database
init_database()
EOF
```

---

## 4️⃣ Rodar Testes

```bash
# Todos os testes
pytest tests/ -v

# Apenas unitários
pytest tests/unit/ -v
```

---

## 5️⃣ Testar Batch Classification

```bash
# Ver estatísticas
python3 -m classifier.cli.classify_batch --stats

# Classificar produtos
python3 -m classifier.cli.classify_batch --limit 100
```

---

## ✅ Pronto!

Se tudo rodou sem erro, seu projeto está configurado.

**Próximo**: Leia `docs/RULES_VALIDATION.md` se encontrar produtos errados.

