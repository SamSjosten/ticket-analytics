#!/bin/bash
echo "Starting IT Ticket Analytics Dashboard..."
echo ""
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run src/dashboard.py
