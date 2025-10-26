#!/usr/bin/env python3
"""
CLI script for batch product classification

Processes multiple products from database in a single operation.
Supports limiting, offset pagination, and optional database updates.

Usage:
    classify-batch --limit 500 --offset 0 --update-db
    classify-batch --limit 100 --where "ncm LIKE '8471%'" --dry-run
    classify-batch --stats
"""

import argparse
import sys
import json
import logging
from typing import Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from classifier.batch import BatchClassifier
from classifier.utils import get_db_connection, setup_logging


def format_summary(summary: dict) -> str:
    """Format batch summary for console output

    Args:
        summary: Batch processing summary dictionary

    Returns:
        str: Formatted summary text
    """
    lines = [
        "\n" + "=" * 60,
        "BATCH CLASSIFICATION SUMMARY",
        "=" * 60,
        f"Total Processed:     {summary['total_processed']:,} products",
        f"Total Matched:       {summary['total_matched']:,} products",
        f"Total No Match:      {summary['total_no_match']:,} products",
        f"Match Rate:          {summary['match_rate']:.1%}",
        f"Elapsed Time:        {summary['elapsed_time_ms']:,} ms ({summary['elapsed_time_ms'] / 1000:.2f}s)",
    ]

    # Add classification breakdown if any matches
    if summary['classifications']:
        lines.append("\nClassifications Breakdown:")
        for classification, count in sorted(summary['classifications'].items(),
                                          key=lambda x: x[1], reverse=True):
            lines.append(f"  - {classification:.<40} {count:>5} products")

    # Add no-match products if requested verbosely
    if summary['no_match_products']:
        lines.append(f"\nNo Match Products ({len(summary['no_match_products'])} total):")
        # Show first 10
        for product_id in summary['no_match_products'][:10]:
            lines.append(f"  - {product_id}")
        if len(summary['no_match_products']) > 10:
            lines.append(f"  ... and {len(summary['no_match_products']) - 10} more")

    lines.append("=" * 60 + "\n")
    return "\n".join(lines)


def format_statistics(stats: dict) -> str:
    """Format batch statistics for console output

    Args:
        stats: Statistics dictionary from get_batch_statistics()

    Returns:
        str: Formatted statistics text
    """
    lines = [
        "\n" + "=" * 60,
        "BATCH CLASSIFICATION STATISTICS",
        "=" * 60,
        f"Total Products:      {stats['total_products']:,}",
    ]

    # Show breakdown by status if available
    if 'by_status' in stats:
        lines.append(f"\nStatus Breakdown:")
        matched = stats['by_status'].get('matched', 0)
        pending = stats['by_status'].get('pending', 0)
        no_match = stats['by_status'].get('no_match', 0)
        unknown = stats['by_status'].get('unknown', 0)

        lines.append(f"  - Matched:       {matched:>6,} products")
        lines.append(f"  - Pending:       {pending:>6,} products (never attempted)")
        lines.append(f"  - No Match:      {no_match:>6,} products (attempted, no rules)")
        if unknown > 0:
            lines.append(f"  - Unknown:       {unknown:>6,} products")
    else:
        # Fallback for older statistics format
        lines.append(f"Classified:          {stats.get('matched', 0):,}")
        lines.append(f"Unclassified:        {stats.get('pending', 0):,}")

    lines.append(f"\nClassification Rate: {stats.get('classification_rate', 0):.1%}")
    lines.append("=" * 60 + "\n")
    return "\n".join(lines)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Batch classify products from database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process 500 products starting from offset 0
  classify-batch --limit 500

  # Process 100 products with dry-run (no database updates)
  classify-batch --limit 100 --dry-run

  # Process only 8471* NCM products
  classify-batch --where "ncm LIKE '8471%%'" --limit 500

  # Show overall classification statistics
  classify-batch --stats

  # Output results as JSON
  classify-batch --limit 500 --json
        """
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=500,
        help='Maximum number of products to process (default: 500)'
    )

    parser.add_argument(
        '--offset',
        type=int,
        default=0,
        help='Starting row offset for pagination (default: 0)'
    )

    parser.add_argument(
        '--where',
        type=str,
        default=None,
        help='Custom WHERE clause for filtering (e.g., "ncm LIKE \'8471%%\'")'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without updating database (simulation mode)'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show overall classification statistics instead of processing batch'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON instead of formatted text'
    )

    parser.add_argument(
        '--verbose',
        '-v',
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
    if args.json:
        logging.getLogger().setLevel(logging.CRITICAL)

    try:
        # Connect to database
        logger.info("Connecting to database...")
        db_conn = get_db_connection()

        # Create batch classifier
        batch = BatchClassifier(db_conn)

        # Show statistics mode
        if args.stats:
            logger.info("Fetching classification statistics...")
            stats = batch.get_batch_statistics()

            if args.json:
                print(json.dumps(stats, indent=2))
            else:
                print(format_statistics(stats))

            logger.info("Statistics retrieved successfully")
            return 0

        # Batch classification mode
        logger.info(
            f"Starting batch classification: "
            f"limit={args.limit}, offset={args.offset}, "
            f"update_db={not args.dry_run}"
        )

        result = batch.classify_batch(
            limit=args.limit,
            offset=args.offset,
            where_clause=args.where,
            update_db=not args.dry_run
        )

        # Output results
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_summary(result))

        logger.info(
            f"Batch classification completed: "
            f"processed={result['total_processed']}, "
            f"matched={result['total_matched']}, "
            f"no_match={result['total_no_match']}"
        )

        # Exit with appropriate code
        if result['total_matched'] == 0 and result['total_processed'] > 0:
            logger.warning("No products matched any rules in this batch")
            return 1

        return 0

    except KeyboardInterrupt:
        logger.warning("Batch classification interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Error during batch classification: {e}", exc_info=True)
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
