"""
Category service for managing product categories

Provides category operations: list, get by ID, get by name, validate.
Implements a caching layer for performance.

Implements US1 (Category reference) and Constitutional Principle II (Code Simplicity)
"""

import logging
from typing import Optional, List, Dict, Any
from classifier.models import Category

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for managing categories and category operations

    Provides methods to:
    - Get all categories
    - Get category by ID
    - Get category by name
    - Validate category ID exists
    - Cache categories for performance

    Constitutional Principle I: Business-Driven Development
    """

    def __init__(self, db_connection):
        """Initialize category service

        Args:
            db_connection: Database connection for category queries
        """
        self.db_connection = db_connection
        self._category_cache = {}  # Cache for performance
        self._cache_loaded = False

    def get_all_categories(self) -> List[Category]:
        """Get all active categories from database

        Returns:
            list: List of Category objects

        Usage:
            >>> service = CategoryService(db_conn)
            >>> categories = service.get_all_categories()
            >>> for cat in categories:
            ...     print(f"{cat.id}: {cat.nome}")
        """
        try:
            cursor = self.db_connection.cursor()

            cursor.execute("""
                SELECT id, nome, descricao, ativo, data_criacao, data_atualizacao
                FROM categorias
                WHERE ativo = TRUE
                ORDER BY nome
            """)

            categories = []
            for row in cursor.fetchall():
                category = Category.from_db_row(row)
                categories.append(category)
                self._category_cache[category.id] = category

            cursor.close()

            logger.debug(f"Loaded {len(categories)} active categories")
            return categories

        except Exception as e:
            logger.error(f"Error loading categories: {e}")
            raise

    def get_category_by_id(self, categoria_id: int) -> Optional[Category]:
        """Get category by ID

        Checks cache first, then queries database if not cached.

        Args:
            categoria_id: Category ID to lookup

        Returns:
            Category: Category object if found, None otherwise

        Usage:
            >>> service = CategoryService(db_conn)
            >>> category = service.get_category_by_id(1)
            >>> if category:
            ...     print(f"Found: {category.nome}")
        """
        try:
            # Check cache first
            if categoria_id in self._category_cache:
                logger.debug(f"Category {categoria_id} found in cache")
                return self._category_cache[categoria_id]

            # Query database
            cursor = self.db_connection.cursor()

            cursor.execute("""
                SELECT id, nome, descricao, ativo, data_criacao, data_atualizacao
                FROM categorias
                WHERE id = %s
            """, (categoria_id,))

            row = cursor.fetchone()
            cursor.close()

            if row:
                category = Category.from_db_row(row)
                self._category_cache[categoria_id] = category
                logger.debug(f"Loaded category {categoria_id}: {category.nome}")
                return category

            logger.warning(f"Category {categoria_id} not found")
            return None

        except Exception as e:
            logger.error(f"Error loading category {categoria_id}: {e}")
            raise

    def get_category_by_name(self, nome: str) -> Optional[Category]:
        """Get category by name (exact match)

        Args:
            nome: Category name to lookup

        Returns:
            Category: Category object if found, None otherwise

        Usage:
            >>> service = CategoryService(db_conn)
            >>> category = service.get_category_by_name('ELETRÔNICOS')
            >>> if category:
            ...     print(f"Category ID: {category.id}")
        """
        try:
            cursor = self.db_connection.cursor()

            cursor.execute("""
                SELECT id, nome, descricao, ativo, data_criacao, data_atualizacao
                FROM categorias
                WHERE nome = %s AND ativo = TRUE
            """, (nome,))

            row = cursor.fetchone()
            cursor.close()

            if row:
                category = Category.from_db_row(row)
                self._category_cache[category.id] = category
                logger.debug(f"Found category by name: {nome} (id={category.id})")
                return category

            logger.warning(f"Category '{nome}' not found")
            return None

        except Exception as e:
            logger.error(f"Error loading category by name '{nome}': {e}")
            raise

    def validate_category_id(self, categoria_id: int) -> bool:
        """Validate that category ID exists

        Used to check FK constraints before inserting/updating.

        Args:
            categoria_id: Category ID to validate

        Returns:
            bool: True if category exists, False otherwise

        Usage:
            >>> service = CategoryService(db_conn)
            >>> if service.validate_category_id(1):
            ...     print("Category exists")
            ... else:
            ...     print("Invalid category ID")
        """
        try:
            category = self.get_category_by_id(categoria_id)
            exists = category is not None
            logger.debug(f"Category {categoria_id} validation: {exists}")
            return exists

        except Exception as e:
            logger.error(f"Error validating category {categoria_id}: {e}")
            return False

    def get_category_breakdown(self) -> Dict[int, str]:
        """Get mapping of category IDs to names for statistics

        Returns:
            dict: Mapping of {categoria_id: nome}

        Usage:
            >>> service = CategoryService(db_conn)
            >>> breakdown = service.get_category_breakdown()
            >>> print(breakdown)  # {1: 'ELETRÔNICOS', 2: 'LIVROS', ...}
        """
        try:
            categories = self.get_all_categories()
            breakdown = {cat.id: cat.nome for cat in categories}
            logger.debug(f"Category breakdown: {breakdown}")
            return breakdown

        except Exception as e:
            logger.error(f"Error getting category breakdown: {e}")
            return {}

    def clear_cache(self):
        """Clear the internal category cache

        Call this if categories are updated outside of this service.

        Usage:
            >>> service = CategoryService(db_conn)
            >>> # After external category update:
            >>> service.clear_cache()
            >>> categories = service.get_all_categories()  # Will reload
        """
        self._category_cache.clear()
        self._cache_loaded = False
        logger.debug("Category cache cleared")

    def __repr__(self) -> str:
        return f"CategoryService(cached={len(self._category_cache)} categories)"
