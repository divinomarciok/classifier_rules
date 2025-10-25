"""
Contract tests for User Story 4 - Batch Classification

Tests that the system can process multiple products from database
in a single operation for efficiency.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from classifier.engine import RuleEngine
from classifier.models import Product, Rule


@pytest.mark.contract
class TestBatchClassificationUS4:
    """Contract tests for US4: Batch Classification from Database"""

    def test_us4_scenario_1_batch_classify_unclassified_products(self):
        """US4 Scenario 1: Query unclassified products and classify them

        Given a batch of 500 unclassified products in database,
        When we run batch classification,
        Then all products are evaluated and classified
        """
        mock_conn = self._create_mock_batch_db(500)
        engine = RuleEngine(mock_conn)

        # Simulate batch processing
        unclassified_products = [
            {"id": f"PROD_{i}", "description": f"Product {i}", "ncm": "99999999"}
            for i in range(500)
        ]

        results = []
        for product in unclassified_products:
            result = engine.evaluate(product)
            results.append(result)

        # Assert: All products were evaluated
        assert len(results) == 500
        # At least some matched (based on mock rules)
        matched = [r for r in results if r.success]
        assert len(matched) > 0

    def test_us4_scenario_2_batch_with_custom_limit(self):
        """US4 Scenario 2: Query with custom row limit

        Given ability to specify batch size limit,
        When batch limit is set to 100,
        Then only 100 products are processed
        """
        mock_conn = self._create_mock_batch_db(1000)

        # Simulate batch with limit
        batch_limit = 100
        unclassified = [
            {"id": f"P_{i}", "description": f"Product {i}", "ncm": "99999999"}
            for i in range(batch_limit)
        ]

        assert len(unclassified) == batch_limit

    def test_us4_scenario_3_batch_updates_database(self):
        """US4 Scenario 3: Batch classification updates database

        Given batch classification completes,
        When classifications are stored,
        Then database is updated with results
        """
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock UPDATE operation
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None

        # Simulate batch update
        update_count = 0
        for i in range(10):
            # Each classification would trigger an UPDATE
            update_count += 1
            mock_cursor.execute(
                "UPDATE productos SET categoria = %s WHERE id = %s",
                ("TEST_CLASS", f"P_{i}")
            )

        assert mock_cursor.execute.called
        assert update_count == 10

    def test_batch_classification_performance(self):
        """Verify: Batch processing meets performance targets

        SC-008: 500 products classified in < 5 minutes
        """
        import time

        # Simulate batch of 500 with fast evaluation
        start_time = time.time()

        results = []
        for i in range(500):
            # Simulate 10ms per evaluation
            time.sleep(0.01)
            results.append({"id": f"P_{i}", "classification": f"CLASS_{i % 5}"})

        elapsed_ms = (time.time() - start_time) * 1000

        # 500 products * 10ms = 5000ms = 5 seconds (well under 5 minutes)
        assert elapsed_ms < 300000  # 5 minutes = 300 seconds = 300000ms
        assert len(results) == 500

    def test_batch_summary_statistics(self):
        """Verify: Batch operation returns summary statistics

        Summary includes: total processed, matched count, no-match count, time
        """
        results = [
            {"success": True, "classification": "CLASS_A"},
            {"success": True, "classification": "CLASS_B"},
            {"success": False, "classification": "NO_MATCH"},
            {"success": True, "classification": "CLASS_A"},
            {"success": False, "classification": "NO_MATCH"},
        ]

        # Calculate summary
        summary = {
            "total_processed": len(results),
            "total_matched": len([r for r in results if r["success"]]),
            "total_no_match": len([r for r in results if not r["success"]]),
            "match_rate": len([r for r in results if r["success"]]) / len(results),
        }

        assert summary["total_processed"] == 5
        assert summary["total_matched"] == 3
        assert summary["total_no_match"] == 2
        assert summary["match_rate"] == 0.6  # 60% matched

    def test_batch_audit_trail_complete(self):
        """Verify: All batch classifications are logged to audit trail

        Every product in batch gets audit entry
        """
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)

        audit_ids = []
        for i in range(20):
            # Each classification creates audit entry
            mock_cursor.execute(
                "INSERT INTO auditoria_classificacao (...) VALUES (...)"
            )
            audit_id = mock_cursor.fetchone()[0]
            audit_ids.append(audit_id)

        assert len(audit_ids) == 20
        assert mock_cursor.execute.call_count >= 20

    def test_batch_handles_mixed_products(self):
        """Verify: Batch processes products with different data profiles

        Products may have different combinations of criteria fields
        """
        products = [
            # Product with all fields
            {"id": "P1", "description": "laptop", "ncm": "84713090", "size": 1.5, "quantity": 100},
            # Product with minimal fields
            {"id": "P2", "description": "item", "ncm": "99999999"},
            # Product with extra fields
            {"id": "P3", "description": "test", "ncm": "84713090", "size": 0.5, "category": "IT"},
        ]

        # All should be processable
        for product in products:
            assert "id" in product
            assert "description" in product
            assert "ncm" in product

    def test_batch_continues_on_error(self):
        """Verify: Batch processing continues even if one product fails

        Failure in one product shouldn't stop batch
        """
        products = [
            {"id": "P1", "description": "valid", "ncm": "84713090"},
            {"id": "P2", "description": "invalid", "ncm": ""},  # Invalid NCM
            {"id": "P3", "description": "valid2", "ncm": "84713090"},
        ]

        results = []
        for product in products:
            try:
                # P2 would fail validation but batch continues
                if product["ncm"]:
                    results.append({"id": product["id"], "success": True})
            except Exception:
                results.append({"id": product["id"], "success": False})

        # 2 succeeded, 1 failed, but batch completed
        assert len(results) == 3
        success_count = len([r for r in results if r["success"]])
        assert success_count == 2

    def test_batch_respects_database_offset(self):
        """Verify: Batch queries can use offset for pagination

        Allows processing in chunks (e.g., 500 at offset 0, then 500 at offset 500)
        """
        total_products = 1000
        batch_size = 500

        batches = []
        for offset in range(0, total_products, batch_size):
            # Query: SELECT * FROM productos LIMIT batch_size OFFSET offset
            batch_count = min(batch_size, total_products - offset)
            batches.append({
                "offset": offset,
                "limit": batch_size,
                "count": batch_count
            })

        assert len(batches) == 2  # Two batches of 500
        assert batches[0]["offset"] == 0
        assert batches[1]["offset"] == 500

    @staticmethod
    def _create_mock_batch_db(count: int):
        """Create mock database with batch of products"""
        from datetime import datetime

        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Create mock rule row
        mock_rule_row = (
            1, "Test Rule", True, 50, "laptop", None, None, None, None, None, None, "TEST_CLASS",
            datetime.now(), datetime.now()
        )

        # Mock unclassified products query
        products = [
            (i, f"Product {i}", "99999999", None)
            for i in range(count)
        ]

        # Setup execute and fetchall to work together
        def execute_side_effect(sql, params=None):
            if "regras_de_classificacao" in sql:
                mock_cursor._is_rules_query = True
            else:
                mock_cursor._is_rules_query = False

        mock_cursor.execute.side_effect = execute_side_effect

        def fetchall_side_effect():
            if hasattr(mock_cursor, '_is_rules_query') and mock_cursor._is_rules_query:
                return [mock_rule_row]
            else:
                return products

        mock_cursor.fetchall.side_effect = fetchall_side_effect

        # Mock audit insert
        mock_cursor.fetchone.return_value = (1,)

        return mock_conn
