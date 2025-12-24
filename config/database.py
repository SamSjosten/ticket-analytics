"""
Database configuration for SQL Server connection.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class DatabaseConfig:
    """SQL Server database configuration."""

    # SQL Server connection settings
    SERVER = os.getenv('SQL_SERVER', 'localhost')
    DATABASE = os.getenv('SQL_DATABASE', 'TicketAnalytics')
    USERNAME = os.getenv('SQL_USERNAME', '')
    PASSWORD = os.getenv('SQL_PASSWORD', '')
    DRIVER = os.getenv('SQL_DRIVER', 'ODBC Driver 17 for SQL Server')
    PORT = os.getenv('SQL_PORT', '1433')

    # Use Windows Authentication if no username/password provided
    USE_WINDOWS_AUTH = not USERNAME or not PASSWORD

    # Connection timeout settings
    CONNECTION_TIMEOUT = int(os.getenv('SQL_CONNECTION_TIMEOUT', '30'))
    COMMAND_TIMEOUT = int(os.getenv('SQL_COMMAND_TIMEOUT', '60'))

    # Table name for tickets
    TICKETS_TABLE = os.getenv('SQL_TICKETS_TABLE', 'tickets')

    @classmethod
    def get_connection_string(cls) -> str:
        """
        Build SQL Server connection string.

        Returns:
            Connection string for pyodbc
        """
        if cls.USE_WINDOWS_AUTH:
            # Windows Authentication
            conn_str = (
                f"DRIVER={{{cls.DRIVER}}};"
                f"SERVER={cls.SERVER},{cls.PORT};"
                f"DATABASE={cls.DATABASE};"
                f"Trusted_Connection=yes;"
                f"Connection Timeout={cls.CONNECTION_TIMEOUT};"
            )
        else:
            # SQL Server Authentication
            conn_str = (
                f"DRIVER={{{cls.DRIVER}}};"
                f"SERVER={cls.SERVER},{cls.PORT};"
                f"DATABASE={cls.DATABASE};"
                f"UID={cls.USERNAME};"
                f"PWD={cls.PASSWORD};"
                f"Connection Timeout={cls.CONNECTION_TIMEOUT};"
            )

        return conn_str

    @classmethod
    def get_sqlalchemy_url(cls) -> str:
        """
        Build SQLAlchemy connection URL.

        Returns:
            SQLAlchemy connection URL
        """
        from urllib.parse import quote_plus

        conn_str = cls.get_connection_string()
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(conn_str)}"

    @classmethod
    def validate_config(cls) -> tuple[bool, str]:
        """
        Validate database configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cls.SERVER:
            return False, "SQL_SERVER is not configured"

        if not cls.DATABASE:
            return False, "SQL_DATABASE is not configured"

        if not cls.USE_WINDOWS_AUTH and (not cls.USERNAME or not cls.PASSWORD):
            return False, "SQL_USERNAME and SQL_PASSWORD must be provided for SQL Server Authentication"

        return True, "Configuration is valid"
