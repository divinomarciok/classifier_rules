# ✅ O Que Precisa Fazer Agora

## 🎯 Resumo Executivo

Você documentou completamente a mudança (4 documentos SpecKit atualizados + 5 migrations SQL criadas). Agora precisa **IMPLEMENTAR** as mudanças no código e banco de dados.

---

## 🚦 Fase Crítica: 3 Etapas Principais

### 1️⃣ **Banco de Dados** (30-45 min)
```bash
# 1. Backup PRIMEIRO!
pg_dump -h localhost -U postgres -d market_v1 > backup_$(date +%Y%m%d).dump

# 2. Renomear tabelas antigas (para rollback seguro)
psql -d market_v1 << 'EOF'
ALTER TABLE regras_de_classificacao RENAME TO regras_de_classificacao_old;
ALTER TABLE auditoria_classificacao RENAME TO auditoria_classificacao_old;
ALTER TABLE criterios_palavras_chave RENAME TO criterios_palavras_chave_old;
EOF

# 3. Executar todas as 5 migrações em ordem
psql -d market_v1 -f migrations/002_create_categorias.sql
psql -d market_v1 -f migrations/003_create_regras_de_classificacao.sql
psql -d market_v1 -f migrations/004_create_auditoria_classificacao.sql
psql -d market_v1 -f migrations/005_create_criterios_palavras_chave.sql

# 4. Verificar que funcionou
psql -d market_v1 << 'EOF'
SELECT COUNT(*) FROM categorias;
SELECT COUNT(*) FROM regras_de_classificacao;
EOF
```

### 2️⃣ **Modelos Python** (1-1.5 horas)
Editar: `src/classifier/models.py`
```python
# ADICIONAR: Classe Category (nova)
class Category:
    def __init__(self, id, nome, descricao, ativo, ...): ...

# MODIFICAR: Classe Rule
# Trocar: resultado_classificacao (str) → categoria_id (int)
self.categoria_id = categoria_id  # novo
# Remover: self.resultado_classificacao

# MODIFICAR: ClassificationResult
# Adicionar: categoria_id para rastrear ID numérico
# Manter: classification (pode ser nome ou ID dependendo contexto)

# MODIFICAR: Product
# Trocar: category (str) → categoria_id (int)
```

### 3️⃣ **Código da Aplicação** (2-2.5 horas)
Editar múltiplos arquivos em ordem:

```
src/classifier/
├── category_service.py      ← NOVO (serviço para categorias)
├── engine.py                ← MODIFICAR (SQL + retorno categoria_id)
├── audit.py                 ← MODIFICAR (armazenar categoria_id)
└── cli/
    ├── classify_batch.py    ← MODIFICAR (UPDATE usa categoria_id)
    └── classify_csv.py      ← MODIFICAR (output tem categoria_id)
```

---

## 📋 Checklist Executável

### Etapa 1: Banco de Dados
```bash
# Rodar isto:
cd /home/divinopc/testes/projects/classifier_regras

# Backup
pg_dump -h localhost -U postgres -d market_v1 > backup_before_categories.dump
echo "✓ Backup criado"

# Renomear tabelas antigas
psql -d market_v1 -c "ALTER TABLE regras_de_classificacao RENAME TO regras_de_classificacao_old;"
psql -d market_v1 -c "ALTER TABLE auditoria_classificacao RENAME TO auditoria_classificacao_old;"
psql -d market_v1 -c "ALTER TABLE criterios_palavras_chave RENAME TO criterios_palavras_chave_old;"
echo "✓ Tabelas antigas renomeadas"

# Executar migrações
psql -d market_v1 -f migrations/002_create_categorias.sql
echo "✓ Migration 002 (categorias) executada"

psql -d market_v1 -f migrations/003_create_regras_de_classificacao.sql
echo "✓ Migration 003 (regras) executada"

psql -d market_v1 -f migrations/004_create_auditoria_classificacao.sql
echo "✓ Migration 004 (auditoria) executada"

psql -d market_v1 -f migrations/005_create_criterios_palavras_chave.sql
echo "✓ Migration 005 (criterios) executada"

# Verificar
psql -d market_v1 << 'VERIFY'
\echo "=== VERIFICAÇÃO ===="
\echo "Categorias:"
SELECT COUNT(*) as count FROM categorias;
\echo "Regras (deve ser 0 antes de migrar dados):"
SELECT COUNT(*) as count FROM regras_de_classificacao;
VERIFY

echo "✓ BD pronto!"
```

### Etapa 2: Modelos Python
```python
# Arquivo: src/classifier/models.py

# Procure por: "class Rule:"
# ADICIONE antes:
class Category:
    """Represents a product category from categorias table"""

    def __init__(
        self,
        id: int,
        nome: str,
        descricao: Optional[str] = None,
        ativo: bool = True,
        data_criacao: Optional[datetime] = None,
        data_atualizacao: Optional[datetime] = None,
    ):
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.ativo = ativo
        self.data_criacao = data_criacao or datetime.now()
        self.data_atualizacao = data_atualizacao or datetime.now()

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Category':
        return cls(
            id=row[0],
            nome=row[1],
            descricao=row[2],
            ativo=row[3],
            data_criacao=row[4],
            data_atualizacao=row[5],
        )

    def __repr__(self) -> str:
        return f"Category(id={self.id}, nome={self.nome})"


# MODIFICAR: class Rule
# No __init__, TROCAR:
# - ANTES: resultado_classificacao: str
# - DEPOIS: categoria_id: int

# E no from_db_row():
# - ANTES: resultado_classificacao=row[11]
# - DEPOIS: categoria_id=row[11]
```

### Etapa 3: Engine Python
```python
# Arquivo: src/classifier/engine.py

# 1. Encontre método _load_rules()
# 2. NO SELECT SQL, MUDE:
#    ANTES: resultado_classificacao,
#    DEPOIS: categoria_id,

# 3. NO método evaluate(), APOS "SELECT winner":
# ADICIONE:
# Buscar nome da categoria
cursor.execute("SELECT nome FROM categorias WHERE id = %s", (winner.categoria_id,))
category_name = cursor.fetchone()[0]

# Retornar com nome
result = ClassificationResult(
    classification=category_name,  # Nome da categoria
    categoria_id=winner.categoria_id,  # ID numérico
    rule_id=winner.id,
    # ... resto igual
)
```

---

## 🧪 Testes Rápidos (Validação)

Depois de implementar, rodar:

```bash
# 1. Testes unitários
pytest tests/unit/test_models.py -v

# 2. Testes de integração
pytest tests/integration/test_rule_evaluation.py -v

# 3. Teste manual no banco
psql -d market_v1 << 'EOF'
-- Deve retornar 5
SELECT COUNT(*) FROM categorias;

-- Deve retornar estrutura com categoria_id FK
\d regras_de_classificacao

-- Deve falhar (FK constraint)
INSERT INTO regras_de_classificacao (nome, ativo, prioridade, categoria_id)
VALUES ('Bad Rule', TRUE, 1, 999);
EOF
```

---

## 📊 Tamanho das Mudanças

| Arquivo | Tipo | Mudanças |
|---------|------|----------|
| `models.py` | ADD + MODIFY | +100 linhas (Category), ~20 linhas (Rule) |
| `engine.py` | MODIFY | ~15 linhas (SQL + retorno) |
| `audit.py` | MODIFY | ~5 linhas (usar categoria_id) |
| `cli/classify_batch.py` | MODIFY | ~2 linhas (coluna update) |
| `cli/classify_csv.py` | MODIFY | ~2 linhas (output CSV) |
| `category_service.py` | NEW | ~100 linhas (novo serviço) |

**Total**: ~260 linhas de código novo/modificado

---

## 🚨 Se Algo Falhar

### Rollback Rápido
```bash
# 1. Restaurar backup
pg_restore -d market_v1 /path/to/backup_before_categories.dump

# 2. Ou desfazer migrações manualmente
psql -d market_v1 << 'EOF'
DROP TABLE IF EXISTS criterios_palavras_chave CASCADE;
DROP TABLE IF EXISTS auditoria_classificacao CASCADE;
DROP TABLE IF EXISTS regras_de_classificacao CASCADE;
DROP TABLE IF EXISTS categorias CASCADE;

-- Restaurar nomes antigos
ALTER TABLE regras_de_classificacao_old RENAME TO regras_de_classificacao;
ALTER TABLE auditoria_classificacao_old RENAME TO auditoria_classificacao;
ALTER TABLE criterios_palavras_chave_old RENAME TO criterios_palavras_chave;
EOF
```

---

## ✨ Benefícios Após Implementação

✅ **Data Normalization** - Sem duplicação de categorias
✅ **Integridade** - Impossível categoria inválida (FK constraint)
✅ **Flexibilidade** - Renomear/desativar categorias sem quebrar regras
✅ **Auditabilidade** - Rastrear uso de cada categoria
✅ **Performance** - Índices otimizados para categoria_id

---

## 📞 Documentação Criada

Todos esses documentos estão sincronizados:

- ✅ `CLAUDE.md` - Setup e troubleshooting
- ✅ `.specify/memory/constitution.md` - Princípios (v1.2.0)
- ✅ `specs/001-rule-engine/spec.md` - Requisitos
- ✅ `specs/001-rule-engine/plan.md` - Arquitetura
- ✅ `specs/001-rule-engine/tasks.md` - Tasks detalhadas (68 tasks)
- ✅ `migrations/002-005_*.sql` - SQLs de migração
- ✅ `migrations/ROLLBACK.md` - Procedimentos de rollback
- ✅ `IMPLEMENTATION_CHECKLIST.md` - Este arquivo (checklist completo)

---

## 🎬 Comece Aqui

```bash
# 1. Vá até o diretório
cd /home/divinopc/testes/projects/classifier_regras

# 2. Faça backup (ESSENCIAL!)
pg_dump -h localhost -U postgres -d market_v1 > backup_$(date +%Y%m%d).dump

# 3. Abra IMPLEMENTATION_CHECKLIST.md para guia detalhado
cat IMPLEMENTATION_CHECKLIST.md

# 4. Ou execute as migrações agora:
psql -d market_v1 -f migrations/002_create_categorias.sql
```

---

**Tempo total estimado**: 6-8 horas
**Dificuldade**: Média (SQL + Python)
**Risco**: Baixo (com backup)

🚀 Você está pronto para começar!
