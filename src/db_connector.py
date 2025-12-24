"""
SQL Server database connector for ticket data.
"""
import logging
from typing import Optional
from datetime import datetime

import pandas as pd
import pyodbc
from sqlalchemy import create_engine, text

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import DatabaseConfig

logger = logging.getLogger(__name__)


class SQLServerConnector:
    """Connector for SQL Server database operations."""

    def __init__(self):
        """Initialize the SQL Server connector."""
        self.config = DatabaseConfig
        self.connection = None
        self.engine = None

    def test_connection(self) -> tuple[bool, str]:
        """
        Test the database connection.

        Returns:
            Tuple of (success, message)
        """
        # First validate configuration
        is_valid, msg = self.config.validate_config()
        if not is_valid:
            return False, f"Configuration error: {msg}"

        try:
            conn_str = self.config.get_connection_string()
            conn = pyodbc.connect(conn_str)
            conn.close()
            return True, "Connection successful"
        except pyodbc.Error as e:
            error_msg = str(e)
            logger.error(f"Connection failed: {error_msg}")
            return False, f"Connection failed: {error_msg}"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error: {error_msg}")
            return False, f"Unexpected error: {error_msg}"

    def connect(self):
        """Establish connection to SQL Server."""
        try:
            conn_str = self.config.get_connection_string()
            self.connection = pyodbc.connect(conn_str)
            logger.info("Connected to SQL Server")
        except pyodbc.Error as e:
            logger.error(f"Failed to connect: {e}")
            raise

    def disconnect(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from SQL Server")

    def get_engine(self):
        """
        Get SQLAlchemy engine for pandas integration.

        Returns:
            SQLAlchemy engine
        """
        if not self.engine:
            url = self.config.get_sqlalchemy_url()
            # Use fast_executemany for better performance and to avoid parameter binding issues
            self.engine = create_engine(
                url,
                fast_executemany=True,
                use_setinputsizes=False  # Avoid pyodbc parameter precision issues
            )
            logger.info("Created SQLAlchemy engine with fast_executemany=True")
        return self.engine

    def load_tickets(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load ticket data from SQL Server with parameterized queries.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            status_filter: Optional status filter

        Returns:
            DataFrame with ticket data
        """
        # Build query with placeholders
        query = f"SELECT * FROM {self.config.TICKETS_TABLE}"
        conditions = []
        params = {}

        if start_date:
            conditions.append("created_date >= :start_date")
            params['start_date'] = start_date.strftime('%Y-%m-%d')

        if end_date:
            conditions.append("created_date <= :end_date")
            params['end_date'] = end_date.strftime('%Y-%m-%d')

        if status_filter:
            conditions.append("status = :status_filter")
            params['status_filter'] = status_filter

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_date DESC"

        logger.info(f"Executing query with params: {params}")

        try:
            engine = self.get_engine()
            # Use parameterized query with SQLAlchemy text()
            df = pd.read_sql(text(query), engine, params=params)
            logger.info(f"Loaded {len(df)} tickets from SQL Server")
            return df
        except Exception as e:
            logger.error(f"Failed to load tickets: {e}")
            raise

    def execute_query(self, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        """
        Execute a custom SQL query and return results as DataFrame.

        WARNING: Use parameterized queries to prevent SQL injection.
        Pass user-controlled values via the params dict, not by string formatting.

        Args:
            query: SQL query to execute (use :param_name for placeholders)
            params: Optional dictionary of parameters for the query

        Returns:
            DataFrame with query results

        Example:
            # Safe - using parameters
            execute_query("SELECT * FROM table WHERE id = :id", {'id': user_id})

            # UNSAFE - DO NOT DO THIS
            execute_query(f"SELECT * FROM table WHERE id = {user_id}")
        """
        try:
            engine = self.get_engine()
            if params:
                df = pd.read_sql(text(query), engine, params=params)
            else:
                # Log warning if query looks like it might have user input
                if any(char in query for char in ["'", '"']) and "WHERE" in query.upper():
                    logger.warning("Query contains quotes and WHERE clause - ensure it's not vulnerable to SQL injection")
                df = pd.read_sql(text(query), engine)
            logger.info(f"Query returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            raise

    def get_table_info(self) -> dict:
        """
        Get information about the tickets table.

        Returns:
            Dictionary with table metadata
        """
        try:
            engine = self.get_engine()

            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {self.config.TICKETS_TABLE}"
            row_count = pd.read_sql(count_query, engine)['row_count'][0]

            # Get column information
            columns_query = f"""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{self.config.TICKETS_TABLE}'
                ORDER BY ORDINAL_POSITION
            """
            columns_df = pd.read_sql(columns_query, engine)

            # Get date range
            date_range_query = f"""
                SELECT
                    MIN(created_date) as min_date,
                    MAX(created_date) as max_date
                FROM {self.config.TICKETS_TABLE}
            """
            date_range = pd.read_sql(date_range_query, engine)

            return {
                'row_count': row_count,
                'columns': columns_df.to_dict('records'),
                'min_date': date_range['min_date'][0],
                'max_date': date_range['max_date'][0]
            }
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise

    def insert_tickets(self, df: pd.DataFrame, if_exists: str = 'append') -> int:
        """
        Insert ticket data into SQL Server.

        Args:
            df: DataFrame with ticket data
            if_exists: How to behave if table exists ('append', 'replace', 'fail')

        Returns:
            Number of rows inserted
        """
        try:
            engine = self.get_engine()

            # Calculate safe chunksize to avoid SQL Server's 2100 parameter limit
            # SQL Server limit is 2100 parameters, and we need to account for all columns
            num_columns = len(df.columns)
            # Use a safe chunksize: 2000 / num_columns to stay under the limit
            safe_chunksize = max(1, min(100, 2000 // num_columns))

            logger.info(f"Inserting {len(df)} rows with chunksize={safe_chunksize} (columns={num_columns})")

            # Use method='multi' for better performance with safe chunksize
            rows_inserted = df.to_sql(
                self.config.TICKETS_TABLE,
                engine,
                if_exists=if_exists,
                index=False,
                method='multi',
                chunksize=safe_chunksize
            )
            logger.info(f"Successfully inserted {rows_inserted} tickets into SQL Server")
            return rows_inserted
        except Exception as e:
            logger.error(f"Failed to insert tickets: {e}")
            raise

    def create_tickets_table(self):
        """Create the tickets table if it doesn't exist."""
        create_table_query = f"""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{self.config.TICKETS_TABLE}')
        BEGIN
            CREATE TABLE {self.config.TICKETS_TABLE} (
                ticket_id VARCHAR(50) PRIMARY KEY,
                created_date DATETIME NOT NULL,
                resolved_date DATETIME NULL,
                category VARCHAR(100) NOT NULL,
                priority VARCHAR(50) NOT NULL,
                assigned_team VARCHAR(100) NOT NULL,
                assigned_technician VARCHAR(100) NULL,
                status VARCHAR(50) NOT NULL,
                resolution_time_hours FLOAT NULL,
                created_week INT NULL,
                created_month VARCHAR(20) NULL,
                created_weekday VARCHAR(20) NULL
            );

            -- Create indexes for better query performance
            CREATE INDEX idx_created_date ON {self.config.TICKETS_TABLE}(created_date);
            CREATE INDEX idx_status ON {self.config.TICKETS_TABLE}(status);
            CREATE INDEX idx_priority ON {self.config.TICKETS_TABLE}(priority);
            CREATE INDEX idx_assigned_team ON {self.config.TICKETS_TABLE}(assigned_team);
            CREATE INDEX idx_assigned_technician ON {self.config.TICKETS_TABLE}(assigned_technician);
        END
        """

        try:
            if not self.connection:
                self.connect()

            cursor = self.connection.cursor()
            cursor.execute(create_table_query)
            self.connection.commit()
            cursor.close()
            logger.info(f"Table '{self.config.TICKETS_TABLE}' created successfully")
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


if __name__ == "__main__":
    # Test the connector
    logging.basicConfig(level=logging.INFO)

    connector = SQLServerConnector()

    # Test connection
    print("Testing SQL Server connection...")
    success, message = connector.test_connection()
    print(f"Result: {message}")

    if success:
        try:
            # Get table info
            print("\nGetting table information...")
            info = connector.get_table_info()
            print(f"Row count: {info['row_count']}")
            print(f"Date range: {info['min_date']} to {info['max_date']}")
            print(f"\nColumns:")
            for col in info['columns']:
                print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']}) - Nullable: {col['IS_NULLABLE']}")

            # Load sample data
            print("\nLoading sample tickets...")
            df = connector.load_tickets()
            print(f"Loaded {len(df)} tickets")
            print(f"\nSample data:")
            print(df.head())

        except Exception as e:
            print(f"Error: {e}")
