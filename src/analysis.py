"""
Analysis functions for ticket data.
"""
from pathlib import Path
from typing import Optional

import pandas as pd

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import SLA_THRESHOLDS


def tickets_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get ticket volume breakdown by category.
    
    Args:
        df: Ticket DataFrame
        
    Returns:
        DataFrame with category counts and percentages
    """
    counts = df["category"].value_counts()
    result = pd.DataFrame({
        "category": counts.index,
        "count": counts.values,
        "percentage": (counts.values / len(df) * 100).round(1)
    })
    return result


def tickets_by_priority(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get ticket volume breakdown by priority.
    
    Args:
        df: Ticket DataFrame
        
    Returns:
        DataFrame with priority counts and percentages
    """
    counts = df["priority"].value_counts()
    result = pd.DataFrame({
        "priority": counts.index,
        "count": counts.values,
        "percentage": (counts.values / len(df) * 100).round(1)
    })
    return result


def tickets_by_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get ticket volume breakdown by status.
    
    Args:
        df: Ticket DataFrame
        
    Returns:
        DataFrame with status counts and percentages
    """
    counts = df["status"].value_counts()
    result = pd.DataFrame({
        "status": counts.index,
        "count": counts.values,
        "percentage": (counts.values / len(df) * 100).round(1)
    })
    return result


def avg_resolution_time_by_priority(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate average resolution time by priority level.

    Args:
        df: Ticket DataFrame

    Returns:
        DataFrame with resolution time stats by priority
    """
    resolved = df[df["status"] == "Resolved"].copy()

    # Guard against empty resolved tickets
    if resolved.empty:
        # Return empty DataFrame with proper structure
        return pd.DataFrame(columns=[
            'priority', 'avg_hours', 'median_hours', 'min_hours',
            'max_hours', 'count', 'sla_threshold', 'within_sla_pct'
        ])

    # Ensure resolution_time_hours is numeric (handle any string/object values)
    resolved["resolution_time_hours"] = pd.to_numeric(
        resolved["resolution_time_hours"],
        errors='coerce'
    )

    # Drop rows where resolution_time_hours is NaN after conversion
    resolved = resolved.dropna(subset=["resolution_time_hours"])

    # Check again if we have data after cleaning
    if resolved.empty:
        return pd.DataFrame(columns=[
            'priority', 'avg_hours', 'median_hours', 'min_hours',
            'max_hours', 'count', 'sla_threshold', 'within_sla_pct'
        ])

    stats = resolved.groupby("priority", as_index=False)["resolution_time_hours"].agg([
        ("avg_hours", "mean"),
        ("median_hours", "median"),
        ("min_hours", "min"),
        ("max_hours", "max"),
        ("count", "count")
    ]).round(2)

    # Reset index to get priority as a column (fixes deprecation)
    stats = stats.reset_index()

    # Ensure all numeric columns are actually numeric type
    for col in ['avg_hours', 'median_hours', 'min_hours', 'max_hours']:
        stats[col] = pd.to_numeric(stats[col], errors='coerce')

    # Add SLA threshold for comparison
    stats["sla_threshold"] = stats["priority"].map(SLA_THRESHOLDS)

    # Calculate within_sla_pct - fixed to avoid deprecated GroupBy behavior
    within_sla_list = []
    for priority in stats["priority"]:
        priority_data = resolved[resolved["priority"] == priority]
        if len(priority_data) > 0:
            sla_threshold = SLA_THRESHOLDS.get(priority, 999)
            within_pct = (priority_data["resolution_time_hours"] <= sla_threshold).mean() * 100
            within_sla_list.append(round(within_pct, 1))
        else:
            within_sla_list.append(0.0)

    stats["within_sla_pct"] = within_sla_list

    return stats


def tickets_over_time(
    df: pd.DataFrame, 
    period: str = "D"
) -> pd.DataFrame:
    """
    Get ticket volume over time.
    
    Args:
        df: Ticket DataFrame
        period: Grouping period - 'D' for daily, 'W' for weekly, 'M' for monthly
        
    Returns:
        DataFrame with ticket counts by period
    """
    df = df.copy()
    df["period"] = df["created_date"].dt.to_period(period)
    
    counts = df.groupby("period").size().reset_index(name="ticket_count")
    counts["period"] = counts["period"].astype(str)
    
    return counts


def team_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze team performance metrics.
    
    Args:
        df: Ticket DataFrame
        
    Returns:
        DataFrame with team performance stats
    """
    # Total tickets per team
    total_tickets = df.groupby("assigned_team").size()
    
    # Resolution stats for resolved tickets
    resolved = df[df["status"] == "Resolved"]
    resolution_stats = resolved.groupby("assigned_team")["resolution_time_hours"].agg([
        ("avg_resolution_hours", "mean"),
        ("median_resolution_hours", "median")
    ]).round(2)
    
    # Resolution rate
    resolution_rate = (
        resolved.groupby("assigned_team").size() / 
        df.groupby("assigned_team").size() * 100
    ).round(1)
    
    # Combine metrics
    result = pd.DataFrame({
        "assigned_team": total_tickets.index,
        "total_tickets": total_tickets.values,
        "resolved_count": resolved.groupby("assigned_team").size().reindex(total_tickets.index, fill_value=0).values,
        "resolution_rate_pct": resolution_rate.values,
        "avg_resolution_hours": resolution_stats["avg_resolution_hours"].reindex(total_tickets.index).values,
        "median_resolution_hours": resolution_stats["median_resolution_hours"].reindex(total_tickets.index).values
    })
    
    return result.sort_values("total_tickets", ascending=False)


def sla_compliance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate SLA compliance rates.
    
    Args:
        df: Ticket DataFrame
        
    Returns:
        DataFrame with SLA compliance by priority
    """
    resolved = df[df["status"] == "Resolved"].copy()
    
    def check_sla(row):
        threshold = SLA_THRESHOLDS.get(row["priority"], 999)
        return row["resolution_time_hours"] <= threshold
    
    resolved["within_sla"] = resolved.apply(check_sla, axis=1)
    
    compliance = resolved.groupby("priority").agg(
        total_resolved=("ticket_id", "count"),
        within_sla=("within_sla", "sum")
    )
    compliance["sla_compliance_pct"] = (
        compliance["within_sla"] / compliance["total_resolved"] * 100
    ).round(1)
    compliance["sla_threshold_hours"] = compliance.index.map(SLA_THRESHOLDS)
    
    return compliance.reset_index()


def technician_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze individual technician performance metrics.

    Args:
        df: Ticket DataFrame

    Returns:
        DataFrame with technician performance stats
    """
    if "assigned_technician" not in df.columns:
        return pd.DataFrame()

    # Total tickets per technician
    total_tickets = df.groupby("assigned_technician").size()

    # Resolution stats for resolved tickets
    resolved = df[df["status"] == "Resolved"]
    resolution_stats = resolved.groupby("assigned_technician")["resolution_time_hours"].agg([
        ("avg_resolution_hours", "mean"),
        ("median_resolution_hours", "median")
    ]).round(2)

    # Resolution rate
    resolution_rate = (
        resolved.groupby("assigned_technician").size() /
        df.groupby("assigned_technician").size() * 100
    ).round(1)

    # Get team for each technician
    technician_team = df.groupby("assigned_technician")["assigned_team"].first()

    # Combine metrics
    result = pd.DataFrame({
        "assigned_technician": total_tickets.index,
        "assigned_team": technician_team.reindex(total_tickets.index).values,
        "total_tickets": total_tickets.values,
        "resolved_count": resolved.groupby("assigned_technician").size().reindex(total_tickets.index, fill_value=0).values,
        "resolution_rate_pct": resolution_rate.values,
        "avg_resolution_hours": resolution_stats["avg_resolution_hours"].reindex(total_tickets.index).values,
        "median_resolution_hours": resolution_stats["median_resolution_hours"].reindex(total_tickets.index).values
    })

    return result.sort_values("total_tickets", ascending=False)


def technician_detailed_breakdown(df: pd.DataFrame, technician_name: str) -> dict:
    """
    Get detailed performance breakdown for a specific technician.

    Args:
        df: Ticket DataFrame
        technician_name: Name of the technician

    Returns:
        Dictionary with detailed performance metrics
    """
    if "assigned_technician" not in df.columns:
        return {}

    # Filter for specific technician
    tech_df = df[df["assigned_technician"] == technician_name].copy()

    if tech_df.empty:
        return {}

    # Basic stats
    total_tickets = len(tech_df)
    resolved_df = tech_df[tech_df["status"] == "Resolved"]
    in_progress_df = tech_df[tech_df["status"] == "In Progress"]
    open_df = tech_df[tech_df["status"] == "Open"]

    # Breakdown by category
    category_breakdown = tech_df.groupby("category").size().to_dict()

    # Breakdown by priority
    priority_breakdown = tech_df.groupby("priority").size().to_dict()

    # SLA compliance by priority
    sla_compliance = {}
    for priority in tech_df["priority"].unique():
        priority_resolved = resolved_df[resolved_df["priority"] == priority]
        if len(priority_resolved) > 0:
            threshold = SLA_THRESHOLDS.get(priority, 999)
            within_sla = (priority_resolved["resolution_time_hours"] <= threshold).sum()
            sla_compliance[priority] = {
                "total": len(priority_resolved),
                "within_sla": within_sla,
                "compliance_pct": round(within_sla / len(priority_resolved) * 100, 1)
            }

    # Time period analysis
    if "created_date" in tech_df.columns:
        tech_df["date"] = tech_df["created_date"].dt.date
        daily_volume = tech_df.groupby("date").size().to_dict()
        avg_daily_volume = round(len(tech_df) / len(daily_volume), 1) if daily_volume else 0
    else:
        daily_volume = {}
        avg_daily_volume = 0

    return {
        "technician_name": technician_name,
        "team": tech_df["assigned_team"].iloc[0] if len(tech_df) > 0 else "Unknown",
        "total_tickets": total_tickets,
        "resolved": len(resolved_df),
        "in_progress": len(in_progress_df),
        "open": len(open_df),
        "resolution_rate_pct": round(len(resolved_df) / total_tickets * 100, 1) if total_tickets > 0 else 0,
        "avg_resolution_hours": round(resolved_df["resolution_time_hours"].mean(), 2) if len(resolved_df) > 0 else None,
        "median_resolution_hours": round(resolved_df["resolution_time_hours"].median(), 2) if len(resolved_df) > 0 else None,
        "min_resolution_hours": round(resolved_df["resolution_time_hours"].min(), 2) if len(resolved_df) > 0 else None,
        "max_resolution_hours": round(resolved_df["resolution_time_hours"].max(), 2) if len(resolved_df) > 0 else None,
        "category_breakdown": category_breakdown,
        "priority_breakdown": priority_breakdown,
        "sla_compliance": sla_compliance,
        "avg_daily_volume": avg_daily_volume
    }


def generate_summary_stats(df: pd.DataFrame) -> dict:
    """
    Generate high-level summary statistics.

    Args:
        df: Ticket DataFrame

    Returns:
        Dictionary with summary statistics
    """
    # Guard against empty dataframe
    if df.empty:
        return {
            "total_tickets": 0,
            "resolved_tickets": 0,
            "open_tickets": 0,
            "in_progress_tickets": 0,
            "resolution_rate_pct": 0.0,
            "avg_resolution_hours": 0.0,
            "median_resolution_hours": 0.0,
            "date_range_start": "N/A",
            "date_range_end": "N/A",
            "top_category": "N/A",
            "busiest_day": "N/A"
        }

    resolved = df[df["status"] == "Resolved"]
    total_tickets = len(df)

    # Safe division for resolution rate
    resolution_rate_pct = round(len(resolved) / total_tickets * 100, 1) if total_tickets > 0 else 0.0

    # Safe mean/median calculation for resolution time
    avg_resolution = resolved["resolution_time_hours"].mean() if len(resolved) > 0 else 0.0
    median_resolution = resolved["resolution_time_hours"].median() if len(resolved) > 0 else 0.0

    # Safe mode calculation - return first mode or "Unknown" if no mode
    category_mode = df["category"].mode()
    top_category = category_mode.iloc[0] if len(category_mode) > 0 else "Unknown"

    weekday_mode = df["created_weekday"].mode() if "created_weekday" in df.columns else pd.Series([])
    busiest_day = weekday_mode.iloc[0] if len(weekday_mode) > 0 else "Unknown"

    return {
        "total_tickets": total_tickets,
        "resolved_tickets": len(resolved),
        "open_tickets": len(df[df["status"] == "Open"]),
        "in_progress_tickets": len(df[df["status"] == "In Progress"]),
        "resolution_rate_pct": resolution_rate_pct,
        "avg_resolution_hours": round(avg_resolution, 2),
        "median_resolution_hours": round(median_resolution, 2),
        "date_range_start": df["created_date"].min().strftime("%Y-%m-%d"),
        "date_range_end": df["created_date"].max().strftime("%Y-%m-%d"),
        "top_category": top_category,
        "busiest_day": busiest_day
    }


if __name__ == "__main__":
    # Test analysis functions
    from data_loader import load_tickets
    
    try:
        df = load_tickets()
        
        print("=== Summary Stats ===")
        stats = generate_summary_stats(df)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n=== Tickets by Category ===")
        print(tickets_by_category(df).to_string(index=False))
        
        print("\n=== Resolution Time by Priority ===")
        print(avg_resolution_time_by_priority(df).to_string(index=False))
        
        print("\n=== Team Performance ===")
        print(team_performance(df).to_string(index=False))
        
        print("\n=== SLA Compliance ===")
        print(sla_compliance(df).to_string(index=False))
        
    except FileNotFoundError:
        print("Run generate_mock_data.py first to create test data.")
