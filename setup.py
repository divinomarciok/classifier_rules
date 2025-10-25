"""
Setup configuration for classifier-rules package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="classifier-rules",
    version="0.1.0",
    author="Classifier Team",
    description="Data-driven rule engine for product classification with priority resolution and audit logging",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/classifier-rules",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.8",
    install_requires=[
        "psycopg2-binary>=2.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "pytest-mock>=3.6.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "classify-batch=classifier.cli.classify_batch:main",
            "classify-csv=classifier.cli.classify_csv:main",
            "export-batch=classifier.cli.export_batch:main",
        ],
    },
)
