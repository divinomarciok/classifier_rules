# 🚨 Problema: Produtos NO_MATCH Ficam Presos

**Identificado por**: User
**Data**: 2025-10-26
**Severidade**: 🔴 CRÍTICA
**Status**: Documentado

---

## 🎯 O Problema

Você está CORRETO! Existe um problema crítico no fluxo:

### Cenário Atual (PROBLEMA):

```
┌─────────────────────────────────────────────────────────────────┐
│ PRIMEIRA EXECUÇÃO - batch.py classify_batch()                   │
│                                                                 │
│ _get_unclassified_products():                                   │
│   SELECT * FROM produtos_tabela                                 │
│   WHERE categoria IS NULL  ← Busca produtos não classificados   │
│   LIMIT 500                                                     │
│                                                                 │
│ Para cada produto:                                              │
│   engine.evaluate(product)                                      │
│   ├─ Se MATCH encontrado: success=True, classification="XXXX"   │
│   │  └─ UPDATE categoria = "XXXX"  ✓ Produto sai da fila      │
│   │                                                             │
│   └─ Se NO MATCH: success=True, classification="NO_MATCH"       │
│      └─ NO UPDATE! ← PROBLEMA!                                 │
│         Produto PERMANECE com categoria=NULL ← BUG             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ SEGUNDA EXECUÇÃO (próxima vez que rodar batch classification)    │
│                                                                 │
│ _get_unclassified_products():                                   │
│   SELECT * FROM produtos_tabela                                 │
│   WHERE categoria IS NULL                                       │
│                                                                 │
│ RESULTADO:                                                       │
│   ✗ Produtos com NO_MATCH aparecem NOVAMENTE                    │
│   ✗ Mesmas regras são testadas (vai resultar em NO_MATCH again) │
│   ✗ Desperdício de tempo processando produtos que já foram      │
│   ✗ Possível loop infinito                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Código que Demonstra o Problema:

**batch.py linhas 97-111:**
```python
for item in results:
    if item['result'].success:
        matched_count += 1
        classification = item['result'].classification
        classifications[classification] = classifications.get(classification, 0) + 1

        # Update database if requested
        if update_db:
            self._update_product_classification(
                item['product_id'],
                item['result'].classification
            )
    else:  # ← Quando success=False (NO_MATCH)
        no_match_count += 1
        no_match_products.append(item['product_id'])
        # ← NENHUM UPDATE NO BD!
```

**engine.py linhas 184-205:**
```python
if not matching_rules:
    logger.info(f"No rules matched for product {product.id}")
    return ClassificationResult(
        classification='NO_MATCH',
        success=True,  # ← IMPORTANTE: success ainda é True!
        evaluation_time_ms=elapsed_ms,
        message='No matching rules found'
    )
```

### O Problema Real:

```
success=True com classification='NO_MATCH'

Significa:
├─ Avaliação COMPLETOU com sucesso
├─ MAS nenhuma regra fez match
└─ Resultado é "NO_MATCH" (string)

Código batch.py verifica:
  if item['result'].success:  ← TRUE mesmo com NO_MATCH!
      update_database(classification)  ← Vai tentar atualizar com "NO_MATCH"?
  else:  ← Nunca entra aqui para NO_MATCH
      log_no_match()
```

---

## 📊 Fluxo CORRETO vs ATUAL

### ATUAL (COM PROBLEMA):
```
Produto entra → Avalia → success=True, classification="NO_MATCH"
                         ↓
                    if success: UPDATE categoria = "NO_MATCH"
                    ├─ Tenta inserir "NO_MATCH" como categoria
                    └─ Se categoria é FK, vai FALHAR! (não existe categoria com nome "NO_MATCH")

Depois de 1000 tentativas → categoria ainda NULL → Reentra na fila infinitamente
```

### CORRETO (O QUE DEVERIA SER):
```
Produto entra → Avalia → success=True, classification="NO_MATCH"
                         ↓
                    if classification != "NO_MATCH":
                        UPDATE categoria = resultado
                    else:
                        UPDATE status = "reviewed_no_match" ou similar
                        OU
                        Log para revisão manual
                        OU
                        Pular para próximo
```

---

## 🔍 Verificação: Como Está Agora?

### Pergunta 1: Como categoria é armazenado para NO_MATCH?

**Código batch.py linha 105-108:**
```python
if update_db:
    self._update_product_classification(
        item['product_id'],
        item['result'].classification  # Pode ser "NO_MATCH"!
    )
```

**Código batch.py linha 224-226:**
```python
cursor.execute(
    "UPDATE produtos_tabela SET categoria = %s, data_classificacao = %s WHERE id = %s",
    (classification, datetime.now(), product_id)
)
```

**O QUE ACONTECE:**
- Se `classification = "NO_MATCH"`, faz: `UPDATE categoria = 'NO_MATCH'`
- Depois a query `WHERE categoria IS NULL` não encontra mais esse produto
- Produto sai da fila, mas com categoria="NO_MATCH" (não é uma categoria real)

### Pergunta 2: Com FK para categorias, o que acontece?

**APÓS a mudança para FK:**
```python
# Novo código (após mudança):
categoria_id = lookup_categoria_id("NO_MATCH")  # Retorna NULL ou erro
UPDATE produtos SET categoria_id = NULL, ...  # Ou FALHA!
```

**Se tentar inserir NULL em FK NOT NULL:**
```
ERROR: violates NOT NULL constraint
```

---

## ⚠️ Problemas Específicos Com a Mudança FK

### Problema 1: categoria_id é NOT NULL (por design)

```sql
CREATE TABLE regras_de_classificacao (
    ...
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    ...
)
```

Mas `produtos_tabela` precisa permitir NULL para não classificados:

```sql
CREATE TABLE produtos_tabela (
    ...
    categoria_id INTEGER NULL REFERENCES categorias(id),  ← Permite NULL
    ...
)
```

### Problema 2: "NO_MATCH" não é uma categoria real

Atualmente:
```sql
UPDATE produtos_tabela SET categoria = 'NO_MATCH' WHERE id = '123';
-- Válido: categoria é VARCHAR
```

Com FK:
```sql
INSERT INTO categorias (nome) VALUES ('NO_MATCH');  ← Precisa ser criada?
UPDATE produtos_tabela SET categoria_id = 2 WHERE id = '123';  ← ID da categoria NO_MATCH
-- OU
UPDATE produtos_tabela SET categoria_id = NULL WHERE id = '123';  ← Deixa NULL?
```

---

## 💡 Soluções Possíveis

### Opção 1: Criar Categoria "NO_MATCH" (Simples)

**Vantagem**: Sem mudanças de código
**Desvantagem**: "NO_MATCH" não é uma categoria real, é um status

```sql
INSERT INTO categorias (nome, descricao, ativo) VALUES
('NO_MATCH', 'Produtos sem match em nenhuma regra', TRUE);
```

Fluxo:
```python
if classification == 'NO_MATCH':
    categoria_id = lookup_categoria_id('NO_MATCH')  # id=6
    UPDATE produtos SET categoria_id = 6  ← Marca como "NO_MATCH"
```

**Problema**: Mistura categorias reais com status artificial

### Opção 2: Campo Separado para Status (Recomendado)

Adicionar coluna em `produtos_tabela`:

```sql
ALTER TABLE produtos_tabela ADD COLUMN
  status_classificacao VARCHAR(20) DEFAULT 'pending';

-- Valores: 'pending', 'matched', 'no_match', 'reviewed'
```

Fluxo:
```python
if classification == 'NO_MATCH':
    UPDATE produtos_tabela
    SET status_classificacao = 'no_match', data_classificacao = NOW()
    WHERE id = '123';
else:
    UPDATE produtos_tabela
    SET categoria_id = categoria_id, status_classificacao = 'matched', data_classificacao = NOW()
    WHERE id = '123';
```

**Vantagem**:
- Separa categoria (o quê foi classificado) de status (se tem classificação)
- Permite "reprocessar" produtos com `WHERE status = 'no_match'`
- Claro semanticamente

**Desvantagem**: Adiciona coluna ao schema

### Opção 3: Deixar NULL (Simples mas Ambíguo)

```python
if classification == 'NO_MATCH':
    # NÃO atualiza categoria_id (deixa NULL)
    UPDATE produtos_tabela
    SET data_classificacao = NOW()
    WHERE id = '123';
else:
    UPDATE produtos_tabela
    SET categoria_id = ?, data_classificacao = NOW()
    WHERE id = '123';
```

**Problema**: Não dá para distinguir:
- Produto que foi processado e não encontrou match
- Produto que nunca foi processado

```sql
SELECT * FROM produtos_tabela WHERE categoria_id IS NULL;
-- Ambos aparecem aqui!
```

### Opção 4: Usar Timestamp para Distinguir

```python
# Se foi processado, terá data_classificacao mesmo sem categoria_id
SELECT * FROM produtos_tabela
WHERE categoria_id IS NULL
AND data_classificacao IS NULL;  ← Apenas nunca processados
```

**Vantagem**: Sem mudanças de schema
**Desvantagem**: Query fica mais complexa

---

## 🎯 Recomendação

**MELHOR SOLUÇÃO: Opção 2 (Campo Status Separado)**

### Implementação:

1. **Adicionar coluna ao schema:**
```sql
ALTER TABLE produtos_tabela ADD COLUMN
  status_classificacao VARCHAR(20) DEFAULT 'pending' NOT NULL;

CREATE INDEX idx_produtos_status ON produtos_tabela(status_classificacao);
```

2. **Modificar batch.py:**
```python
def _get_unclassified_products(self, limit, offset, where_clause=None):
    # ANTES:
    # WHERE categoria IS NULL

    # DEPOIS:
    # WHERE status_classificacao IN ('pending', 'no_match_review')
    # OU melhor ainda:

    if reprocess_failed:
        query += " WHERE status_classificacao IN ('pending', 'no_match')"
    else:
        query += " WHERE status_classificacao = 'pending'"
```

3. **Modificar batch._update_product_classification():**
```python
if classification == 'NO_MATCH':
    cursor.execute(
        "UPDATE produtos_tabela SET status_classificacao = %s, data_classificacao = %s WHERE id = %s",
        ('no_match', datetime.now(), product_id)
    )
else:
    cursor.execute(
        """UPDATE produtos_tabela
           SET categoria_id = %s, status_classificacao = %s, data_classificacao = %s
           WHERE id = %s""",
        (categoria_id, 'matched', datetime.now(), product_id)
    )
```

---

## 📋 Ações Necessárias (Com Implementação FK)

### Durante a Migração do Schema:

```sql
-- Migration 003_create_regras_de_classificacao.sql JÁ CRIA COM categoria_id
-- Mas migrations não mexem em produtos_tabela

-- NECESSÁRIO: Nova migration para produtos_tabela

-- Migration: 001_alter_produtos_tabela.sql (ANTES das outras!)
ALTER TABLE produtos_tabela RENAME COLUMN categoria TO categoria_id_old;
ALTER TABLE produtos_tabela ADD COLUMN categoria_id INTEGER REFERENCES categorias(id);
ALTER TABLE produtos_tabela ADD COLUMN status_classificacao VARCHAR(20)
    DEFAULT 'pending' NOT NULL;

-- Migrar dados antigos
UPDATE produtos_tabela
SET categoria_id = c.id, status_classificacao = 'matched'
FROM categorias c
WHERE categoria_id_old = c.nome AND c.ativo = TRUE;

-- Marcar que falharam como "no_match"
UPDATE produtos_tabela
SET status_classificacao = 'no_match'
WHERE categoria_id IS NULL AND categoria_id_old IS NOT NULL;

-- Limpar coluna antiga
ALTER TABLE produtos_tabela DROP COLUMN categoria_id_old;

CREATE INDEX idx_produtos_status ON produtos_tabela(status_classificacao);
```

---

## ✅ Resumo: O Que Mudar

### Problema Identificado:
- ✗ Produtos com "NO_MATCH" ficam NULL e são reprocessados infinitamente
- ✗ Com FK, impossível inserir "NO_MATCH" como categoria

### Solução:
- ✓ Adicionar `status_classificacao` (pending, matched, no_match)
- ✓ Usar status para controlar qual produtos processar
- ✓ Permitir reprocessar produtos com `WHERE status = 'no_match'`

### Mudanças no Código:
1. **batch.py**: Alterar `WHERE categoria_id IS NULL` para `WHERE status IN (...)`
2. **batch.py**: Atualizar _update_product_classification() para usar status
3. **migrations**: Adicionar coluna status_classificacao
4. **conftest.py**: Atualizar testes para incluir status

### Sem Esta Solução:
- ❌ Loop infinito de produtos NO_MATCH
- ❌ FK constraint violations
- ❌ Impossível distinguir produtos processados de não processados
- ❌ Não dá para reprocessar após adicionar novas regras

---

**Conclusão**: Você identificou um bug crítico! Precisamos implementar a Opção 2 (status_classificacao) ANTES de fazer o deploy da mudança FK.

Quer que eu crie um documento com a implementação exata dessa solução?
