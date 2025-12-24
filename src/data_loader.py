"""
Data loading and cleaning functions for ticket data.
"""
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

import pandas as pd

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATA_DIR, DATETIME_FORMAT

logger = logging.getLogger(__name__)


def load_tickets(
    filepath: Optional[Path] = None,
    source: str = "file",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status_filter: Optional[str] = None
) -> pd.DataFrame:
    """
    Load ticket data from a file or SQL Server database.

    Args:
        filepath: Path to the data file. Defaults to DATA_DIR/tickets.csv (only used if source='file')
        source: Data source - 'file' or 'sql'
        start_date: Optional start date filter (only for SQL)
        end_date: Optional end date filter (only for SQL)
        status_filter: Optional status filter (only for SQL)

    Returns:
        Cleaned DataFrame with ticket data
    """
    if source == "sql":
        # Load from SQL Server
        from src.db_connector import SQLServerConnector

        logger.info("Loading data from SQL Server")
        connector = SQLServerConnector()
        df = connector.load_tickets(
            start_date=start_date,
            end_date=end_date,
            status_filter=status_filter
        )
    else:
        # Load from file
        if filepath is None:
            filepath = DATA_DIR / "tickets.csv"

        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")

        logger.info(f"Loading data from: {filepath}")

        # Load based on file extension
        if filepath.suffix.lower() == ".csv":
            df = pd.read_csv(filepath)
        elif filepath.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")

    # Clean the data
    df = clean_ticket_data(df)

    logger.info(f"Loaded {len(df)} tickets")
    return df


def map_company_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map company-specific field names to standard schema.

    Supports multiple field name formats:
    - Company format: "Dispatch No.", "Call No.", "CSR", "Techassigned", etc.
    - Standard format: "ticket_id", "created_date", etc.

    Args:
        df: Raw DataFrame with company-specific fields

    Returns:
        DataFrame with standardized field names
    """
    df = df.copy()

    # Define field mapping: company_field -> standard_field
    field_mapping = {
        # Ticket identifiers
        "Dispatch No.": "ticket_id",
        "Call No.": "call_number",

        # Personnel
        "CSR": "assigned_team",  # Customer Service Representative -> Team
        "Techassigned": "assigned_technician",

        # Status and dates
        "Status": "status",
        "Date": "created_date",
        "Close Date": "resolved_date",

        # Company and problem details
        "Company Name": "company_name",
        "Problemcode": "category",  # Problem code maps to category
        "Problem": "problem_type",
        "Problem Description": "description",

        # Metrics
        "RESPONSETIME": "resolution_time_hours"
    }

    # Rename columns that exist in the DataFrame
    rename_dict = {}
    for company_field, standard_field in field_mapping.items():
        if company_field in df.columns:
            rename_dict[company_field] = standard_field
            logger.info(f"Mapping '{company_field}' -> '{standard_field}'")

    if rename_dict:
        df = df.rename(columns=rename_dict)
        logger.info(f"Mapped {len(rename_dict)} company-specific fields to standard schema")

    return df


def clean_ticket_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize ticket data.

    Args:
        df: Raw ticket DataFrame

    Returns:
        Cleaned DataFrame
    """
    df = df.copy()

    # First, map company-specific fields to standard schema
    df = map_company_fields(df)

    # Convert date columns
    date_columns = ["created_date", "resolved_date"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Standardize text columns
    text_columns = ["category", "priority", "assigned_team", "assigned_technician", "status"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    # Ensure numeric columns are proper types
    if "resolution_time_hours" in df.columns:
        df["resolution_time_hours"] = pd.to_numeric(
            df["resolution_time_hours"], errors="coerce"
        )

    # If we have a ticket_id but no explicit priority, try to infer it from other fields
    if "ticket_id" in df.columns and "priority" not in df.columns:
        # Default priority to Medium if not specified
        df["priority"] = "Medium"
        logger.info("No priority field found, defaulting to 'Medium'")

    # Add derived columns
    if "created_date" in df.columns:
        df["created_week"] = df["created_date"].dt.isocalendar().week
        df["created_month"] = df["created_date"].dt.to_period("M").astype(str)
        df["created_weekday"] = df["created_date"].dt.day_name()

    # Log data quality info
    null_counts = df.isnull().sum()
    if null_counts.any():
        logger.warning(f"Null values found:\n{null_counts[null_counts > 0]}")

    # Log final schema
    logger.info(f"Final schema: {list(df.columns)}")

    return df


def get_date_range(df: pd.DataFrame) -> tuple:
    """
    Get the date range of the ticket data.
    
    Args:
        df: Ticket DataFrame
        
    Returns:
        Tuple of (min_date, max_date)
    """
    return df["created_date"].min(), df["created_date"].max()


if __name__ == "__main__":
    # Test the loader
    logging.basicConfig(level=logging.INFO)
    
    try:
        df = load_tickets()
        print(f"\nLoaded {len(df)} tickets")
        print(f"Date range: {get_date_range(df)}")
        print(f"\nColumns: {list(df.columns)}")
        print(f"\nSample:\n{df.head()}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run generate_mock_data.py first to create test data.")
