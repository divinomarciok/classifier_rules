"""
Integration tests for User Story 2 - Priority Resolution

Tests the complete workflow of evaluating multiple matching rules
and selecting the correct winner based on priority and tiebreaker logic.
"""

import pytest
from datetime import datetime
from classifier.engine import RuleEngine
from classifier.models import Product, Rule


@pytest.mark.integration
class TestPriorityResolutionIntegration:
    """Integration tests for priority-based rule selection"""

    def test_priority_resolution_complete_workflow(self):
        """Test complete workflow: match multiple rules, resolve by priority"""
        engine = RuleEngine()

        # Simulate real-world scenario: multiple rules that could match
        rules = [
            Rule(id=1, prioridade=50, nome="Electronics Keyword", ativo=True,
                 resultado_classificacao="ELECTRONICS",
                 criterio_palavras_chave="laptop"),
            Rule(id=2, prioridade=30, nome="IT Equipment NCM", ativo=True,
                 resultado_classificacao="IT_EQUIPMENT",
                 criterio_ncm="8471*"),
            Rule(id=3, prioridade=10, nome="Generic NCM", ativo=True,
                 resultado_classificacao="GENERIC",
                 criterio_ncm="84*"),
        ]
        engine._load_rules = lambda: rules

        product = Product(
            id="PROD001",
            description="Dell laptop computer",
            ncm="84713090"
        )

        result = engine.evaluate(product)

        # Assert: Highest priority (keyword rule #1) wins
        assert result.success is True
        assert result.classification == "ELECTRONICS"
        assert result.rule_id == 1
        assert result.rule_name == "Electronics Keyword"
        assert result.priority == 50

    def test_priority_changes_classification_result(self):
        """Verify that priority determines the final classification

        If we had just matched rules without priority, we might get
        any of the 3 results. With priority, we always get rule 1's result.
        """
        engine = RuleEngine()

        # Three rules all matching the same product, different classifications
        rules = [
            Rule(id=1, prioridade=100, nome="Most Important", ativo=True,
                 resultado_classificacao="CLASS_A",
                 criterio_palavras_chave="product"),
            Rule(id=2, prioridade=50, nome="Medium", ativo=True,
                 resultado_classificacao="CLASS_B",
                 criterio_palavras_chave="product"),
            Rule(id=3, prioridade=10, nome="Least Important", ativo=True,
                 resultado_classificacao="CLASS_C",
                 criterio_palavras_chave="product"),
        ]
        engine._load_rules = lambda: rules

        product = Product(
            description="Some product",
            ncm="99999999"
        )

        result = engine.evaluate(product)

        # Assert: We get the result from the highest-priority rule
        assert result.classification == "CLASS_A"
        assert result.classification != "CLASS_B"
        assert result.classification != "CLASS_C"

    def test_tiebreaker_oldest_rule_creation_date(self):
        """Test tiebreaker: when priorities are equal, oldest rule wins"""
        engine = RuleEngine()

        # Three rules with identical priority
        rules = [
            Rule(id=1, prioridade=50, nome="Newest", ativo=True,
                 resultado_classificacao="NEWEST",
                 criterio_palavras_chave="test",
                 data_criacao=datetime(2025, 1, 15)),
            Rule(id=2, prioridade=50, nome="Oldest", ativo=True,
                 resultado_classificacao="OLDEST",
                 criterio_palavras_chave="test",
                 data_criacao=datetime(2020, 1, 1)),
            Rule(id=3, prioridade=50, nome="Middle", ativo=True,
                 resultado_classificacao="MIDDLE",
                 criterio_palavras_chave="test",
                 data_criacao=datetime(2022, 6, 15)),
        ]
        engine._load_rules = lambda: rules

        product = Product(description="test", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Oldest rule (id=2) wins the tiebreaker
        assert result.rule_id == 2
        assert result.classification == "OLDEST"

    def test_priority_with_cascading_criteria(self):
        """Test priority resolution with rules having different criteria sets"""
        engine = RuleEngine()

        rules = [
            # High priority, few criteria
            Rule(id=1, prioridade=100, nome="Simple High", ativo=True,
                 resultado_classificacao="SIMPLE_HIGH",
                 criterio_palavras_chave="laptop"),
            # Lower priority, many criteria
            Rule(id=2, prioridade=50, nome="Complex Low", ativo=True,
                 resultado_classificacao="COMPLEX_LOW",
                 criterio_palavras_chave="laptop",
                 criterio_ncm="8471*",
                 criterio_tamanho_max=2.0),
            # Lowest priority, brand new
            Rule(id=3, prioridade=10, nome="Very Low", ativo=True,
                 resultado_classificacao="VERY_LOW",
                 criterio_ncm="84*"),
        ]
        engine._load_rules = lambda: rules

        # Product matches all three rules
        product = Product(
            description="gaming laptop",
            ncm="84713090",
            size=1.8
        )

        result = engine.evaluate(product)

        # Assert: High priority simple rule wins despite complexity of others
        assert result.rule_id == 1
        assert result.classification == "SIMPLE_HIGH"

    def test_priority_skips_non_matching_rules(self):
        """Verify: Non-matching rules don't affect priority resolution

        Even if a non-matching rule has higher priority, it shouldn't affect
        which matching rule is selected.
        """
        engine = RuleEngine()

        rules = [
            # Highest priority but DOESN'T match
            Rule(id=1, prioridade=999, nome="High But No Match", ativo=True,
                 resultado_classificacao="DOESNT_APPLY",
                 criterio_palavras_chave="iphone"),
            # Lower priority but DOES match
            Rule(id=2, prioridade=50, nome="Medium Match", ativo=True,
                 resultado_classificacao="APPLIES",
                 criterio_palavras_chave="laptop"),
        ]
        engine._load_rules = lambda: rules

        product = Product(description="laptop", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Matching rule (id=2) is selected despite lower priority
        assert result.rule_id == 2
        assert result.classification == "APPLIES"

    def test_priority_with_size_and_quantity_criteria(self):
        """Integration test with size and quantity criteria in priority resolution"""
        engine = RuleEngine()

        rules = [
            Rule(id=1, prioridade=100, nome="Premium Small", ativo=True,
                 resultado_classificacao="PREMIUM",
                 criterio_tamanho_max=0.5),
            Rule(id=2, prioridade=50, nome="Standard Medium", ativo=True,
                 resultado_classificacao="STANDARD",
                 criterio_tamanho_max=2.0),
            Rule(id=3, prioridade=10, nome="Bulk Large", ativo=True,
                 resultado_classificacao="BULK",
                 criterio_quantidade_min=100),
        ]
        engine._load_rules = lambda: rules

        # Medium-sized item, high quantity
        product = Product(
            description="standard product",
            ncm="99999999",
            size=1.5,
            quantity=500
        )

        result = engine.evaluate(product)

        # Rules 2 and 3 match, rule 2 has higher priority
        assert result.rule_id == 2
        assert result.classification == "STANDARD"

    def test_priority_metadata_in_result(self):
        """Verify that priority information is included in result"""
        engine = RuleEngine()

        rule = Rule(
            id=42, prioridade=87, nome="Test Rule", ativo=True,
            resultado_classificacao="TEST",
            criterio_palavras_chave="test"
        )
        engine._load_rules = lambda: [rule]

        product = Product(description="test", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Priority is included in result
        assert result.priority == 87
        assert result.priority is not None

    def test_many_priority_levels(self):
        """Stress test: select correct winner from rules with many priority levels"""
        engine = RuleEngine()

        # Create rules with priorities: 1, 2, 3, ..., 50
        rules = [
            Rule(id=i, prioridade=i, nome=f"Rule {i}", ativo=True,
                 resultado_classificacao=f"CLASS_{i}",
                 criterio_palavras_chave="test",
                 data_criacao=datetime(2020, 1, i % 30 + 1))
            for i in range(1, 51)
        ]
        engine._load_rules = lambda: rules

        product = Product(description="test", ncm="99999999")
        result = engine.evaluate(product)

        # Assert: Rule with highest priority (50) is selected
        assert result.rule_id == 50
        assert result.priority == 50
        assert result.classification == "CLASS_50"

    def test_priority_consistency_across_evaluations(self):
        """Verify: Same product evaluated multiple times gives same result due to priority"""
        engine = RuleEngine()

        rules = [
            Rule(id=1, prioridade=100, nome="High", ativo=True,
                 resultado_classificacao="HIGH",
                 criterio_palavras_chave="test",
                 data_criacao=datetime(2025, 1, 1)),
            Rule(id=2, prioridade=100, nome="Old", ativo=True,
                 resultado_classificacao="OLD",
                 criterio_palavras_chave="test",
                 data_criacao=datetime(2020, 1, 1)),
        ]
        engine._load_rules = lambda: rules

        product = Product(description="test", ncm="99999999")

        # Evaluate 5 times
        results = [engine.evaluate(product) for _ in range(5)]

        # Assert: All results are identical
        for r in results:
            assert r.rule_id == 2  # Oldest rule wins the tiebreaker
            assert r.classification == "OLD"
            assert r.priority == 100
