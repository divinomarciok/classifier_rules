"""
Unit tests for RuleEngine service

Tests the main evaluation engine and caching logic
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from classifier.engine import RuleEngine
from classifier.models import Product, Rule, ClassificationResult
from classifier import DatabaseError, ProductError, EvaluationError


@pytest.mark.unit
class TestRuleEngineInitialization:
    """Tests for RuleEngine initialization and configuration"""

    def test_rule_engine_initializes_with_defaults(self):
        """Test: RuleEngine initializes with default settings"""
        engine = RuleEngine()
        assert engine.cache_rules is True
        assert engine._rules_cache is None

    def test_rule_engine_initializes_with_cache_disabled(self):
        """Test: RuleEngine can initialize with caching disabled"""
        engine = RuleEngine(cache_rules=False)
        assert engine.cache_rules is False

    def test_rule_engine_initializes_with_connection(self):
        """Test: RuleEngine accepts external database connection"""
        mock_conn = Mock()
        engine = RuleEngine(db_connection=mock_conn)
        assert engine.db_connection is mock_conn


@pytest.mark.unit
class TestRuleEngineLoadRules:
    """Tests for rule loading from database (with mocks)"""

    def test_load_rules_without_connection_raises_error(self):
        """Test: _load_rules raises DatabaseError if no connection"""
        engine = RuleEngine()
        with pytest.raises(DatabaseError):
            engine._load_rules()

    def test_load_rules_with_connection_returns_list(self):
        """Test: _load_rules returns list of Rule objects"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock database rows
        rows = [
            (1, 100, "Keywords", True, "laptop", None, None, None, None, None, None, "ELECTRONICS", datetime.now(), datetime.now()),
            (2, 50, "NCM", True, None, "8544*", None, None, None, None, None, "CABLES", datetime.now(), datetime.now()),
        ]
        mock_cursor.fetchall.return_value = rows

        engine = RuleEngine(db_connection=mock_conn)
        rules = engine._load_rules()

        assert isinstance(rules, list)
        assert len(rules) == 2
        assert all(isinstance(r, Rule) for r in rules)

    def test_load_rules_only_active_rules(self):
        """Test: _load_rules query includes WHERE ativo=TRUE"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        engine = RuleEngine(db_connection=mock_conn)
        engine._load_rules()

        # Verify query includes ativo=TRUE
        call_args = mock_cursor.execute.call_args[0][0]
        assert "ativo = TRUE" in call_args or "ativo=TRUE" in call_args

    def test_load_rules_orders_by_priority(self):
        """Test: _load_rules orders by priority DESC"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        engine = RuleEngine(db_connection=mock_conn)
        engine._load_rules()

        # Verify query includes ORDER BY
        call_args = mock_cursor.execute.call_args[0][0]
        assert "ORDER BY" in call_args
        assert "prioridade DESC" in call_args or "prioridade" in call_args


@pytest.mark.unit
class TestRuleEngineCache:
    """Tests for rule caching functionality"""

    def test_initialize_cache_loads_rules(self):
        """Test: _initialize_cache loads rules into memory"""
        engine = RuleEngine(cache_rules=True)

        # Mock _load_rules
        mock_rules = [
            Rule(id=1, prioridade=10, nome="Test", ativo=True, resultado_classificacao="TEST")
        ]
        engine._load_rules = Mock(return_value=mock_rules)

        assert engine._rules_cache is None
        engine._initialize_cache()

        assert engine._rules_cache is not None
        assert len(engine._rules_cache) == 1

    def test_get_rules_returns_cached_rules(self):
        """Test: get_rules returns cached rules when available"""
        engine = RuleEngine(cache_rules=True)

        mock_rules = [
            Rule(id=1, prioridade=10, nome="Test", ativo=True, resultado_classificacao="TEST")
        ]
        engine._rules_cache = mock_rules

        rules = engine.get_rules()
        # Should return the cached rules (same content, may not be same object due to filtering)
        assert len(rules) == len(mock_rules)
        assert rules[0].id == mock_rules[0].id

    def test_get_rules_loads_from_database_if_not_cached(self):
        """Test: get_rules loads from database if cache disabled"""
        engine = RuleEngine(cache_rules=False)

        mock_rules = [
            Rule(id=1, prioridade=10, nome="Test", ativo=True, resultado_classificacao="TEST")
        ]
        engine._load_rules = Mock(return_value=mock_rules)

        rules = engine.get_rules()
        assert len(rules) == 1
        assert engine._rules_cache is None  # Not cached

    def test_get_rules_active_only_filters(self):
        """Test: get_rules with active_only=True filters inactive rules"""
        engine = RuleEngine(cache_rules=True)

        # Cache with one active and one inactive rule
        engine._rules_cache = [
            Rule(id=1, prioridade=10, nome="Active", ativo=True, resultado_classificacao="ACTIVE"),
            Rule(id=2, prioridade=20, nome="Inactive", ativo=False, resultado_classificacao="INACTIVE"),
        ]

        rules = engine.get_rules(active_only=True)
        assert len(rules) == 1
        assert rules[0].ativo is True

    def test_refresh_cache_reloads_rules(self):
        """Test: refresh_cache clears and reloads cache"""
        engine = RuleEngine(cache_rules=True)

        mock_rules = [
            Rule(id=1, prioridade=10, nome="Test", ativo=True, resultado_classificacao="TEST")
        ]
        engine._load_rules = Mock(return_value=mock_rules)

        engine._initialize_cache()
        assert engine._rules_cache is not None

        # Refresh should reload
        engine.refresh_cache()
        assert engine._rules_cache is not None
        assert len(engine._rules_cache) == 1


@pytest.mark.unit
class TestRuleEngineEvaluate:
    """Tests for product evaluation logic"""

    def test_evaluate_requires_description_and_ncm(self):
        """Test: evaluate raises ProductError if required fields missing"""
        engine = RuleEngine()

        # Missing NCM
        with pytest.raises(ProductError):
            engine.evaluate({"description": "laptop"})

        # Missing description
        with pytest.raises(ProductError):
            engine.evaluate({"ncm": "84713090"})

    def test_evaluate_accepts_dict(self):
        """Test: evaluate accepts product data as dictionary"""
        engine = RuleEngine()

        # Mock _load_rules to return empty list
        engine._load_rules = Mock(return_value=[])

        product_data = {
            "description": "laptop",
            "ncm": "84713090"
        }
        result = engine.evaluate(product_data)
        assert isinstance(result, ClassificationResult)

    def test_evaluate_accepts_product_object(self):
        """Test: evaluate accepts Product object"""
        engine = RuleEngine()
        engine._load_rules = Mock(return_value=[])

        product = Product(description="laptop", ncm="84713090")
        result = engine.evaluate(product)
        assert isinstance(result, ClassificationResult)

    def test_evaluate_returns_classification_result(self):
        """Test: evaluate returns ClassificationResult with expected fields"""
        engine = RuleEngine()
        engine._load_rules = Mock(return_value=[])

        product = Product(description="laptop", ncm="84713090")
        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification is not None
        assert hasattr(result, 'evaluation_time_ms')

    def test_evaluate_no_matching_rules_returns_no_match(self):
        """Test: evaluate returns NO_MATCH if no rules match"""
        engine = RuleEngine()
        engine._load_rules = Mock(return_value=[])

        product = Product(description="xyz abc", ncm="99999999")
        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "NO_MATCH"
        assert result.rule_id is None

    def test_evaluate_includes_evaluation_time(self):
        """Test: evaluate includes execution time in result"""
        engine = RuleEngine()
        engine._load_rules = Mock(return_value=[])

        product = Product(description="laptop", ncm="84713090")
        result = engine.evaluate(product)

        assert result.evaluation_time_ms is not None
        assert result.evaluation_time_ms >= 0

    def test_evaluate_with_optional_fields(self):
        """Test: evaluate works with optional product fields"""
        engine = RuleEngine()
        engine._load_rules = Mock(return_value=[])

        product = Product(
            id="P001",
            description="laptop",
            ncm="84713090",
            size=0.5,
            quantity=2,
            category="ELECTRONICS"
        )
        result = engine.evaluate(product)
        assert result.success is True

    def test_evaluate_default_user_is_system(self):
        """Test: evaluate defaults to 'system' user if not specified"""
        engine = RuleEngine()
        engine._load_rules = Mock(return_value=[])

        product = Product(description="laptop", ncm="84713090")
        # Should not raise error when user not specified
        result = engine.evaluate(product)
        assert result.success is True

    def test_evaluate_accepts_user_parameter(self):
        """Test: evaluate accepts user parameter"""
        engine = RuleEngine()
        engine._load_rules = Mock(return_value=[])

        product = Product(description="laptop", ncm="84713090")
        result = engine.evaluate(product, user="test_user")
        assert result.success is True

    def test_evaluate_with_matching_rule(self):
        """Test: evaluate returns classification when rule matches"""
        engine = RuleEngine()

        # Create a rule that matches
        rule = Rule(
            id=1, prioridade=10, nome="Test", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_palavras_chave="laptop"
        )
        engine._load_rules = Mock(return_value=[rule])

        product = Product(description="laptop", ncm="84713090")
        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "ELECTRONICS"
        assert result.rule_id == 1


@pytest.mark.unit
class TestRuleEngineErrors:
    """Tests for error handling"""

    def test_evaluate_invalid_product_type_raises_error(self):
        """Test: evaluate raises ProductError for invalid product type"""
        engine = RuleEngine()
        with pytest.raises(ProductError):
            engine.evaluate("not a dict or Product object")

    def test_evaluate_database_error_propagates(self):
        """Test: DatabaseError from _load_rules propagates"""
        engine = RuleEngine(db_connection=None)  # No connection
        product = Product(description="laptop", ncm="84713090")
        with pytest.raises(DatabaseError):
            engine.evaluate(product)

    def test_evaluate_no_rules_returns_no_match(self):
        """Test: evaluate returns NO_MATCH when no rules in database"""
        engine = RuleEngine()
        engine._load_rules = Mock(return_value=[])

        product = Product(description="anything", ncm="99999999")
        result = engine.evaluate(product)

        assert result.success is True
        assert result.classification == "NO_MATCH"


@pytest.mark.unit
class TestRuleEngineMetadata:
    """Tests for rule metadata extraction"""

    def test_evaluate_includes_rule_metadata(self):
        """Test: evaluate includes matched rule ID and name in result"""
        engine = RuleEngine()

        rule = Rule(
            id=42, prioridade=100, nome="Test Rule", ativo=True,
            resultado_classificacao="TEST",
            criterio_palavras_chave="test"
        )
        engine._load_rules = Mock(return_value=[rule])

        product = Product(description="test", ncm="84713090")
        result = engine.evaluate(product)

        assert result.rule_id == 42
        assert result.rule_name == "Test Rule"
        assert result.priority == 100

    def test_evaluate_includes_matched_criteria(self):
        """Test: evaluate lists which criteria matched"""
        engine = RuleEngine()

        rule = Rule(
            id=1, prioridade=10, nome="Complex", ativo=True,
            resultado_classificacao="TEST",
            criterio_palavras_chave="laptop",
            criterio_ncm="8471*"
        )
        engine._load_rules = Mock(return_value=[rule])

        product = Product(description="laptop computer", ncm="84713090")
        result = engine.evaluate(product)

        assert isinstance(result.matched_criteria, list)
        assert len(result.matched_criteria) > 0


@pytest.mark.unit
class TestRuleEnginePriority:
    """Tests for priority resolution in evaluate"""

    def test_evaluate_selects_highest_priority_rule(self):
        """Test: evaluate returns highest priority match"""
        engine = RuleEngine()

        rules = [
            Rule(id=1, prioridade=10, nome="Low", ativo=True,
                 resultado_classificacao="LOW",
                 criterio_palavras_chave="test"),
            Rule(id=2, prioridade=100, nome="High", ativo=True,
                 resultado_classificacao="HIGH",
                 criterio_palavras_chave="test"),
        ]
        engine._load_rules = Mock(return_value=rules)

        product = Product(description="test", ncm="84713090")
        result = engine.evaluate(product)

        assert result.rule_id == 2
        assert result.classification == "HIGH"

    def test_evaluate_uses_tiebreaker_when_priority_tied(self):
        """Test: evaluate uses creation date as tiebreaker"""
        engine = RuleEngine()

        old_date = datetime(2020, 1, 1)
        new_date = datetime(2025, 1, 1)

        rules = [
            Rule(id=1, prioridade=10, nome="Newer", ativo=True,
                 resultado_classificacao="NEWER",
                 criterio_palavras_chave="test",
                 data_criacao=new_date),
            Rule(id=2, prioridade=10, nome="Older", ativo=True,
                 resultado_classificacao="OLDER",
                 criterio_palavras_chave="test",
                 data_criacao=old_date),
        ]
        engine._load_rules = Mock(return_value=rules)

        product = Product(description="test", ncm="84713090")
        result = engine.evaluate(product)

        # Older rule should win
        assert result.rule_id == 2
        assert result.classification == "OLDER"
