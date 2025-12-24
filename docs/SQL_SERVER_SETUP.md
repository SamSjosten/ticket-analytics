# SQL Server Integration Guide

This guide explains how to configure and use SQL Server as a data source for the IT Ticket Analytics Dashboard.

## Prerequisites

1. **SQL Server**: Access to a SQL Server instance (2016 or later recommended)
2. **ODBC Driver**: ODBC Driver for SQL Server installed on your machine
3. **Permissions**: Appropriate database permissions (read/write access to the tickets table)

## Step 1: Install Required Packages

The SQL Server integration requires additional Python packages. Install them using:

```bash
pip install -r requirements.txt
```

This will install:
- `pyodbc>=5.0.0` - Python ODBC database connector
- `sqlalchemy>=2.0.0` - SQL toolkit and ORM
- `python-dotenv>=1.0.0` - Environment variable management

## Step 2: Install ODBC Driver

### Windows

Download and install the **Microsoft ODBC Driver for SQL Server**:
- [ODBC Driver 17](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- [ODBC Driver 18](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) (recommended)

To verify installed drivers, run in PowerShell:
```powershell
Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"}
```

### Linux

```bash
# Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Red Hat/CentOS
curl https://packages.microsoft.com/config/rhel/8/prod.repo > /etc/yum.repos.d/mssql-release.repo
sudo yum remove unixODBC-utf16 unixODBC-utf16-devel
sudo ACCEPT_EULA=Y yum install -y msodbcsql17
```

### macOS

```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_NO_ENV_FILTERING=1 ACCEPT_EULA=Y brew install msodbcsql17
```

## Step 3: Configure Database Connection

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your SQL Server credentials:**

   ### Option A: Windows Authentication (Recommended for Windows)
   ```ini
   SQL_SERVER=your-server-name
   SQL_PORT=1433
   SQL_DATABASE=TicketAnalytics
   SQL_USERNAME=
   SQL_PASSWORD=
   SQL_DRIVER=ODBC Driver 17 for SQL Server
   ```

   ### Option B: SQL Server Authentication
   ```ini
   SQL_SERVER=your-server-name
   SQL_PORT=1433
   SQL_DATABASE=TicketAnalytics
   SQL_USERNAME=your_username
   SQL_PASSWORD=your_password
   SQL_DRIVER=ODBC Driver 17 for SQL Server
   ```

3. **Configuration Parameters:**

   | Parameter | Description | Example |
   |-----------|-------------|---------|
   | `SQL_SERVER` | Server hostname or IP address | `localhost`, `192.168.1.100`, `myserver.database.windows.net` |
   | `SQL_PORT` | SQL Server port | `1433` (default) |
   | `SQL_DATABASE` | Database name | `TicketAnalytics` |
   | `SQL_USERNAME` | Username (leave empty for Windows Auth) | `sa`, `ticketuser` |
   | `SQL_PASSWORD` | Password (leave empty for Windows Auth) | Your password |
   | `SQL_DRIVER` | ODBC driver name | `ODBC Driver 17 for SQL Server` |
   | `SQL_TICKETS_TABLE` | Table name for tickets | `tickets` |

## Step 4: Create the Database and Table

### Method 1: Using the Python Script

Run the database connector script to create the table structure:

```bash
python src/db_connector.py
```

### Method 2: Manual SQL Script

Execute the following SQL in SQL Server Management Studio (SSMS) or Azure Data Studio:

```sql
-- Create database
CREATE DATABASE TicketAnalytics;
GO

USE TicketAnalytics;
GO

-- Create tickets table
CREATE TABLE tickets (
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
GO

-- Create indexes for better performance
CREATE INDEX idx_created_date ON tickets(created_date);
CREATE INDEX idx_status ON tickets(status);
CREATE INDEX idx_priority ON tickets(priority);
CREATE INDEX idx_assigned_team ON tickets(assigned_team);
CREATE INDEX idx_assigned_technician ON tickets(assigned_technician);
GO
```

## Step 5: Load Data into SQL Server

### Option 1: Load Mock Data

Generate and load mock data directly into SQL Server:

```python
# create_and_load_data.py
from src.generate_mock_data import generate_tickets
from src.db_connector import SQLServerConnector

# Generate mock data
df = generate_tickets(num_tickets=500, days_back=90)

# Load into SQL Server
connector = SQLServerConnector()
connector.create_tickets_table()  # Create table if it doesn't exist
connector.insert_tickets(df, if_exists='replace')

print(f"Loaded {len(df)} tickets into SQL Server")
```

### Option 2: Import from CSV

If you already have CSV data:

```python
from src.data_loader import load_tickets
from src.db_connector import SQLServerConnector
from pathlib import Path

# Load from CSV
df = load_tickets(filepath=Path("data/raw/tickets.csv"), source="file")

# Insert into SQL Server
connector = SQLServerConnector()
connector.insert_tickets(df, if_exists='replace')
```

### Option 3: Bulk Insert (SQL)

For large datasets, use SQL Server's BULK INSERT:

```sql
BULK INSERT tickets
FROM 'C:\path\to\tickets.csv'
WITH (
    FIRSTROW = 2,  -- Skip header row
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    TABLOCK
);
```

## Step 6: Test the Connection

Run the test script to verify connectivity:

```bash
python src/db_connector.py
```

Expected output:
```
Testing SQL Server connection...
Result: Connection successful
Getting table information...
Row count: 500
Date range: 2024-10-01 to 2025-01-15
...
```

## Step 7: Use SQL Server in the Dashboard

1. Launch the dashboard:
   ```bash
   streamlit run src/dashboard.py
   ```

2. In the sidebar, select **"SQL Server Database"** as the data source

3. The dashboard will:
   - Test the connection
   - Display connection status
   - Show available records and date range
   - Load and analyze data from SQL Server

## Troubleshooting

### Connection Failed Errors

**Error: "Data source name not found"**
- Solution: Verify the ODBC driver name matches what's installed
- Check installed drivers: Run `Get-OdbcDriver` (Windows) or `odbcinst -q -d` (Linux)

**Error: "Login failed for user"**
- Solution: Verify username and password are correct
- Check SQL Server authentication mode (must allow SQL Server authentication)
- Ensure user has appropriate permissions

**Error: "Cannot open database"**
- Solution: Ensure the database exists
- Run the CREATE DATABASE script from Step 4
- Verify user has access to the database

**Error: "Could not connect to server"**
- Solution: Check server name and port
- Verify SQL Server is running
- Check firewall settings (port 1433 must be open)
- Test with: `telnet your-server 1433`

### Performance Issues

**Slow queries**
- Ensure indexes are created (see Step 4)
- Consider adding additional indexes based on your query patterns
- Review and optimize date range filters

**Timeout errors**
- Increase timeout values in `.env`:
  ```ini
  SQL_CONNECTION_TIMEOUT=60
  SQL_COMMAND_TIMEOUT=120
  ```

### Data Quality Issues

**Date format problems**
- Ensure dates are in ISO format (YYYY-MM-DD) or datetime objects
- Check the `clean_ticket_data()` function in `data_loader.py`

**Missing technician data**
- Verify the `assigned_technician` column exists and is populated
- Update NULL values if needed

## Azure SQL Database

For Azure SQL Database, use these settings:

```ini
SQL_SERVER=your-server.database.windows.net
SQL_PORT=1433
SQL_DATABASE=TicketAnalytics
SQL_USERNAME=your-username@your-server
SQL_PASSWORD=your-password
SQL_DRIVER=ODBC Driver 17 for SQL Server
```

Additional considerations:
- Enable Azure services access in firewall rules
- Add your IP address to firewall whitelist
- Consider using Azure AD authentication for better security

## Security Best Practices

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use Windows Authentication** when possible (more secure than SQL auth)
3. **Limit database permissions** - Grant only necessary permissions (SELECT, INSERT, UPDATE)
4. **Rotate passwords** regularly
5. **Use SSL/TLS** encryption for connections:
   ```ini
   SQL_DRIVER=ODBC Driver 17 for SQL Server;Encrypt=yes;TrustServerCertificate=no
   ```
6. **Monitor access logs** - Review who accesses the database

## Data Migration

### Migrate from CSV to SQL Server

```python
from pathlib import Path
from src.data_loader import load_tickets
from src.db_connector import SQLServerConnector

# Load existing CSV data
csv_path = Path("data/raw/tickets.csv")
df = load_tickets(filepath=csv_path, source="file")

# Connect to SQL Server and migrate
connector = SQLServerConnector()
connector.create_tickets_table()
connector.insert_tickets(df, if_exists='replace')

print(f"Migrated {len(df)} records from CSV to SQL Server")
```

### Sync Data Periodically

Create a scheduled task to sync data:

```python
# sync_data.py
from datetime import datetime, timedelta
from src.db_connector import SQLServerConnector
from src.data_loader import load_tickets

# Load new tickets from source system
new_tickets_df = load_tickets(source="file")  # or from another source

# Filter for recent tickets (e.g., last 7 days)
cutoff_date = datetime.now() - timedelta(days=7)
recent_df = new_tickets_df[new_tickets_df['created_date'] >= cutoff_date]

# Insert into SQL Server
connector = SQLServerConnector()
connector.insert_tickets(recent_df, if_exists='append')

print(f"Synced {len(recent_df)} new tickets")
```

## Support

For additional help:
- Check SQL Server logs for detailed error messages
- Review the [Microsoft ODBC documentation](https://docs.microsoft.com/en-us/sql/connect/odbc/)
- Consult the project README for general setup instructions
