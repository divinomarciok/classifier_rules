"""
CSV classification service - Process CSV files for product classification

Implements US5 (CSV Classification) - Import, classify, and export CSV data
"""

import csv
import logging
import time
from typing import Dict, List, Any, Optional, TextIO
from datetime import datetime
from pathlib import Path

from classifier.engine import RuleEngine
from classifier.models import Product

logger = logging.getLogger(__name__)


class CSVClassifier:
    """Process CSV files for product classification

    Handles importing product data from CSV, classifying products,
    and exporting results to new CSV files.

    Constitutional Principle I: Business-Driven Development
    """

    def __init__(self, db_connection):
        """Initialize CSV classifier

        Args:
            db_connection: Database connection for rule queries
        """
        self.db_connection = db_connection
        self.engine = RuleEngine(db_connection)

    def classify_csv(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        skip_classified: bool = False,
        encoding: str = 'utf-8',
        delimiter: str = ',',
        batch_size: int = 1000,
        update_db: bool = False
    ) -> Dict[str, Any]:
        """Classify products from CSV file

        Reads products from CSV, evaluates each against rules,
        optionally updates database, and exports results.

        Args:
            input_file: Path to input CSV file
            output_file: Path for output CSV (default: input_file_classified.csv)
            skip_classified: Skip rows where classification column exists (default: False)
            encoding: CSV file encoding (default: utf-8)
            delimiter: CSV delimiter character (default: ',')
            batch_size: Products per batch (default: 1000)
            update_db: Whether to update database with classifications (default: False)

        Returns:
            dict: Classification summary with:
                - total_processed: Number of products evaluated
                - total_matched: Count of products that matched a rule
                - total_no_match: Count of products with no match
                - match_rate: Percentage of matched products (0.0-1.0)
                - classifications: Dict of classification -> count
                - elapsed_time_ms: Total processing time
                - no_match_products: List of unclassified product IDs
                - rows_skipped: Rows skipped due to errors or filters
                - output_file: Path to generated output CSV

        Implementation Plan:
            1. Validate input CSV file exists and is readable
            2. Read CSV headers and validate required columns
            3. Process products in batches
            4. For each product, call engine.evaluate()
            5. Write results to output CSV
            6. Optionally update database
            7. Return comprehensive summary
        """
        try:
            start_time = time.time()
            logger.info(
                f"Starting CSV classification: input={input_file}, "
                f"skip_classified={skip_classified}, batch_size={batch_size}"
            )

            # 1. Validate input file
            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")

            # 2. Determine output file
            if output_file is None:
                output_path = input_path.parent / f"{input_path.stem}_classified.csv"
            else:
                output_path = Path(output_file)

            # 3. Process CSV
            results = self._process_csv_file(
                input_path,
                output_path,
                skip_classified,
                encoding,
                delimiter,
                update_db
            )

            # 4. Compute statistics
            elapsed_ms = (time.time() - start_time) * 1000

            matched_count = len([r for r in results['classifications_list'] if r['result'].success])
            no_match_count = len([r for r in results['classifications_list'] if not r['result'].success])
            match_rate = matched_count / results['total_rows'] if results['total_rows'] > 0 else 0.0

            # Build classification summary
            classifications = {}
            no_match_products = []
            for item in results['classifications_list']:
                if item['result'].success:
                    classification = item['result'].classification
                    classifications[classification] = classifications.get(classification, 0) + 1
                else:
                    no_match_products.append(item['product_id'])

            summary = {
                'total_processed': results['total_rows'],
                'total_matched': matched_count,
                'total_no_match': no_match_count,
                'match_rate': match_rate,
                'classifications': classifications,
                'elapsed_time_ms': int(elapsed_ms),
                'no_match_products': no_match_products,
                'rows_skipped': results['rows_skipped'],
                'output_file': str(output_path),
            }

            logger.info(
                f"CSV classification complete: "
                f"processed={results['total_rows']}, "
                f"matched={matched_count}, "
                f"no_match={no_match_count}, "
                f"skipped={results['rows_skipped']}, "
                f"time={elapsed_ms:.0f}ms, "
                f"output={output_path}"
            )

            return summary

        except Exception as e:
            logger.error(f"Error during CSV classification: {e}")
            raise

    def _process_csv_file(
        self,
        input_path: Path,
        output_path: Path,
        skip_classified: bool,
        encoding: str,
        delimiter: str,
        update_db: bool
    ) -> Dict[str, Any]:
        """Process CSV file: read, classify, write results

        Args:
            input_path: Input CSV file path
            output_path: Output CSV file path
            skip_classified: Skip already classified rows
            encoding: File encoding
            delimiter: CSV delimiter
            update_db: Update database flag

        Returns:
            dict: Processing results with classifications_list, total_rows, rows_skipped
        """
        classifications_list = []
        rows_skipped = 0
        total_rows = 0

        try:
            with open(input_path, 'r', encoding=encoding, newline='') as infile, \
                 open(output_path, 'w', encoding=encoding, newline='') as outfile:

                reader = csv.DictReader(infile, delimiter=delimiter)

                # Validate headers
                if reader.fieldnames is None:
                    raise ValueError("CSV file is empty or has no headers")

                required_fields = {'id', 'description', 'ncm'}
                if not required_fields.issubset(set(reader.fieldnames)):
                    missing = required_fields - set(reader.fieldnames)
                    raise ValueError(f"CSV missing required columns: {missing}")

                # Prepare output headers (add classification columns if not present)
                output_headers = list(reader.fieldnames)
                if 'classification' not in output_headers:
                    output_headers.append('classification')
                if 'data_classificacao' not in output_headers:
                    output_headers.append('data_classificacao')

                writer = csv.DictWriter(outfile, fieldnames=output_headers, delimiter=delimiter)
                writer.writeheader()

                # Process rows
                for row_num, row in enumerate(reader, start=2):  # start=2 (line 1 is header)
                    try:
                        total_rows += 1

                        # Skip if already classified and skip_classified flag is set
                        if skip_classified and row.get('classification'):
                            rows_skipped += 1
                            writer.writerow(row)
                            continue

                        # Validate required fields
                        if not all(row.get(field) for field in ['id', 'description', 'ncm']):
                            logger.warning(f"Row {row_num}: Missing required fields, skipping")
                            rows_skipped += 1
                            writer.writerow(row)
                            continue

                        # Create product from row
                        product = self._row_to_product(row)

                        # Classify product
                        result = self.engine.evaluate(product)

                        # Store result
                        classifications_list.append({
                            'product_id': product.id,
                            'result': result,
                            'row': row
                        })

                        # Update row with classification
                        if result.success:
                            row['classification'] = result.classification
                            row['data_classificacao'] = datetime.now().isoformat()

                            # Update database if requested
                            if update_db:
                                self._update_product_classification(
                                    product.id,
                                    result.classification
                                )
                        else:
                            row['classification'] = 'NO_MATCH'
                            row['data_classificacao'] = datetime.now().isoformat()

                        # Write row
                        writer.writerow(row)

                    except Exception as e:
                        logger.error(f"Error processing row {row_num}: {e}")
                        rows_skipped += 1
                        writer.writerow(row)

            logger.debug(f"Processed {total_rows} rows, skipped {rows_skipped}")

            return {
                'classifications_list': classifications_list,
                'total_rows': total_rows - rows_skipped,  # Don't count skipped rows in total
                'rows_skipped': rows_skipped
            }

        except Exception as e:
            logger.error(f"Error processing CSV file: {e}")
            raise

    def _row_to_product(self, row: dict) -> Product:
        """Convert CSV row to Product object

        Handles flexible CSV schema with optional fields.

        Args:
            row: CSV row dictionary

        Returns:
            Product: Product object for evaluation
        """
        product_id = row.get('id', '').strip()
        description = row.get('description', '').strip()
        ncm = row.get('ncm', '').strip()

        # Extract optional fields
        size = row.get('size')
        if size:
            try:
                size = float(size)
            except (ValueError, TypeError):
                size = None

        quantity = row.get('quantity')
        if quantity:
            try:
                quantity = float(quantity)
            except (ValueError, TypeError):
                quantity = None

        categoria = row.get('category') or row.get('categoria')

        # Create product with flexible schema
        product = Product(
            id=product_id,
            description=description,
            ncm=ncm,
            size=size,
            quantity=quantity,
            category=categoria
        )

        return product

    def _update_product_classification(self, product_id: str, classification: str) -> bool:
        """Update database with classification from CSV

        Args:
            product_id: Product ID to update
            classification: Classification result

        Returns:
            bool: True if successful
        """
        try:
            cursor = self.db_connection.cursor()

            cursor.execute(
                "UPDATE produtos_tabela SET categoria = %s, data_classificacao = %s WHERE id = %s",
                (classification, datetime.now(), product_id)
            )

            self.db_connection.commit()
            cursor.close()

            logger.debug(f"Updated product {product_id} with classification {classification}")
            return True

        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            self.db_connection.rollback()
            raise

    def validate_csv(
        self,
        input_file: str,
        encoding: str = 'utf-8',
        delimiter: str = ','
    ) -> Dict[str, Any]:
        """Validate CSV file for classification

        Checks file format, headers, and data quality.

        Args:
            input_file: Path to CSV file
            encoding: File encoding
            delimiter: CSV delimiter

        Returns:
            dict: Validation results with:
                - valid: True if CSV is valid
                - headers: Column names
                - row_count: Number of data rows
                - issues: List of validation issues
                - missing_fields: Rows with missing required fields
        """
        try:
            input_path = Path(input_file)
            issues = []
            missing_fields = []
            row_count = 0

            with open(input_path, 'r', encoding=encoding, newline='') as f:
                reader = csv.DictReader(f, delimiter=delimiter)

                if reader.fieldnames is None:
                    return {
                        'valid': False,
                        'headers': [],
                        'row_count': 0,
                        'issues': ['CSV file is empty or has no headers'],
                        'missing_fields': []
                    }

                required_fields = {'id', 'description', 'ncm'}
                if not required_fields.issubset(set(reader.fieldnames)):
                    missing = required_fields - set(reader.fieldnames)
                    issues.append(f"Missing required columns: {missing}")

                for row_num, row in enumerate(reader, start=2):
                    row_count += 1

                    # Check required fields
                    if not all(row.get(field) for field in ['id', 'description', 'ncm']):
                        missing_fields.append(row_num)

            return {
                'valid': len(issues) == 0 and len(missing_fields) == 0,
                'headers': list(reader.fieldnames) if reader.fieldnames else [],
                'row_count': row_count,
                'issues': issues,
                'missing_fields': missing_fields
            }

        except Exception as e:
            return {
                'valid': False,
                'headers': [],
                'row_count': 0,
                'issues': [str(e)],
                'missing_fields': []
            }
