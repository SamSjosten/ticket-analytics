"""
Load mock ticket data into SQL Server using direct SQL INSERT statements.
Works with older ODBC drivers that have SQLAlchemy compatibility issues.
"""
import sys
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generate_mock_data import generate_tickets
import pyodbc
from config.database import DatabaseConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data_direct(num_tickets=500, days_back=90):
    """Load mock data using direct SQL INSERT statements."""

    logger.info(f"Generating {num_tickets} mock tickets ({days_back} days of history)...")
    df = generate_tickets(num_tickets=num_tickets, days_back=days_back)
    logger.info(f"Generated {len(df)} tickets")

    # Connect to SQL Server
    config = DatabaseConfig()
    conn_str = config.get_connection_string()

    logger.info("Connecting to SQL Server...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        # Clear existing data
        logger.info("Clearing existing data...")
        cursor.execute("DELETE FROM tickets")
        conn.commit()

        # Prepare INSERT statement
        insert_sql = """
        INSERT INTO tickets (
            ticket_id, created_date, resolved_date, category, priority,
            assigned_team, assigned_technician, status, resolution_time_hours,
            created_week, created_month, created_weekday
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        logger.info(f"Inserting {len(df)} tickets...")

        # Insert data row by row
        inserted = 0
        for idx, row in df.iterrows():
            try:
                # Handle NaN values for resolution_time_hours
                import pandas as pd
                resolution_hours = row['resolution_time_hours']
                if pd.isna(resolution_hours):
                    resolution_hours = None
                else:
                    resolution_hours = float(resolution_hours)

                cursor.execute(insert_sql, (
                    row['ticket_id'],
                    row['created_date'],
                    row['resolved_date'] if row['resolved_date'] else None,
                    row['category'],
                    row['priority'],
                    row['assigned_team'],
                    row['assigned_technician'],
                    row['status'],
                    resolution_hours,
                    None,  # created_week - will be calculated
                    None,  # created_month - will be calculated
                    None   # created_weekday - will be calculated
                ))
                inserted += 1

                # Commit every 100 rows
                if inserted % 100 == 0:
                    conn.commit()
                    logger.info(f"  Inserted {inserted}/{len(df)} tickets...")
            except Exception as e:
                logger.error(f"Error inserting row {idx}: {e}")
                logger.error(f"Row data: {row.to_dict()}")
                continue

        # Final commit
        conn.commit()
        logger.info(f"✅ Successfully inserted {inserted} tickets")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM tickets")
        count = cursor.fetchone()[0]
        logger.info(f"Total tickets in database: {count}")

        # Get date range
        cursor.execute("""
            SELECT
                MIN(created_date) as min_date,
                MAX(created_date) as max_date
            FROM tickets
        """)
        date_range = cursor.fetchone()
        logger.info(f"Date range: {date_range[0]} to {date_range[1]}")

    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
        logger.info("Connection closed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load mock data into SQL Server")
    parser.add_argument('--num-tickets', type=int, default=500, help='Number of tickets to generate')
    parser.add_argument('--days-back', type=int, default=90, help='Days of history to generate')

    args = parser.parse_args()

    load_data_direct(num_tickets=args.num_tickets, days_back=args.days_back)
