"""
Classifier v2: Data-Driven Rule Engine for Product Classification

Package: classifier
Version: 0.1.0

Core exception classes and package initialization.
"""

__version__ = "0.1.0"
__author__ = "Classifier Team"


# Exception Classes (per FR-007 and error handling strategy)

class ClassifierException(Exception):
    """Base exception for all classifier-related errors"""
    pass


class ConfigError(ClassifierException):
    """Raised when configuration is invalid or missing"""
    pass


class DatabaseError(ClassifierException):
    """Raised when database operations fail"""
    pass


class ProductError(ClassifierException):
    """Raised when product data is invalid"""
    pass


class EvaluationError(ClassifierException):
    """Raised when rule evaluation fails"""
    pass


class ValidationError(ClassifierException):
    """Raised when data validation fails"""
    pass


class ProcessingError(ClassifierException):
    """Raised when CSV or batch processing fails"""
    pass


# Export main components (will be populated after implementation)
__all__ = [
    'RuleEngine',
    'AuditLog',
    'Matcher',
    'Evaluator',
    'ConfigError',
    'DatabaseError',
    'ProductError',
    'EvaluationError',
    'ValidationError',
    'ProcessingError',
]
