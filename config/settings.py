"""
Configuration settings for the ticket analytics project.
"""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Data settings
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ticket categories (customize for your environment)
TICKET_CATEGORIES = [
    "Hardware",
    "Software",
    "Network",
    "Access Request",
    "Email",
    "Password Reset",
    "Other"
]

# Priority levels
PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]

# Teams (customize for your environment)
TEAMS = [
    "Service Desk",
    "Desktop Support",
    "Network Team",
    "Systems Admin"
]

# Technicians by team (customize for your environment)
TECHNICIANS = {
    "Service Desk": ["Alice Johnson", "Bob Smith", "Carol White", "David Brown"],
    "Desktop Support": ["Emma Davis", "Frank Miller", "Grace Lee", "Henry Wilson"],
    "Network Team": ["Ivy Martinez", "Jack Taylor", "Karen Anderson", "Leo Thomas"],
    "Systems Admin": ["Maria Garcia", "Nathan Moore", "Olivia Jackson", "Paul Martinez"]
}

# SLA thresholds (in hours)
SLA_THRESHOLDS = {
    "Critical": 4,
    "High": 8,
    "Medium": 24,
    "Low": 48
}

# Report settings
REPORT_TITLE = "IT Ticket Analytics Report"
