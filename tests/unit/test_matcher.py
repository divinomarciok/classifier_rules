"""
Unit tests for Matcher service

Tests individual criteria matching methods
"""

import pytest
from classifier.matcher import Matcher
from classifier.models import Product, Rule


@pytest.mark.unit
class TestMatcherKeywords:
    """Tests for keyword matching"""

    def test_match_keywords_single_keyword_found(self):
        """Test: Single keyword found in description"""
        assert Matcher._match_keywords("laptop computer", "laptop") is True

    def test_match_keywords_single_keyword_not_found(self):
        """Test: Single keyword not found"""
        assert Matcher._match_keywords("USB cable", "laptop") is False

    def test_match_keywords_multiple_keywords_first_matches(self):
        """Test: Multiple keywords, first one matches"""
        assert Matcher._match_keywords("laptop computer", "laptop,desktop") is True

    def test_match_keywords_multiple_keywords_second_matches(self):
        """Test: Multiple keywords, second one matches"""
        assert Matcher._match_keywords("USB cable", "laptop,cable") is True

    def test_match_keywords_case_insensitive(self):
        """Test: Keyword matching is case-insensitive"""
        assert Matcher._match_keywords("Laptop Computer", "LAPTOP") is True
        assert Matcher._match_keywords("LAPTOP", "laptop") is True

    def test_match_keywords_substring_match(self):
        """Test: Keywords match as substring"""
        assert Matcher._match_keywords("monitor display screen", "monitor") is True

    def test_match_keywords_empty_description(self):
        """Test: Empty description returns False"""
        assert Matcher._match_keywords("", "laptop") is False

    def test_match_keywords_empty_keywords(self):
        """Test: Empty keywords returns False"""
        assert Matcher._match_keywords("laptop", "") is False

    def test_match_keywords_with_spaces(self):
        """Test: Keywords with spaces handled correctly"""
        assert Matcher._match_keywords("laptop computer system", "laptop,computer") is True


@pytest.mark.unit
class TestMatcherNCM:
    """Tests for NCM pattern matching"""

    def test_match_ncm_exact_match(self):
        """Test: Exact NCM match (no wildcard)"""
        assert Matcher._match_ncm("84713090", "84713090") is True

    def test_match_ncm_exact_no_match(self):
        """Test: Exact NCM doesn't match"""
        assert Matcher._match_ncm("84713090", "85444290") is False

    def test_match_ncm_wildcard_prefix(self):
        """Test: Wildcard prefix pattern matching"""
        assert Matcher._match_ncm("84713090", "8471*") is True
        assert Matcher._match_ncm("84714000", "8471*") is True
        assert Matcher._match_ncm("85444290", "8471*") is False

    def test_match_ncm_wildcard_multiple_digits(self):
        """Test: Wildcard matches multiple digits"""
        assert Matcher._match_ncm("8544", "8544*") is True
        assert Matcher._match_ncm("85444290", "8544*") is True

    def test_match_ncm_empty_code(self):
        """Test: Empty NCM code returns False"""
        assert Matcher._match_ncm("", "8471*") is False

    def test_match_ncm_empty_pattern(self):
        """Test: Empty pattern returns False"""
        assert Matcher._match_ncm("84713090", "") is False

    def test_match_ncm_wildcard_only(self):
        """Test: Wildcard-only pattern matches everything"""
        assert Matcher._match_ncm("12345678", "*") is True
        assert Matcher._match_ncm("", "*") is False  # Empty still fails


@pytest.mark.unit
class TestMatcherSize:
    """Tests for size range matching"""

    def test_match_size_within_range(self):
        """Test: Size within range matches"""
        assert Matcher._match_size(5.0, 1.0, 10.0) is True

    def test_match_size_at_min_boundary(self):
        """Test: Size at minimum boundary (inclusive)"""
        assert Matcher._match_size(1.0, 1.0, 10.0) is True

    def test_match_size_at_max_boundary(self):
        """Test: Size at maximum boundary (inclusive)"""
        assert Matcher._match_size(10.0, 1.0, 10.0) is True

    def test_match_size_below_min(self):
        """Test: Size below minimum doesn't match"""
        assert Matcher._match_size(0.5, 1.0, 10.0) is False

    def test_match_size_above_max(self):
        """Test: Size above maximum doesn't match"""
        assert Matcher._match_size(15.0, 1.0, 10.0) is False

    def test_match_size_none_no_range(self):
        """Test: None size with no range criteria matches"""
        assert Matcher._match_size(None, None, None) is True

    def test_match_size_none_with_range(self):
        """Test: None size with range criteria doesn't match"""
        assert Matcher._match_size(None, 1.0, 10.0) is False

    def test_match_size_min_only(self):
        """Test: Minimum boundary only"""
        assert Matcher._match_size(5.0, 1.0, None) is True
        assert Matcher._match_size(0.5, 1.0, None) is False

    def test_match_size_max_only(self):
        """Test: Maximum boundary only"""
        assert Matcher._match_size(5.0, None, 10.0) is True
        assert Matcher._match_size(15.0, None, 10.0) is False


@pytest.mark.unit
class TestMatcherQuantity:
    """Tests for quantity range matching"""

    def test_match_quantity_within_range(self):
        """Test: Quantity within range matches"""
        assert Matcher._match_quantity(50, 10, 100) is True

    def test_match_quantity_at_min_boundary(self):
        """Test: Quantity at minimum boundary (inclusive)"""
        assert Matcher._match_quantity(10, 10, 100) is True

    def test_match_quantity_at_max_boundary(self):
        """Test: Quantity at maximum boundary (inclusive)"""
        assert Matcher._match_quantity(100, 10, 100) is True

    def test_match_quantity_below_min(self):
        """Test: Quantity below minimum doesn't match"""
        assert Matcher._match_quantity(5, 10, 100) is False

    def test_match_quantity_above_max(self):
        """Test: Quantity above maximum doesn't match"""
        assert Matcher._match_quantity(150, 10, 100) is False

    def test_match_quantity_none_no_range(self):
        """Test: None quantity with no range criteria matches"""
        assert Matcher._match_quantity(None, None, None) is True

    def test_match_quantity_none_with_range(self):
        """Test: None quantity with range criteria doesn't match"""
        assert Matcher._match_quantity(None, 10, 100) is False


@pytest.mark.unit
class TestMatcherCategory:
    """Tests for category matching"""

    def test_match_category_exact_match(self):
        """Test: Exact category match"""
        assert Matcher._match_category("ELECTRONICS", "ELECTRONICS") is True

    def test_match_category_case_insensitive(self):
        """Test: Category match is case-insensitive"""
        assert Matcher._match_category("electronics", "ELECTRONICS") is True
        assert Matcher._match_category("ELECTRONICS", "electronics") is True

    def test_match_category_no_match(self):
        """Test: Category doesn't match"""
        assert Matcher._match_category("CABLES", "ELECTRONICS") is False

    def test_match_category_none_product(self):
        """Test: None category doesn't match"""
        assert Matcher._match_category(None, "ELECTRONICS") is False

    def test_match_category_empty_criteria(self):
        """Test: Empty criteria always matches"""
        assert Matcher._match_category("ELECTRONICS", "") is True
        assert Matcher._match_category(None, "") is True


@pytest.mark.unit
class TestMatcherIntegration:
    """Tests for full criteria matching"""

    def test_matches_all_criteria_keyword_only(self):
        """Test: Matching with keyword criteria only"""
        product = Product(description="laptop computer", ncm="99999999")
        rule = Rule(
            id=1, prioridade=10, nome="Test", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_palavras_chave="laptop"
        )
        assert Matcher.matches_all_criteria(product, rule) is True

    def test_matches_all_criteria_ncm_only(self):
        """Test: Matching with NCM criteria only"""
        product = Product(description="something", ncm="84713090")
        rule = Rule(
            id=1, prioridade=10, nome="Test", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_ncm="8471*"
        )
        assert Matcher.matches_all_criteria(product, rule) is True

    def test_matches_all_criteria_multiple(self):
        """Test: Matching with multiple criteria (all must pass)"""
        product = Product(
            description="laptop",
            ncm="84713090",
            size=0.5,
            quantity=5
        )
        rule = Rule(
            id=1, prioridade=10, nome="Test", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_palavras_chave="laptop",
            criterio_ncm="8471*",
            criterio_tamanho_min=0.1,
            criterio_tamanho_max=1.0,
            criterio_quantidade_min=1,
            criterio_quantidade_max=10
        )
        assert Matcher.matches_all_criteria(product, rule) is True

    def test_matches_all_criteria_one_fails(self):
        """Test: If ANY criteria fails, whole match fails"""
        product = Product(
            description="laptop",
            ncm="84713090",
            size=2.0,  # Out of range!
            quantity=5
        )
        rule = Rule(
            id=1, prioridade=10, nome="Test", ativo=True,
            resultado_classificacao="ELECTRONICS",
            criterio_palavras_chave="laptop",
            criterio_ncm="8471*",
            criterio_tamanho_min=0.1,
            criterio_tamanho_max=1.0,  # Size doesn't match
            criterio_quantidade_min=1,
            criterio_quantidade_max=10
        )
        assert Matcher.matches_all_criteria(product, rule) is False

    def test_matches_all_criteria_no_criteria(self):
        """Test: Rule with no criteria matches everything"""
        product = Product(description="anything", ncm="99999999")
        rule = Rule(
            id=1, prioridade=10, nome="Test", ativo=True,
            resultado_classificacao="UNKNOWN"
        )
        # Rule has no criteria specified, so it matches
        assert Matcher.matches_all_criteria(product, rule) is True
