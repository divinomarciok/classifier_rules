# 🐳 Setup para PostgreSQL no Docker

Se você está rodando PostgreSQL no Docker, siga este guia.

---

## 📍 Passo 1: Verificar se o Container Docker Está Rodando

```bash
# Ver containers em execução
docker ps

# Ou ver todos os containers
docker ps -a
```

Procure por um container com PostgreSQL. Exemplo:
```
CONTAINER ID   IMAGE           NAMES
abc123def456   postgres:15     pg-classifier
```

Se o container não está rodando:
```bash
# Iniciar o container (substitua o nome do seu container)
docker start pg-classifier

# Ou criar um novo container
docker run -d \
  --name pg-classifier \
  -e POSTGRES_PASSWORD=senha_secreta \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=market_v1 \
  -p 5432:5432 \
  postgres:15
```

---

## 📍 Passo 2: Configurar as Credenciais no .env

Edite o arquivo `.env`:

```bash
nano .env
```

Configure com as credenciais do seu container Docker:

```bash
# Database Configuration
DB_HOST=localhost              # Ou o IP do seu Docker host
DB_NAME=market_v1              # Nome do banco criado
DB_USER=postgres               # Usuário padrão
DB_PASSWORD=senha_secreta      # A senha que você configurou
DB_PORT=5432                   # Porta padrão PostgreSQL

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

---

## 📍 Passo 3: Executar o Setup

Agora o script `setup.sh` foi corrigido para aceitar PostgreSQL no Docker:

```bash
bash setup.sh
```

**O que o script fará:**
- ✅ Cria ambiente virtual Python (venv)
- ✅ Instala dependências
- ✅ Copia .env (se não existir)
- ⏭️ Pula verificação se psql não está instalado (ok para Docker)
- ⏭️ Tenta rodar migrations (pede confirmação se conseguir conectar)
- ✅ Testa conexão com banco

---

## 📍 Passo 4: Ativar Ambiente Virtual

Após o setup:

```bash
source venv/bin/activate
```

Você deve ver `(venv)` no seu prompt.

---

## 📍 Passo 5: Verificar Conexão

```bash
# Teste a conexão (após ativar venv)
python3 -m classifier.cli.classify_batch --stats
```

Se conectar com sucesso, você verá estatísticas dos produtos.

---

## 🛠️ Troubleshooting

### ❌ Erro: `could not connect to server`

**Solução:**
1. Verifique se o container Docker está rodando:
   ```bash
   docker ps
   ```

2. Verifique se as credenciais em `.env` estão corretas

3. Teste a conexão diretamente (se tiver psql instalado):
   ```bash
   psql -U postgres -h localhost -d market_v1 -c "SELECT 1;"
   ```

### ❌ Erro: `password authentication failed`

**Solução:**
- Verifique a senha em `.env`
- Ou resete o container:
  ```bash
  docker stop pg-classifier
  docker rm pg-classifier
  docker run -d \
    --name pg-classifier \
    -e POSTGRES_PASSWORD=nova_senha \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_DB=market_v1 \
    -p 5432:5432 \
    postgres:15
  ```

### ❌ Erro: `database "market_v1" does not exist`

**Solução:**
- Quando criou o container, esqueceu de adicionar `-e POSTGRES_DB=market_v1`
- Crie o banco dentro do container:
  ```bash
  docker exec pg-classifier psql -U postgres -c "CREATE DATABASE market_v1;"
  ```

### ❌ PostgreSQL cliente não encontrado

**Solução (opcional):**
Se quiser instalar o cliente PostgreSQL localmente:
```bash
# Linux
sudo apt-get install postgresql-client

# macOS
brew install postgresql
```

Mas não é necessário - o script foi ajustado para funcionar sem ele.

---

## 🚀 Setup Completo (Docker)

Resume:

```bash
# 1. Certifique que Docker está rodando
docker ps

# 2. Inicie o container PostgreSQL (se não estiver)
docker start pg-classifier

# 3. Configure .env com credenciais do Docker
nano .env

# 4. Execute o setup
bash setup.sh

# 5. Ative venv
source venv/bin/activate

# 6. Teste
python3 -m classifier.cli.classify_batch --stats

# Pronto! ✅
```

---

## 📞 Próximos Passos

Após o setup estar funcionando:

```bash
# Ver estatísticas
python3 -m classifier.cli.classify_batch --stats

# Classificar 100 produtos
python3 -m classifier.cli.classify_batch --limit 100

# Rodar testes
pytest tests/unit/ -v
```

---

## 💡 Dicas

- Sempre verifique que o container Docker está rodando antes de usar o projeto
- As credenciais em `.env` devem coincidir com as do container
- Se o container foi removido, recrie-o com os mesmos parâmetros
- Para ver os logs do container: `docker logs pg-classifier`

---

**Pronto?** Volte para `QUICKSTART.md` ou `docs/GUIA_COMPLETO.md`
