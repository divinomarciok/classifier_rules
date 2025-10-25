"""Unit tests for data models

Tests Rule, Product, ClassificationResult, and AuditEntry models
"""

import pytest
from datetime import datetime

from classifier.models import Rule, Product, ClassificationResult, AuditEntry


@pytest.mark.unit
class TestRuleModel:
    """Tests for Rule model"""

    def test_rule_initialization(self):
        """Test Rule can be initialized with all fields"""
        rule = Rule(
            id=1,
            prioridade=100,
            nome="Test Rule",
            ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_palavras_chave="laptop,computer"
        )

        assert rule.id == 1
        assert rule.prioridade == 100
        assert rule.nome == "Test Rule"
        assert rule.ativo is True
        assert rule.resultado_classificacao == "ELECTRONICS"
        assert rule.criterio_palavras_chave == "laptop,computer"

    def test_rule_from_db_row(self):
        """Test Rule.from_db_row() constructor from database tuple

        Database returns row as tuple in this order:
        (id, prioridade, nome, ativo, criterio_palavras_chave, criterio_ncm,
         criterio_tamanho_min, criterio_tamanho_max, criterio_quantidade_min,
         criterio_quantidade_max, criterio_categoria, resultado_classificacao,
         data_criacao, data_atualizacao)
        """
        now = datetime.now()
        row = (
            1,  # id
            100,  # prioridade
            "Test Rule",  # nome
            True,  # ativo
            "laptop,computer",  # criterio_palavras_chave
            "8471*",  # criterio_ncm
            0.5,  # criterio_tamanho_min
            5.0,  # criterio_tamanho_max
            1,  # criterio_quantidade_min
            100,  # criterio_quantidade_max
            "ELECTRONICS",  # criterio_categoria
            "ELECTRONICS",  # resultado_classificacao
            now,  # data_criacao
            now,  # data_atualizacao
        )

        rule = Rule.from_db_row(row)

        assert rule.id == 1
        assert rule.prioridade == 100
        assert rule.nome == "Test Rule"
        assert rule.ativo is True
        assert rule.criterio_palavras_chave == "laptop,computer"
        assert rule.resultado_classificacao == "ELECTRONICS"

    def test_rule_is_active(self):
        """Test Rule.is_active() method"""
        active_rule = Rule(
            id=1, prioridade=10, nome="Active", ativo=True,
            resultado_classificacao="TEST"
        )
        assert active_rule.is_active() is True

        inactive_rule = Rule(
            id=2, prioridade=10, nome="Inactive", ativo=False,
            resultado_classificacao="TEST"
        )
        assert inactive_rule.is_active() is False

    def test_rule_repr(self):
        """Test Rule string representation"""
        rule = Rule(
            id=42, prioridade=50, nome="Sample Rule", ativo=True,
            resultado_classificacao="TEST"
        )
        repr_str = repr(rule)

        assert "Rule" in repr_str
        assert "id=42" in repr_str
        assert "nome=Sample Rule" in repr_str
        assert "prioridade=50" in repr_str

    def test_rule_equality(self):
        """Test Rule equality based on ID"""
        rule1 = Rule(id=1, prioridade=10, nome="A", ativo=True, resultado_classificacao="X")
        rule2 = Rule(id=1, prioridade=20, nome="B", ativo=False, resultado_classificacao="Y")
        rule3 = Rule(id=2, prioridade=10, nome="A", ativo=True, resultado_classificacao="X")

        assert rule1 == rule2, "Rules with same ID should be equal"
        assert rule1 != rule3, "Rules with different IDs should not be equal"


@pytest.mark.unit
class TestProductModel:
    """Tests for Product model"""

    def test_product_initialization_minimal(self):
        """Test Product initialization with required fields only"""
        product = Product(description="laptop", ncm="84713090")

        assert product.description == "laptop"
        assert product.ncm == "84713090"
        assert product.id is None
        assert product.size is None
        assert product.quantity is None

    def test_product_initialization_complete(self):
        """Test Product initialization with all standard fields"""
        product = Product(
            id="P001",
            description="laptop computer",
            ncm="84713090",
            size=0.5,
            quantity=1,
            category="ELECTRONICS"
        )

        assert product.id == "P001"
        assert product.description == "laptop computer"
        assert product.ncm == "84713090"
        assert product.size == 0.5
        assert product.quantity == 1
        assert product.category == "ELECTRONICS"

    def test_product_initialization_with_extra_fields(self):
        """Test Product can accept arbitrary extra fields via kwargs"""
        product = Product(
            id="P001",
            description="product",
            ncm="99999999",
            supplier="Supplier X",
            purchase_price=100.50,
            stock_level=50
        )

        # Extra fields should be accessible via get_field() method
        assert product.get_field('supplier') == "Supplier X"
        assert product.get_field('purchase_price') == 100.50
        assert product.get_field('stock_level') == 50

    def test_product_get_field_standard_fields(self):
        """Test Product.get_field() for standard fields"""
        product = Product(
            id="P001",
            description="laptop",
            ncm="8471*",
            size=0.5,
            quantity=10
        )

        assert product.get_field('id') == "P001"
        assert product.get_field('description') == "laptop"
        assert product.get_field('ncm') == "8471*"
        assert product.get_field('size') == 0.5
        assert product.get_field('quantity') == 10

    def test_product_get_field_extra_fields(self):
        """Test Product.get_field() for extra fields"""
        product = Product(
            description="product",
            ncm="99999999",
            custom_field="custom_value",
            another_field=123
        )

        assert product.get_field('custom_field') == "custom_value"
        assert product.get_field('another_field') == 123

    def test_product_get_field_nonexistent(self):
        """Test Product.get_field() returns None for nonexistent fields"""
        product = Product(description="product", ncm="99999999")

        assert product.get_field('nonexistent_field') is None
        assert product.get_field('custom') is None

    def test_product_to_dict(self):
        """Test Product.to_dict() converts to dictionary"""
        product = Product(
            id="P001",
            description="laptop",
            ncm="8471*",
            size=0.5,
            quantity=10,
            extra_field="extra_value"
        )

        result = product.to_dict()

        assert isinstance(result, dict)
        assert result['id'] == "P001"
        assert result['description'] == "laptop"
        assert result['ncm'] == "8471*"
        assert result['size'] == 0.5
        assert result['quantity'] == 10
        assert result['extra_field'] == "extra_value"

    def test_product_repr(self):
        """Test Product string representation"""
        product = Product(id="P001", description="laptop computer", ncm="8471*")
        repr_str = repr(product)

        assert "Product" in repr_str
        assert "P001" in repr_str
        assert "laptop" in repr_str


@pytest.mark.unit
class TestClassificationResultModel:
    """Tests for ClassificationResult model"""

    def test_result_initialization_minimal(self):
        """Test ClassificationResult with just classification"""
        result = ClassificationResult(classification="ELECTRONICS")

        assert result.classification == "ELECTRONICS"
        assert result.rule_id is None
        assert result.success is True
        assert result.matched_criteria == []
        assert result.evaluation_time_ms == 0

    def test_result_initialization_complete(self):
        """Test ClassificationResult with all fields"""
        result = ClassificationResult(
            classification="ELECTRONICS",
            rule_id=1,
            rule_name="Laptop Rule",
            priority=100,
            matched_criteria=["criterio_palavras_chave"],
            evaluation_time_ms=42,
            success=True,
            message="Matched via keywords"
        )

        assert result.classification == "ELECTRONICS"
        assert result.rule_id == 1
        assert result.rule_name == "Laptop Rule"
        assert result.priority == 100
        assert result.matched_criteria == ["criterio_palavras_chave"]
        assert result.evaluation_time_ms == 42
        assert result.success is True
        assert result.message == "Matched via keywords"

    def test_result_to_dict(self):
        """Test ClassificationResult.to_dict() conversion"""
        result = ClassificationResult(
            classification="TEST",
            rule_id=5,
            rule_name="Test Rule",
            matched_criteria=["criterion1", "criterion2"]
        )

        result_dict = result.to_dict()

        assert result_dict['classification'] == "TEST"
        assert result_dict['rule_id'] == 5
        assert result_dict['rule_name'] == "Test Rule"
        assert result_dict['matched_criteria'] == ["criterion1", "criterion2"]

    def test_result_repr(self):
        """Test ClassificationResult string representation"""
        result = ClassificationResult(
            classification="ELECTRONICS",
            rule_id=1,
            evaluation_time_ms=50,
            success=True
        )

        repr_str = repr(result)
        assert "ClassificationResult" in repr_str
        assert "ELECTRONICS" in repr_str


@pytest.mark.unit
class TestAuditEntryModel:
    """Tests for AuditEntry model"""

    def test_audit_entry_initialization(self):
        """Test AuditEntry initialization"""
        entry = AuditEntry(
            id_regra=1,
            id_produto="P001",
            descricao_produto="laptop",
            ncm_produto="8471*",
            resultado_classificacao="ELECTRONICS",
            criterios_combinados='["criterio_palavras_chave"]',
            tempo_avaliacao_ms=50
        )

        assert entry.id_regra == 1
        assert entry.id_produto == "P001"
        assert entry.resultado_classificacao == "ELECTRONICS"
        assert entry.tempo_avaliacao_ms == 50

    def test_audit_entry_no_match(self):
        """Test AuditEntry for NO_MATCH case"""
        entry = AuditEntry(
            id_regra=None,  # No rule matched
            id_produto="P002",
            descricao_produto="unknown product",
            ncm_produto="99999999",
            resultado_classificacao="NO_MATCH"
        )

        assert entry.id_regra is None
        assert entry.resultado_classificacao == "NO_MATCH"

    def test_audit_entry_to_dict(self):
        """Test AuditEntry.to_dict() conversion"""
        entry = AuditEntry(
            id_regra=1,
            id_produto="P001",
            descricao_produto="laptop",
            ncm_produto="8471*",
            resultado_classificacao="ELECTRONICS"
        )

        entry_dict = entry.to_dict()

        assert isinstance(entry_dict, dict)
        assert entry_dict['id_regra'] == 1
        assert entry_dict['id_produto'] == "P001"
        assert entry_dict['resultado_classificacao'] == "ELECTRONICS"

    def test_audit_entry_repr(self):
        """Test AuditEntry string representation"""
        entry = AuditEntry(
            id_regra=1,
            id_produto="P001",
            descricao_produto="test",
            ncm_produto="12345",
            resultado_classificacao="TEST"
        )

        repr_str = repr(entry)
        assert "AuditEntry" in repr_str
        assert "P001" in repr_str
