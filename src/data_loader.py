"""
Data loading and cleaning functions for ticket data.
"""
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATA_DIR, DATETIME_FORMAT

logger = logging.getLogger(__name__)


def load_tickets(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load ticket data from a CSV or Excel file.
    
    Args:
        filepath: Path to the data file. Defaults to DATA_DIR/tickets.csv
        
    Returns:
        Cleaned DataFrame with ticket data
    """
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


def clean_ticket_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize ticket data.
    
    Args:
        df: Raw ticket DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    df = df.copy()
    
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
    
    # Add derived columns
    if "created_date" in df.columns:
        df["created_week"] = df["created_date"].dt.isocalendar().week
        df["created_month"] = df["created_date"].dt.to_period("M").astype(str)
        df["created_weekday"] = df["created_date"].dt.day_name()
    
    # Log data quality info
    null_counts = df.isnull().sum()
    if null_counts.any():
        logger.warning(f"Null values found:\n{null_counts[null_counts > 0]}")
    
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
