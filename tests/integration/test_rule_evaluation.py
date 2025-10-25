"""
Integration tests for rule evaluation workflow

Tests the complete flow from product data through rule matching
to classification result.
"""

import pytest
from datetime import datetime
from classifier.engine import RuleEngine
from classifier.models import Product, Rule, ClassificationResult


@pytest.mark.integration
class TestRuleEvaluationWorkflow:
    """Tests for complete rule evaluation workflow"""

    def test_evaluate_product_with_keyword_match(self):
        """Test: Complete workflow - product matches keyword rule"""
        engine = RuleEngine()

        # Create a rule that matches laptops
        rule = Rule(
            id=1, prioridade=100, nome="Electronics", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_palavras_chave="laptop"
        )
        engine._load_rules = lambda: [rule]

        # Create a product description that matches
        product = Product(
            id="P001",
            description="Dell laptop computer",
            ncm="84713090"
        )

        # Evaluate
        result = engine.evaluate(product)

        # Verify result
        assert result.success is True
        assert result.classification == "ELECTRONICS"
        assert result.rule_id == 1
        assert result.rule_name == "Electronics"

    def test_evaluate_product_with_ncm_match(self):
        """Test: Complete workflow - product matches NCM pattern"""
        engine = RuleEngine()

        # Create NCM-based rule
        rule = Rule(
            id=2, prioridade=50, nome="Cables", ativo=True,
            resultado_classificacao="CABLES",
            criterio_ncm="8544*"
        )
        engine._load_rules = lambda: [rule]

        # Product matches NCM pattern
        product = Product(
            id="P002",
            description="Fiber optic cable",
            ncm="85444290"
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "CABLES"
        assert result.rule_id == 2

    def test_evaluate_product_with_size_criteria(self):
        """Test: Complete workflow - product matches size range"""
        engine = RuleEngine()

        rule = Rule(
            id=3, prioridade=30, nome="Small Items", ativo=True,
            resultado_classificacao="SMALL",
            criterio_tamanho_max=1.0
        )
        engine._load_rules = lambda: [rule]

        # Small product
        product = Product(
            description="Small device",
            ncm="99999999",
            size=0.5
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "SMALL"
        assert result.rule_id == 3

    def test_evaluate_product_with_quantity_criteria(self):
        """Test: Complete workflow - product matches quantity range"""
        engine = RuleEngine()

        rule = Rule(
            id=4, prioridade=20, nome="Bulk Items", ativo=True,
            resultado_classificacao="BULK",
            criterio_quantidade_min=100,
            criterio_quantidade_max=1000
        )
        engine._load_rules = lambda: [rule]

        # Product with quantity in range
        product = Product(
            description="Widget",
            ncm="99999999",
            quantity=500
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "BULK"
        assert result.rule_id == 4

    def test_evaluate_product_with_multiple_criteria(self):
        """Test: Complete workflow - product matches rule with AND criteria"""
        engine = RuleEngine()

        # Complex rule: keyword AND size AND quantity
        rule = Rule(
            id=5, prioridade=150, nome="Complex", ativo=True,
            resultado_classificacao="COMPLEX_MATCH",
            criterio_palavras_chave="laptop",
            criterio_tamanho_max=2.0,
            criterio_quantidade_min=1,
            criterio_quantidade_max=100
        )
        engine._load_rules = lambda: [rule]

        # Product matches all criteria
        product = Product(
            description="Gaming laptop",
            ncm="84713090",
            size=1.5,
            quantity=5
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "COMPLEX_MATCH"
        assert result.rule_id == 5

    def test_evaluate_product_fails_one_criteria(self):
        """Test: Complete workflow - product fails one criterion (AND logic)"""
        engine = RuleEngine()

        rule = Rule(
            id=6, prioridade=100, nome="Test", ativo=True,
            resultado_classificacao="TEST",
            criterio_palavras_chave="laptop",
            criterio_tamanho_max=0.5  # Product is too large
        )
        engine._load_rules = lambda: [rule]

        # Product matches keyword but NOT size
        product = Product(
            description="Large gaming laptop",
            ncm="84713090",
            size=2.0  # Exceeds max
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "NO_MATCH"
        assert result.rule_id is None

    def test_evaluate_priority_resolution(self):
        """Test: Complete workflow - priority resolution selects correct rule"""
        engine = RuleEngine()

        # Two rules that both match, but different priorities
        rules = [
            Rule(id=1, prioridade=10, nome="Low", ativo=True,
                 resultado_classificacao="LOW",
                 criterio_palavras_chave="test"),
            Rule(id=2, prioridade=100, nome="High", ativo=True,
                 resultado_classificacao="HIGH",
                 criterio_palavras_chave="test"),
        ]
        engine._load_rules = lambda: rules

        product = Product(
            description="test product",
            ncm="99999999"
        )

        result = engine.evaluate(product)

        # Should select higher priority rule
        assert result.success is True
        assert result.classification == "HIGH"
        assert result.rule_id == 2
        assert result.priority == 100

    def test_evaluate_tiebreaker_oldest_wins(self):
        """Test: Complete workflow - tiebreaker selects oldest rule"""
        engine = RuleEngine()

        old_date = datetime(2020, 1, 1)
        new_date = datetime(2025, 1, 1)

        # Two rules with same priority, different creation dates
        rules = [
            Rule(id=1, prioridade=50, nome="Newer", ativo=True,
                 resultado_classificacao="NEWER",
                 criterio_palavras_chave="test",
                 data_criacao=new_date),
            Rule(id=2, prioridade=50, nome="Older", ativo=True,
                 resultado_classificacao="OLDER",
                 criterio_palavras_chave="test",
                 data_criacao=old_date),
        ]
        engine._load_rules = lambda: rules

        product = Product(
            description="test",
            ncm="99999999"
        )

        result = engine.evaluate(product)

        # Older rule should win
        assert result.success is True
        assert result.classification == "OLDER"
        assert result.rule_id == 2

    def test_evaluate_no_matching_rules(self):
        """Test: Complete workflow - no rules match product"""
        engine = RuleEngine()

        rule = Rule(
            id=1, prioridade=10, nome="Laptop", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_palavras_chave="laptop"
        )
        engine._load_rules = lambda: [rule]

        # Product doesn't match
        product = Product(
            description="cable and adapters",
            ncm="99999999"
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "NO_MATCH"
        assert result.rule_id is None
        assert result.rule_name is None

    def test_evaluate_empty_rule_database(self):
        """Test: Complete workflow - no rules in database"""
        engine = RuleEngine()
        engine._load_rules = lambda: []

        product = Product(
            description="anything",
            ncm="99999999"
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "NO_MATCH"

    def test_evaluate_measures_execution_time(self):
        """Test: Complete workflow - execution time is measured"""
        engine = RuleEngine()

        rules = [
            Rule(id=i, prioridade=10+i, nome=f"Rule{i}", ativo=True,
                 resultado_classificacao=f"CLASS{i}",
                 criterio_palavras_chave="test")
            for i in range(5)
        ]
        engine._load_rules = lambda: rules

        product = Product(
            description="test",
            ncm="99999999"
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.evaluation_time_ms is not None
        assert result.evaluation_time_ms >= 0
        assert result.evaluation_time_ms < 1000  # Should be fast

    def test_evaluate_includes_all_metadata(self):
        """Test: Complete workflow - result includes all expected metadata"""
        engine = RuleEngine()

        rule = Rule(
            id=42, prioridade=99, nome="Complex Rule", ativo=True,
            resultado_classificacao="COMPLEX",
            criterio_palavras_chave="laptop",
            criterio_ncm="8471*",
            criterio_tamanho_max=2.0
        )
        engine._load_rules = lambda: [rule]

        product = Product(
            description="gaming laptop",
            ncm="84713090",
            size=1.5
        )

        result = engine.evaluate(product)

        # Verify all expected fields are present
        assert isinstance(result, ClassificationResult)
        assert result.success is True
        assert result.classification == "COMPLEX"
        assert result.rule_id == 42
        assert result.rule_name == "Complex Rule"
        assert result.priority == 99
        assert isinstance(result.matched_criteria, list)
        assert result.evaluation_time_ms is not None
        assert isinstance(result.message, str)

    def test_evaluate_with_category_criteria(self):
        """Test: Complete workflow - product matches category criteria"""
        engine = RuleEngine()

        rule = Rule(
            id=10, prioridade=50, nome="Electronics Only", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_categoria="ELECTRONICS"
        )
        engine._load_rules = lambda: [rule]

        # Product with matching category
        product = Product(
            description="laptop",
            ncm="84713090",
            category="ELECTRONICS"
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "ELECTRONICS"
        assert result.rule_id == 10

    def test_evaluate_category_mismatch(self):
        """Test: Complete workflow - product category doesn't match"""
        engine = RuleEngine()

        rule = Rule(
            id=11, prioridade=50, nome="Electronics Only", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_categoria="ELECTRONICS"
        )
        engine._load_rules = lambda: [rule]

        # Product with different category
        product = Product(
            description="laptop",
            ncm="84713090",
            category="OTHER"
        )

        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "NO_MATCH"


@pytest.mark.integration
class TestMultipleRuleEvaluation:
    """Tests for scenarios with multiple rules"""

    def test_multiple_rules_all_match_highest_wins(self):
        """Test: When multiple rules match, highest priority wins"""
        engine = RuleEngine()

        # Three rules that all match the same product
        rules = [
            Rule(id=1, prioridade=10, nome="Low", ativo=True,
                 resultado_classificacao="LOW",
                 criterio_palavras_chave="device"),
            Rule(id=2, prioridade=50, nome="Medium", ativo=True,
                 resultado_classificacao="MEDIUM",
                 criterio_palavras_chave="device"),
            Rule(id=3, prioridade=100, nome="High", ativo=True,
                 resultado_classificacao="HIGH",
                 criterio_palavras_chave="device"),
        ]
        engine._load_rules = lambda: rules

        product = Product(
            description="smart device",
            ncm="99999999"
        )

        result = engine.evaluate(product)

        # Highest priority (id=3) should win
        assert result.classification == "HIGH"
        assert result.rule_id == 3

    def test_multiple_rules_cascading_criteria(self):
        """Test: Multiple rules with different criteria"""
        engine = RuleEngine()

        # Rules with different criteria
        rules = [
            Rule(id=1, prioridade=10, nome="Keyword", ativo=True,
                 resultado_classificacao="KEYWORD_MATCH",
                 criterio_palavras_chave="laptop"),
            Rule(id=2, prioridade=10, nome="NCM", ativo=True,
                 resultado_classificacao="NCM_MATCH",
                 criterio_ncm="8471*"),
            Rule(id=3, prioridade=10, nome="Size", ativo=True,
                 resultado_classificacao="SIZE_MATCH",
                 criterio_tamanho_max=2.0),
        ]
        engine._load_rules = lambda: rules

        # Product that matches all three
        product = Product(
            description="laptop computer",
            ncm="84713090",
            size=1.5
        )

        result = engine.evaluate(product)

        # With tied priorities, oldest rule (id=1) wins
        assert result.classification == "KEYWORD_MATCH"
        assert result.rule_id == 1

    def test_evaluate_with_inactive_rules_ignored(self):
        """Test: Inactive rules are not considered"""
        engine = RuleEngine()

        rules = [
            Rule(id=1, prioridade=100, nome="Active", ativo=True,
                 resultado_classificacao="ACTIVE",
                 criterio_palavras_chave="test"),
            Rule(id=2, prioridade=200, nome="Inactive", ativo=False,
                 resultado_classificacao="INACTIVE",
                 criterio_palavras_chave="test"),
        ]
        # Only return active rules (as RuleEngine._load_rules does)
        engine._load_rules = lambda: [r for r in rules if r.ativo]

        product = Product(
            description="test",
            ncm="99999999"
        )

        result = engine.evaluate(product)

        # Active rule should be selected despite inactive one having higher priority
        assert result.classification == "ACTIVE"
        assert result.rule_id == 1
