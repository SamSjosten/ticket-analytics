"""
Helper script to load ticket data into SQL Server.
"""
import sys
from pathlib import Path
import argparse
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db_connector import SQLServerConnector
from src.generate_mock_data import generate_tickets
from src.data_loader import load_tickets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_from_csv(csv_path: str, if_exists: str = 'replace'):
    """
    Load tickets from a CSV file into SQL Server.

    Args:
        csv_path: Path to CSV file
        if_exists: How to behave if table exists ('replace', 'append', 'fail')
    """
    logger.info(f"Loading tickets from CSV: {csv_path}")

    # Load CSV data
    df = load_tickets(filepath=Path(csv_path), source="file")
    logger.info(f"Loaded {len(df)} tickets from CSV")

    # Connect to SQL Server
    connector = SQLServerConnector()

    # Test connection
    success, message = connector.test_connection()
    if not success:
        logger.error(f"Connection failed: {message}")
        return False

    logger.info("Connection successful")

    # Create table if needed
    if if_exists == 'replace':
        logger.info("Creating/recreating tickets table...")
        connector.create_tickets_table()

    # Insert data
    logger.info(f"Inserting data (mode: {if_exists})...")
    try:
        connector.insert_tickets(df, if_exists=if_exists)
        logger.info(f"✅ Successfully loaded {len(df)} tickets into SQL Server")

        # Verify
        info = connector.get_table_info()
        logger.info(f"Table now contains {info['row_count']} total records")
        logger.info(f"Date range: {info['min_date']} to {info['max_date']}")

        return True
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")
        return False


def generate_and_load(num_tickets: int = 500, days_back: int = 90, if_exists: str = 'replace'):
    """
    Generate mock data and load into SQL Server.

    Args:
        num_tickets: Number of tickets to generate
        days_back: How many days of history to generate
        if_exists: How to behave if table exists ('replace', 'append', 'fail')
    """
    logger.info(f"Generating {num_tickets} mock tickets ({days_back} days of history)...")

    # Generate mock data
    df = generate_tickets(num_tickets=num_tickets, days_back=days_back)
    logger.info(f"Generated {len(df)} tickets")

    # Connect to SQL Server
    connector = SQLServerConnector()

    # Test connection
    success, message = connector.test_connection()
    if not success:
        logger.error(f"Connection failed: {message}")
        return False

    logger.info("Connection successful")

    # Create table if needed
    if if_exists == 'replace':
        logger.info("Creating/recreating tickets table...")
        connector.create_tickets_table()

    # Insert data
    logger.info(f"Inserting data (mode: {if_exists})...")
    try:
        connector.insert_tickets(df, if_exists=if_exists)
        logger.info(f"✅ Successfully loaded {len(df)} tickets into SQL Server")

        # Verify
        info = connector.get_table_info()
        logger.info(f"Table now contains {info['row_count']} total records")
        logger.info(f"Date range: {info['min_date']} to {info['max_date']}")

        return True
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")
        return False


def test_connection():
    """Test SQL Server connection."""
    logger.info("Testing SQL Server connection...")

    connector = SQLServerConnector()
    success, message = connector.test_connection()

    if success:
        logger.info(f"✅ {message}")

        try:
            info = connector.get_table_info()
            logger.info(f"\nDatabase Information:")
            logger.info(f"  Table: {connector.config.TICKETS_TABLE}")
            logger.info(f"  Records: {info['row_count']:,}")
            logger.info(f"  Date Range: {info['min_date']} to {info['max_date']}")
            logger.info(f"\n  Columns:")
            for col in info['columns']:
                logger.info(f"    - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
        except Exception as e:
            logger.warning(f"Could not retrieve table info: {e}")

        return True
    else:
        logger.error(f"❌ {message}")
        logger.info("\nTroubleshooting:")
        logger.info("1. Ensure .env file is configured correctly")
        logger.info("2. Verify SQL Server is running and accessible")
        logger.info("3. Check firewall settings")
        logger.info("4. Verify ODBC driver is installed")
        return False


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Load ticket data into SQL Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection
  python scripts/load_to_sql.py --test

  # Generate and load mock data
  python scripts/load_to_sql.py --generate --num-tickets 1000

  # Load from CSV file
  python scripts/load_to_sql.py --csv data/raw/tickets.csv

  # Append data instead of replacing
  python scripts/load_to_sql.py --generate --mode append
        """
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test SQL Server connection'
    )

    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate and load mock data'
    )

    parser.add_argument(
        '--csv',
        type=str,
        help='Load data from CSV file'
    )

    parser.add_argument(
        '--num-tickets',
        type=int,
        default=500,
        help='Number of tickets to generate (default: 500)'
    )

    parser.add_argument(
        '--days-back',
        type=int,
        default=90,
        help='Days of history to generate (default: 90)'
    )

    parser.add_argument(
        '--mode',
        type=str,
        choices=['replace', 'append', 'fail'],
        default='replace',
        help='How to handle existing table (default: replace)'
    )

    args = parser.parse_args()

    # If no arguments, show help
    if not any([args.test, args.generate, args.csv]):
        parser.print_help()
        return

    # Test connection
    if args.test:
        test_connection()
        return

    # Generate and load
    if args.generate:
        success = generate_and_load(
            num_tickets=args.num_tickets,
            days_back=args.days_back,
            if_exists=args.mode
        )
        sys.exit(0 if success else 1)

    # Load from CSV
    if args.csv:
        success = load_from_csv(
            csv_path=args.csv,
            if_exists=args.mode
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
