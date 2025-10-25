#!/usr/bin/env python3
"""
CLI script for CSV-based product classification

Processes a CSV file with product data, classifies all products,
and exports results to a new CSV file with classifications.

Usage:
    classify-csv input.csv --output output.csv
    classify-csv products.csv --skip-classified
    classify-csv data.csv --validate
    classify-csv large_file.csv --batch-size 2000 --update-db
"""

import argparse
import sys
import json
import logging
from typing import Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from classifier.csv_classifier import CSVClassifier
from classifier.utils import get_db_connection, setup_logging


def format_csv_summary(summary: dict) -> str:
    """Format CSV classification summary for console output

    Args:
        summary: CSV processing summary dictionary

    Returns:
        str: Formatted summary text
    """
    lines = [
        "\n" + "=" * 70,
        "CSV CLASSIFICATION SUMMARY",
        "=" * 70,
        f"Input File:          (processed in batch)",
        f"Output File:         {summary['output_file']}",
        f"Total Processed:     {summary['total_processed']:,} products",
        f"Total Matched:       {summary['total_matched']:,} products",
        f"Total No Match:      {summary['total_no_match']:,} products",
        f"Match Rate:          {summary['match_rate']:.1%}",
        f"Rows Skipped:        {summary['rows_skipped']:,}",
        f"Elapsed Time:        {summary['elapsed_time_ms']:,} ms ({summary['elapsed_time_ms'] / 1000:.2f}s)",
    ]

    # Add classification breakdown if any matches
    if summary['classifications']:
        lines.append("\nClassifications Breakdown:")
        for classification, count in sorted(summary['classifications'].items(),
                                          key=lambda x: x[1], reverse=True):
            lines.append(f"  - {classification:.<50} {count:>5} products")

    # Add no-match products summary
    if summary['no_match_products']:
        lines.append(f"\nNo Match Products: {len(summary['no_match_products'])} total")
        if len(summary['no_match_products']) <= 10:
            for product_id in summary['no_match_products']:
                lines.append(f"  - {product_id}")
        else:
            for product_id in summary['no_match_products'][:10]:
                lines.append(f"  - {product_id}")
            lines.append(f"  ... and {len(summary['no_match_products']) - 10} more")

    lines.append("=" * 70 + "\n")
    return "\n".join(lines)


def format_csv_validation(validation: dict) -> str:
    """Format CSV validation results for console output

    Args:
        validation: Validation results dictionary

    Returns:
        str: Formatted validation text
    """
    lines = [
        "\n" + "=" * 70,
        "CSV VALIDATION RESULTS",
        "=" * 70,
    ]

    if validation['valid']:
        lines.append("✓ CSV file is valid and ready for classification")
    else:
        lines.append("✗ CSV file has issues - see details below")

    lines.append(f"\nColumns Found:       {', '.join(validation['headers'])}")
    lines.append(f"Data Rows:           {validation['row_count']}")

    if validation['issues']:
        lines.append("\nIssues Found:")
        for issue in validation['issues']:
            lines.append(f"  - {issue}")

    if validation['missing_fields']:
        lines.append(f"\nRows with Missing Fields: {len(validation['missing_fields'])} rows")
        if len(validation['missing_fields']) <= 10:
            for row_num in validation['missing_fields']:
                lines.append(f"  - Row {row_num}")
        else:
            for row_num in validation['missing_fields'][:10]:
                lines.append(f"  - Row {row_num}")
            lines.append(f"  ... and {len(validation['missing_fields']) - 10} more")

    lines.append("=" * 70 + "\n")
    return "\n".join(lines)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Classify products from CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process CSV and save output
  classify-csv products.csv --output classified.csv

  # Skip already classified products
  classify-csv products.csv --skip-classified

  # Validate CSV before processing
  classify-csv products.csv --validate

  # Process with custom batch size
  classify-csv large_file.csv --batch-size 2000

  # Update database with classifications
  classify-csv products.csv --update-db

  # Process with UTF-8 encoding (default)
  classify-csv products_utf8.csv --encoding utf-8

  # Process with different encoding
  classify-csv products_latin1.csv --encoding latin-1

  # Output results as JSON
  classify-csv products.csv --json
        """
    )

    parser.add_argument(
        'input_file',
        help='Path to input CSV file'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Path for output CSV file (default: input_classified.csv)'
    )

    parser.add_argument(
        '--skip-classified',
        action='store_true',
        help='Skip rows that are already classified'
    )

    parser.add_argument(
        '--encoding',
        type=str,
        default='utf-8',
        help='CSV file encoding (default: utf-8)'
    )

    parser.add_argument(
        '--delimiter',
        type=str,
        default=',',
        help='CSV delimiter character (default: comma)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Products per batch for processing (default: 1000)'
    )

    parser.add_argument(
        '--update-db',
        action='store_true',
        help='Update database with classifications'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate CSV format without processing'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(log_level=args.log_level if args.verbose else 'INFO')
    logger = logging.getLogger(__name__)

    # Suppress logging if outputting JSON
    if args.json and not args.validate:
        logging.getLogger().setLevel(logging.CRITICAL)

    try:
        # Connect to database
        logger.info("Connecting to database...")
        db_conn = get_db_connection()

        # Create CSV classifier
        classifier = CSVClassifier(db_conn)

        # Validation mode
        if args.validate:
            logger.info(f"Validating CSV file: {args.input_file}")
            validation = classifier.validate_csv(
                args.input_file,
                encoding=args.encoding,
                delimiter=args.delimiter
            )

            if args.json:
                print(json.dumps(validation, indent=2))
            else:
                print(format_csv_validation(validation))

            return 0 if validation['valid'] else 1

        # Classification mode
        logger.info(
            f"Starting CSV classification: "
            f"input={args.input_file}, "
            f"skip_classified={args.skip_classified}, "
            f"batch_size={args.batch_size}, "
            f"update_db={args.update_db}"
        )

        result = classifier.classify_csv(
            input_file=args.input_file,
            output_file=args.output,
            skip_classified=args.skip_classified,
            encoding=args.encoding,
            delimiter=args.delimiter,
            batch_size=args.batch_size,
            update_db=args.update_db
        )

        # Output results
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_csv_summary(result))

        logger.info(
            f"CSV classification completed: "
            f"processed={result['total_processed']}, "
            f"matched={result['total_matched']}, "
            f"no_match={result['total_no_match']}, "
            f"output={result['output_file']}"
        )

        # Exit with appropriate code
        if result['total_matched'] == 0 and result['total_processed'] > 0:
            logger.warning("No products matched any rules in this CSV")
            return 1

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        if args.json:
            print(json.dumps({
                'error': str(e),
                'type': 'FileNotFoundError'
            }, indent=2))
        else:
            print(f"\nERROR: {e}\n", file=sys.stderr)
        return 1

    except ValueError as e:
        logger.error(f"Invalid CSV format: {e}")
        if args.json:
            print(json.dumps({
                'error': str(e),
                'type': 'ValueError'
            }, indent=2))
        else:
            print(f"\nERROR: {e}\n", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        logger.warning("CSV classification interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Error during CSV classification: {e}", exc_info=True)
        if args.json:
            print(json.dumps({
                'error': str(e),
                'type': type(e).__name__
            }, indent=2))
        else:
            print(f"\nERROR: {e}\n", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
