"""
Main entry point for the IT Ticket Analytics tool.
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DATA_DIR, OUTPUT_DIR
from src.data_loader import load_tickets, get_date_range
from src.analysis import (
    tickets_by_category,
    tickets_by_priority,
    tickets_by_status,
    avg_resolution_time_by_priority,
    tickets_over_time,
    team_performance,
    sla_compliance,
    generate_summary_stats
)
from src.report_generator import create_excel_report, create_charts


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="IT Ticket Analytics - Generate insights from ticket data"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=DATA_DIR / "tickets.csv",
        help="Input data file (CSV or Excel)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for reports"
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip generating chart images"
    )
    parser.add_argument(
        "--no-excel",
        action="store_true",
        help="Skip generating Excel report"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("IT Ticket Analytics")
    logger.info("=" * 50)
    
    # Load data
    try:
        logger.info(f"Loading data from: {args.input}")
        df = load_tickets(args.input)
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {args.input}")
        logger.error("Run 'python src/generate_mock_data.py' to create sample data.")
        sys.exit(1)
    
    # Get date range
    date_start, date_end = get_date_range(df)
    logger.info(f"Data range: {date_start.date()} to {date_end.date()}")
    logger.info(f"Total tickets: {len(df)}")
    
    # Run analysis
    logger.info("Running analysis...")
    
    analysis_results = {
        "summary_stats": generate_summary_stats(df),
        "by_category": tickets_by_category(df),
        "by_priority": tickets_by_priority(df),
        "by_status": tickets_by_status(df),
        "resolution_by_priority": avg_resolution_time_by_priority(df),
        "team_performance": team_performance(df),
        "trend_daily": tickets_over_time(df, "D"),
        "trend_weekly": tickets_over_time(df, "W"),
        "sla_compliance": sla_compliance(df)
    }
    
    # Print summary to console
    print("\n" + "=" * 50)
    print("SUMMARY STATISTICS")
    print("=" * 50)
    for key, value in analysis_results["summary_stats"].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\n" + "-" * 50)
    print("TICKETS BY CATEGORY")
    print("-" * 50)
    print(analysis_results["by_category"].to_string(index=False))
    
    print("\n" + "-" * 50)
    print("SLA COMPLIANCE")
    print("-" * 50)
    print(analysis_results["sla_compliance"].to_string(index=False))
    
    # Generate outputs
    args.output.mkdir(parents=True, exist_ok=True)
    
    if not args.no_excel:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = args.output / f"ticket_report_{timestamp}.xlsx"
        create_excel_report(df, analysis_results, report_path)
        print(f"\nExcel report saved: {report_path}")
    
    if not args.no_charts:
        chart_files = create_charts(df, args.output)
        print(f"Charts saved: {[str(f) for f in chart_files]}")
    
    logger.info("Analysis complete!")
    print("\n" + "=" * 50)
    print("DONE")
    print("=" * 50)


if __name__ == "__main__":
    main()
