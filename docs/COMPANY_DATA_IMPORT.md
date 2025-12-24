# Company Data Import Guide

This guide explains how to import your company-specific ticket data into the Analytics Dashboard.

## Two Ways to Import Data

### Method 1: Web Upload (Recommended - Easy!)

1. Log in to the dashboard
2. Go to the **Administration** tab
3. Scroll to the **Data Import** section
4. Click "Choose a file" and select your CSV or Excel file
5. Preview the data and field mappings
6. Choose import mode (Replace or Append)
7. Click "Import Data to Database"

**Benefits:**
- ✅ User-friendly interface
- ✅ Preview data before importing
- ✅ See field mappings automatically
- ✅ Immediate feedback on success/errors
- ✅ No command line needed

### Method 2: Command Line Import

For advanced users or automation:

```bash
python scripts\load_to_sql.py --csv path\to\your\file.csv
```

## Supported Field Names

The application automatically maps your company-specific field names to the standard schema:

| Your Field Name | Maps To | Purpose |
|----------------|---------|---------|
| `Dispatch No.` | `ticket_id` | Unique ticket identifier |
| `Call No.` | `call_number` | Call reference number |
| `CSR` | `assigned_team` | Customer Service Representative (team) |
| `Techassigned` | `assigned_technician` | Assigned technician name |
| `Status` | `status` | Ticket status (Open, In Progress, Resolved, etc.) |
| `Date` | `created_date` | Ticket creation date |
| `Close Date` | `resolved_date` | Ticket resolution date |
| `Company Name` | `company_name` | Customer company name |
| `Problemcode` | `category` | Problem category/type |
| `Problem` | `problem_type` | Problem classification |
| `Problem Description` | `description` | Detailed problem description |
| `RESPONSETIME` | `resolution_time_hours` | Resolution time in hours |

## Required Fields

At minimum, your CSV must contain:
- **Dispatch No.** (ticket identifier)
- **Date** (creation date)
- **Status** (ticket status)
- **Problemcode** (category)

Optional but recommended:
- **Techassigned** (for technician performance tracking)
- **CSR** (for team analysis)
- **RESPONSETIME** (for SLA compliance tracking)

## Import Steps (Web Upload)

### 1. Prepare Your File

Ensure your CSV or Excel file has the column headers listed above. Example:

```csv
Dispatch No.,Call No.,CSR,Techassigned,Status,Date,Close Date,Company Name,Problemcode,Problem,Problem Description,RESPONSETIME
12345,C001,Support Team,John Doe,Resolved,2024-01-15,2024-01-16,Acme Corp,Hardware,Printer,Printer not working,24
12346,C002,IT Team,Jane Smith,Open,2024-01-16,,Beta Inc,Software,Email,Email sync issue,
```

### 2. Upload to Dashboard

1. **Launch the dashboard:**
   ```bash
   streamlit run src\dashboard.py
   ```

2. **Log in** with your Auth0 account

3. **Go to Administration tab** (top of page)

4. **Scroll to "Data Import" section**

5. **Upload your file:**
   - Click "Choose a file to upload"
   - Select your .xlsx, .xls, or .csv file
   - Wait for preview to load

6. **Review the preview:**
   - Check the first 5 rows of data
   - Verify field mappings (shown automatically)
   - Confirm total record count

7. **Choose import mode:**
   - **Replace existing data:** Deletes all current tickets and loads your file
   - **Append to existing data:** Adds your tickets to existing data

8. **Click "Import Data to Database"**

9. **Wait for confirmation:**
   - Success message shows number of tickets imported
   - Import summary shows total records and date range

### 3. Verify the Import

1. **Refresh the page** (or go to Analytics tab)
2. Check that your data appears correctly
3. Verify charts and metrics update
4. Test filters and drill-downs

### 4. If Using Command Line

For automation or large files:

```bash
# Windows
python scripts\load_to_sql.py --csv "C:\path\to\your\file.xlsx"

# Linux/Mac
python scripts/load_to_sql.py --csv /path/to/your/file.csv
```

## Data Quality Notes

### Automatic Handling

The application automatically:
- Converts date formats to standard datetime
- Standardizes text to Title Case
- Handles missing values gracefully
- Adds derived fields (week, month, weekday)

### Priority Field

If your data doesn't include a "Priority" field, the application will:
- Default all tickets to "Medium" priority
- You can add a Priority column to your CSV with values: Critical, High, Medium, Low

### Resolution Time

If `RESPONSETIME` is not in hours:
- The application expects hours (e.g., 24 for 24 hours)
- If you have minutes, divide by 60 first in Excel: `=RESPONSETIME/60`
- If you have days, multiply by 24: `=RESPONSETIME*24`

### Status Values

Recommended status values:
- `Open` - Newly created tickets
- `In Progress` - Being worked on
- `Resolved` - Completed tickets
- `Closed` - Archived tickets

The application will work with any status values, but these align with built-in analytics.

## Troubleshooting

### "Column not found" errors

**Problem**: CSV headers don't exactly match expected names.

**Solution**:
1. Check for extra spaces: `"Dispatch No. "` should be `"Dispatch No."`
2. Check capitalization: `"dispatch no."` should be `"Dispatch No."`
3. Use exact field names from the table above

### Date parsing errors

**Problem**: Dates not recognized properly.

**Solution**:
- Use format: `YYYY-MM-DD` (e.g., `2024-01-15`)
- Or: `MM/DD/YYYY` (e.g., `01/15/2024`)
- Avoid: Text dates like "January 15, 2024"

### Missing technician performance

**Problem**: Technician Performance section is empty.

**Solution**:
- Ensure `Techassigned` column exists and has values
- Check for blank/null technician names
- Standardize technician names (e.g., "John Doe" vs "John D." vs "JDoe")

### Duplicate ticket IDs

**Problem**: Import fails due to duplicate `Dispatch No.` values.

**Solution**:
- `Dispatch No.` must be unique for each ticket
- Check for duplicate rows in your CSV
- Use `--mode append` carefully to avoid re-importing same data

## Advanced: Custom Field Mapping

If your field names are different, you can edit the mapping in `src/data_loader.py`:

```python
field_mapping = {
    "Your Field Name": "standard_field",
    # Add your custom mappings here
}
```

## Example Import Session

```bash
# 1. Test connection
python scripts\load_to_sql.py --test

# 2. Load company data
python scripts\load_to_sql.py --csv C:\Data\tickets_2024.csv --mode replace

# 3. Verify output
✅ Successfully loaded 1523 tickets into SQL Server
Table now contains 1523 total records
Date range: 2024-01-01 to 2024-12-20

# 4. Launch dashboard
streamlit run src\dashboard.py
```

## Support

If you encounter issues:
1. Check the console output for specific error messages
2. Verify your CSV file opens correctly in Excel
3. Try with a small sample (5-10 rows) first
4. Check the logs for field mapping confirmations
