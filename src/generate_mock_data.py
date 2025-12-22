"""
Generate realistic mock IT ticket data for testing and development.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    DATA_DIR,
    TICKET_CATEGORIES,
    PRIORITY_LEVELS,
    TEAMS,
    TECHNICIANS,
    SLA_THRESHOLDS
)


def generate_tickets(num_tickets: int = 500, days_back: int = 90) -> pd.DataFrame:
    """
    Generate mock ticket data.
    
    Args:
        num_tickets: Number of tickets to generate
        days_back: How many days of history to generate
        
    Returns:
        DataFrame with mock ticket data
    """
    tickets = []
    start_date = datetime.now() - timedelta(days=days_back)
    
    for i in range(num_tickets):
        # Random creation date within the date range
        created_date = start_date + timedelta(
            days=random.randint(0, days_back),
            hours=random.randint(8, 17),  # Business hours
            minutes=random.randint(0, 59)
        )
        
        # Assign category with weighted distribution
        category = random.choices(
            TICKET_CATEGORIES,
            weights=[15, 25, 10, 15, 10, 20, 5],  # Adjust weights as needed
            k=1
        )[0]
        
        # Assign priority with weighted distribution
        priority = random.choices(
            PRIORITY_LEVELS,
            weights=[30, 40, 20, 10],  # More low/medium than high/critical
            k=1
        )[0]
        
        # Assign team based on category
        team_weights = {
            "Hardware": [10, 70, 10, 10],
            "Software": [30, 50, 5, 15],
            "Network": [5, 10, 80, 5],
            "Access Request": [20, 10, 10, 60],
            "Email": [40, 30, 10, 20],
            "Password Reset": [80, 10, 5, 5],
            "Other": [50, 20, 15, 15]
        }
        team = random.choices(TEAMS, weights=team_weights[category], k=1)[0]

        # Assign technician from the selected team
        technician = random.choice(TECHNICIANS[team])

        # Determine status and resolution
        status_roll = random.random()
        if status_roll < 0.85:  # 85% resolved
            status = "Resolved"
            # Resolution time based on priority (with some variance)
            base_hours = SLA_THRESHOLDS[priority]
            resolution_hours = max(0.5, random.gauss(base_hours * 0.7, base_hours * 0.3))
            resolved_date = created_date + timedelta(hours=resolution_hours)
        elif status_roll < 0.95:  # 10% in progress
            status = "In Progress"
            resolved_date = None
            resolution_hours = None
        else:  # 5% open
            status = "Open"
            resolved_date = None
            resolution_hours = None
        
        tickets.append({
            "ticket_id": f"TKT-{10000 + i}",
            "created_date": created_date.strftime("%Y/%m/%d"),
            "resolved_date": resolved_date.strftime("%Y/%m/%d") if resolved_date else None,
            "category": category,
            "priority": priority,
            "assigned_team": team,
            "assigned_technician": technician,
            "status": status,
            "resolution_time_hours": round(resolution_hours, 2) if resolution_hours else None
        })
    
    return pd.DataFrame(tickets)


def main():
    """Generate and save mock ticket data."""
    print("Generating mock ticket data...")
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate tickets
    df = generate_tickets(num_tickets=500, days_back=90)
    
    # Save to CSV
    output_path = DATA_DIR / "tickets.csv"
    df.to_csv(output_path, index=False)
    
    print(f"Generated {len(df)} tickets")
    print(f"Saved to: {output_path}")
    print(f"\nSample data:")
    print(df.head(10).to_string())
    
    print(f"\nStatus breakdown:")
    print(df["status"].value_counts())


if __name__ == "__main__":
    main()
