# 🔄 Guia de Migração de Banco de Dados

**Para quando você precisar trocar de banco de dados ou alterar a estrutura da tabela `produtos_tabela`**

---

## 🎯 Visão Geral

O projeto foi design para ser **flexível com mudanças de banco de dados**. Se você precisa:
- ✅ Trocar de PostgreSQL para outro banco
- ✅ Renomear a tabela `produtos_tabela`
- ✅ Adicionar/remover/renomear colunas
- ✅ Alterar nomes de campos

Você consegue fazer isso com **mudanças em poucos arquivos**.

---

## 📍 Arquivos que Precisam Ser Alterados

### 1. **src/classifier/batch.py** (PRINCIPAL)

Este é o **arquivo mais importante** que você precisa alterar.

**Onde está a referência:**
```python
# Linhas 105-120 aproximadamente
query = "SELECT * FROM produtos_tabela WHERE status_classificacao = 'pending'"
# ...
"UPDATE produtos_tabela SET categoria_id = %s, status_classificacao = %s, data_classificacao = %s WHERE id = %s"
```

**O que muda:**
- Nome da tabela: `produtos_tabela` → seu novo nome
- Coluna de ID: `id` → seu novo nome de coluna ID
- Coluna de descrição: O código assu me `descricao` (verifique se é a mesma)
- Coluna de NCM: O código assume `ncm` (verifique se é a mesma)

---

### 2. **src/classifier/csv_classifier.py**

Referências ao `produtos_tabela`:
```python
# Linha ~150 aproximadamente
"UPDATE produtos_tabela SET categoria = %s, data_classificacao = %s WHERE id = %s"
```

**O que muda:**
- Nome da tabela
- Nomes das colunas de atualização

---

### 3. **src/classifier/models.py**

Define a estrutura da classe `Product`:
```python
@dataclass
class Product:
    id: str
    descricao: str
    ncm: str
    size: Optional[float] = None
    quantity: Optional[int] = None
```

**O que muda:**
- Se seus nomes de campo forem diferentes, atualize aqui
- Se tiver novos campos, adicione como `Optional[tipo]`

---

### 4. **src/classifier/utils.py** (Verificar)

Na função `verify_database_connection()` (linha ~272), há uma lista de tabelas obrigatórias:
```python
required_tables = [
    'categorias',
    'regras_de_classificacao',
    'auditoria_classificacao',
    'criterios_palavras_chave',
]
```

⚠️ **Nota**: A tabela `produtos_tabela` **NÃO está** nesta lista, então você **não precisa alterar** este arquivo.

---

## 📋 Passo a Passo: Trocar Banco de Dados

### Cenário 1: Trocar Nome da Tabela de `produtos_tabela` para `produtos`

#### Passo 1: Atualizar `batch.py`

```bash
# Abra o arquivo
vim src/classifier/batch.py
```

Procure por todas as ocorrências de `produtos_tabela` e substitua por `produtos`:

**Linha ~105:**
```python
# ANTES:
query = "SELECT * FROM produtos_tabela WHERE status_classificacao = 'pending'"

# DEPOIS:
query = "SELECT * FROM produtos WHERE status_classificacao = 'pending'"
```

**Linha ~120-130:**
```python
# ANTES:
"UPDATE produtos_tabela SET categoria_id = %s, status_classificacao = %s, data_classificacao = %s WHERE id = %s"

# DEPOIS:
"UPDATE produtos SET categoria_id = %s, status_classificacao = %s, data_classificacao = %s WHERE id = %s"
```

**Linha ~170-180:**
```python
# ANTES:
COUNT(*) FROM produtos_tabela

# DEPOIS:
COUNT(*) FROM produtos
```

#### Passo 2: Atualizar `csv_classifier.py`

```bash
vim src/classifier/csv_classifier.py
```

Procure por `produtos_tabela` e substitua por `produtos`.

#### Passo 3: Testar

```bash
python3 -m classifier.cli.classify_batch --stats
```

Se funcionar sem erros, está tudo bem!

---

### Cenário 2: Alterar Nomes de Colunas

Vamos supor que sua tabela tenha:
- ID da tabela: `product_id` (ao invés de `id`)
- Descrição: `product_name` (ao invés de `descricao`)
- NCM: `ncm_code` (ao invés de `ncm`)

#### Passo 1: Atualizar `models.py`

```python
# Adicione comentário explicando o mapeamento
@dataclass
class Product:
    # Mapeamento: product_id (DB) -> id (modelo)
    id: str  # Maps to product_id in database

    # Mapeamento: product_name (DB) -> descricao (modelo)
    descricao: str  # Maps to product_name in database

    # Mapeamento: ncm_code (DB) -> ncm (modelo)
    ncm: str  # Maps to ncm_code in database

    size: Optional[float] = None
    quantity: Optional[int] = None
```

#### Passo 2: Atualizar `batch.py`

Na função `_get_unclassified_products()`, atualize o SELECT:

```python
# ANTES:
query = "SELECT * FROM produtos_tabela WHERE status_classificacao = 'pending' LIMIT %s OFFSET %s"

# DEPOIS:
query = """
SELECT
    product_id as id,
    product_name as descricao,
    ncm_code as ncm,
    size,
    quantity
FROM produtos
WHERE status_classificacao = 'pending'
LIMIT %s OFFSET %s
"""
```

E no UPDATE:

```python
# ANTES:
"UPDATE produtos_tabela SET categoria_id = %s, status_classificacao = %s, data_classificacao = %s WHERE id = %s"

# DEPOIS:
"UPDATE produtos SET categoria_id = %s, status_classificacao = %s, data_classificacao = %s WHERE product_id = %s"
```

#### Passo 3: Atualizar `csv_classifier.py`

Faça as mesmas mudanças no arquivo de CSV.

---

### Cenário 3: Trocar de PostgreSQL para Outro Banco (ex: MySQL)

#### Passo 1: Instalar Driver do Novo Banco

```bash
# Para MySQL:
pip install mysql-connector-python
# ou
pip install PyMySQL

# Para SQLite:
# Já vem com Python!

# Para MSSQL:
pip install pyodbc
```

#### Passo 2: Atualizar `utils.py`

Na função `get_db_connection()`:

```python
# ANTES (PostgreSQL):
import psycopg2
conn = psycopg2.connect(**db_config)

# DEPOIS (MySQL exemplo):
import mysql.connector
conn = mysql.connector.connect(**db_config)
```

#### Passo 3: Atualizar Variáveis de Ambiente

No seu `.env`:

```bash
# ANTES (PostgreSQL):
DB_HOST=localhost
DB_NAME=market_v1
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_PORT=5432

# DEPOIS (MySQL exemplo):
DB_HOST=localhost
DB_NAME=market_v1
DB_USER=root
DB_PASSWORD=sua_senha
DB_PORT=3306
```

#### Passo 4: Verificar SQL Específico do Banco

Alguns comandos SQL são diferentes entre bancos:

```python
# PostgreSQL:
SELECT * FROM information_schema.tables WHERE table_schema = 'public'

# MySQL:
SELECT * FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'market_v1'

# SQLite:
SELECT name FROM sqlite_master WHERE type='table'
```

Atualize em `utils.py` na função `verify_database_connection()`.

---

## 🗂️ Resumo de Alterações por Cenário

| Cenário | batch.py | csv_classifier.py | models.py | utils.py |
|---------|----------|-------------------|-----------|----------|
| Renomear tabela | ✅ | ✅ | ❌ | ❌ |
| Renomear coluna | ✅ | ✅ | ✅ | ❌ |
| Trocar banco | ✅ | ✅ | ❌ | ✅ |
| Adicionar coluna | ✅ | ✅ | ✅ | ❌ |

---

## ⚙️ Verificação Rápida: Quais Colunas o Código Espera?

Para saber **exatamente** quais colunas o código espera, procure por:

```bash
# Ver todas as referências a colunas específicas
grep -n "\.id\|\.descricao\|\.ncm\|\.size\|\.quantity" src/classifier/*.py
```

Resultado esperado:
- `id`: Identificador único do produto (string)
- `descricao`: Descrição do produto (string)
- `ncm`: Código NCM (string)
- `size`: Tamanho (float, opcional)
- `quantity`: Quantidade (int, opcional)

Se seu banco tem nomes diferentes, você precisa fazer mapeamento no SELECT!

---

## 🧪 Teste Após Alterações

Sempre teste depois de fazer mudanças:

```bash
# 1. Testar estatísticas
python3 -m classifier.cli.classify_batch --stats

# 2. Testar classificação de pequeno lote
python3 -m classifier.cli.classify_batch --limit 10

# 3. Rodar testes
pytest tests/ -v
```

Se tudo passar, sua migração foi um sucesso! 🎉

---

## 🆘 Se Algo der Errado

### Erro: "relation \"produtos_tabela\" does not exist"

```bash
# Você não atualizou o nome da tabela em batch.py
# Verifique e atualize TODAS as referências
grep -n "produtos_tabela" src/classifier/batch.py
```

### Erro: "column \"descricao\" does not exist"

```bash
# Sua coluna tem um nome diferente
# Atualize em models.py e no SELECT de batch.py
# Use mapeamento: SELECT coluna_real AS descricao
```

### Erro: "No module named psycopg2"

```bash
# Você trocou de banco mas não instalou o driver
# Instale o driver correto:
pip install [driver-name]
```

---

## 💡 Boas Práticas

1. **Faça backup do banco antes** de fazer mudanças estruturais
2. **Teste em ambiente de desenvolvimento** primeiro
3. **Use controle de versão (git)** para rastrear suas mudanças
4. **Documente** quais foram seus mapeamentos de coluna
5. **Execute testes** após cada alteração

---

## 📞 Próximos Passos

Você tem dúvidas específicas sobre:
- [ ] Renomear coluna específica
- [ ] Trocar para banco de dados específico
- [ ] Adicionar nova coluna ao modelo
- [ ] Migrar dados existentes

Se sim, descreva qual é o seu cenário exato e vou criar um guia específico! 🚀
