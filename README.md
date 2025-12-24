# IT Ticket Analytics Dashboard

A Python project for analyzing IT support ticket data, generating insights, and producing automated reports with an interactive Streamlit dashboard.

## Features

- **Interactive Dashboard**: Real-time data visualization with filters and drill-downs
- **SQL Server Integration**: Direct connection to SQL Server database for real-time analytics
- **Auth0 Authentication**: Secure user authentication with automatic user profile syncing to database
- **Flexible Data Import**: Automatic field mapping for company-specific CSV formats
- **CSV Export**: Download filtered data directly from the dashboard
- Analyze ticket volume, resolution times, and team performance
- Generate formatted Excel reports with charts
- Filter data by date range, category, priority, team, and status
- Track SLA compliance and resolution metrics
- Modular design for easy extension

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Configure SQL Server Connection

```bash
cp .env.example .env
# Edit .env with your SQL Server credentials
```

See [SQL Server Setup Guide](docs/SQL_SERVER_SETUP.md) for detailed configuration instructions.

### 2. Load Data into SQL Server

```bash
# Test connection
python scripts/load_to_sql.py --test

# Load your company data from CSV
python scripts/load_to_sql.py --csv path/to/your/company_data.csv

# Or generate mock data for testing
python scripts/load_to_sql.py --generate --num-tickets 1000
```

**Importing Company Data:**
The application automatically maps your company-specific field names (Dispatch No., CSR, Techassigned, etc.) to the standard schema. See the [Company Data Import Guide](docs/COMPANY_DATA_IMPORT.md) for detailed instructions.

### 3. Launch the Interactive Dashboard

**Windows:**
```bash
run_dashboard.bat
```

**Linux/Mac:**
```bash
chmod +x run_dashboard.sh
./run_dashboard.sh
```

**Or run directly:**
```bash
streamlit run src/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501` and automatically connect to your SQL Server database.

### Additional Options

#### Generate Static Reports (Optional)

Run the command-line analysis tool:
```bash
python src/main.py
```

Run with custom options:
```bash
python src/main.py --input data/raw/tickets.csv --output output/
```

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
ticket-analytics/
├── config/                    # Configuration settings
│   ├── settings.py           # Constants and configuration
│   └── database.py           # SQL Server configuration
├── data/raw/                  # Raw input data files
├── docs/                      # Documentation
│   └── SQL_SERVER_SETUP.md   # SQL Server setup guide
├── scripts/                   # Utility scripts
│   └── load_to_sql.py        # Load data to SQL Server
├── src/                       # Source code modules
│   ├── dashboard.py          # Streamlit interactive dashboard
│   ├── main.py               # CLI analysis tool
│   ├── data_loader.py        # Data loading and cleaning
│   ├── db_connector.py       # SQL Server connector
│   ├── analysis.py           # Analysis functions
│   ├── report_generator.py   # Excel report generation
│   └── generate_mock_data.py # Mock data generator
├── output/                    # Generated reports
├── tests/                     # Unit tests
├── .env.example               # Example environment configuration
├── run_dashboard.bat          # Windows dashboard launcher
└── run_dashboard.sh           # Linux/Mac dashboard launcher
```

## Dashboard Features

The interactive Streamlit dashboard provides:

- **SQL Server Connection Status**: Real-time connection monitoring and database statistics
- **Key Metrics Cards**: Total tickets, resolution rates, average times
- **Interactive Filters**: Filter by date range, category, priority, team, technician, and status
- **Modular Dashboard**: Configure which sections to display (preset or custom)
- **Visual Analytics**:
  - Tickets by category (bar chart)
  - Priority distribution (pie chart)
  - Status breakdown (bar chart)
  - Resolution time vs SLA thresholds
  - Team performance comparison
  - Technician performance tracking
  - SLA compliance tracking
  - Trend analysis (daily/weekly/monthly)
- **Data Tables**: Detailed views of team performance, technician performance, SLA compliance, and raw data
- **Individual Technician Breakdown**: Drill down into individual performance metrics
- **Real-time Updates**: Instantly see filtered results with live database connection

## SQL Server Integration

This application uses SQL Server as its primary data source, providing:
- **Real-time data access** from live databases
- **Better performance** for large datasets
- **Data persistence** and centralized storage
- **Multi-user access** to shared data
- **Enterprise integration** with existing systems
- **Automated connection monitoring** with status indicators in the dashboard

The dashboard automatically connects to your configured SQL Server database and displays connection status, record count, and date range information.

See the [SQL Server Setup Guide](docs/SQL_SERVER_SETUP.md) for complete setup instructions.

## Next Steps

- [x] Connect to live database (SQL Server)
- [ ] Add email report delivery
- [x] Build Streamlit dashboard
- [x] Add technician performance tracking
- [x] Add user authentication (Auth0)
- [x] Export filtered data to CSV
- [ ] Support for other databases (PostgreSQL, MySQL)
