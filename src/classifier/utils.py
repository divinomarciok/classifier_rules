"""
Application utilities: Configuration loading and database connection management

Implements FR-010 (Configuration management)
Implements Constitutional Principle II (Code Simplicity)
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

import psycopg2
from psycopg2 import OperationalError, DatabaseError as PgDatabaseError

from classifier import ConfigError, DatabaseError


# Configure logging module-level
logger = logging.getLogger(__name__)


def setup_logging(log_level: str = 'INFO') -> None:
    """Configure application-wide logging

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Usage:
        >>> setup_logging('DEBUG')  # Enable debug logging
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Format: [TIMESTAMP] [LEVEL] [MODULE] Message
    log_format = '[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s'

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(console_handler)

    # Optional: File handler for persistent logs
    log_dir = Path(__file__).parent.parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    try:
        file_handler = logging.FileHandler(log_dir / 'classifier.log')
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not configure file logging: {e}")

    logger.debug(f"Logging configured at level {log_level}")


class Config:
    """Application configuration loaded from environment variables"""

    def __init__(self):
        """Load configuration from .env file and environment variables"""
        self._load_from_env()

    def _load_from_env(self):
        """Load configuration from environment"""
        # Load from .env file if it exists
        env_file = Path(__file__).parent.parent.parent / '.env'
        if env_file.exists():
            self._load_env_file(env_file)

    @staticmethod
    def _load_env_file(env_path: Path):
        """Load environment variables from .env file"""
        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
        except IOError as e:
            logger.warning(f"Could not load {env_path}: {e}")

    @staticmethod
    def get_db_config() -> Dict[str, Any]:
        """Get database configuration from environment"""
        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']

        # Check required variables
        missing = [var for var in required_vars if var not in os.environ]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please set them in .env file or environment."
            )

        return {
            'host': os.environ.get('DB_HOST'),
            'database': os.environ.get('DB_NAME'),
            'user': os.environ.get('DB_USER'),
            'password': os.environ.get('DB_PASSWORD'),
            'port': int(os.environ.get('DB_PORT', 5432)),
            'connect_timeout': int(os.environ.get('DB_CONNECTION_TIMEOUT', 30)),
        }

    @staticmethod
    def get_app_config() -> Dict[str, Any]:
        """Get application configuration"""
        return {
            'env': os.environ.get('APP_ENV', 'production'),
            'log_level': os.environ.get('APP_LOG_LEVEL', 'INFO'),
            'enable_caching': os.environ.get('ENABLE_RULE_CACHING', 'true').lower() == 'true',
            'enable_audit': os.environ.get('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true',
        }


def load_config() -> Dict[str, Any]:
    """Load and return full application configuration

    Returns:
        dict: Configuration dictionary with 'db' and 'app' keys

    Raises:
        ConfigError: If required configuration is missing or invalid
    """
    config = Config()
    return {
        'db': config.get_db_config(),
        'app': config.get_app_config(),
    }


def get_db_connection(db_config: Optional[Dict[str, Any]] = None):
    """Create and return a database connection

    Args:
        db_config: Database configuration dict. If None, loads from environment.

    Returns:
        psycopg2.connection: Database connection object

    Raises:
        ConfigError: If configuration is missing
        DatabaseError: If connection fails

    Usage:
        >>> conn = get_db_connection()
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT * FROM regras_de_classificacao")
    """
    try:
        if db_config is None:
            config = Config()
            db_config = config.get_db_config()

        logger.info(f"Connecting to database {db_config['database']} at {db_config['host']}")

        conn = psycopg2.connect(**db_config)
        logger.info("Database connection successful")
        return conn

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except (OperationalError, PgDatabaseError) as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseError(
            f"Could not connect to database {db_config.get('database')} at {db_config.get('host')}. "
            f"Check DB_HOST, DB_NAME, DB_USER, DB_PASSWORD in .env file."
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error during database connection: {e}")
        raise DatabaseError(f"Unexpected database error: {e}") from e


def init_database(db_config: Optional[Dict[str, Any]] = None) -> bool:
    """Initialize database by executing all migration files in order

    Creates all required tables (regras_de_classificacao, auditoria_classificacao, criterios_palavras_chave)

    Args:
        db_config: Database configuration dict. If None, loads from environment.

    Returns:
        bool: True if all migrations successful, False otherwise

    Raises:
        DatabaseError: If any migration fails

    Usage:
        >>> init_database()
        >>> # Tables now exist in database
    """
    try:
        conn = get_db_connection(db_config)
        cursor = conn.cursor()

        # Find and execute migration files in order
        migrations_dir = Path(__file__).parent.parent.parent / 'migrations'
        migration_files = sorted([
            f for f in migrations_dir.glob('*.sql')
            if f.name.startswith(('001_', '002_', '003_', '004_', '005_', '006_'))
        ])

        if not migration_files:
            logger.warning(f"No migration files found in {migrations_dir}")
            return False

        logger.info(f"Executing {len(migration_files)} migrations...")

        for migration_file in migration_files:
            logger.info(f"  Executing: {migration_file.name}")

            try:
                with open(migration_file) as f:
                    sql = f.read()
                    cursor.execute(sql)
                    conn.commit()
                    logger.info(f"  ✓ {migration_file.name} completed")
            except Exception as e:
                conn.rollback()
                logger.error(f"  ✗ {migration_file.name} failed: {e}")
                raise DatabaseError(
                    f"Migration {migration_file.name} failed: {e}"
                ) from e

        cursor.close()
        conn.close()

        logger.info("✓ All migrations completed successfully")
        return True

    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise DatabaseError(f"Database initialization failed: {e}") from e


def verify_database_connection(db_config: Optional[Dict[str, Any]] = None) -> bool:
    """Verify that database is accessible and migrations are applied

    Args:
        db_config: Database configuration dict. If None, loads from environment.

    Returns:
        bool: True if database is accessible and tables exist

    Usage:
        >>> if verify_database_connection():
        ...     print("Database is ready")
    """
    try:
        conn = get_db_connection(db_config)
        cursor = conn.cursor()

        # Check if required tables exist
        required_tables = [
            'categorias',
            'regras_de_classificacao',
            'auditoria_classificacao',
            'criterios_palavras_chave',
        ]

        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}

        missing_tables = [t for t in required_tables if t not in existing_tables]

        cursor.close()
        conn.close()

        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
            return False

        logger.info("✓ Database verification successful - all required tables exist")
        return True

    except DatabaseError:
        logger.error("Database verification failed - cannot connect")
        return False
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False


if __name__ == '__main__':
    # Quick test of utilities
    logging.basicConfig(level=logging.INFO)

    print("Testing configuration loading...")
    try:
        config = load_config()
        print(f"✓ Configuration loaded: {list(config.keys())}")
    except ConfigError as e:
        print(f"✗ Configuration error: {e}")
