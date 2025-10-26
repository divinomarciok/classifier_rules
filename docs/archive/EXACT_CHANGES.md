# 🎯 Mudanças Exatas no Código (Pré-Implementação)

**Data**: 2025-10-26
**Objetivo**: Mostrar EXATAMENTE o que mudará no código

---

## 1. models.py - Adicionar Category e Modificar Rule

### NOVO: Classe Category
```python
# ADICIONAR NO INÍCIO DE models.py (após imports)

class Category:
    """Represents a product category from categorias table

    Attributes:
        id: Category unique identifier
        nome: Category name (e.g., "ELETRÔNICOS", "CABOS")
        descricao: Category description
        ativo: Whether category is currently in use
        data_criacao: When category was created
        data_atualizacao: When category was last updated
    """

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
        """Construct Category from database tuple"""
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

### MODIFICAR: Classe Rule

**Linha 27-43 (__init__):**
```diff
  def __init__(
      self,
      id: int,
      prioridade: int,
      nome: str,
      ativo: bool,
-     resultado_classificacao: str,  ← REMOVER
+     categoria_id: int,              ← ADICIONAR (nova)
      criterio_palavras_chave: Optional[str] = None,
      criterio_ncm: Optional[str] = None,
      criterio_tamanho_min: Optional[float] = None,
      criterio_tamanho_max: Optional[float] = None,
      criterio_quantidade_min: Optional[int] = None,
      criterio_quantidade_max: Optional[int] = None,
      criterio_categoria: Optional[str] = None,
      data_criacao: Optional[datetime] = None,
      data_atualizacao: Optional[datetime] = None,
  ):
```

**Linha 44-57 (body de __init__):**
```diff
      self.id = id
      self.prioridade = prioridade
      self.nome = nome
      self.ativo = ativo
      self.criterio_palavras_chave = criterio_palavras_chave
      self.criterio_ncm = criterio_ncm
      self.criterio_tamanho_min = criterio_tamanho_min
      self.criterio_tamanho_max = criterio_tamanho_max
      self.criterio_quantidade_min = criterio_quantidade_min
      self.criterio_quantidade_max = criterio_quantidade_max
      self.criterio_categoria = criterio_categoria
-     self.resultado_classificacao = resultado_classificacao  ← REMOVER
+     self.categoria_id = categoria_id  ← ADICIONAR (nova)
      self.data_criacao = data_criacao or datetime.now()
      self.data_atualizacao = data_atualizacao or datetime.now()
```

**Linha 59-84 (from_db_row):**
```diff
  @classmethod
  def from_db_row(cls, row: tuple) -> 'Rule':
      return cls(
          id=row[0],
          prioridade=row[1],
          nome=row[2],
          ativo=row[3],
          criterio_palavras_chave=row[4],
          criterio_ncm=row[5],
          criterio_tamanho_min=row[6],
          criterio_tamanho_max=row[7],
          criterio_quantidade_min=row[8],
          criterio_quantidade_max=row[9],
          criterio_categoria=row[10],
-         resultado_classificacao=row[11],  ← REMOVER
+         categoria_id=row[11],  ← ADICIONAR (nova)
          data_criacao=row[12],
          data_atualizacao=row[13],
      )
```

### MODIFICAR: Classe Product

**Linha 119-136 (__init__):**
```diff
  def __init__(
      self,
      description: str,
      ncm: str,
      id: Optional[str] = None,
      size: Optional[float] = None,
      quantity: Optional[int] = None,
-     category: Optional[str] = None,  ← REMOVER
+     categoria_id: Optional[int] = None,  ← ADICIONAR (nova)
      **kwargs
  ):
      self.id = id
      self.description = description
      self.ncm = ncm
      self.size = size
      self.quantity = quantity
-     self.category = category  ← REMOVER
+     self.categoria_id = categoria_id  ← ADICIONAR (nova)
      self._extra_fields = kwargs
```

**Linha 159-174 (to_dict):**
```diff
  def to_dict(self) -> Dict[str, Any]:
      data = {
          'id': self.id,
          'description': self.description,
          'ncm': self.ncm,
          'size': self.size,
          'quantity': self.quantity,
-         'category': self.category,  ← REMOVER
+         'categoria_id': self.categoria_id,  ← ADICIONAR (nova)
      }
      data.update(self._extra_fields)
      return data
```

---

## 2. engine.py - Modificar SQL e Evaluate

### MODIFICAR: Método _load_rules() - SQL

**Linha 62-74 (SELECT statement):**
```diff
      cursor.execute("""
          SELECT
              id, prioridade, nome, ativo,
              criterio_palavras_chave, criterio_ncm,
              criterio_tamanho_min, criterio_tamanho_max,
              criterio_quantidade_min, criterio_quantidade_max,
              criterio_categoria,
-             resultado_classificacao,  ← REMOVER
+             categoria_id,  ← ADICIONAR (nova)
              data_criacao, data_atualizacao
          FROM regras_de_classificacao
          WHERE ativo = TRUE
          ORDER BY prioridade DESC, data_criacao ASC
      """)
```

### MODIFICAR: Método evaluate() - Retorno

**Linha 214-224 (Construir ClassificationResult):**
```diff
  # 5. Select winner (FR-004, FR-005, FR-006)
  try:
      winner = Evaluator.select_winner(matching_rules)
  except EvaluationError as e:
      logger.error(f"Error selecting winner: {e}")
      raise

+ # NOVO: Buscar nome da categoria
+ try:
+     cursor = self.db_connection.cursor()
+     cursor.execute("SELECT nome FROM categorias WHERE id = %s", (winner.categoria_id,))
+     category_row = cursor.fetchone()
+     category_name = category_row[0] if category_row else "UNKNOWN"
+     cursor.close()
+ except Exception as e:
+     logger.error(f"Error fetching category name: {e}")
+     category_name = f"CATEGORY_{winner.categoria_id}"

  # 6. Build result
  result = ClassificationResult(
-     classification=winner.resultado_classificacao,  ← REMOVER
+     classification=category_name,  ← ADICIONAR (usando nome)
+     categoria_id=winner.categoria_id,  ← ADICIONAR (novo)
      rule_id=winner.id,
      rule_name=winner.nome,
      priority=winner.prioridade,
      matched_criteria=['criterio_' + c for c in ['palavras_chave', 'ncm', 'tamanho_min', 'tamanho_max', 'quantidade_min', 'quantidade_max', 'categoria'] if getattr(winner, f'criterio_{c}', None) is not None],
      evaluation_time_ms=elapsed_ms,
      success=True,
-     message=f'Matched rule {winner.id} ({winner.nome})'
+     message=f'Matched rule {winner.id} ({winner.nome}) → {category_name}'
  )
```

---

## 3. batch.py - Modificar Leitura e Update

### MODIFICAR: Método _row_to_product()

**Linha 178-209:**
```diff
  def _row_to_product(self, row: tuple) -> Product:
      # Extract required fields (always present)
      product_id = row[0]
      description = row[1]
      ncm = row[2]

      # Extract optional fields with safe indexing
-     categoria = row[3] if len(row) > 3 else None  ← REMOVER
+     categoria_id = row[3] if len(row) > 3 else None  ← ADICIONAR (nova)
      size = row[4] if len(row) > 4 else None
      quantity = row[5] if len(row) > 5 else None

      # Create product with flexible schema
      product = Product(
          id=product_id,
          description=description,
          ncm=ncm,
          size=size,
          quantity=quantity,
-         category=categoria  ← REMOVER
+         categoria_id=categoria_id  ← ADICIONAR (nova)
      )

      return product
```

### MODIFICAR: Método _update_product_classification()

**Linha 211-238 (UPDATE statement):**
```diff
  def _update_product_classification(self, product_id: str, classification: str) -> bool:
      try:
          cursor = self.db_connection.cursor()

-         cursor.execute(
-             "UPDATE produtos_tabela SET categoria = %s, data_classificacao = %s WHERE id = %s",
-             (classification, datetime.now(), product_id)
-         )

+         # NOVO: Buscar categoria_id a partir do nome
+         cursor.execute(
+             "SELECT id FROM categorias WHERE nome = %s AND ativo = TRUE",
+             (classification,)
+         )
+         category_row = cursor.fetchone()
+         if not category_row:
+             logger.error(f"Category '{classification}' not found in categorias table")
+             cursor.close()
+             return False
+
+         categoria_id = category_row[0]
+
+         cursor.execute(
+             "UPDATE produtos_tabela SET categoria_id = %s, data_classificacao = %s WHERE id = %s",
+             (categoria_id, datetime.now(), product_id)
+         )

          self.db_connection.commit()
          cursor.close()

-         logger.debug(f"Updated product {product_id} with classification {classification}")
+         logger.debug(f"Updated product {product_id} with categoria_id {categoria_id}")
          return True

      except Exception as e:
          logger.error(f"Error updating product {product_id}: {e}")
          self.db_connection.rollback()
          raise
```

### MODIFICAR: Método get_batch_statistics()

**Linha 240-273 (verificações):**
```diff
  def get_batch_statistics(self) -> Dict[str, Any]:
      try:
          cursor = self.db_connection.cursor()

          # Count classified vs unclassified
-         cursor.execute("SELECT COUNT(*) FROM produtos_tabela WHERE categoria IS NOT NULL")
+         cursor.execute("SELECT COUNT(*) FROM produtos_tabela WHERE categoria_id IS NOT NULL")
          classified_count = cursor.fetchone()[0]

-         cursor.execute("SELECT COUNT(*) FROM produtos_tabela WHERE categoria IS NULL")
+         cursor.execute("SELECT COUNT(*) FROM produtos_tabela WHERE categoria_id IS NULL")
          unclassified_count = cursor.fetchone()[0]

          total_count = classified_count + unclassified_count

          cursor.close()

          statistics = {
              'total_products': total_count,
              'classified': classified_count,
              'unclassified': unclassified_count,
              'classification_rate': classified_count / total_count if total_count > 0 else 0.0,
          }

          return statistics

      except Exception as e:
          logger.error(f"Error getting batch statistics: {e}")
          return {}
```

### MODIFICAR: Método _get_unclassified_products()

**Linha 139-176 (SELECT unclassified):**
```diff
  def _get_unclassified_products(self, limit: int, offset: int, where_clause: Optional[str] = None) -> List[tuple]:
      try:
          cursor = self.db_connection.cursor()

          # Build query for unclassified products
-         query = "SELECT * FROM produtos_tabela WHERE categoria IS NULL"
+         query = "SELECT * FROM produtos_tabela WHERE categoria_id IS NULL"

          if where_clause:
              query += f" AND {where_clause}"

          query += f" LIMIT %s OFFSET %s"

          params = [limit, offset]
          cursor.execute(query, params)
          rows = cursor.fetchall()
          cursor.close()

          logger.debug(f"Queried {len(rows)} unclassified products")
          return rows

      except Exception as e:
          logger.error(f"Error querying products: {e}")
          raise
```

---

## 4. audit.py - Armazenar categoria_id

### MODIFICAR: Método record()

**Encontrar assinatura do método record e modificar:**
```diff
- def record(self, rule_id, product_data, matched_criteria, classification, evaluation_time_ms, user='system'):
+ def record(self, rule_id, product_data, matched_criteria, categoria_id, evaluation_time_ms, user='system'):
```

**Modificar INSERT statement:**
```diff
  cursor.execute(
      """INSERT INTO auditoria_classificacao (
          id_regra, id_produto, descricao_produto, ncm_produto,
          resultado_classificacao, criterios_combinados,
          data_classificacao, tempo_avaliacao_ms, usuario_sistema
      ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
      (
          rule_id,
          product_data.get('id'),
          product_data.get('description'),
          product_data.get('ncm'),
-         classification,  ← REMOVER (era string)
+         categoria_id,    ← ADICIONAR (novo - será int)
          json.dumps(matched_criteria),
          datetime.now(),
          evaluation_time_ms,
          user
      )
  )
```

---

## 5. ClassificationResult - Adicionar categoria_id

### MODIFICAR: models.py - ClassificationResult.__init__

**Linha 194-212:**
```diff
  def __init__(
      self,
      classification: str,
+     categoria_id: Optional[int] = None,  ← ADICIONAR
      rule_id: Optional[int] = None,
      rule_name: Optional[str] = None,
      priority: Optional[int] = None,
      matched_criteria: Optional[List[str]] = None,
      evaluation_time_ms: int = 0,
      success: bool = True,
      message: str = '',
  ):
      self.classification = classification
+     self.categoria_id = categoria_id  ← ADICIONAR
      self.rule_id = rule_id
      self.rule_name = rule_name
      self.priority = priority
      self.matched_criteria = matched_criteria or []
      self.evaluation_time_ms = evaluation_time_ms
      self.success = success
      self.message = message
```

**Linha 214-229 (to_dict):**
```diff
  def to_dict(self) -> Dict[str, Any]:
      return {
          'classification': self.classification,
+         'categoria_id': self.categoria_id,  ← ADICIONAR
          'rule_id': self.rule_id,
          'rule_name': self.rule_name,
          'priority': self.priority,
          'matched_criteria': self.matched_criteria,
          'evaluation_time_ms': self.evaluation_time_ms,
          'success': self.success,
          'message': self.message,
      }
```

---

## 6. Category Service (NOVO ARQUIVO)

### NOVO: src/classifier/category_service.py

```python
"""
Category service for managing product categories
Implements CRUD operations for categorias table
"""

import logging
from typing import List, Optional, Dict, Any

from classifier import DatabaseError

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for managing product categories"""

    def __init__(self, db_connection):
        """Initialize category service

        Args:
            db_connection: Database connection
        """
        self.db_connection = db_connection

    def get_all_categories(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all categories

        Args:
            active_only: If True, return only active categories

        Returns:
            List of category dictionaries
        """
        try:
            cursor = self.db_connection.cursor()

            query = "SELECT id, nome, descricao, ativo FROM categorias"
            if active_only:
                query += " WHERE ativo = TRUE"
            query += " ORDER BY nome"

            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()

            categories = [
                {
                    'id': row[0],
                    'nome': row[1],
                    'descricao': row[2],
                    'ativo': row[3]
                }
                for row in rows
            ]

            return categories
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            raise DatabaseError(f"Failed to fetch categories: {e}") from e

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID

        Args:
            category_id: Category ID

        Returns:
            Category dictionary or None if not found
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(
                "SELECT id, nome, descricao, ativo FROM categorias WHERE id = %s",
                (category_id,)
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                'id': row[0],
                'nome': row[1],
                'descricao': row[2],
                'ativo': row[3]
            }
        except Exception as e:
            logger.error(f"Error fetching category {category_id}: {e}")
            raise DatabaseError(f"Failed to fetch category: {e}") from e

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get category by name

        Args:
            name: Category name

        Returns:
            Category dictionary or None if not found
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(
                "SELECT id, nome, descricao, ativo FROM categorias WHERE LOWER(nome) = LOWER(%s)",
                (name,)
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                'id': row[0],
                'nome': row[1],
                'descricao': row[2],
                'ativo': row[3]
            }
        except Exception as e:
            logger.error(f"Error fetching category by name {name}: {e}")
            raise DatabaseError(f"Failed to fetch category: {e}") from e

    def validate_category_id(self, category_id: int) -> bool:
        """Validate that category exists and is active

        Args:
            category_id: Category ID to validate

        Returns:
            True if category exists and is active
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(
                "SELECT id FROM categorias WHERE id = %s AND ativo = TRUE",
                (category_id,)
            )
            result = cursor.fetchone()
            cursor.close()

            return result is not None
        except Exception as e:
            logger.error(f"Error validating category {category_id}: {e}")
            raise DatabaseError(f"Failed to validate category: {e}") from e
```

---

## 7. CLI Scripts - Pequenas Mudanças

### MODIFICAR: src/classifier/cli/classify_batch.py

Procure por toda referência a `categoria` e mude para `categoria_id`:

```bash
# Buscar todas as referências
grep -n "categoria" src/classifier/cli/classify_batch.py

# Mudanças esperadas:
# - Outputs mostram categoria_id ao invés de categoria (string)
# - Queries usam categoria_id IS NULL ao invés de categoria IS NULL
```

---

## 📊 Resumo de Mudanças por Arquivo

| Arquivo | Tipo | Mudanças | Linhas |
|---------|------|----------|--------|
| models.py | ADD + MODIFY | Category class nova + Rule.categoria_id | +50, ~30 |
| engine.py | MODIFY | SQL + evaluate() com JOIN | ~30 |
| batch.py | MODIFY | _row_to_product, _update_classification | ~40 |
| audit.py | MODIFY | record() com categoria_id | ~15 |
| category_service.py | NEW | Novo serviço | ~120 |
| cli/*.py | MODIFY | Pequenas mudanças em queries | ~10 |
| **TOTAL** | | | **~295 linhas** |

---

## ✅ Validação Pós-Mudança

Após implementar, verificar:

```python
# 1. Models importam corretamente
from classifier.models import Category, Rule, Product

# 2. Engine carrega regras com categoria_id (não resultado_classificacao)
engine = RuleEngine(db_conn)
rules = engine.get_rules()
assert hasattr(rules[0], 'categoria_id')
assert not hasattr(rules[0], 'resultado_classificacao')

# 3. Resultados têm categoria_id
result = engine.evaluate({'id': '123', 'description': 'laptop', 'ncm': '8471'})
assert hasattr(result, 'categoria_id')

# 4. Produtos armazenam categoria_id
batch = BatchClassifier(db_conn)
products = batch._get_unclassified_products(limit=1)
product = batch._row_to_product(products[0])
assert hasattr(product, 'categoria_id')

# 5. FK constraint funciona
# Tentar inserir regra com categoria_id inválido deve falhar
```

---

Isso é tudo que muda! O resto do código continua igual. ✅
