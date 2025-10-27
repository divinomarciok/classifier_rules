# 🤖 Guia Rápido: Implementar Novas Regras de Classificação (IA Only)

**Versão**: 1.0
**Data**: 2025-10-26
**Propósito**: Instruções detalhadas para IA adicionar novas regras sem erros

---

## ⚡ TL;DR - Os 3 Erros Mais Comuns

| # | Erro | Impacto | Solução |
|---|------|--------|---------|
| 1 | Keywords com `\|` em vez de `,` | Nenhuma regra funciona | Use **VÍRGULA** sempre |
| 2 | Migration não reconhecida | Regras não são inseridas | Atualizar `src/classifier/utils.py` |
| 3 | Teste sem `cache_rules=False` | Cache antigo mascara problemas | Sempre usar `cache_rules=False` |

---

## 📋 Checklist Executivo (Siga Exatamente)

```
[ ] PASSO 1: Ler especificação do usuário
    └─> Que categoria? Que produtos?

[ ] PASSO 2: Explorar estrutura existente
    └─> Verificar migration atual (migrations/XXX_create_regras*.sql)
    └─> Entender formato de keywords (grep para `,` em regras existentes)

[ ] PASSO 3: Planejar variações
    └─> Danone Iogurte → múltiplas variações (Natural, Grego, Kids, etc.)
    └─> Cada variação = 1 regra separada com prioridades diferentes

[ ] PASSO 4: Criar migration file
    └─> Nome: migrations/NNN_add_nome_rules.sql
    └─> Comentário no topo: "Keywords separated by COMMA (,)"
    └─> SQL: INSERT com ON CONFLICT para segurança

[ ] PASSO 5: Atualizar src/classifier/utils.py
    └─> Adicionar novo prefixo no startswith() da função init_database()

[ ] PASSO 6: Executar migration
    └─> Usar get_db_connection() + cursor.execute()
    └─> Verificar saída: "Migration executed!"

[ ] PASSO 7: Testar regras
    └─> Teste 1: Verificar se regras foram inseridas (engine.get_rules())
    └─> Teste 2: Testar keyword matching (Matcher.matches_all_criteria())
    └─> Teste 3: Avaliar 5+ produtos reais (engine.evaluate())

[ ] PASSO 8: Validar 100% passam
    └─> Se algum produto falha → DEBUG com Matcher._match_keywords()
    └─> Se tudo passa → SUCESSO!
```

---

## 🔧 Implementação Detalhada

### PASSO 1: Explorar Banco de Dados

```python
from src.classifier.utils import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Ver categorias disponíveis
cursor.execute("SELECT id, nome FROM categorias ORDER BY id")
for cat_id, cat_name in cursor.fetchall():
    print(f"{cat_id}: {cat_name}")

# Ver regras existentes para a categoria (ex: Laticínios = 7)
cursor.execute("""
    SELECT id, nome, prioridade, criterio_palavras_chave
    FROM regras_de_classificacao
    WHERE categoria_id = 7
    ORDER BY prioridade DESC
""")

for rule_id, nome, prioridade, keywords in cursor.fetchall():
    print(f"{rule_id:3d} | {nome:40s} | Pri:{prioridade:3d} | {keywords[:50]}")
```

### PASSO 2: Criar Migration com Formato Correto

**TEMPLATE**: `migrations/NNN_add_NOME_rules.sql`

```sql
-- Migration NNN: Add [DESCRIPTION] rules
-- DEPENDS ON: 003_create_regras_de_classificacao.sql
-- Date: YYYY-MM-DD
-- Status: Up
-- NOTE: Keywords are separated by COMMA (,) NOT pipe (|)

-- Rule 1: More specific variant
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Danone Activia Laticinio',
    7,              -- Category ID for Laticínios
    130,            -- HIGHER priority = more specific
    'activia,danone activia,iog. activia',  -- COMMA-separated keywords!
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'activia,danone activia,iog. activia',
    prioridade = 130,
    data_atualizacao = CURRENT_TIMESTAMP;

-- Rule 2: Generic variant
INSERT INTO regras_de_classificacao (
    nome,
    categoria_id,
    prioridade,
    criterio_palavras_chave,
    ativo
) VALUES (
    'Iogurte Genérico Laticinio',
    7,
    110,            -- LOWER priority = less specific
    'iogurte,iog.',
    TRUE
) ON CONFLICT (nome) DO UPDATE SET
    criterio_palavras_chave = 'iogurte,iog.',
    prioridade = 110,
    data_atualizacao = CURRENT_TIMESTAMP;
```

**Regras de Prioridade**:
```
Mais específico (prioridade ALTA 130-150):
  - Brands específicas: Activia, Danone Grego
  - Linhas específicas: Light, Diet, Integral

Médio (prioridade MÉDIA 120-125):
  - Variações principais: Natural, Com Frutas, Kids

Genérico (prioridade BAIXA 100-115):
  - Categoria geral: Iogurte, Danone
```

### PASSO 3: Atualizar src/classifier/utils.py

```python
# Linha ~214-216, função init_database()

# ANTES:
if f.name.startswith(('001_', '002_', '003_', '004_', '005_'))

# DEPOIS:
if f.name.startswith(('001_', '002_', '003_', '004_', '005_', '006_'))
```

### PASSO 4: Executar Migration

```python
from src.classifier.utils import get_db_connection
from pathlib import Path

conn = get_db_connection()
cursor = conn.cursor()

# OPÇÃO A: Se migration é NOVA
migration_file = Path('migrations/006_add_lacteos_danone_rules.sql')
with open(migration_file) as f:
    sql = f.read()

cursor.execute(sql)
conn.commit()
print('✓ Migration executed successfully')

# OPÇÃO B: Se migration já foi executada (precisa limpar)
# DELETE regras antigas ANTES de re-executar
cursor.execute("""
    DELETE FROM regras_de_classificacao
    WHERE nome IN ('Danone Activia Laticinio', 'Iogurte Genérico Laticinio')
""")
conn.commit()
# DEPOIS rodar o migration novamente

cursor.close()
conn.close()
```

### PASSO 5: Testar - Fase 1 (Regras Inseridas)

```python
from src.classifier.engine import RuleEngine
from src.classifier.utils import get_db_connection

conn = get_db_connection()

# IMPORTANTE: cache_rules=False para pegar do banco, não do cache
engine = RuleEngine(db_connection=conn, cache_rules=False)
rules = engine.get_rules(active_only=True)

# Filtrar regras adicionadas
new_rules = [r for r in rules if 'danone' in r.nome.lower()]
print(f'✓ Found {len(new_rules)} Danone rules in database')

for rule in new_rules[:3]:  # Mostrar primeiras 3
    print(f"  - {rule.nome}: {rule.criterio_palavras_chave}")

conn.close()
```

**Output esperado:**
```
✓ Found 13 Danone rules in database
  - Danone Activia Laticinio: activia,danone activia,iog. activia
  - Danone Natural Laticinio: danone natural,iog. danone natural,danio natural
  - Iogurte Genérico Laticinio: iogurte,iog.
```

### PASSO 6: Testar - Fase 2 (Keyword Matching)

```python
from src.classifier.matcher import Matcher
from src.classifier.models import Product, Rule

# Teste com formato ERRADO (não deve bater)
product = Product(description='Danone Iogurte Natural 500ml', ncm='0402')
rule_wrong = Rule(
    id=1, prioridade=100, nome="Test Wrong", ativo=True, categoria_id=7,
    criterio_palavras_chave='danone|iogurte'  # ERRADO: pipe em vez de vírgula
)
result_wrong = Matcher.matches_all_criteria(product, rule_wrong)
print(f'With pipe (|): {result_wrong}')  # False

# Teste com formato CORRETO (deve bater)
rule_correct = Rule(
    id=1, prioridade=100, nome="Test Correct", ativo=True, categoria_id=7,
    criterio_palavras_chave='danone,iogurte'  # CERTO: vírgula
)
result_correct = Matcher.matches_all_criteria(product, rule_correct)
print(f'With comma (,): {result_correct}')  # True
```

**Output esperado:**
```
With pipe (|): False
With comma (,): True
```

### PASSO 7: Testar - Fase 3 (Avaliação Completa)

```python
from src.classifier.engine import RuleEngine
from src.classifier.utils import get_db_connection

# Produtos de teste - use nomes reais da vida!
test_products = [
    {'id': '001', 'description': 'Iog.Danone Danio Banana 125G', 'ncm': '0402'},
    {'id': '002', 'description': 'Danone Iogurte Natural 500ml', 'ncm': '0402'},
    {'id': '003', 'description': 'Iogurte Danone Grego 200g', 'ncm': '0402'},
    {'id': '004', 'description': 'Danone Activia Morango 125ml', 'ncm': '0402'},
    {'id': '005', 'description': 'Iogurte Genérico 1L', 'ncm': '0402'},
]

conn = get_db_connection()
engine = RuleEngine(db_connection=conn, cache_rules=False)

passed = 0
for product in test_products:
    result = engine.evaluate(product)
    status = '✓' if result.classification == 'Laticínios' else '✗'
    if status == '✓':
        passed += 1
    print(f'{status} {product["description"]:<50} → {result.classification}')

print(f'\nResult: {passed}/{len(test_products)} tests passed')
conn.close()
```

**Output esperado:**
```
✓ Iog.Danone Danio Banana 125G                         → Laticínios
✓ Danone Iogurte Natural 500ml                         → Laticínios
✓ Iogurte Danone Grego 200g                            → Laticínios
✓ Danone Activia Morango 125ml                         → Laticínios
✓ Iogurte Genérico 1L                                  → Laticínios

Result: 5/5 tests passed
```

---

## 🐛 Debug: Se Algo Não Funcionar

### Sintoma 1: Regras não aparecem na lista
```python
# Verificar se foram inseridas
cursor.execute("SELECT COUNT(*) FROM regras_de_classificacao WHERE nome LIKE '%danone%'")
count = cursor.fetchone()[0]
print(f'Danone rules in DB: {count}')  # Deve ser > 0

# Se 0, então:
#   1. Migration não foi executada (ver erros SQL)
#   2. ON CONFLICT causou problema
#   3. categoria_id = 7 não existe
```

### Sintoma 2: Matcher retorna False quando deveria True
```python
# Testar keyword matching diretamente
from src.classifier.matcher import Matcher

description = 'Danone Iogurte Natural 500ml'
keywords = 'danone,iogurte'  # VÍRGULA

result = Matcher._match_keywords(description, keywords)
print(f'Match result: {result}')  # Deve ser True

# Debug: ver o que o matcher vê
description_lower = description.lower()
keyword_list = [kw.strip().lower() for kw in keywords.split(',')]
print(f'Description: {description_lower}')
print(f'Keywords to find: {keyword_list}')
for keyword in keyword_list:
    print(f'  "{keyword}" in description? {keyword in description_lower}')
```

### Sintoma 3: Migration falha com erro SQL
```python
# Ver o erro completo
try:
    cursor.execute(sql)
except Exception as e:
    print(f'SQL Error: {e}')
    # Erros comuns:
    # - "column already exists" → deletar regras antigas primeiro
    # - "constraint violation" → nome de regra já existe (ON CONFLICT deve resolver)
    # - "category_id not found" → verificar se categoria_id = 7 existe
```

---

## 📊 Fluxo Completo - Exemplo Real (Danone 2025-10-26)

```
ENTRADA DO USUÁRIO:
"adicione uma nova regra para Laticínios incluindo Iogurte e Danone"

PASSO 1: Explorar
├─ Verificar categoria Laticínios (ID 7)
├─ Ver regras existentes → 1 regra genérica "Iogurte Laticinio"
└─ Entender formato → keywords com VÍRGULA

PASSO 2: Planejar
├─ Listar variações Danone:
│  ├─ Danone Activia (prioridade 130 - mais específica)
│  ├─ Danone Grego (prioridade 130)
│  ├─ Danone Natural (prioridade 125)
│  ├─ Danone Light (prioridade 125)
│  └─ Iogurte Genérico (prioridade 110 - menos específica)
└─ Total: 13 regras novas

PASSO 3: Criar Migration
└─ File: migrations/006_add_lacteos_danone_rules.sql
   └─ 13 INSERT statements com keywords separadas por VÍRGULA

PASSO 4: Atualizar Utils
└─ src/classifier/utils.py linha 216
   └─ Adicionar '006_' ao startswith()

PASSO 5: Executar
└─ get_db_connection() → cursor.execute(migration_sql)
   └─ Output: "✓ 13 rules inserted"

PASSO 6: Testar
├─ Teste 1: engine.get_rules() → 13 rules encontradas ✓
├─ Teste 2: Matcher com produto real → True ✓
└─ Teste 3: evaluate() 10 produtos → 10/10 passam ✓

SAÍDA:
"✓ Test complete! 10/10 products correctly classified as Laticínios"
```

---

## 📝 Template Cópia-Cola para Próximas Implementações

```python
# 1. PASSO: Executar migration
from src.classifier.utils import get_db_connection
from pathlib import Path

conn = get_db_connection()
cursor = conn.cursor()

migration_file = Path('migrations/XXX_add_rules.sql')
with open(migration_file) as f:
    sql = f.read()

cursor.execute(sql)
conn.commit()
print('✓ Migration executed')

cursor.close()
conn.close()

# 2. PASSO: Testar regras
from src.classifier.engine import RuleEngine

conn = get_db_connection()
engine = RuleEngine(db_connection=conn, cache_rules=False)

test_products = [
    {'id': '001', 'description': 'PRODUTO 1', 'ncm': 'XXXX'},
    {'id': '002', 'description': 'PRODUTO 2', 'ncm': 'XXXX'},
]

passed = 0
for product in test_products:
    result = engine.evaluate(product)
    status = '✓' if result.classification == 'CATEGORIA_ESPERADA' else '✗'
    if status == '✓':
        passed += 1
    print(f'{status} {product["description"]:<50} → {result.classification}')

print(f'Result: {passed}/{len(test_products)} tests passed')
conn.close()
```

---

## ✅ Conclusão

**Regra de Ouro**: Se tudo isso funcionar na primeira vez, você entendeu o sistema corretamente.

Se não funcionar, volte a este documento e encontre o padrão de erro correspondente.

**Próxima vez que adicionar regras**: Use este arquivo como guia passo-a-passo.
