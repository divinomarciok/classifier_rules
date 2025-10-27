# ⚙️ Setup Inicial do Projeto

**Leia isto PRIMEIRO se está começando do zero.**

Se PostgreSQL está em Docker, veja `../SETUP_DOCKER.md`.

---

## 1️⃣ Pré-requisitos

```bash
# Python 3.8+
python3 --version

# PostgreSQL (local OU Docker)
# Se local:
sudo systemctl start postgresql  # Linux
brew services start postgresql  # Mac

# Se Docker:
docker start pg-classifier  # ou seu container name
```

---

## 2️⃣ Criar Banco de Dados (se local)

```bash
# Se usando PostgreSQL local
createdb -U postgres market_v1

# Se usando Docker, banco já deve existir
# Ou criar com: docker exec pg-classifier psql -U postgres -c "CREATE DATABASE market_v1;"
```

---

## 3️⃣ Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas credenciais
nano .env
```

Configure (exemplo para Docker):
```bash
DB_HOST=localhost
DB_NAME=market_v1
DB_USER=postgres
DB_PASSWORD=sua_senha_docker
DB_PORT=5432
```

---

## 4️⃣ Setup Automático

```bash
bash setup.sh
```

O script faz:
- ✅ Cria venv
- ✅ Instala dependências
- ✅ Configura .env (se não existir)
- ✅ Tenta rodar migrations
- ✅ Testa conexão

---

## 5️⃣ Rodar Migrations Manualmente (se necessário)

```bash
python3 << 'EOF'
from src.classifier.utils import init_database
init_database()
EOF
```

---

## 6️⃣ Rodar Testes

```bash
# Todos os testes
pytest tests/ -v

# Apenas unitários
pytest tests/unit/ -v
```

---

## 7️⃣ Testar Classificação

```bash
# Ver estatísticas
python3 -m classifier.cli.classify_batch --stats

# Classificar 100 produtos
python3 -m classifier.cli.classify_batch --limit 100

# Testar sem atualizar banco
python3 -m classifier.cli.classify_batch --limit 100 --dry-run
```

---

## ✅ Pronto!

Se tudo funcionou, seu projeto está configurado.

**Próximo**:
- Se encontrou produtos errados: `docs/RULES_VALIDATION.md`
- Para entender a arquitetura: `docs/reference/CURRENT_ARCHITECTURE.md`
- Para migração de banco: `docs/guides/DATABASE_MIGRATION_GUIDE.md`

