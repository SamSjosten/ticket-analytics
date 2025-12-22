"""
Unit tests for analysis functions.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis import (
    tickets_by_category,
    tickets_by_priority,
    tickets_by_status,
    avg_resolution_time_by_priority,
    team_performance,
    generate_summary_stats
)


@pytest.fixture
def sample_tickets():
    """Create sample ticket data for testing."""
    return pd.DataFrame({
        "ticket_id": ["TKT-001", "TKT-002", "TKT-003", "TKT-004", "TKT-005"],
        "created_date": [
            datetime.now() - timedelta(days=5),
            datetime.now() - timedelta(days=4),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1)
        ],
        "resolved_date": [
            datetime.now() - timedelta(days=4),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=2),
            None,
            None
        ],
        "category": ["Software", "Hardware", "Software", "Network", "Software"],
        "priority": ["Low", "High", "Medium", "Critical", "Low"],
        "assigned_team": ["Service Desk", "Desktop Support", "Service Desk", "Network Team", "Service Desk"],
        "status": ["Resolved", "Resolved", "Resolved", "In Progress", "Open"],
        "resolution_time_hours": [8.0, 4.5, 12.0, None, None],
        "created_weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    })


class TestTicketsByCategory:
    """Tests for tickets_by_category function."""
    
    def test_returns_dataframe(self, sample_tickets):
        result = tickets_by_category(sample_tickets)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_required_columns(self, sample_tickets):
        result = tickets_by_category(sample_tickets)
        assert "category" in result.columns
        assert "count" in result.columns
        assert "percentage" in result.columns
    
    def test_counts_are_correct(self, sample_tickets):
        result = tickets_by_category(sample_tickets)
        software_count = result[result["category"] == "Software"]["count"].values[0]
        assert software_count == 3  # 3 Software tickets in sample
    
    def test_percentages_sum_to_100(self, sample_tickets):
        result = tickets_by_category(sample_tickets)
        assert abs(result["percentage"].sum() - 100.0) < 0.1


class TestTicketsByPriority:
    """Tests for tickets_by_priority function."""
    
    def test_returns_dataframe(self, sample_tickets):
        result = tickets_by_priority(sample_tickets)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_required_columns(self, sample_tickets):
        result = tickets_by_priority(sample_tickets)
        assert "priority" in result.columns
        assert "count" in result.columns


class TestTicketsByStatus:
    """Tests for tickets_by_status function."""
    
    def test_returns_dataframe(self, sample_tickets):
        result = tickets_by_status(sample_tickets)
        assert isinstance(result, pd.DataFrame)
    
    def test_counts_match_total(self, sample_tickets):
        result = tickets_by_status(sample_tickets)
        assert result["count"].sum() == len(sample_tickets)


class TestAvgResolutionTime:
    """Tests for avg_resolution_time_by_priority function."""
    
    def test_returns_dataframe(self, sample_tickets):
        result = avg_resolution_time_by_priority(sample_tickets)
        assert isinstance(result, pd.DataFrame)
    
    def test_only_includes_resolved(self, sample_tickets):
        result = avg_resolution_time_by_priority(sample_tickets)
        # Should only have priorities that have resolved tickets
        total_resolved = result["count"].sum()
        assert total_resolved == 3  # Only 3 resolved in sample


class TestTeamPerformance:
    """Tests for team_performance function."""
    
    def test_returns_dataframe(self, sample_tickets):
        result = team_performance(sample_tickets)
        assert isinstance(result, pd.DataFrame)
    
    def test_has_required_columns(self, sample_tickets):
        result = team_performance(sample_tickets)
        assert "assigned_team" in result.columns
        assert "total_tickets" in result.columns
        assert "resolution_rate_pct" in result.columns


class TestGenerateSummaryStats:
    """Tests for generate_summary_stats function."""
    
    def test_returns_dict(self, sample_tickets):
        result = generate_summary_stats(sample_tickets)
        assert isinstance(result, dict)
    
    def test_has_required_keys(self, sample_tickets):
        result = generate_summary_stats(sample_tickets)
        assert "total_tickets" in result
        assert "resolved_tickets" in result
        assert "resolution_rate_pct" in result
    
    def test_total_tickets_correct(self, sample_tickets):
        result = generate_summary_stats(sample_tickets)
        assert result["total_tickets"] == 5
    
    def test_resolved_count_correct(self, sample_tickets):
        result = generate_summary_stats(sample_tickets)
        assert result["resolved_tickets"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
