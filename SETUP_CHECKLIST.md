# ✅ Setup Checklist - Classifier Project

Use este checklist para garantir que tudo está configurado corretamente.

---

## 📋 Pré-requisitos

- [ ] Python 3.8+ instalado
  ```bash
  python3 --version  # Deve ser 3.8 ou maior
  ```

- [ ] PostgreSQL 12+ instalado
  ```bash
  psql --version  # Deve ser 12 ou maior
  ```

- [ ] PostgreSQL rodando
  ```bash
  sudo systemctl start postgresql  # Linux
  brew services start postgresql  # macOS
  ```

---

## 🔧 Configuração Inicial

- [ ] Navegar para o diretório do projeto
  ```bash
  cd /home/divinopc/testes/projects/classifier_regras
  ```

- [ ] Criar ambiente virtual
  ```bash
  python3 -m venv venv
  ```

- [ ] Ativar ambiente virtual
  ```bash
  source venv/bin/activate
  ```
  ✔️ Verificar: Você deve ver `(venv)` no prompt

- [ ] Atualizar pip
  ```bash
  python3 -m pip install --upgrade pip
  ```

---

## 📦 Dependências

- [ ] Instalar dependências
  ```bash
  python3 -m pip install -r requirements.txt
  ```

- [ ] Verificar psycopg2 instalado
  ```bash
  python3 -m pip list | grep psycopg
  ```
  ✔️ Verificar: `psycopg2-binary` deve estar listado

---

## 🗄️ Banco de Dados

- [ ] Criar banco de dados
  ```bash
  sudo -u postgres psql
  CREATE DATABASE market_v1;
  \q
  ```

- [ ] Testar conexão
  ```bash
  psql -U postgres -h localhost -d market_v1 -c "SELECT 1;"
  ```
  ✔️ Verificar: Deve retornar `?column?: 1`

---

## ⚙️ Variáveis de Ambiente

- [ ] Copiar .env
  ```bash
  cp .env.example .env
  ```

- [ ] Editar .env com credenciais
  ```bash
  nano .env
  ```

  Configure:
  - `DB_HOST=localhost`
  - `DB_NAME=market_v1`
  - `DB_USER=postgres`
  - `DB_PASSWORD=sua_senha`

- [ ] Verificar .env está correto
  ```bash
  source .env
  echo $DB_NAME  # Deve imprimir "market_v1"
  ```

---

## 🔄 Migrations

- [ ] Rodar migrations
  ```bash
  python3 << 'EOF'
  from src.classifier.utils import init_database
  init_database()
  print("✅ Migrations OK")
  EOF
  ```

- [ ] Verificar tabelas no banco
  ```bash
  psql -U postgres -d market_v1 -c "\dt"
  ```
  ✔️ Verificar: Deve listar tabelas como `categorias`, `regras_de_classificacao`, etc.

---

## 🧪 Testes

- [ ] Rodar testes unitários
  ```bash
  pytest tests/unit/ -v
  ```
  ✔️ Verificar: Deve ter ~127 passed, ~35 failed (esperado)

- [ ] Verificar conectividade com banco
  ```bash
  python3 -m classifier.cli.classify_batch --stats
  ```
  ✔️ Verificar: Deve mostrar estatísticas de produtos

---

## 🚀 Operacional

- [ ] Testar classificação dry-run (sem atualizar banco)
  ```bash
  python3 -m classifier.cli.classify_batch --limit 10 --dry-run
  ```
  ✔️ Verificar: Deve processar 10 produtos sem erro

- [ ] Testar classificação real
  ```bash
  python3 -m classifier.cli.classify_batch --limit 10
  ```
  ✔️ Verificar: Deve atualizar banco com categorias

- [ ] Ver resultado
  ```bash
  python3 -m classifier.cli.classify_batch --stats
  ```
  ✔️ Verificar: Deve mostrar produtos classificados aumentados

---

## 📚 Documentação

- [ ] Ler QUICKSTART.md
  ```bash
  cat QUICKSTART.md
  ```

- [ ] Ler GUIA_COMPLETO.md
  ```bash
  cat docs/GUIA_COMPLETO.md
  ```

- [ ] Ler SETUP.md
  ```bash
  cat docs/SETUP.md
  ```

---

## 🎉 Status Final

Marque tudo que completou:

```
SETUP COMPLETO? Responda sim/não para cada:

🐍 Ambiente Python:
   [ ] Python 3.8+ instalado
   [ ] venv criado e ativado
   [ ] pip atualizado

🗄️  Banco de Dados:
   [ ] PostgreSQL rodando
   [ ] Banco market_v1 criado
   [ ] Conexão testada

📦 Dependências:
   [ ] requirements.txt instalado
   [ ] psycopg2 instalado

⚙️  Configuração:
   [ ] .env copiado
   [ ] .env editado com credenciais
   [ ] Migrations rodadas

✅ Testes:
   [ ] Testes unitários passam
   [ ] Conexão com banco OK
   [ ] Classificação funciona

✨ PRONTO! Seu projeto está configurado!
```

---

## 🆘 Problemas?

Se encontrar erros:

1. **Veja a seção "Troubleshooting" em:** `docs/GUIA_COMPLETO.md`
2. **Ou consulte:** `docs/SETUP.md`
3. **Ou procure em:** `docs/guides/`

---

## ⚡ Quick Reference

**Comandos mais usados:**

```bash
# Ativar venv
source venv/bin/activate

# Ver estatísticas
python3 -m classifier.cli.classify_batch --stats

# Classificar 100 produtos
python3 -m classifier.cli.classify_batch --limit 100

# Testar antes de atualizar
python3 -m classifier.cli.classify_batch --limit 100 --dry-run

# Rodar testes
pytest tests/unit/ -v
```

---

**Data de checklist:** ___________

**Pessoa responsável:** ___________

**Notas:** _____________________________________________________________________

