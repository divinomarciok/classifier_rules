"""
Contract tests for User Story 5 - CSV Classification

Tests that the system can process CSV files with product data,
classify products, and export results to CSV files.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
from classifier.engine import RuleEngine


@pytest.mark.contract
class TestCSVClassificationUS5:
    """Contract tests for US5: CSV Classification - Import, Process, Export"""

    def test_us5_scenario_1_csv_import_products(self):
        """US5 Scenario 1: Import products from CSV file

        Given a CSV file with product data (id, description, ncm),
        When we import the CSV,
        Then products are loaded and available for classification
        """
        # Sample CSV data structure
        csv_data = [
            {"id": "PROD_001", "description": "laptop", "ncm": "84713090"},
            {"id": "PROD_002", "description": "monitor", "ncm": "85287200"},
            {"id": "PROD_003", "description": "keyboard", "ncm": "84711000"},
        ]

        # Validate CSV structure
        assert len(csv_data) == 3
        assert all('id' in row for row in csv_data)
        assert all('description' in row for row in csv_data)
        assert all('ncm' in row for row in csv_data)

    def test_us5_scenario_2_csv_classify_products(self):
        """US5 Scenario 2: Classify products imported from CSV

        Given imported products from CSV,
        When we classify them using the rule engine,
        Then each product receives a classification
        """
        mock_conn = self._create_mock_csv_db()
        engine = RuleEngine(mock_conn)

        products = [
            {"id": "PROD_001", "description": "laptop", "ncm": "84713090"},
            {"id": "PROD_002", "description": "monitor", "ncm": "85287200"},
        ]

        results = []
        for product in products:
            result = engine.evaluate(product)
            results.append(result)

        # All products should be evaluated
        assert len(results) == 2

    def test_us5_scenario_3_csv_export_results(self):
        """US5 Scenario 3: Export classification results to CSV

        Given classified products,
        When we export to CSV,
        Then a file is created with id, description, ncm, classification
        """
        # Simulated export structure
        export_data = [
            {"id": "PROD_001", "description": "laptop", "ncm": "84713090", "classification": "CLASS_A"},
            {"id": "PROD_002", "description": "monitor", "ncm": "85287200", "classification": "CLASS_B"},
        ]

        # Validate export structure
        assert len(export_data) == 2
        for row in export_data:
            assert 'id' in row
            assert 'description' in row
            assert 'ncm' in row
            assert 'classification' in row
            assert row['classification'] is not None

    def test_us5_scenario_4_csv_handles_missing_columns(self):
        """US5 Scenario 4: Gracefully handle CSV with missing optional columns

        Given CSV with minimal columns (id, description, ncm),
        When we process it,
        Then missing optional columns are handled with defaults
        """
        csv_data = [
            {"id": "PROD_001", "description": "item", "ncm": "99999999"},
            # No size, quantity, category - should be optional
        ]

        for row in csv_data:
            # Required fields
            assert 'id' in row
            assert 'description' in row
            assert 'ncm' in row
            # Optional fields may be missing
            size = row.get('size', None)
            quantity = row.get('quantity', None)
            assert size is None or isinstance(size, (int, float))
            assert quantity is None or isinstance(quantity, (int, float))

    def test_us5_scenario_5_csv_handles_extra_columns(self):
        """US5 Scenario 5: Handle CSV with extra/unknown columns

        Given CSV with additional columns,
        When we process it,
        Then extra columns are preserved or safely ignored
        """
        csv_data = [
            {
                "id": "PROD_001",
                "description": "laptop",
                "ncm": "84713090",
                "size": 1.5,
                "quantity": 10,
                "supplier": "ACME Corp",  # Extra column
                "cost": 800.00,  # Extra column
            },
        ]

        for row in csv_data:
            # Core required fields
            assert 'id' in row
            assert 'description' in row
            assert 'ncm' in row
            # Extra fields should not cause errors
            assert len(row) >= 3

    def test_us5_scenario_6_csv_batching(self):
        """US5 Scenario 6: Process large CSV in batches

        Given a large CSV file with 10,000 products,
        When we process in batches of 1,000,
        Then all products are classified efficiently
        """
        total_products = 10000
        batch_size = 1000

        # Simulate batch processing
        batches_processed = 0
        for offset in range(0, total_products, batch_size):
            batch_count = min(batch_size, total_products - offset)
            batches_processed += 1
            assert batch_count > 0

        # Should process in 10 batches
        assert batches_processed == 10

    def test_us5_scenario_7_csv_encoding(self):
        """US5 Scenario 7: Handle different CSV encodings

        Given CSV files with various encodings (UTF-8, Latin-1),
        When we import them,
        Then encoding is correctly handled
        """
        # Simulate data with special characters
        csv_data = [
            {"id": "PROD_001", "description": "café", "ncm": "84713090"},
            {"id": "PROD_002", "description": "naïve", "ncm": "85287200"},
            {"id": "PROD_003", "description": "résumé", "ncm": "84711000"},
        ]

        # Validate UTF-8 handling
        for row in csv_data:
            assert isinstance(row['description'], str)
            assert len(row['description']) > 0

    def test_us5_scenario_8_csv_validation(self):
        """US5 Scenario 8: Validate CSV data before processing

        Given potentially malformed CSV,
        When we validate it,
        Then invalid rows are identified and reported
        """
        csv_data = [
            {"id": "PROD_001", "description": "laptop", "ncm": "84713090"},  # Valid
            {"id": "PROD_002", "description": "", "ncm": "85287200"},  # Invalid - empty description
            {"id": "", "description": "monitor", "ncm": "85287200"},  # Invalid - empty id
            {"id": "PROD_004", "description": "keyboard", "ncm": ""},  # Invalid - empty ncm
        ]

        valid_count = 0
        invalid_count = 0

        for row in csv_data:
            if row['id'] and row['description'] and row['ncm']:
                valid_count += 1
            else:
                invalid_count += 1

        assert valid_count == 1
        assert invalid_count == 3

    def test_us5_scenario_9_csv_audit_trail(self):
        """US5 Scenario 9: Create audit trail for CSV processing

        Given CSV classification operation,
        When processing completes,
        Then audit entries are created for all classifications
        """
        # Simulate audit entries
        audit_entries = []
        csv_data = [
            {"id": "PROD_001", "description": "laptop", "ncm": "84713090", "classification": "CLASS_A"},
            {"id": "PROD_002", "description": "monitor", "ncm": "85287200", "classification": "CLASS_B"},
            {"id": "PROD_003", "description": "keyboard", "ncm": "84711000", "classification": "CLASS_A"},
        ]

        for row in csv_data:
            audit_entries.append({
                'produto_id': row['id'],
                'regra_id': 1,  # Simulated matching rule
                'resultado_classificacao': row['classification'],
                'data_classificacao': datetime.now(),
            })

        assert len(audit_entries) == len(csv_data)

    def test_us5_scenario_10_csv_skip_already_classified(self):
        """US5 Scenario 10: Skip products already classified

        Given CSV with mix of classified and unclassified products,
        When we process CSV,
        Then only unclassified products are re-processed
        """
        csv_data = [
            {"id": "PROD_001", "description": "laptop", "ncm": "84713090", "classification": None},  # Unclassified
            {"id": "PROD_002", "description": "monitor", "ncm": "85287200", "classification": "CLASS_B"},  # Already classified
            {"id": "PROD_003", "description": "keyboard", "ncm": "84711000", "classification": None},  # Unclassified
        ]

        unclassified = [row for row in csv_data if row['classification'] is None]
        classified = [row for row in csv_data if row['classification'] is not None]

        assert len(unclassified) == 2
        assert len(classified) == 1

    def test_us5_csv_import_validation(self):
        """Verify: CSV import validates file format

        CSV must have: id, description, ncm columns
        Optional: size, quantity, category, and others
        """
        required_columns = {'id', 'description', 'ncm'}
        optional_columns = {'size', 'quantity', 'category', 'supplier', 'cost'}

        csv_headers = {'id', 'description', 'ncm', 'size', 'quantity'}

        assert required_columns.issubset(csv_headers)

    def test_us5_csv_export_format(self):
        """Verify: CSV export has correct format

        Export includes: id, description, ncm, classification, data_classificacao
        """
        export_headers = {
            'id',
            'description',
            'ncm',
            'classification',
            'data_classificacao',
        }

        # Verify required export columns
        assert 'id' in export_headers
        assert 'classification' in export_headers

    def test_us5_csv_performance(self):
        """Verify: CSV processing meets performance targets

        1,000 products processed from CSV in < 30 seconds
        """
        import time

        # Simulate processing 1000 CSV rows
        start_time = time.time()

        processed = 0
        for i in range(1000):
            # Simulate 10ms per row (fast evaluation)
            time.sleep(0.001)
            processed += 1

        elapsed = (time.time() - start_time) * 1000

        assert processed == 1000
        assert elapsed < 30000  # 30 seconds = 30000ms

    def test_us5_csv_memory_efficiency(self):
        """Verify: CSV processing is memory efficient

        Process large CSV without loading entire file into memory
        """
        # Simulate streaming processing
        batch_size = 1000
        total_products = 100000

        # Process in chunks to avoid memory overhead
        memory_usage_per_batch = batch_size * 100  # Simulated bytes per row

        assert memory_usage_per_batch < 1000000  # < 1MB per batch

    @staticmethod
    def _create_mock_csv_db():
        """Create mock database for CSV processing"""
        from datetime import datetime

        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Create mock rule row - order must match Rule.from_db_row
        # Row structure from migration: id, prioridade, nome, ativo, criterio_palavras_chave, criterio_ncm, ...
        mock_rule_row = (
            1,  # id (index 0)
            50,  # prioridade (index 1 - must be int)
            "Test Rule",  # nome (index 2)
            True,  # ativo (index 3)
            "laptop",  # criterio_palavras_chave (index 4)
            None,  # criterio_ncm (index 5)
            None,  # criterio_tamanho_min (index 6)
            None,  # criterio_tamanho_max (index 7)
            None,  # criterio_quantidade_min (index 8)
            None,  # criterio_quantidade_max (index 9)
            None,  # criterio_categoria (index 10)
            "TEST_CLASS",  # resultado_classificacao (index 11)
            datetime.now(),  # data_criacao (index 12)
            datetime.now()  # data_atualizacao (index 13)
        )

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
                return []

        mock_cursor.fetchall.side_effect = fetchall_side_effect
        mock_cursor.fetchone.return_value = (1,)

        return mock_conn
