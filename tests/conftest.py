"""
Pytest configuration and fixtures for classifier tests

Provides database connections, test data, and cleanup utilities
for all test modules.
"""

import os
import logging
import pytest
import psycopg2
from pathlib import Path

# Configure test logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope='session')
def test_db_config():
    """Database configuration for tests

    Loads from .env.local or environment variables.
    Uses a separate test database to avoid contaminating production data.

    Returns:
        dict: Database configuration with host, name, user, password, port
    """
    # Load .env.local if exists
    env_file = Path(__file__).parent.parent / '.env.local'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

    return {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'database': os.environ.get('DB_NAME', 'classifier_test'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'postgres'),
        'port': int(os.environ.get('DB_PORT', 5432)),
    }


@pytest.fixture(scope='function')
def db_connection(test_db_config):
    """Database connection for individual tests

    Creates a fresh connection for each test.
    Connection is automatically closed after test.

    Yields:
        psycopg2.connection: Database connection object

    Usage:
        def test_something(db_connection):
            cursor = db_connection.cursor()
            cursor.execute("SELECT * FROM regras_de_classificacao")
            rows = cursor.fetchall()
            assert len(rows) > 0
    """
    conn = psycopg2.connect(**test_db_config)
    yield conn
    conn.close()


@pytest.fixture(scope='function')
def sample_categories(db_connection):
    """Create sample categories for testing

    Inserts 5 test categories into categorias table.
    **MUST be called before sample_rules fixture** since rules have FK to categories.

    Yields:
        dict: Dictionary with category IDs indexed by name

    Usage:
        def test_rules_with_categories(db_connection, sample_categories, sample_rules):
            assert sample_categories['electronics'] is not None
            # Categories are now in database and rules reference them
    """
    cursor = db_connection.cursor()

    # Insert sample categories
    categories = {
        'electronics': 'ELECTRONICS',
        'cables': 'CABLES',
        'small': 'SMALL ITEMS',
        'bulk': 'BULK ITEMS',
        'monitors': 'MONITORS & DISPLAYS',
    }

    inserted_categories = {}

    for key, nome in categories.items():
        cursor.execute("""
            INSERT INTO categorias (nome, descricao, ativo)
            VALUES (%s, %s, true)
            RETURNING id
        """, (nome, f'Test category: {nome}'))

        category_id = cursor.fetchone()[0]
        inserted_categories[key] = category_id
        print(f"Inserted sample category '{key}' (nome={nome}) with ID {category_id}")

    db_connection.commit()

    yield inserted_categories

    # Cleanup: Delete all sample categories after test
    cursor.execute("DELETE FROM categorias")
    db_connection.commit()
    cursor.close()


@pytest.fixture(scope='function')
def sample_rules(db_connection, sample_categories):
    """Create sample rules for testing

    Inserts 5 test rules into regras_de_classificacao table:
    1. Keyword-based rule for ELECTRONICS (keywords: laptop, computer, desktop)
    2. NCM-based rule for CABLES (NCM: 8544*)
    3. Size-based rule for SMALL items (size < 1)
    4. Quantity-based rule for BULK items (quantity > 100)
    5. Combined criteria rule (keywords + NCM)

    **Depends on sample_categories fixture** for categoria_id FK references.

    Yields:
        dict: Dictionary with rule IDs indexed by name

    Usage:
        def test_rule_matching(db_connection, sample_categories, sample_rules):
            assert sample_rules['electronics'] is not None
            # Rules are now in database with proper categoria_id references
    """
    cursor = db_connection.cursor()

    # Insert sample rules using categoria_id from sample_categories
    rules = {
        'electronics': {
            'prioridade': 100,
            'nome': 'Laptop Rule',
            'criterio_palavras_chave': 'laptop,computer',
            'categoria_id': sample_categories['electronics'],
        },
        'cables': {
            'prioridade': 50,
            'nome': 'Cable Rule',
            'criterio_ncm': '8544*',
            'categoria_id': sample_categories['cables'],
        },
        'small_items': {
            'prioridade': 30,
            'nome': 'Small Items Rule',
            'criterio_tamanho_max': 1.0,
            'categoria_id': sample_categories['small'],
        },
        'bulk_items': {
            'prioridade': 20,
            'nome': 'Bulk Items Rule',
            'criterio_quantidade_min': 100,
            'categoria_id': sample_categories['bulk'],
        },
        'combined': {
            'prioridade': 150,
            'nome': 'Combined Rule',
            'criterio_palavras_chave': 'monitor',
            'criterio_ncm': '8528*',
            'categoria_id': sample_categories['monitors'],
        },
    }

    inserted_rules = {}

    for key, rule_data in rules.items():
        cursor.execute("""
            INSERT INTO regras_de_classificacao (
                prioridade, nome, ativo,
                criterio_palavras_chave, criterio_ncm,
                criterio_tamanho_min, criterio_tamanho_max,
                criterio_quantidade_min, criterio_quantidade_max,
                categoria_id
            ) VALUES (
                %(prioridade)s, %(nome)s, true,
                %(criterio_palavras_chave)s, %(criterio_ncm)s,
                %(criterio_tamanho_min)s, %(criterio_tamanho_max)s,
                %(criterio_quantidade_min)s, %(criterio_quantidade_max)s,
                %(categoria_id)s
            )
            RETURNING id
        """, {
            'prioridade': rule_data.get('prioridade', 0),
            'nome': rule_data.get('nome', ''),
            'criterio_palavras_chave': rule_data.get('criterio_palavras_chave'),
            'criterio_ncm': rule_data.get('criterio_ncm'),
            'criterio_tamanho_min': rule_data.get('criterio_tamanho_min'),
            'criterio_tamanho_max': rule_data.get('criterio_tamanho_max'),
            'criterio_quantidade_min': rule_data.get('criterio_quantidade_min'),
            'criterio_quantidade_max': rule_data.get('criterio_quantidade_max'),
            'categoria_id': rule_data.get('categoria_id'),
        })

        rule_id = cursor.fetchone()[0]
        inserted_rules[key] = rule_id
        print(f"Inserted sample rule '{key}' with ID {rule_id} and categoria_id {rule_data['categoria_id']}")

    db_connection.commit()

    yield inserted_rules

    # Cleanup: Delete all sample rules after test
    cursor.execute("DELETE FROM regras_de_classificacao")
    db_connection.commit()
    cursor.close()


@pytest.fixture(scope='function')
def cleanup(db_connection):
    """Clean up database before and after test

    Clears audit logs, rules, and categories tables to ensure clean test state.

    Usage:
        def test_something(db_connection, cleanup):
            # Database starts clean
            # After test, database is cleaned again
    """
    cursor = db_connection.cursor()

    # Clean before test
    try:
        cursor.execute("TRUNCATE TABLE criterios_palavras_chave CASCADE")
    except:
        pass
    try:
        cursor.execute("TRUNCATE TABLE auditoria_classificacao CASCADE")
    except:
        pass
    try:
        cursor.execute("TRUNCATE TABLE regras_de_classificacao CASCADE")
    except:
        pass
    try:
        cursor.execute("TRUNCATE TABLE categorias CASCADE")
    except:
        pass
    # Reset status_classificacao in products_tabela if it exists
    try:
        cursor.execute("UPDATE produtos_tabela SET status_classificacao = 'pending', categoria_id = NULL")
    except:
        pass

    db_connection.commit()

    yield  # Test runs here

    # Clean after test
    try:
        cursor.execute("TRUNCATE TABLE criterios_palavras_chave CASCADE")
    except:
        pass
    try:
        cursor.execute("TRUNCATE TABLE auditoria_classificacao CASCADE")
    except:
        pass
    try:
        cursor.execute("TRUNCATE TABLE regras_de_classificacao CASCADE")
    except:
        pass
    try:
        cursor.execute("TRUNCATE TABLE categorias CASCADE")
    except:
        pass
    # Reset status_classificacao in products_tabela if it exists
    try:
        cursor.execute("UPDATE produtos_tabela SET status_classificacao = 'pending', categoria_id = NULL")
    except:
        pass

    db_connection.commit()

    cursor.close()


@pytest.fixture(scope='function')
def sample_products():
    """Provide sample products for classification testing

    Returns:
        dict: Dictionary with sample product data

    Usage:
        def test_evaluation(sample_products):
            product = sample_products['laptop']
            assert product['description'] == 'laptop computer'
    """
    return {
        'laptop': {
            'id': 'P001',
            'description': 'laptop computer',
            'ncm': '84713090',
            'size': 0.5,
            'quantity': 1,
        },
        'cable': {
            'id': 'P002',
            'description': 'USB cable',
            'ncm': '85444290',
            'size': 0.02,
            'quantity': 100,
        },
        'monitor': {
            'id': 'P003',
            'description': 'monitor display',
            'ncm': '85287000',
            'size': 0.3,
            'quantity': 1,
        },
        'small_item': {
            'id': 'P004',
            'description': 'small accessory',
            'ncm': '99999999',
            'size': 0.5,
            'quantity': 50,
        },
        'bulk_item': {
            'id': 'P005',
            'description': 'generic product',
            'ncm': '99999999',
            'size': 2.0,
            'quantity': 200,
        },
    }


# Markers for test organization
def pytest_configure(config):
    """Register pytest markers"""
    config.addinivalue_line(
        "markers", "unit: unit tests (test individual components)"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests (test components together)"
    )
    config.addinivalue_line(
        "markers", "contract: contract tests (test API contracts)"
    )
    config.addinivalue_line(
        "markers", "slow: slow tests (takes > 1 second)"
    )
    config.addinivalue_line(
        "markers", "db: tests that use database"
    )
