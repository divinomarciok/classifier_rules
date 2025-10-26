# 🏗️ Arquitetura Atual: Como o Projeto Acessa Produtos

**Data**: 2025-10-26
**Status**: Documentação da arquitetura existente

---

## 📊 Fluxo Atual de Classificação

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. BANCO DE DADOS (PostgreSQL)                                  │
│                                                                 │
│  produtos_tabela (79.201 produtos):                            │
│  ├─ id (VARCHAR) - Código de barras                            │
│  ├─ descricao (VARCHAR) - Descrição do produto                 │
│  ├─ ncm (VARCHAR) - Código NCM                                 │
│  ├─ categoria (VARCHAR NULL) - Categoria resultado ← SERÁ FK   │
│  ├─ size (FLOAT) - Tamanho (opcional)                          │
│  ├─ quantity (INT) - Quantidade (opcional)                     │
│  └─ data_classificacao (TIMESTAMP NULL)                        │
│                                                                 │
│  regras_de_classificacao (N regras):                           │
│  ├─ id, prioridade, nome, ativo                                │
│  ├─ criterios (palavras_chave, ncm, size, quantity, etc)      │
│  ├─ resultado_classificacao (VARCHAR) ← SERÁ categoria_id (FK) │
│  └─ data_criacao, data_atualizacao                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CARREGAMENTO (batch.py)                                      │
│                                                                 │
│  _get_unclassified_products():                                  │
│    SELECT * FROM produtos_tabela WHERE categoria IS NULL       │
│    LIMIT 500 OFFSET 0                                           │
│                                                                 │
│  RETORNA: List[tuple]                                           │
│    (id, descricao, ncm, categoria, size, quantity, ...)        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CONVERSÃO PARA OBJETO (batch._row_to_product)                │
│                                                                 │
│  tuple → Product(object)                                        │
│  ├─ product.id = row[0]                                         │
│  ├─ product.description = row[1]                                │
│  ├─ product.ncm = row[2]                                        │
│  ├─ product.category = row[3] (NULL para não classificado)     │
│  ├─ product.size = row[4]                                       │
│  ├─ product.quantity = row[5]                                   │
│  └─ product._extra_fields = {}                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. AVALIAÇÃO (engine.evaluate)                                   │
│                                                                 │
│  RuleEngine._load_rules():                                      │
│    SELECT id, prioridade, nome, ativo,                         │
│           criterios_*,                                         │
│           resultado_classificacao  ← STRING                    │
│    FROM regras_de_classificacao                                │
│    WHERE ativo = TRUE                                           │
│    ORDER BY prioridade DESC                                     │
│                                                                 │
│  Para cada rule, Evaluator.get_matching_rules():               │
│    ├─ Matcher: Compara product.description vs rule criterios   │
│    ├─ Evaluator: Filtra regras ativas e combinadas             │
│    └─ Seleciona winner (maior prioridade)                       │
│                                                                 │
│  RETORNA: ClassificationResult                                  │
│    ├─ classification = winner.resultado_classificacao  ← STRING│
│    ├─ rule_id, rule_name, matched_criteria                     │
│    └─ success = True/False                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. ATUALIZAÇÃO BD (batch._update_product_classification)         │
│                                                                 │
│  UPDATE produtos_tabela                                        │
│  SET categoria = %s,  ← SERÁ categoria_id (INT FK)            │
│      data_classificacao = %s                                    │
│  WHERE id = %s                                                  │
│                                                                 │
│  Armazena a string direto (ex: "ELETRÔNICOS")                  │
│  APÓS MUDANÇA: Armazenará o ID (ex: 1)                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Campos Usados para Comparação

### Campos Obrigatórios (sempre presente)
```python
product.id           # row[0] - VARCHAR - Código de barras
product.description  # row[1] - VARCHAR - Onde acontecem matches de palavras-chave
product.ncm          # row[2] - VARCHAR - Padrão NCM (ex: "8471*")
```

### Campos Opcionais (podem ser NULL)
```python
product.size         # row[4] - FLOAT - Comparado contra criterio_tamanho_min/max
product.quantity     # row[5] - INT - Comparado contra criterio_quantidade_min/max
product.category     # row[3] - VARCHAR NULL - Status de classificação (não usado em comparação)
```

### Critérios de Matching (na tabela regras_de_classificacao)
```sql
criterio_palavras_chave     -- Procura substring em product.description
criterio_ncm                -- Padrão SQL LIKE contra product.ncm
criterio_tamanho_min/max    -- Range contra product.size
criterio_quantidade_min/max -- Range contra product.quantity
criterio_categoria          -- Filtro por categoria do produto (opcional)
```

---

## ⚙️ Como Funciona o Matching

### Exemplo: Classificar um Produto

**Produto de entrada:**
```python
{
    'id': '7898765432101',
    'description': 'Laptop Dell Inspiron 15',
    'ncm': '84713090',
    'size': 15.0,
    'quantity': 1
}
```

**Regra 1 (Prioridade 100):**
```sql
id=1, criterio_palavras_chave='laptop', resultado_classificacao='ELETRÔNICOS'
```
→ MATCH: 'laptop' encontrado em 'Laptop Dell Inspiron 15'

**Regra 2 (Prioridade 50):**
```sql
id=2, criterio_ncm='8471%', resultado_classificacao='COMPONENTES'
```
→ MATCH: '84713090' começa com '8471%'

**Resultado:**
```
winner = Regra 1 (prioridade 100 > 50)
classification = 'ELETRÔNICOS'
```

**Update no BD:**
```sql
UPDATE produtos_tabela
SET categoria = 'ELETRÔNICOS', data_classificacao = NOW()
WHERE id = '7898765432101'
```

---

## 🔄 Mudanças Necessárias Com a Nova Arquitetura

### ANTES (String)
```python
# batch.py - row_to_product()
product.category = row[3]  # ex: NULL ou "ELETRÔNICOS"

# engine.py - evaluate()
result.classification = winner.resultado_classificacao  # ex: "ELETRÔNICOS"

# batch.py - update
UPDATE produtos_tabela SET categoria = 'ELETRÔNICOS' WHERE id = ...
```

### DEPOIS (FK - categoria_id)
```python
# batch.py - row_to_product()
product.categoria_id = row[3]  # ex: NULL ou 1 (FK)

# engine.py - evaluate()
# Buscar nome da categoria via JOIN
SELECT c.nome FROM categorias WHERE id = winner.categoria_id
result.classification = category_name  # ex: "ELETRÔNICOS" (nome)
result.categoria_id = winner.categoria_id  # ex: 1 (ID)

# batch.py - update
UPDATE produtos_tabela SET categoria_id = 1 WHERE id = ...  # FK
```

---

## 📋 Campos que NÃO MUDAM

Estes campos continuam iguais (não afetados pela mudança):

```python
# Sempre usados para matching:
product.id           ← Não muda
product.description  ← Não muda
product.ncm          ← Não muda
product.size         ← Não muda
product.quantity     ← Não muda

# Critérios de matching (na regra):
criterio_palavras_chave     ← Não muda (ainda procura em description)
criterio_ncm                ← Não muda (ainda compara com ncm)
criterio_tamanho_min/max    ← Não muda (ainda compara com size)
criterio_quantidade_min/max ← Não muda (ainda compara com quantity)
```

---

## 🎯 O Que Muda Especificamente

### 1. Carregamento de Regras (engine.py)

**ANTES:**
```python
cursor.execute("""
    SELECT id, prioridade, nome, ativo,
           criterio_palavras_chave, criterio_ncm, ...,
           resultado_classificacao,  ← STRING
           data_criacao, data_atualizacao
    FROM regras_de_classificacao WHERE ativo = TRUE
""")
# resultado_classificacao = "ELETRÔNICOS" (string)
```

**DEPOIS:**
```python
cursor.execute("""
    SELECT id, prioridade, nome, ativo,
           criterio_palavras_chave, criterio_ncm, ...,
           categoria_id,  ← INTEGER FK
           data_criacao, data_atualizacao
    FROM regras_de_classificacao WHERE ativo = TRUE
""")
# categoria_id = 1 (integer FK para categorias.id)
```

### 2. Conversão Produto (batch.py)

**ANTES:**
```python
def _row_to_product(row):
    product = Product(
        id=row[0],
        description=row[1],
        ncm=row[2],
        category=row[3],  # NULL ou "ELETRÔNICOS"
        size=row[4],
        quantity=row[5]
    )
```

**DEPOIS:**
```python
def _row_to_product(row):
    product = Product(
        id=row[0],
        description=row[1],
        ncm=row[2],
        categoria_id=row[3],  # NULL ou 1 (FK)
        size=row[4],
        quantity=row[5]
    )
```

### 3. Resultado da Classificação (engine.py)

**ANTES:**
```python
result = ClassificationResult(
    classification=winner.resultado_classificacao,  # "ELETRÔNICOS"
    rule_id=winner.id,
    # ...
)
```

**DEPOIS:**
```python
# Buscar nome da categoria
cursor.execute("SELECT nome FROM categorias WHERE id = %s",
               (winner.categoria_id,))
category_name = cursor.fetchone()[0]  # "ELETRÔNICOS"

result = ClassificationResult(
    classification=category_name,  # "ELETRÔNICOS" (nome)
    categoria_id=winner.categoria_id,  # 1 (ID)
    rule_id=winner.id,
    # ...
)
```

### 4. Update no BD (batch.py)

**ANTES:**
```python
UPDATE produtos_tabela
SET categoria = %s,  # 'ELETRÔNICOS' (string)
    data_classificacao = %s
WHERE id = %s
```

**DEPOIS:**
```python
UPDATE produtos_tabela
SET categoria_id = %s,  # 1 (integer FK)
    data_classificacao = %s
WHERE id = %s
```

---

## 🔐 Validações Automáticas com FK

**Com a mudança para FK:**

✅ **Inserir regra com categoria inválida:**
```sql
INSERT INTO regras_de_classificacao (nome, ativo, prioridade, categoria_id)
VALUES ('Bad Rule', TRUE, 1, 999);  -- 999 não existe em categorias
-- ERRO: violates foreign key constraint ✓
```

✅ **Tentar deletar categoria em uso:**
```sql
DELETE FROM categorias WHERE id = 1;  -- Id 1 é usado por regras
-- ERRO: ON DELETE RESTRICT ✓
```

✅ **Update automático se categoria renomeada:**
```sql
UPDATE categorias SET nome = 'NOVO_NOME' WHERE id = 1;
-- Todas as regras que referenciam id=1 veem o novo nome (via JOIN)
-- Automático! Não precisa atualizar regras ✓
```

---

## 📌 Resumo: Impacto nas Camadas

| Camada | ANTES | DEPOIS | Impacto |
|--------|-------|--------|---------|
| **BD - SELECT produtos** | categoria (VARCHAR NULL) | categoria_id (INT FK NULL) | ✅ Compatível |
| **BD - SELECT regras** | resultado_classificacao (VARCHAR) | categoria_id (INT FK) | ✅ FK obrigatório |
| **Batch - _row_to_product()** | product.category = row[3] | product.categoria_id = row[3] | ✅ Type change |
| **Engine - _load_rules()** | SQL SELECT resultado_classificacao | SQL SELECT categoria_id | ✅ Type change |
| **Engine - evaluate()** | return resultado_classificacao | return categoria_id + nome | ✅ JOIN extra |
| **Batch - update BD** | UPDATE categoria = string | UPDATE categoria_id = int | ✅ Type change |

---

## ✨ Conclusão

**O projeto funciona assim:**

1. **Carrega produtos** com `SELECT * FROM produtos_tabela`
2. **Converte para Product** object (campos: id, description, ncm, size, quantity, category)
3. **Carrega regras** com `SELECT * FROM regras_de_classificacao`
4. **Faz matching** usando: description, ncm, size, quantity (ignora category)
5. **Retorna resultado** com classification (a string ou ID da categoria)
6. **Atualiza BD** com categoria = resultado

**A mudança:**
- Usa FK em regras para vincular a categorias.id
- Armazena categoria_id (int) em produtos ao invés de categoria (string)
- Mantém toda a lógica de matching igual (usa description, ncm, size, quantity)
- Adiciona segurança: impossível categoria inválida

**Compatibilidade:**
- ✅ Campos de matching (description, ncm, size, quantity) não mudam
- ✅ Lógica de evaluation não muda
- ✅ Critérios de matching não mudam
- ✅ Apenas tipos de dados mudam (str → int FK)
