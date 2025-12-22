# IT Ticket Analytics Dashboard

A Python project for analyzing IT support ticket data, generating insights, and producing automated reports with an interactive Streamlit dashboard.

## Features

- **Interactive Dashboard**: Real-time data visualization with filters and drill-downs
- Load and clean ticket data from CSV/Excel
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

### 1. Generate Mock Data

First, generate sample ticket data for testing:
```bash
python src/generate_mock_data.py
```

### 2. Launch the Interactive Dashboard

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

The dashboard will open in your browser at `http://localhost:8501`

### 3. Generate Static Reports (Optional)

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
├── config/              # Configuration settings
│   └── settings.py     # Constants and configuration
├── data/raw/            # Raw input data files
├── src/                 # Source code modules
│   ├── dashboard.py    # Streamlit interactive dashboard
│   ├── main.py         # CLI analysis tool
│   ├── data_loader.py  # Data loading and cleaning
│   ├── analysis.py     # Analysis functions
│   ├── report_generator.py  # Excel report generation
│   └── generate_mock_data.py  # Mock data generator
├── output/              # Generated reports
├── tests/               # Unit tests
├── run_dashboard.bat   # Windows dashboard launcher
└── run_dashboard.sh    # Linux/Mac dashboard launcher
```

## Dashboard Features

The interactive Streamlit dashboard provides:

- **Key Metrics Cards**: Total tickets, resolution rates, average times
- **Interactive Filters**: Filter by date range, category, priority, team, and status
- **Visual Analytics**:
  - Tickets by category (bar chart)
  - Priority distribution (pie chart)
  - Status breakdown (bar chart)
  - Resolution time vs SLA thresholds
  - Team performance comparison
  - SLA compliance tracking
  - Trend analysis (daily/weekly/monthly)
- **Data Tables**: Detailed views of team performance, SLA compliance, and raw data
- **Real-time Updates**: Instantly see filtered results

## Next Steps

- [ ] Connect to live database
- [ ] Add email report delivery
- [x] Build Streamlit dashboard
- [ ] Add user authentication
- [ ] Export filtered data to CSV
