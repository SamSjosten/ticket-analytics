"""
Create users table in SQL Server for Auth0 user management.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import DatabaseConfig
from src.db_connector import SQLServerConnector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_users_table():
    """Create the users table for Auth0 authentication."""

    create_table_sql = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
    BEGIN
        CREATE TABLE users (
            user_id INT IDENTITY(1,1) PRIMARY KEY,
            auth0_id NVARCHAR(255) UNIQUE NOT NULL,
            email NVARCHAR(255) NOT NULL,
            name NVARCHAR(255),
            picture NVARCHAR(500),
            email_verified BIT DEFAULT 0,
            created_at DATETIME2 DEFAULT GETDATE(),
            last_login DATETIME2 DEFAULT GETDATE(),
            role NVARCHAR(50) DEFAULT 'user',
            is_active BIT DEFAULT 1,
            metadata NVARCHAR(MAX)
        );

        -- Create indexes for better query performance
        CREATE UNIQUE INDEX idx_auth0_id ON users(auth0_id);
        CREATE INDEX idx_email ON users(email);
        CREATE INDEX idx_role ON users(role);
        CREATE INDEX idx_last_login ON users(last_login);

        PRINT 'Users table created successfully';
    END
    ELSE
    BEGIN
        PRINT 'Users table already exists';
    END
    """

    try:
        logger.info("Connecting to SQL Server...")
        connector = SQLServerConnector()

        # Test connection first
        success, message = connector.test_connection()
        if not success:
            logger.error(f"Connection test failed: {message}")
            return False

        logger.info("Connection successful")

        # Connect and create table
        connector.connect()
        cursor = connector.connection.cursor()

        logger.info("Creating users table...")
        cursor.execute(create_table_sql)
        connector.connection.commit()

        logger.info("Users table setup completed successfully")

        cursor.close()
        connector.disconnect()

        return True

    except Exception as e:
        logger.error(f"Failed to create users table: {e}")
        return False


if __name__ == "__main__":
    success = create_users_table()
    sys.exit(0 if success else 1)
