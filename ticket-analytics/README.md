# IT Ticket Analytics Dashboard

A Python project for analyzing IT support ticket data, generating insights, and producing automated reports.

## Features

- Load and clean ticket data from CSV/Excel
- Analyze ticket volume, resolution times, and team performance
- Generate formatted Excel reports with charts
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

Generate mock data:
```bash
python src/generate_mock_data.py
```

Run the analysis:
```bash
python src/main.py
```

Run with options:
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
├── config/          # Configuration settings
├── data/raw/        # Raw input data files
├── src/             # Source code modules
├── output/          # Generated reports
└── tests/           # Unit tests
```

## Next Steps

- [ ] Connect to live database
- [ ] Add email report delivery
- [ ] Build Streamlit dashboard
