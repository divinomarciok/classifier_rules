# 📌 Quick Reference: Mudança Categorias (FK)

**Mudança**: String → Foreign Key
**Complexidade**: 🟡 Média
**Tempo**: ~8 horas
**Risco**: 🟢 Baixo (com backup)

---

## 🗺️ O QUE MUDA

```
ANTES                          DEPOIS
════════════════════════════════════════════════════════════
resultado_classificacao (str)  categoria_id (int FK)
"ELETRÔNICOS"                  → 1 (FK para categorias.id)
"CABOS"                        → 2
"ACESSÓRIOS"                   → 3

SEM tabela de referência       COM tabela categorias
(valores duplicados)           (1 fonte de verdade)
```

---

## 🔄 Ordem de Execução

### 1. Database Changes
```
📁 migrations/
  002_create_categorias.sql             ← PRIMEIRA
  003_create_regras_de_classificacao.sql ← SEGUNDA (depende de 002)
  004_create_auditoria_classificacao.sql ← TERCEIRA
  005_create_criterios_palavras_chave.sql ← QUARTA
```

### 2. Code Changes
```
📁 src/classifier/
  ├── models.py                    ← ADD Category, MODIFY Rule
  ├── category_service.py          ← NEW (serviço)
  ├── engine.py                    ← MODIFY (SQL + retorno)
  ├── audit.py                     ← MODIFY (armazenar FK)
  └── cli/
      ├── classify_batch.py        ← MODIFY (UPDATE)
      └── classify_csv.py          ← MODIFY (output)
```

---

## 📝 Mudanças Específicas

### models.py
```diff
+ class Category:
+     id: int
+     nome: str
+     descricao: str
+     ativo: bool

class Rule:
-   resultado_classificacao: str
+   categoria_id: int
```

### engine.py _load_rules() SQL
```diff
  SELECT
    id, prioridade, nome, ativo,
    criterio_*,
-   resultado_classificacao,
+   categoria_id,
    data_criacao, data_atualizacao
  FROM regras_de_classificacao
```

### engine.py evaluate()
```diff
  winner = Evaluator.select_winner(...)
+ # Buscar nome da categoria
+ cursor.execute("SELECT nome FROM categorias WHERE id = %s",
+                (winner.categoria_id,))
+ category_name = cursor.fetchone()[0]

  result = ClassificationResult(
-   classification=winner.resultado_classificacao,
+   classification=category_name,
+   categoria_id=winner.categoria_id,
```

---

## ✅ Checklist Rápida

**Antes de tudo**:
- [ ] Backup do banco: `pg_dump -d market_v1 > backup_$(date +%Y%m%d).dump`
- [ ] Lido `IMPLEMENTATION_CHECKLIST.md`
- [ ] Todos venv Python ativado

**Banco de Dados**:
- [ ] Tabelas antigas renomeadas (_old)
- [ ] Migration 002 executada
- [ ] Migration 003 executada
- [ ] Migration 004 executada
- [ ] Migration 005 executada
- [ ] `SELECT COUNT(*) FROM categorias;` retorna 5

**Código Python**:
- [ ] `models.py` - Category classe adicionada
- [ ] `models.py` - Rule.categoria_id adicionado
- [ ] `engine.py` - SQL atualizado
- [ ] `engine.py` - evaluate() retorna categoria_id
- [ ] `category_service.py` - Criado

**Testes**:
- [ ] `pytest tests/unit/ -v` passa
- [ ] `pytest tests/integration/ -v` passa
- [ ] Teste manual: categorias criadas, FK validado

**Documentação**:
- [ ] `docs/api.md` atualizado
- [ ] `docs/rules_guide.md` atualizado

---

## 🔍 Verificação Rápida SQL

```sql
-- 1. Categorias criadas?
SELECT COUNT(*) FROM categorias;  -- Deve ser 5

-- 2. Nova tabela estrutura correta?
\d regras_de_classificacao

-- 3. FK funciona?
INSERT INTO regras_de_classificacao
  (nome, ativo, prioridade, categoria_id)
VALUES ('Test', TRUE, 1, 999);
-- Deve FALHAR com "violates foreign key constraint"

-- 4. Nenhum NULL em categoria_id?
SELECT COUNT(*) FROM regras_de_classificacao
WHERE categoria_id IS NULL;  -- Deve ser 0
```

---

## 🚨 Se Falhar

### Erro: "FK constraint violation"
```sql
-- Problema: categoria_id não existe
-- Solução: Verificar categorias disponíveis
SELECT id, nome FROM categorias;
```

### Erro: "Cannot drop regras_de_classificacao"
```sql
-- Problema: Outra tabela referencia-a
-- Solução: Dropar nessa ordem:
DROP TABLE criterios_palavras_chave CASCADE;
DROP TABLE auditoria_classificacao CASCADE;
DROP TABLE regras_de_classificacao CASCADE;
DROP TABLE categorias CASCADE;
```

### Rollback Total
```bash
pg_restore -d market_v1 backup_YYYYMMDD.dump
```

---

## 📊 Impacto nas Queries

### Antes (String)
```sql
SELECT r.* FROM regras_de_classificacao r
WHERE r.resultado_classificacao = 'ELETRÔNICOS';
```

### Depois (FK)
```sql
SELECT r.* FROM regras_de_classificacao r
JOIN categorias c ON r.categoria_id = c.id
WHERE c.nome = 'ELETRÔNICOS';
```

---

## 🎯 Arquivos Principais para Editar

| Arquivo | Linhas | Tipo | Prioridade |
|---------|--------|------|-----------|
| `src/classifier/models.py` | +100, ~20 | ADD + MODIFY | 🔴 CRÍTICO |
| `src/classifier/engine.py` | ~20 | MODIFY | 🔴 CRÍTICO |
| `tests/conftest.py` | +20 | MODIFY | 🟡 IMPORTANTE |
| `src/classifier/audit.py` | ~5 | MODIFY | 🟢 MENOR |
| `src/classifier/cli/*.py` | ~5 | MODIFY | 🟢 MENOR |

---

## 🏃 Começar Agora

```bash
# 1. Backup
pg_dump -h localhost -U postgres -d market_v1 > backup_$(date +%Y%m%d).dump && echo "✓"

# 2. Verificar migrações
ls -la migrations/00[25]_*.sql

# 3. Abrir checklist completo
cat IMPLEMENTATION_CHECKLIST.md | less

# 4. Começar com Etapa 1 (BD)
psql -d market_v1 -f migrations/002_create_categorias.sql
```

---

## 📞 Referências

- Checklist completo: `IMPLEMENTATION_CHECKLIST.md`
- Próximos passos detalhados: `NEXT_STEPS.md`
- Documentação SpecKit: `.specify/memory/constitution.md` (v1.2.0)
- Migrações: `migrations/002-005_*.sql`
- Rollback: `migrations/ROLLBACK.md`

---

**Status**: Documentação 100% completa ✅
**Pronto para implementação**: SIM 🚀
