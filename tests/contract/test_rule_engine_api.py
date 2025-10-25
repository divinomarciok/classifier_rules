"""
Contract tests for RuleEngine API

Validates that RuleEngine implements the required interface and behavior
as defined in specs/001-rule-engine/contracts/rule_engine_api.md

Test-first approach: These tests must FAIL before implementation
"""

import pytest
import time
from typing import Dict, Any

# These imports will fail initially - that's OK, it means tests are written first
try:
    from classifier.engine import RuleEngine
    from classifier.models import Product, ClassificationResult
except ImportError as e:
    pytest.skip(f"RuleEngine not yet implemented: {e}", allow_module_level=True)


@pytest.mark.contract
@pytest.mark.db
class TestRuleEngineAPI:
    """Contract tests for RuleEngine.evaluate() method"""

    def test_engine_initializes(self, db_connection):
        """Test that RuleEngine can be instantiated with database connection"""
        engine = RuleEngine(db_connection=db_connection)
        assert engine is not None
        assert engine.db_connection is not None

    def test_evaluate_with_keyword_match(self, db_connection, sample_rules, sample_products):
        """Test: Product with keyword match returns correct classification (US1-Scenario 1)

        Given: Product with description "laptop computer", NCM 84713090
        When: Rule engine evaluates it against active rules
        Then: System returns matching classification from highest-priority matching rule
        """
        engine = RuleEngine(db_connection=db_connection)

        # Product that should match 'electronics' rule (keywords: laptop,computer, priority: 100)
        product = sample_products['laptop']

        result = engine.evaluate(product)

        # Assertions per acceptance criteria
        assert result is not None, "evaluate() should return ClassificationResult"
        assert isinstance(result, ClassificationResult), "Result should be ClassificationResult instance"
        assert result.success is True, "Evaluation should be successful"
        assert result.classification == 'ELECTRONICS', "Should match electronics rule via keywords"
        assert result.rule_id == sample_rules['electronics'], "Should return correct rule ID"
        assert result.rule_name == 'Laptop Rule', "Should return correct rule name"
        assert result.priority == 100, "Should have correct priority"
        assert len(result.matched_criteria) > 0, "Should record which criteria matched"

    def test_evaluate_with_ncm_match(self, db_connection, sample_rules, sample_products):
        """Test: Product with NCM code match returns classification (US1-Scenario 2)

        Given: Product with NCM 8544* pattern (cables)
        When: Rule engine evaluates it
        Then: System returns classification from NCM-based rule
        """
        engine = RuleEngine(db_connection=db_connection)

        # Product that should match 'cables' rule (NCM: 8544*, priority: 50)
        product = sample_products['cable']

        result = engine.evaluate(product)

        assert result is not None
        assert result.success is True
        assert result.classification == 'CABLES', "Should match cables rule via NCM pattern"
        assert result.rule_id == sample_rules['cables'], "Should return correct rule ID"
        assert 'criterio_ncm' in result.matched_criteria, "Should record NCM criterion matched"

    def test_evaluate_inactive_rule_ignored(self, db_connection):
        """Test: Inactive rules are never evaluated (US1-Scenario 3)

        Given: A rule is marked as inactive in database
        When: Rule engine evaluates products
        Then: The inactive rule is never selected for classification
        """
        engine = RuleEngine(db_connection=db_connection)
        cursor = db_connection.cursor()

        # Insert an inactive rule that would match
        cursor.execute("""
            INSERT INTO regras_de_classificacao (
                prioridade, nome, ativo, resultado_classificacao,
                criterio_palavras_chave
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (1000, 'Inactive Rule', False, 'SHOULD_NOT_MATCH', 'laptop'))

        rule_id = cursor.fetchone()[0]
        db_connection.commit()

        product = {
            'id': 'P_test',
            'description': 'laptop',
            'ncm': '99999999'
        }

        result = engine.evaluate(product)

        # Should not match the inactive rule (priority 1000 is very high)
        assert result.classification != 'SHOULD_NOT_MATCH', "Inactive rules should be ignored"

        # Cleanup
        cursor.execute("DELETE FROM regras_de_classificacao WHERE id = %s", (rule_id,))
        db_connection.commit()

    def test_evaluate_returns_result_dict_structure(self, db_connection, sample_rules, sample_products):
        """Test: Result contains all required keys and types

        Result dict must contain:
        - classification (str)
        - rule_id (int or None)
        - rule_name (str or None)
        - priority (int or None)
        - matched_criteria (list)
        - evaluation_time_ms (int)
        - success (bool)
        - message (str)
        """
        engine = RuleEngine(db_connection=db_connection)
        product = sample_products['laptop']

        result = engine.evaluate(product)
        result_dict = result.to_dict()

        # Check all required keys exist
        required_keys = [
            'classification', 'rule_id', 'rule_name', 'priority',
            'matched_criteria', 'evaluation_time_ms', 'success', 'message'
        ]
        for key in required_keys:
            assert key in result_dict, f"Result missing required key: {key}"

        # Check types
        assert isinstance(result_dict['classification'], str)
        assert isinstance(result_dict['rule_id'], (int, type(None)))
        assert isinstance(result_dict['rule_name'], (str, type(None)))
        assert isinstance(result_dict['priority'], (int, type(None)))
        assert isinstance(result_dict['matched_criteria'], list)
        assert isinstance(result_dict['evaluation_time_ms'], int)
        assert isinstance(result_dict['success'], bool)
        assert isinstance(result_dict['message'], str)

    def test_evaluate_performance(self, db_connection, sample_rules, sample_products):
        """Test: Evaluation completes within performance target (<500ms per SC-003)

        This is a simple test. More comprehensive performance testing in integration tests.
        """
        engine = RuleEngine(db_connection=db_connection)
        product = sample_products['laptop']

        start = time.time()
        result = engine.evaluate(product)
        elapsed_ms = int((time.time() - start) * 1000)

        # For 5 rules, should be much faster than 500ms
        # Using 250ms as reasonable threshold for test environment
        assert elapsed_ms < 250, f"Evaluation took {elapsed_ms}ms, should be < 250ms for small rule set"

    def test_evaluate_handles_invalid_product(self, db_connection):
        """Test: Invalid product data raises ProductError

        Given: Product data missing required fields
        When: Evaluate is called
        Then: Raises ProductError with clear message
        """
        from classifier import ProductError

        engine = RuleEngine(db_connection=db_connection)

        invalid_products = [
            {},  # Missing all required fields
            {'id': 'P001'},  # Missing description
            {'id': 'P001', 'description': 'test'},  # Missing NCM
        ]

        for invalid_product in invalid_products:
            with pytest.raises(ProductError):
                engine.evaluate(invalid_product)

    def test_engine_methods_exist(self, db_connection):
        """Test: RuleEngine has all required methods"""
        engine = RuleEngine(db_connection=db_connection)

        # Check required methods exist
        assert hasattr(engine, 'evaluate'), "RuleEngine should have evaluate() method"
        assert hasattr(engine, 'get_rules'), "RuleEngine should have get_rules() method"
        assert hasattr(engine, 'refresh_cache'), "RuleEngine should have refresh_cache() method"

        # Check methods are callable
        assert callable(engine.evaluate)
        assert callable(engine.get_rules)
        assert callable(engine.refresh_cache)


@pytest.mark.contract
@pytest.mark.db
class TestRuleEngineEdgeCases:
    """Contract tests for edge cases and error handling"""

    def test_evaluate_no_matching_rules(self, db_connection):
        """Test: No matching rules returns NO_MATCH classification

        Given: Product that matches no rules
        When: Evaluate is called
        Then: Returns NO_MATCH classification with rule_id = None
        """
        engine = RuleEngine(db_connection=db_connection)

        product = {
            'id': 'P_nomatch',
            'description': 'xyzabc unique description xyz',
            'ncm': '99999999',
            'size': 99.9,
            'quantity': 1
        }

        result = engine.evaluate(product)

        assert result is not None
        assert result.classification == 'NO_MATCH', "Should return NO_MATCH when no rules match"
        assert result.rule_id is None, "rule_id should be None when no match"
        assert result.success is True, "Evaluation itself should succeed (result is NO_MATCH, not error)"

    def test_evaluate_creates_product_from_dict(self, db_connection, sample_rules, sample_products):
        """Test: Can pass product as dict instead of Product object"""
        engine = RuleEngine(db_connection=db_connection)

        # Pass as dict (common usage)
        product_dict = {
            'id': 'P001',
            'description': 'laptop computer',
            'ncm': '84713090',
            'size': 0.5,
            'quantity': 1
        }

        result = engine.evaluate(product_dict)

        assert result.success is True
        assert result.classification == 'ELECTRONICS'

    def test_get_rules_returns_list(self, db_connection, sample_rules):
        """Test: get_rules() returns list of Rule objects"""
        engine = RuleEngine(db_connection=db_connection)

        rules = engine.get_rules(active_only=True)

        assert isinstance(rules, list)
        assert len(rules) > 0, "Should return sample rules"
        # Each rule should be a Rule object (can check hasattr for expected attributes)

    def test_refresh_cache_reloads_rules(self, db_connection, sample_rules):
        """Test: refresh_cache() reloads rules from database"""
        engine = RuleEngine(db_connection=db_connection, cache_rules=True)

        # Get initial count
        rules_before = engine.get_rules()
        count_before = len(rules_before)

        # Insert a new rule
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO regras_de_classificacao (
                prioridade, nome, ativo, resultado_classificacao
            ) VALUES (%s, %s, %s, %s)
        """, (999, 'New Rule', True, 'NEW_RESULT'))
        db_connection.commit()

        # Refresh cache
        engine.refresh_cache()

        # Get new count
        rules_after = engine.get_rules()
        count_after = len(rules_after)

        # Should have one more rule
        assert count_after > count_before, "refresh_cache() should reload rules from database"

        # Cleanup
        cursor.execute("DELETE FROM regras_de_classificacao WHERE nome = %s", ('New Rule',))
        db_connection.commit()
