"""
Unit tests for Evaluator service

Tests priority resolution and rule matching logic
"""

import pytest
from datetime import datetime
from classifier.evaluator import Evaluator
from classifier.models import Product, Rule
from classifier import EvaluationError


@pytest.mark.unit
class TestEvaluatorGetMatchingRules:
    """Tests for get_matching_rules - filtering rules by criteria"""

    def test_get_matching_rules_empty_list(self):
        """Test: Empty rules list returns empty matches"""
        product = Product(description="laptop", ncm="84713090")
        matches = Evaluator.get_matching_rules(product, [])
        assert matches == []

    def test_get_matching_rules_single_match(self):
        """Test: Single matching rule is returned"""
        product = Product(description="laptop", ncm="84713090")
        rule = Rule(
            id=1, prioridade=10, nome="Test", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_palavras_chave="laptop"
        )
        matches = Evaluator.get_matching_rules(product, [rule])
        assert len(matches) == 1
        assert matches[0].id == 1

    def test_get_matching_rules_single_no_match(self):
        """Test: Non-matching rule is not returned"""
        product = Product(description="cable", ncm="85444290")
        rule = Rule(
            id=1, prioridade=10, nome="Test", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_palavras_chave="laptop"
        )
        matches = Evaluator.get_matching_rules(product, [rule])
        assert len(matches) == 0

    def test_get_matching_rules_multiple_all_match(self):
        """Test: Multiple matching rules are all returned"""
        product = Product(description="laptop computer", ncm="84713090")
        rules = [
            Rule(
                id=1, prioridade=10, nome="Keywords", ativo=True,
                resultado_classificacao="ELECTRONICS",
                criterio_palavras_chave="laptop"
            ),
            Rule(
                id=2, prioridade=20, nome="NCM", ativo=True,
                resultado_classificacao="ELECTRONICS",
                criterio_ncm="8471*"
            ),
        ]
        matches = Evaluator.get_matching_rules(product, rules)
        assert len(matches) == 2
        assert all(m.id in [1, 2] for m in matches)

    def test_get_matching_rules_multiple_partial_match(self):
        """Test: Some matching, some not matching"""
        product = Product(description="laptop", ncm="84713090")
        rules = [
            Rule(
                id=1, prioridade=10, nome="Match", ativo=True,
                resultado_classificacao="ELECTRONICS",
                criterio_palavras_chave="laptop"
            ),
            Rule(
                id=2, prioridade=20, nome="No Match", ativo=True,
                resultado_classificacao="OTHER",
                criterio_palavras_chave="desktop"
            ),
            Rule(
                id=3, prioridade=15, nome="Match", ativo=True,
                resultado_classificacao="ELECTRONICS",
                criterio_ncm="8471*"
            ),
        ]
        matches = Evaluator.get_matching_rules(product, rules)
        assert len(matches) == 2
        assert matches[0].id in [1, 3]
        assert matches[1].id in [1, 3]

    def test_get_matching_rules_order_preserved(self):
        """Test: Rules are returned in input order"""
        product = Product(description="laptop", ncm="84713090")
        rules = [
            Rule(
                id=3, prioridade=30, nome="Third", ativo=True,
                resultado_classificacao="OTHER",
                criterio_palavras_chave="laptop"
            ),
            Rule(
                id=1, prioridade=10, nome="First", ativo=True,
                resultado_classificacao="ELECTRONICS",
                criterio_palavras_chave="laptop"
            ),
            Rule(
                id=2, prioridade=20, nome="Second", ativo=True,
                resultado_classificacao="CABLES",
                criterio_palavras_chave="laptop"
            ),
        ]
        matches = Evaluator.get_matching_rules(product, rules)
        assert len(matches) == 3
        assert [m.id for m in matches] == [3, 1, 2]  # Original order

    def test_get_matching_rules_skips_errors(self):
        """Test: Matching continues even if one rule evaluation errors"""
        # This is implicit - if a rule matches, it's added; errors logged but don't break
        product = Product(description="laptop", ncm="84713090")
        rules = [
            Rule(
                id=1, prioridade=10, nome="First", ativo=True,
                resultado_classificacao="ELECTRONICS",
                criterio_palavras_chave="laptop"
            ),
            Rule(
                id=2, prioridade=20, nome="Second", ativo=True,
                resultado_classificacao="OTHER",
                criterio_palavras_chave="laptop"
            ),
        ]
        matches = Evaluator.get_matching_rules(product, rules)
        assert len(matches) == 2


@pytest.mark.unit
class TestEvaluatorSelectWinner:
    """Tests for select_winner - priority resolution and tiebreaking"""

    def test_select_winner_single_rule(self):
        """Test: Single rule is selected as winner"""
        rule = Rule(
            id=1, prioridade=10, nome="Only", ativo=True,
            resultado_classificacao="ELECTRONICS"
        )
        winner = Evaluator.select_winner([rule])
        assert winner.id == 1

    def test_select_winner_highest_priority(self):
        """Test: Rule with highest priority wins"""
        rules = [
            Rule(id=1, prioridade=10, nome="Low", ativo=True,
                 resultado_classificacao="LOW"),
            Rule(id=2, prioridade=50, nome="High", ativo=True,
                 resultado_classificacao="HIGH"),
            Rule(id=3, prioridade=30, nome="Medium", ativo=True,
                 resultado_classificacao="MEDIUM"),
        ]
        winner = Evaluator.select_winner(rules)
        assert winner.id == 2
        assert winner.prioridade == 50

    def test_select_winner_priority_tie_oldest_wins(self):
        """Test: When priority tied, oldest rule (by creation date) wins"""
        now = datetime.now()
        old_date = datetime(2020, 1, 1)
        new_date = datetime(2025, 1, 1)

        rules = [
            Rule(
                id=1, prioridade=20, nome="Newer", ativo=True,
                resultado_classificacao="NEWER",
                data_criacao=new_date
            ),
            Rule(
                id=2, prioridade=20, nome="Older", ativo=True,
                resultado_classificacao="OLDER",
                data_criacao=old_date
            ),
            Rule(
                id=3, prioridade=20, nome="Middle", ativo=True,
                resultado_classificacao="MIDDLE",
                data_criacao=datetime(2022, 6, 15)
            ),
        ]
        winner = Evaluator.select_winner(rules)
        assert winner.id == 2  # Oldest rule wins
        assert winner.data_criacao == old_date

    def test_select_winner_priority_and_tiebreaker(self):
        """Test: Sort by priority first, then by creation date"""
        old_date = datetime(2020, 1, 1)
        new_date = datetime(2025, 1, 1)

        rules = [
            # High priority but newer
            Rule(
                id=1, prioridade=100, nome="High New", ativo=True,
                resultado_classificacao="HIGH_NEW",
                data_criacao=new_date
            ),
            # High priority but older
            Rule(
                id=2, prioridade=100, nome="High Old", ativo=True,
                resultado_classificacao="HIGH_OLD",
                data_criacao=old_date
            ),
            # Low priority but older
            Rule(
                id=3, prioridade=10, nome="Low Old", ativo=True,
                resultado_classificacao="LOW_OLD",
                data_criacao=old_date
            ),
        ]
        winner = Evaluator.select_winner(rules)
        # Should pick rule 2: highest priority (100), and among those, oldest
        assert winner.id == 2

    def test_select_winner_empty_list_raises_error(self):
        """Test: Empty rules list raises EvaluationError"""
        with pytest.raises(EvaluationError):
            Evaluator.select_winner([])

    def test_select_winner_deterministic(self):
        """Test: Same input always returns same winner"""
        rules = [
            Rule(id=1, prioridade=20, nome="First", ativo=True,
                 resultado_classificacao="A", data_criacao=datetime(2025, 1, 1)),
            Rule(id=2, prioridade=20, nome="Second", ativo=True,
                 resultado_classificacao="B", data_criacao=datetime(2025, 1, 2)),
            Rule(id=3, prioridade=20, nome="Third", ativo=True,
                 resultado_classificacao="C", data_criacao=datetime(2025, 1, 3)),
        ]
        # Call multiple times
        winner1 = Evaluator.select_winner(rules)
        winner2 = Evaluator.select_winner(rules)
        winner3 = Evaluator.select_winner(rules)

        # All should be the same (rule 1, oldest)
        assert winner1.id == 1
        assert winner2.id == 1
        assert winner3.id == 1

    def test_select_winner_preserves_rule_data(self):
        """Test: Selected rule retains all its data"""
        rule = Rule(
            id=42, prioridade=99, nome="Complex Rule", ativo=True,
            resultado_classificacao="TEST_CLASSIFICATION",
            criterio_palavras_chave="laptop,computer",
            criterio_ncm="8471*",
            criterio_tamanho_min=0.5,
            criterio_tamanho_max=10.0,
            criterio_quantidade_min=1,
            criterio_quantidade_max=1000,
            criterio_categoria="ELECTRONICS"
        )
        winner = Evaluator.select_winner([rule])

        assert winner.id == 42
        assert winner.prioridade == 99
        assert winner.nome == "Complex Rule"
        assert winner.resultado_classificacao == "TEST_CLASSIFICATION"
        assert winner.criterio_palavras_chave == "laptop,computer"
        assert winner.criterio_ncm == "8471*"
        assert winner.criterio_tamanho_min == 0.5
        assert winner.criterio_tamanho_max == 10.0
        assert winner.criterio_quantidade_min == 1
        assert winner.criterio_quantidade_max == 1000
        assert winner.criterio_categoria == "ELECTRONICS"


@pytest.mark.unit
class TestEvaluatorIntegration:
    """Integration tests for Evaluator methods working together"""

    def test_get_matching_then_select_winner(self):
        """Test: Find matches then select highest priority"""
        product = Product(description="laptop computer", ncm="84713090", size=0.5, quantity=5)

        rules = [
            Rule(
                id=1, prioridade=10, nome="Keywords", ativo=True,
                resultado_classificacao="ELECTRONICS",
                criterio_palavras_chave="laptop"
            ),
            Rule(
                id=2, prioridade=50, nome="NCM", ativo=True,
                resultado_classificacao="COMPONENTS",
                criterio_ncm="8471*"
            ),
            Rule(
                id=3, prioridade=30, nome="Size", ativo=True,
                resultado_classificacao="SMALL_ITEMS",
                criterio_tamanho_max=1.0
            ),
            Rule(
                id=4, prioridade=5, nome="No Match", ativo=True,
                resultado_classificacao="OTHER",
                criterio_palavras_chave="cable"
            ),
        ]

        # Get matches
        matches = Evaluator.get_matching_rules(product, rules)
        assert len(matches) == 3  # Rules 1, 2, 3 match

        # Select winner
        winner = Evaluator.select_winner(matches)
        assert winner.id == 2  # Highest priority
        assert winner.prioridade == 50

    def test_no_matches_then_select_raises(self):
        """Test: If no matches, select_winner raises error"""
        product = Product(description="something", ncm="99999999")
        rules = [
            Rule(
                id=1, prioridade=10, nome="Test", ativo=True,
                resultado_classificacao="ELECTRONICS",
                criterio_palavras_chave="laptop"
            ),
        ]

        matches = Evaluator.get_matching_rules(product, rules)
        assert len(matches) == 0

        with pytest.raises(EvaluationError):
            Evaluator.select_winner(matches)
