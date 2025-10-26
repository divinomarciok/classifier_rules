# 📋 Checklist de Implementação: Tabela de Categorias

**Data**: 2025-10-26
**Status**: Planning
**Objetivo**: Implementar refatoração de schema para usar tabela `categorias` com Foreign Keys

---

## 🎯 Visão Geral

Mudar de armazenar categorias como strings diretas em `regras_de_classificacao.resultado_classificacao` para uma tabela de referência centralizada `categorias` com relacionamentos via Foreign Key.

**Impacto**:
- ✅ Tabelas: 4 → 5 (adiciona `categorias`)
- ✅ Migrações: 4 → 5 (reordenadas)
- ✅ Modelos Python: 3 → 4 (adiciona `Category`)
- ✅ Banco de Dados: Schema completamente modificado

---

## 📊 Fases de Implementação

### Fase 0: Preparação do Banco de Dados

#### 0.1 Backup do Banco de Dados Atual
- [ ] **Criar backup** do banco `market_v1` antes de qualquer mudança
  ```bash
  pg_dump -h localhost -U postgres -d market_v1 > market_v1_backup_$(date +%Y%m%d).dump
  ```
- [ ] Verificar que o backup foi criado com sucesso

#### 0.2 Renomear Tabelas Antigas (Strategy: Copy → Rename)
- [ ] Criar snapshot da tabela atual:
  ```sql
  ALTER TABLE regras_de_classificacao RENAME TO regras_de_classificacao_old;
  ALTER TABLE auditoria_classificacao RENAME TO auditoria_classificacao_old;
  ALTER TABLE criterios_palavras_chave RENAME TO criterios_palavras_chave_old;
  ```
- [ ] Verificar que as tabelas foram renomeadas

#### 0.3 Opcional: Manter dados de regras antigas
- [ ] Se houver dados em `regras_de_classificacao_old`:
  ```sql
  -- Exportar dados para arquivo
  COPY regras_de_classificacao_old TO '/tmp/regras_backup.csv' WITH CSV HEADER;
  ```

---

### Fase 1: Aplicar Migrações de Banco de Dados

#### 1.1 Executar Migration 002 (Criar tabela categorias)
- [ ] Execute:
  ```bash
  psql -h localhost -U postgres -d market_v1 -f migrations/002_create_categorias.sql
  ```
- [ ] Verificar que tabela foi criada:
  ```sql
  SELECT COUNT(*) FROM categorias;
  -- Deve retornar 5 (categorias padrão seeded)
  ```
- [ ] Verificar dados seeded:
  ```sql
  SELECT id, nome FROM categorias ORDER BY id;
  ```

#### 1.2 Executar Migration 003 (Criar tabela regras_de_classificacao com FK)
- [ ] Execute:
  ```bash
  psql -h localhost -U postgres -d market_v1 -f migrations/003_create_regras_de_classificacao.sql
  ```
- [ ] Verificar estrutura:
  ```sql
  \d regras_de_classificacao
  ```
- [ ] Verificar FK:
  ```sql
  SELECT constraint_name, table_name, column_name
  FROM information_schema.key_column_usage
  WHERE table_name = 'regras_de_classificacao';
  ```

#### 1.3 Executar Migration 004 (Criar auditoria_classificacao)
- [ ] Execute:
  ```bash
  psql -h localhost -U postgres -d market_v1 -f migrations/004_create_auditoria_classificacao.sql
  ```

#### 1.4 Executar Migration 005 (Criar criterios_palavras_chave)
- [ ] Execute:
  ```bash
  psql -h localhost -U postgres -d market_v1 -f migrations/005_create_criterios_palavras_chave.sql
  ```

#### 1.5 Verificar Integridade Geral
- [ ] Verificar que não há erros:
  ```sql
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'public'
  ORDER BY table_name;
  -- Deve mostrar: auditoria_classificacao, categorias, criterios_palavras_chave, regras_de_classificacao
  ```

---

### Fase 2: Migrar Dados (Se existir dados históricos)

#### 2.1 Migrar Regras Antigas para Novo Schema
- [ ] Se tinha dados em `regras_de_classificacao_old`:
  ```sql
  -- Mapeamento: resultado_classificacao (string) → categoria_id (FK)
  INSERT INTO regras_de_classificacao (
    nome, ativo, prioridade,
    criterio_palavras_chave, criterio_ncm,
    criterio_tamanho_min, criterio_tamanho_max,
    criterio_quantidade_min, criterio_quantidade_max,
    criterio_categoria, categoria_id,
    data_criacao, data_atualizacao
  )
  SELECT
    r_old.nome, r_old.ativo, r_old.prioridade,
    r_old.criterio_palavras_chave, r_old.criterio_ncm,
    r_old.criterio_tamanho_min, r_old.criterio_tamanho_max,
    r_old.criterio_quantidade_min, r_old.criterio_quantidade_max,
    r_old.criterio_categoria, c.id,
    r_old.data_criacao, r_old.data_atualizacao
  FROM regras_de_classificacao_old r_old
  JOIN categorias c ON LOWER(c.nome) = LOWER(r_old.resultado_classificacao)
  WHERE c.ativo = TRUE
    AND r_old.resultado_classificacao IS NOT NULL;
  ```
- [ ] Verificar count de registros migrados:
  ```sql
  SELECT COUNT(*) FROM regras_de_classificacao;
  -- Deve ser >= número de regras antigas
  ```

#### 2.2 Migrar Auditoria Antiga (Opcional)
- [ ] Se tinha dados em `auditoria_classificacao_old`:
  ```sql
  -- Mapeamento similar para auditoria
  INSERT INTO auditoria_classificacao (
    id_regra, id_produto, descricao_produto, ncm_produto,
    resultado_classificacao, criterios_combinados,
    data_classificacao, tempo_avaliacao_ms, usuario_sistema
  )
  SELECT
    -- Pode deixar NULL se regra foi deletada
    NULL,
    a_old.id_produto, a_old.descricao_produto, a_old.ncm_produto,
    a_old.resultado_classificacao, a_old.criterios_combinados,
    a_old.data_classificacao, a_old.tempo_avaliacao_ms, a_old.usuario_sistema
  FROM auditoria_classificacao_old a_old;
  ```

#### 2.3 Limpar Tabelas Antigas
- [ ] Depois de verificar que dados foram migrados:
  ```sql
  DROP TABLE IF EXISTS regras_de_classificacao_old CASCADE;
  DROP TABLE IF EXISTS auditoria_classificacao_old CASCADE;
  DROP TABLE IF EXISTS criterios_palavras_chave_old CASCADE;
  ```

---

### Fase 3: Atualizar Modelos Python

#### 3.1 Criar Modelo Category
- [ ] **Arquivo**: `src/classifier/models.py`
- [ ] **Adicionar classe**:
  ```python
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
          return f"Category(id={self.id}, nome={self.nome}, ativo={self.ativo})"
  ```

#### 3.2 Atualizar Modelo Rule
- [ ] **Arquivo**: `src/classifier/models.py`
- [ ] **Modificar construtor**:
  ```python
  def __init__(
      self,
      id: int,
      prioridade: int,
      nome: str,
      ativo: bool,
      categoria_id: int,  # ← NOVO (era resultado_classificacao: str)
      criterio_palavras_chave: Optional[str] = None,
      # ... resto dos critérios
      data_criacao: Optional[datetime] = None,
      data_atualizacao: Optional[datetime] = None,
  ):
      # ... adicionar
      self.categoria_id = categoria_id
      # remover: self.resultado_classificacao
  ```
- [ ] **Atualizar from_db_row()**:
  ```python
  @classmethod
  def from_db_row(cls, row: tuple) -> 'Rule':
      return cls(
          id=row[0],
          prioridade=row[1],
          nome=row[2],
          ativo=row[3],
          criterio_palavras_chave=row[4],
          # ...
          categoria_id=row[11],  # ← NOVO (era resultado_classificacao)
          data_criacao=row[12],
          data_atualizacao=row[13],
      )
  ```

#### 3.3 Atualizar Modelo ClassificationResult
- [ ] **Arquivo**: `src/classifier/models.py`
- [ ] **Modificar para usar categoria_id**:
  ```python
  def __init__(
      self,
      classification: str,  # Ainda pode ser nome da categoria ou ID
      categoria_id: Optional[int] = None,  # ← NOVO
      rule_id: Optional[int] = None,
      # ... resto dos campos
  ):
      self.classification = classification
      self.categoria_id = categoria_id
      # ...
  ```

#### 3.4 Atualizar Modelo Product
- [ ] **Arquivo**: `src/classifier/models.py`
- [ ] **Mudar category field**:
  ```python
  def __init__(
      self,
      description: str,
      ncm: str,
      id: Optional[str] = None,
      size: Optional[float] = None,
      quantity: Optional[int] = None,
      categoria_id: Optional[int] = None,  # ← NOVO (era category: str)
      **kwargs
  ):
      # ...
      self.categoria_id = categoria_id  # (era self.category)
  ```

---

### Fase 4: Atualizar Camada de Acesso a Dados

#### 4.1 Criar Serviço CategoryService
- [ ] **Arquivo**: `src/classifier/category_service.py` (NOVO)
- [ ] **Implementar métodos**:
  ```python
  class CategoryService:
      def __init__(self, db_connection):
          self.db_connection = db_connection

      def get_all_categories(self, active_only=True):
          """Get all categories"""
          # ...

      def get_category_by_id(self, category_id: int):
          """Get category by ID"""
          # ...

      def get_category_by_name(self, name: str):
          """Get category by name"""
          # ...

      def validate_category_id(self, category_id: int):
          """Validate that category exists"""
          # ...
  ```

#### 4.2 Atualizar engine.py - SQL Query
- [ ] **Arquivo**: `src/classifier/engine.py`
- [ ] **Método `_load_rules()`**: Atualizar SELECT:
  ```python
  cursor.execute("""
      SELECT
          id, prioridade, nome, ativo,
          criterio_palavras_chave, criterio_ncm,
          criterio_tamanho_min, criterio_tamanho_max,
          criterio_quantidade_min, criterio_quantidade_max,
          criterio_categoria,
          categoria_id,  -- ← NOVO (era resultado_classificacao)
          data_criacao, data_atualizacao
      FROM regras_de_classificacao
      WHERE ativo = TRUE
      ORDER BY prioridade DESC, data_criacao ASC
  """)
  ```

#### 4.3 Atualizar engine.py - Retornar Nome da Categoria
- [ ] **Arquivo**: `src/classifier/engine.py`
- [ ] **Método `evaluate()`**: Quando retorna ClassificationResult:
  ```python
  # JOIN com categorias para obter nome
  cursor.execute("""
      SELECT c.nome FROM categorias c WHERE c.id = %s
  """, (winner.categoria_id,))
  category_name = cursor.fetchone()[0]

  result = ClassificationResult(
      classification=category_name,  # Nome da categoria
      categoria_id=winner.categoria_id,  # ID numérico
      rule_id=winner.id,
      # ...
  )
  ```

---

### Fase 5: Atualizar Audit Service

#### 5.1 Atualizar audit.py
- [ ] **Arquivo**: `src/classifier/audit.py`
- [ ] **Método `record()`**: Deve aceitar `categoria_id` ao invés de categoria string:
  ```python
  def record(
      self,
      rule_id: Optional[int],
      product_data: dict,
      matched_criteria: list,
      categoria_id: int,  # ← NOVO (era categoria_name: str)
      evaluation_time_ms: int,
      user: str = 'system'
  ):
      # ...
  ```
- [ ] **Insert Statement**:
  ```python
  cursor.execute("""
      INSERT INTO auditoria_classificacao (
          id_regra, id_produto, descricao_produto, ncm_produto,
          resultado_classificacao, criterios_combinados,
          data_classificacao, tempo_avaliacao_ms, usuario_sistema
      ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
  """, (
      rule_id,
      product_data.get('id'),
      product_data.get('description'),
      product_data.get('ncm'),
      categoria_id,  # Armazenar ID, não nome
      json.dumps(matched_criteria),
      datetime.now(),
      evaluation_time_ms,
      user
  ))
  ```

---

### Fase 6: Atualizar CLI Scripts

#### 6.1 Atualizar classify_batch.py
- [ ] **Arquivo**: `src/classifier/cli/classify_batch.py`
- [ ] **Modificar para usar categoria_id** nas UPDATEs:
  ```python
  # Antes:
  # UPDATE produtos_tabela SET categoria = %s WHERE id = %s

  # Depois:
  # UPDATE produtos_tabela SET categoria_id = %s WHERE id = %s
  ```

#### 6.2 Atualizar classify_csv.py
- [ ] **Arquivo**: `src/classifier/cli/classify_csv.py`
- [ ] **Output CSV**: Inclua tanto `categoria_id` quanto `categoria_nome`

---

### Fase 7: Atualizar Testes

#### 7.1 Atualizar conftest.py
- [ ] **Arquivo**: `tests/conftest.py`
- [ ] **Fixture `sample_categories`** (NOVA):
  ```python
  @pytest.fixture(scope="function")
  def sample_categories(db_connection):
      cursor = db_connection.cursor()
      cursor.execute("""
          INSERT INTO categorias (nome, descricao, ativo)
          VALUES
              ('ELETRÔNICOS', 'Eletrônicos', TRUE),
              ('CABOS', 'Cabos', TRUE),
              ('ACESSÓRIOS', 'Acessórios', TRUE)
          RETURNING id
      """)
      ids = [row[0] for row in cursor.fetchall()]
      db_connection.commit()

      yield ids

      # Cleanup
      cursor.execute("TRUNCATE TABLE categorias CASCADE")
      db_connection.commit()
  ```

#### 7.2 Atualizar fixture `sample_rules`
- [ ] **Arquivo**: `tests/conftest.py`
- [ ] **Modificar para DEPENDER de `sample_categories`**:
  ```python
  @pytest.fixture(scope="function")
  def sample_rules(db_connection, sample_categories):
      # Deve executar DEPOIS de sample_categories
      categoria_id = sample_categories[0]  # Use primeira categoria

      cursor = db_connection.cursor()
      cursor.execute("""
          INSERT INTO regras_de_classificacao (
              nome, ativo, prioridade,
              criterio_palavras_chave, categoria_id
          )
          VALUES (%s, %s, %s, %s, %s)
      """, ('Test Rule', True, 1, 'laptop', categoria_id))
      # ...
  ```

#### 7.3 Atualizar Testes de Modelos
- [ ] **Arquivo**: `tests/unit/test_models.py`
- [ ] Adicionar testes para `Category` class
- [ ] Atualizar testes de `Rule.from_db_row()` para nova ordem de colunas

#### 7.4 Atualizar Testes de Engine
- [ ] **Arquivo**: `tests/integration/test_rule_evaluation.py`
- [ ] Atualizar esperado `resultado_classificacao` → `categoria_id`
- [ ] Verificar que `engine.evaluate()` retorna `categoria_id`

---

### Fase 8: Validação e Testes

#### 8.1 Rodar Suite de Testes
- [ ] Execute:
  ```bash
  pytest tests/ -v
  ```
- [ ] Todos os testes devem passar
- [ ] Cobertura deve ser >= 85%

#### 8.2 Testes Manuais
- [ ] **Teste 1**: Criar categoria e regra manualmente:
  ```sql
  INSERT INTO categorias (nome, descricao) VALUES ('TEST', 'Test Category');
  INSERT INTO regras_de_classificacao (nome, ativo, prioridade, criterio_palavras_chave, categoria_id)
  VALUES ('Test Rule', TRUE, 1, 'test', 1);
  ```
- [ ] **Teste 2**: Classificar produto via CLI:
  ```bash
  python -m classifier.cli.classify_batch --limit 10
  ```
- [ ] **Teste 3**: Verificar audit logs:
  ```sql
  SELECT * FROM auditoria_classificacao LIMIT 5;
  ```

#### 8.3 Testes de Performance
- [ ] Rodar com 1000+ regras para verificar < 500ms
- [ ] Verificar índices foram criados:
  ```sql
  SELECT * FROM pg_indexes WHERE tablename = 'regras_de_classificacao';
  ```

#### 8.4 Testes de Integridade Referencial
- [ ] Tentar inserir regra com categoria_id inválido:
  ```sql
  INSERT INTO regras_de_classificacao (nome, ativo, prioridade, categoria_id)
  VALUES ('Bad Rule', TRUE, 1, 999);
  -- Deve FALHAR com FK constraint error
  ```
- [ ] Tentar deletar categoria em uso:
  ```sql
  DELETE FROM categorias WHERE id = 1;
  -- Deve FALHAR com ON DELETE RESTRICT
  ```

---

### Fase 9: Documentação

#### 9.1 Atualizar API Docs
- [ ] **Arquivo**: `docs/api.md`
- [ ] Documentar novo endpoint/método `CategoryService.get_category_by_id()`

#### 9.2 Atualizar Rules Guide
- [ ] **Arquivo**: `docs/rules_guide.md`
- [ ] Exemplo: "Como criar regra com nova FK"

#### 9.3 Atualizar README
- [ ] Mencionar que categorias agora são tabela de referência

---

## 🔍 Verificações Finais

### Checklist de Validação
- [ ] Todas as 5 migrações executadas com sucesso
- [ ] Não há violações de FK constraint
- [ ] Todos os testes passam
- [ ] Banco tem 79,201+ produtos com categorias atribuídas
- [ ] Documentação sincronizada
- [ ] Não há breaking changes em APIs públicas (versão minor bump)

### Rollback Plan
- [ ] Se algo falhar, usar `migrations/ROLLBACK.md`
- [ ] Restore backup: `pg_restore -d market_v1 market_v1_backup_YYYYMMDD.dump`

---

## 📅 Estimativa de Tempo

| Fase | Tarefa | Tempo |
|------|--------|-------|
| 0 | Preparação BD | 30 min |
| 1 | Migrações | 15 min |
| 2 | Migração dados | 30 min |
| 3 | Modelos Python | 1 hora |
| 4 | Acesso dados | 1.5 horas |
| 5 | Audit | 30 min |
| 6 | CLI Scripts | 1 hora |
| 7 | Testes | 1.5 horas |
| 8 | Validação | 1 hora |
| 9 | Docs | 30 min |
| **TOTAL** | | **~8 horas** |

---

## 🚀 Próximos Passos

1. **Confirmar que tudo está documentado** ✅ (já feito)
2. **Fazer backup** (fase 0.1)
3. **Executar migrações** (fase 1)
4. **Atualizar código Python** (fases 3-6)
5. **Rodar testes** (fase 7-8)
6. **Atualizar documentação** (fase 9)

---

**Gerado em**: 2025-10-26
**Última atualização**: IMPLEMENTATION_CHECKLIST.md
