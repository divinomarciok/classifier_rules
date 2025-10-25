"""
Data models for classifier

Defines the core entities: Rule, Product, ClassificationResult, and AuditEntry

Implements FR-001 (Rule representation) and Constitutional Principle II (Code Simplicity)
"""

from typing import Optional, Dict, Any, List
from datetime import datetime


class Rule:
    """Represents a classification rule from regras_de_classificacao table

    Attributes:
        id: Rule unique identifier
        prioridade: Priority (higher = more important)
        nome: Rule name
        ativo: Whether rule is active
        criterio_*: Various matching criteria (keywords, NCM, sizes, quantities)
        resultado_classificacao: Classification result if rule matches
        data_criacao: When rule was created
        data_atualizacao: When rule was last updated
    """

    def __init__(
        self,
        id: int,
        prioridade: int,
        nome: str,
        ativo: bool,
        resultado_classificacao: str,
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
        self.resultado_classificacao = resultado_classificacao
        self.data_criacao = data_criacao or datetime.now()
        self.data_atualizacao = data_atualizacao or datetime.now()

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Rule':
        """Construct Rule from database tuple

        Args:
            row: Database row from regras_de_classificacao table

        Returns:
            Rule: Constructed Rule object
        """
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
            resultado_classificacao=row[11],
            data_criacao=row[12],
            data_atualizacao=row[13],
        )

    def is_active(self) -> bool:
        """Check if rule is active

        Returns:
            bool: True if rule is active (ativo=True), False otherwise
        """
        return self.ativo

    def __repr__(self) -> str:
        return f"Rule(id={self.id}, nome={self.nome}, prioridade={self.prioridade}, ativo={self.ativo})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Rule):
            return False
        return self.id == other.id


class Product:
    """Represents a product to be classified

    Flexible model that accepts any attributes via kwargs.
    Provides safe access to optional fields.

    Attributes:
        id: Product unique identifier (optional)
        description: Product description
        ncm: NCM code
        size: Product size (optional)
        quantity: Product quantity (optional)
        category: Category (optional, filled by classifier)
        other_fields: Any other product attributes passed via kwargs
    """

    def __init__(
        self,
        description: str,
        ncm: str,
        id: Optional[str] = None,
        size: Optional[float] = None,
        quantity: Optional[int] = None,
        category: Optional[str] = None,
        **kwargs
    ):
        self.id = id
        self.description = description
        self.ncm = ncm
        self.size = size
        self.quantity = quantity
        self.category = category
        self._extra_fields = kwargs

    def get_field(self, field_name: str) -> Any:
        """Safely access product field

        Supports built-in fields (id, description, ncm, size, quantity, category)
        and any additional fields passed via kwargs.

        Args:
            field_name: Name of field to access

        Returns:
            Field value or None if field doesn't exist

        Usage:
            >>> product = Product(description="laptop", ncm="8471*")
            >>> product.get_field('description')
            "laptop"
            >>> product.get_field('custom_field')  # Returns None
        """
        if hasattr(self, field_name):
            return getattr(self, field_name)
        return self._extra_fields.get(field_name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary

        Returns:
            dict: Product data as dictionary
        """
        data = {
            'id': self.id,
            'description': self.description,
            'ncm': self.ncm,
            'size': self.size,
            'quantity': self.quantity,
            'category': self.category,
        }
        data.update(self._extra_fields)
        return data

    def __repr__(self) -> str:
        return f"Product(id={self.id}, description={self.description[:30]}, ncm={self.ncm})"


class ClassificationResult:
    """Result of a classification evaluation

    Attributes:
        classification: Classification code/result
        rule_id: ID of rule that matched (or None if no match)
        rule_name: Name of rule that matched
        priority: Priority of matched rule
        matched_criteria: Which criteria matched (list of criterion names)
        evaluation_time_ms: How long evaluation took
        success: Whether evaluation completed successfully
        message: Optional message (error, no-match reason, etc)
    """

    def __init__(
        self,
        classification: str,
        rule_id: Optional[int] = None,
        rule_name: Optional[str] = None,
        priority: Optional[int] = None,
        matched_criteria: Optional[List[str]] = None,
        evaluation_time_ms: int = 0,
        success: bool = True,
        message: str = '',
    ):
        self.classification = classification
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.priority = priority
        self.matched_criteria = matched_criteria or []
        self.evaluation_time_ms = evaluation_time_ms
        self.success = success
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for responses/logging

        Returns:
            dict: Result as dictionary
        """
        return {
            'classification': self.classification,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'priority': self.priority,
            'matched_criteria': self.matched_criteria,
            'evaluation_time_ms': self.evaluation_time_ms,
            'success': self.success,
            'message': self.message,
        }

    def __repr__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"{status} ClassificationResult(classification={self.classification}, rule_id={self.rule_id}, time={self.evaluation_time_ms}ms)"


class AuditEntry:
    """Audit log entry for a classification decision

    Attributes:
        id: Entry unique identifier
        id_regra: ID of rule that was applied
        id_produto: Product ID that was classified
        descricao_produto: Product description
        ncm_produto: Product NCM code
        resultado_classificacao: Classification result
        criterios_combinados: Which criteria matched (JSON)
        data_classificacao: When classification occurred
        tempo_avaliacao_ms: Evaluation time
        usuario_sistema: User/system that performed classification
    """

    def __init__(
        self,
        id_regra: Optional[int],
        id_produto: Optional[str],
        descricao_produto: Optional[str],
        ncm_produto: Optional[str],
        resultado_classificacao: str,
        criterios_combinados: Optional[str] = None,
        data_classificacao: Optional[datetime] = None,
        tempo_avaliacao_ms: int = 0,
        usuario_sistema: str = 'system',
        id: Optional[int] = None,
    ):
        self.id = id
        self.id_regra = id_regra
        self.id_produto = id_produto
        self.descricao_produto = descricao_produto
        self.ncm_produto = ncm_produto
        self.resultado_classificacao = resultado_classificacao
        self.criterios_combinados = criterios_combinados
        self.data_classificacao = data_classificacao or datetime.now()
        self.tempo_avaliacao_ms = tempo_avaliacao_ms
        self.usuario_sistema = usuario_sistema

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit entry to dictionary

        Returns:
            dict: Audit entry as dictionary
        """
        return {
            'id': self.id,
            'id_regra': self.id_regra,
            'id_produto': self.id_produto,
            'descricao_produto': self.descricao_produto,
            'ncm_produto': self.ncm_produto,
            'resultado_classificacao': self.resultado_classificacao,
            'criterios_combinados': self.criterios_combinados,
            'data_classificacao': self.data_classificacao,
            'tempo_avaliacao_ms': self.tempo_avaliacao_ms,
            'usuario_sistema': self.usuario_sistema,
        }

    def __repr__(self) -> str:
        return f"AuditEntry(id_regra={self.id_regra}, id_produto={self.id_produto}, resultado={self.resultado_classificacao})"
