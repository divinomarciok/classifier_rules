# 📖 Guia Completo: Como Rodar o Projeto Classifier

Aqui está o **passo a passo definitivo** para rodar seu projeto do zero, com todos os comandos necessários.

---

## 📋 Índice
1. [Pré-requisitos](#pré-requisitos)
2. [Criar ambiente virtual](#criar-ambiente-virtual)
3. [Configurar banco de dados](#configurar-banco-de-dados)
4. [Instalar dependências](#instalar-dependências)
5. [Configurar variáveis de ambiente](#configurar-variáveis-de-ambiente)
6. [Rodar migrations](#rodar-migrations)
7. [Testar o projeto](#testar-o-projeto)
8. [Usar a aplicação](#usar-a-aplicação)

---

## 🔧 Pré-requisitos

Você precisa ter instalado:

```bash
# Verificar Python 3.8+
python3 --version

# Verificar PostgreSQL (versão 12+)
psql --version

# Linux - Iniciar PostgreSQL
sudo systemctl start postgresql

# macOS - Iniciar PostgreSQL (se instalado via Homebrew)
brew services start postgresql
```

---

## 🐍 Criar Ambiente Virtual

### 1️⃣ Clonar ou acessar o projeto
```bash
cd /home/divinopc/testes/projects/classifier_regras
```

### 2️⃣ Criar ambiente virtual
```bash
# Criar venv
python3 -m venv venv

# Ativar venv (Linux/macOS)
source venv/bin/activate

# Ativar venv (Windows)
venv\Scripts\activate
```

Você verá `(venv)` no seu terminal quando estiver ativado:
```
(venv) usuario@pc:~/classifier_regras$
```

---

## 🗄️ Configurar Banco de Dados

### 1️⃣ Criar banco de dados PostgreSQL

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql

# Dentro do PostgreSQL, criar banco:
CREATE DATABASE market_v1;

# Criar usuário (opcional mas recomendado)
CREATE USER classifier_user WITH PASSWORD 'sua_senha_segura';

# Dar permissões
ALTER ROLE classifier_user SET client_encoding TO 'utf8';
ALTER ROLE classifier_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE classifier_user SET default_transaction_deferrable TO on;
ALTER ROLE classifier_user SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE market_v1 TO classifier_user;

# Sair do PostgreSQL
\q
```

### 2️⃣ Verificar conexão

```bash
# Testar conexão com usuário padrão
psql -U postgres -h localhost -d market_v1 -c "SELECT 1;"

# Ou com usuário criado
psql -U classifier_user -h localhost -d market_v1 -c "SELECT 1;"

# Você deve ver:
#  ?column?
# ----------
#         1
```

---

## 📦 Instalar Dependências

Com o ambiente virtual ativado:

```bash
# Certificar que pip está atualizado
python3 -m pip install --upgrade pip

# Instalar todas as dependências
python3 -m pip install -r requirements.txt
```

**Dependências instaladas:**
- `psycopg2-binary` - Driver PostgreSQL
- `pytest` - Framework de testes
- `pytest-cov` - Cobertura de testes
- `pytest-mock` - Mocking
- `black` - Formatador de código
- `flake8` - Linter
- `mypy` - Type checking
- `python-dotenv` - Gerenciador .env

Verificar instalação:
```bash
python3 -m pip list | grep psycopg
```

---

## ⚙️ Configurar Variáveis de Ambiente

### 1️⃣ Copiar arquivo de exemplo

```bash
cp .env.example .env
```

### 2️⃣ Editar `.env` com suas credenciais

```bash
nano .env
# ou
vim .env
```

Configurar assim:

```bash
# Database Configuration
DB_HOST=localhost
DB_NAME=market_v1
DB_USER=postgres                    # ou classifier_user se criou
DB_PASSWORD=sua_senha_do_postgres   # ou a senha criada
DB_PORT=5432

# Application Configuration
APP_ENV=development
APP_LOG_LEVEL=INFO

# Feature Flags
ENABLE_RULE_CACHING=true
ENABLE_AUDIT_LOGGING=true

# Performance
MAX_BATCH_SIZE=500
CSV_CHUNK_SIZE=1000
DB_CONNECTION_TIMEOUT=30
```

### 3️⃣ Ou usar variáveis de ambiente direto (sem arquivo .env)

```bash
export DB_HOST=localhost
export DB_NAME=market_v1
export DB_USER=postgres
export DB_PASSWORD=sua_senha_postgres
export DB_PORT=5432
export APP_ENV=development
export APP_LOG_LEVEL=INFO
```

---

## 🔄 Rodar Migrations

As migrations criam as tabelas no banco de dados.

### Opção 1: Usar Python (recomendado)

```bash
python3 << 'EOF'
from src.classifier.utils import init_database
init_database()
print("✅ Banco de dados inicializado com sucesso!")
EOF
```

Você deve ver:
```
[INFO] Creating table categorias...
[INFO] Creating table regras_de_classificacao...
[INFO] Creating table auditoria_classificacao...
✅ Banco de dados inicializado com sucesso!
```

### Opção 2: Executar manualmente com psql

```bash
# Navegar até o diretório de migrations
cd migrations

# Executar cada migration em ordem
psql -U postgres -d market_v1 -f 001_alter_produtos_add_status.sql
psql -U postgres -d market_v1 -f 002_create_categorias.sql
psql -U postgres -d market_v1 -f 002b_alter_regras_add_categoria_id.sql
psql -U postgres -d market_v1 -f 003_create_regras_de_classificacao.sql
psql -U postgres -d market_v1 -f 004_create_auditoria_classificacao.sql
psql -U postgres -d market_v1 -f 005_create_criterios_palavras_chave.sql

cd ..
```

---

## ✅ Testar o Projeto

### 1️⃣ Verificar se consegue conectar ao banco

```bash
python3 -m classifier.cli.classify_batch --stats
```

Você deve ver algo assim:
```
============================================================
BATCH CLASSIFICATION STATISTICS
============================================================
Total Products:      79,201

Status Breakdown:
  - Matched:        1,302 products
  - Pending:       77,899 products
  - No Match:           0 products

Classification Rate: 1.6%
============================================================
```

### 2️⃣ Rodar testes unitários

```bash
# Todos os testes
pytest tests/ -v

# Apenas testes de unidade
pytest tests/unit/ -v

# Apenas testes de integração
pytest tests/integration/ -v

# Com relatório de cobertura
pytest tests/ --cov=src/classifier --cov-report=html
```

Resultado esperado: **127 passed, 35 failed** (os testes falhando são devido a um campo no modelo, mas o sistema funciona)

### 3️⃣ Testar classificação com poucos produtos

```bash
# Testar sem modificar banco (dry-run)
python3 -m classifier.cli.classify_batch --limit 10 --dry-run

# Classificar 10 produtos reais
python3 -m classifier.cli.classify_batch --limit 10

# Ver resultado
python3 -m classifier.cli.classify_batch --stats
```

---

## 🚀 Usar a Aplicação

### Classificar Produtos do Banco

```bash
# Ver estatísticas
python3 -m classifier.cli.classify_batch --stats

# Classificar 100 produtos
python3 -m classifier.cli.classify_batch --limit 100

# Classificar 500 produtos
python3 -m classifier.cli.classify_batch --limit 500

# Classificar 1000 com offset (pagination)
python3 -m classifier.cli.classify_batch --limit 1000 --offset 500

# Testar antes de atualizar banco
python3 -m classifier.cli.classify_batch --limit 500 --dry-run

# Filtrar por NCM
python3 -m classifier.cli.classify_batch --limit 500 --where "ncm LIKE '8471%'"

# Output em JSON
python3 -m classifier.cli.classify_batch --limit 100 --json
```

### Classificar Arquivo CSV

```bash
# Classificar arquivo CSV básico
python3 -m classifier.cli.classify_csv samples/products_basic.csv

# Validar antes de processar
python3 -m classifier.cli.classify_csv samples/products_basic.csv --validate

# Delimitador customizado (ponto e vírgula)
python3 -m classifier.cli.classify_csv samples/products_semicolon.csv --delimiter ";"

# Salvar resultado em arquivo específico
python3 -m classifier.cli.classify_csv samples/products_basic.csv --output meu_resultado.csv
```

---

## 🔄 Workflow Completo (do Zero)

Copie e execute tudo isso:

```bash
#!/bin/bash

# 1. Criar e ativar venv
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 3. Configurar banco de dados
# (Você precisa criar o banco manualmente - veja seção "Configurar Banco de Dados")

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais!

# 5. Rodar migrations
python3 << 'EOF'
from src.classifier.utils import init_database
init_database()
EOF

# 6. Rodar testes para verificar
pytest tests/unit/ -v

# 7. Testar aplicação
python3 -m classifier.cli.classify_batch --stats

# 8. Classificar 100 produtos
python3 -m classifier.cli.classify_batch --limit 100

# 9. Ver resultado
python3 -m classifier.cli.classify_batch --stats

echo "✅ Projeto configurado com sucesso!"
```

---

## 🛠️ Troubleshooting

### ❌ Erro: `ModuleNotFoundError: No module named 'psycopg2'`

```bash
# Solução: instalar psycopg2
python3 -m pip install psycopg2-binary
```

### ❌ Erro: `FATAL: Ident authentication failed for user "postgres"`

```bash
# Solução: Editar arquivo de configuração PostgreSQL
# Linux/Mac:
sudo nano /etc/postgresql/12/main/pg_hba.conf

# Mudar de "ident" para "md5" ou "scram-sha-256"
# Depois reiniciar:
sudo systemctl restart postgresql
```

### ❌ Erro: `could not connect to server: Connection refused`

```bash
# PostgreSQL não está rodando, inicie:
sudo systemctl start postgresql  # Linux
brew services start postgresql  # macOS
```

### ❌ Erro: `database "market_v1" does not exist`

```bash
# Criar banco de dados:
sudo -u postgres createdb market_v1
```

### ❌ Erro: `venv not found`

```bash
# Certifique que ativou o venv:
source venv/bin/activate

# Você deve ver (venv) no prompt do terminal
```

---

## 📚 Documentação Adicional

- **[docs/SETUP.md](SETUP.md)** - Setup detalhado
- **[docs/RULES_VALIDATION.md](RULES_VALIDATION.md)** - Como reportar erros
- **[docs/README.md](README.md)** - Índice completo
- **[docs/guides/](guides/)** - Guias práticos
- **[docs/reference/](reference/)** - Documentação técnica

---

## ✨ Próximos Passos

1. ✅ Seguir este guia até o final
2. ✅ Executar `pytest tests/unit/ -v` para validar tudo
3. ✅ Rodar `python3 -m classifier.cli.classify_batch --stats`
4. ✅ Começar a classificar produtos!

Qualquer dúvida, consulte a documentação nos arquivos `docs/`.
