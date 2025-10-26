# 🚀 Migration & Test Execution Guide

**Data**: 2025-10-26
**Status**: Tudo implementado e pronto para execução

---

## 📋 Pré-requisitos

Para rodar as migrations e testes, você precisa ter:

```bash
# 1. PostgreSQL rodando
sudo systemctl start postgresql  # Linux
brew services start postgresql  # Mac

# 2. Banco de dados criado
createdb -U postgres market_v1

# 3. Python 3.8+ com dependências
python3 -m pip install psycopg2-binary pytest pytest-cov
```

---

## 🔧 Passo 1: Rodar as Migrations

### Opção A: Usando o script Python (Recomendado)

```bash
cd /home/divinopc/testes/projects/classifier_regras

python3 << 'EOF'
from src.classifier.utils import init_database, load_config

print("=" * 70)
print("EXECUTING DATABASE MIGRATIONS (001-005)")
print("=" * 70)

try:
    result = init_database()
    if result:
        print("\n✅ All migrations executed successfully!")
    else:
        print("\n⚠️  Some migrations were skipped")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
EOF
```

### Opção B: Executar migrations manualmente

```bash
# 1. Fazer backup (IMPORTANTE!)
pg_dump -d market_v1 > backup_$(date +%Y%m%d).dump

# 2. Executar migrations em ordem
psql -d market_v1 -f migrations/001_alter_produtos_add_status.sql
psql -d market_v1 -f migrations/002_create_categorias.sql
psql -d market_v1 -f migrations/003_create_regras_de_classificacao.sql
psql -d market_v1 -f migrations/004_create_auditoria_classificacao.sql
psql -d market_v1 -f migrations/005_create_criterios_palavras_chave.sql

# 3. Verificar
psql -d market_v1 << 'SQL'
\dt
SELECT COUNT(*) as categorias FROM categorias;
SELECT COUNT(*) as regras FROM regras_de_classificacao;
SQL
```

---

## ✅ Passo 2: Rodar os Testes

### Opção A: Rodar todos os testes

```bash
cd /home/divinopc/testes/projects/classifier_regras

# Instalar dependências de teste
python3 -m pip install pytest pytest-cov

# Rodar todos os testes
pytest tests/ -v

# Com coverage
pytest tests/ -v --cov=src/classifier --cov-report=html
```

### Opção B: Rodar testes específicos

```bash
# Apenas testes unitários
pytest tests/unit/ -v

# Apenas testes de integração
pytest tests/integration/ -v

# Apenas testes de contrato
pytest tests/contract/ -v

# Apenas testes CLI
pytest tests/cli/ -v

# Apenas modelos
pytest tests/unit/test_models.py -v

# Apenas batch
pytest tests/unit/test_batch_classifier.py -v -s
pytest tests/integration/test_batch_classification.py -v -s
```

### Opção C: Rodar com filtro

```bash
# Apenas testes que mencionam 'category'
pytest -v -k "category"

# Apenas testes que mencionam 'batch'
pytest -v -k "batch"

# Apenas testes que não são 'slow'
pytest -v -m "not slow"
```

---

## 🎯 Passo 3: Testar Batch Classification End-to-End

### Opção A: Usando o CLI script

```bash
cd /home/divinopc/testes/projects/classifier_regras

# 1. Verificar estatísticas atuais
python3 -m classifier.cli.classify_batch --stats

# 2. Executar classificação (primeiras 100)
python3 -m classifier.cli.classify_batch --limit 100 --verbose

# 3. Executar classificação (500 produtos)
python3 -m classifier.cli.classify_batch --limit 500

# 4. Filtrar por NCM específico
python3 -m classifier.cli.classify_batch --where "ncm LIKE '8471%'" --limit 500

# 5. Modo simulação (sem atualizar BD)
python3 -m classifier.cli.classify_batch --limit 100 --dry-run

# 6. Saída JSON
python3 -m classifier.cli.classify_batch --limit 100 --json
```

### Opção B: Usando Python diretamente

```python
from src.classifier.utils import get_db_connection
from src.classifier.batch import BatchClassifier

# Conectar ao banco
conn = get_db_connection()

# Criar classificador
batch = BatchClassifier(conn)

# 1. Verificar estatísticas
stats = batch.get_batch_statistics()
print(f"Total: {stats['total_products']}")
print(f"Status breakdown: {stats['by_status']}")

# 2. Classificar batch
result = batch.classify_batch(limit=100, offset=0, update_db=True)

print(f"Processados: {result['total_processed']}")
print(f"Matched: {result['total_matched']}")
print(f"No Match: {result['total_no_match']}")
print(f"Taxa: {result['match_rate']:.1%}")
print(f"Tempo: {result['elapsed_time_ms']}ms")

conn.close()
```

### Opção C: Teste com dados de teste (Fixtures)

```python
import pytest
from src.classifier.engine import RuleEngine

def test_batch_with_fk(db_connection, sample_categories, sample_rules):
    """Test batch classification with FK categories"""

    engine = RuleEngine(db_connection)

    # Produto que deve bater com a regra 'electronics'
    product = {
        'id': 'TEST_001',
        'description': 'laptop computer',
        'ncm': '84713090'
    }

    result = engine.evaluate(product)

    # Validações
    assert result.success == True
    assert result.classification == 'ELECTRONICS'  # Nome da categoria
    assert result.categoria_id == sample_categories['electronics']  # ID do FK
    assert result.rule_id is not None

    print("✅ Test passed!")
    print(f"  - Classification: {result.classification}")
    print(f"  - Category ID: {result.categoria_id}")
    print(f"  - Rule ID: {result.rule_id}")
```

---

## 📊 Esperado vs Resultado

### Antes (Fase 1)
```
produto → categoria="ELETRÔNICOS" (string)
UPDATE produtos SET categoria="ELETRÔNICOS"
```

### Depois (Fase 2) - O que você verá
```
produto → categoria_id=1 (int FK)
           classification="ELETRÔNICOS" (name from category lookup)
UPDATE produtos SET categoria_id=1, status_classificacao='matched'
```

---

## 🔍 Verificações Importantes

### 1. Verificar Migrations Aplicadas

```bash
psql -d market_v1 << 'SQL'
-- Listar todas as tabelas
\dt

-- Verificar estrutura da tabela categorias
\d categorias

-- Verificar estrutura da tabela regras
\d regras_de_classificacao

-- Verificar coluna categoria_id em produtos
\d produtos_tabela

-- Verificar coluna status_classificacao
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'produtos_tabela'
ORDER BY ordinal_position;
SQL
```

### 2. Verificar Dados

```bash
psql -d market_v1 << 'SQL'
-- Contar categorias
SELECT COUNT(*) FROM categorias;

-- Contar regras
SELECT COUNT(*) FROM regras_de_classificacao;

-- Verificar status dos produtos
SELECT status_classificacao, COUNT(*) as count
FROM produtos_tabela
GROUP BY status_classificacao;

-- Ver exemplos de produtos
SELECT id, descricao, categoria_id, status_classificacao
FROM produtos_tabela
LIMIT 5;
SQL
```

### 3. Verificar Auditoria

```bash
psql -d market_v1 << 'SQL'
-- Verificar registros de auditoria
SELECT COUNT(*) FROM auditoria_classificacao;

-- Ver exemplo com categoria_id
SELECT id, id_produto, categoria_id, resultado_classificacao, data_classificacao
FROM auditoria_classificacao
LIMIT 5;
SQL
```

---

## ⚠️ Troubleshooting

### Erro: "relation 'categorias' does not exist"
```
Causa: Migrations não foram executadas na ordem correta
Solução: Rodar migrations 001-005 em ordem, começando do 001
```

### Erro: "Foreign key constraint violation"
```
Causa: Tentar inserir categoria_id que não existe em categorias
Solução: Verificar que a categoria existe antes de inserir regra
```

### Erro: "column 'status_classificacao' does not exist"
```
Causa: Migration 001 não foi executada
Solução: Rodar migration 001 primeiro
```

### Erro: "psycopg2 not found"
```
Solução: pip install psycopg2-binary
```

### Erro: "pytest not found"
```
Solução: pip install pytest pytest-cov
```

---

## 📈 Expected Test Results

Depois de rodar os testes, você deve ver algo como:

```
============================== test session starts ==============================
platform linux -- Python 3.x.x, pytest-x.x.x, ...
collected XX items

tests/unit/test_models.py::test_category_creation PASSED           [ 2%]
tests/unit/test_models.py::test_rule_with_categoria_id PASSED      [ 4%]
tests/integration/test_batch_classification.py::test_batch_with_categories PASSED
...

============================== XX passed in X.XXs ==============================
```

---

## 🚀 Fluxo Completo de Teste

1. **Conectar ao banco**
   ```bash
   psql -U postgres -d market_v1
   ```

2. **Aplicar migrations**
   ```bash
   python3 << 'EOF'
   from src.classifier.utils import init_database
   init_database()
   EOF
   ```

3. **Rodar testes unitários**
   ```bash
   pytest tests/unit/ -v
   ```

4. **Rodar testes de integração**
   ```bash
   pytest tests/integration/ -v
   ```

5. **Testar batch classification**
   ```bash
   python3 -m classifier.cli.classify_batch --stats
   python3 -m classifier.cli.classify_batch --limit 100
   ```

6. **Verificar estatísticas**
   ```bash
   psql -d market_v1 -c "SELECT status_classificacao, COUNT(*) FROM produtos_tabela GROUP BY status_classificacao;"
   ```

---

## ✅ Checklist de Validação

- [ ] Migrations executadas em ordem (001-005)
- [ ] Tabela `categorias` criada com dados
- [ ] Tabela `regras_de_classificacao` atualizada com categoria_id FK
- [ ] Coluna `status_classificacao` adicionada em produtos_tabela
- [ ] Todos os testes passam (pytest)
- [ ] Batch classification funciona (--stats mostra status breakdown)
- [ ] Produtos classificados têm categoria_id preenchido
- [ ] Produtos NO_MATCH ficam com status='pending'
- [ ] Auditoria registra categoria_id
- [ ] FK constraints funcionam

---

## 📝 Comandos Rápidos

```bash
# Setup rápido
createdb -U postgres market_v1
cd /home/divinopc/testes/projects/classifier_regras

# Migrations
python3 << 'EOF'
from src.classifier.utils import init_database
init_database()
EOF

# Testes
python3 -m pip install pytest
pytest tests/ -v

# Batch test
python3 -m classifier.cli.classify_batch --limit 100 --verbose
```

---

## 🎉 Pronto!

Quando todos os testes passarem e o batch rodar com sucesso, você terá:

✅ Banco de dados com suporte a Foreign Keys
✅ Categorias gerenciadas corretamente
✅ Regras apontando para categorias (não strings)
✅ Batch classification funcional
✅ Auditoria completa
✅ NO_MATCH handling preservado

**Parabéns! 🚀**

