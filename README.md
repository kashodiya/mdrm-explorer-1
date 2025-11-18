
# MDRM Explorer

A comprehensive tool for exploring the Federal Reserve's Micro Data Reference Manual (MDRM) database.

## What is MDRM?

The **Micro Data Reference Manual (MDRM)** is a catalog of micro and macro data collected from depository institutions and other respondents by the Federal Reserve System. The data are organized into reports, or data series, and consist primarily of financial and structure data. The MDRM documents the labels and values associated with each data item.

### Key Features of MDRM Data:

- **MDRM Identifier**: An 8-character combination of Mnemonic (4 letters) and Item Code (4 numbers)
- **Mnemonics**: Four-letter codes representing reporting forms (e.g., RCON, SVGL, BHCK)
- **Item Codes**: Four-digit numbers representing specific data items (e.g., 2170 = Total Assets)
- **Data Types**: Financial/reported (F), Structure (S), Derived (D), Rate (R), Percentage (P), Examination (E), Projected (J)

## Project Contents

This project downloads the official MDRM data from the Federal Reserve and creates a SQLite database for easy querying and exploration.

### Files:

- `create_mdrm_database.py` - Script to download and process MDRM data into SQLite
- `query_mdrm_database.py` - Command-line tool for querying the database
- `mdrm_web_explorer.py` - Web interface for browsing and searching MDRM data
- `mdrm_database.db` - SQLite database containing all MDRM data
- `MDRM_CSV.csv` - Original CSV data from Federal Reserve
- `README File for MDRM.txt` - Official documentation from Federal Reserve

## Database Schema

The SQLite database contains two main tables:

### `mdrm_data` Table:
- `mdrm_identifier` - Full 8-character MDRM ID
- `mnemonic` - 4-letter reporting form code
- `item_code` - 4-digit item number
- `start_date` - When data collection began
- `end_date` - When data collection ended
- `item_name` - Descriptive name of the data item
- `confidentiality` - Y/N for public availability
- `item_type` - Type of data (F/S/D/R/P/E/J)
- `reporting_form` - Associated reporting form
- `description` - Detailed description of the item
- `series_glossary` - Additional context information

### `mdrm_summary` Table:
- Summary statistics about the database contents

## Usage

### 1. Create the Database

```bash
python3 create_mdrm_database.py
```

This will:
- Download the latest MDRM.zip from the Federal Reserve
- Extract and process the CSV data
- Create a SQLite database with proper indexing
- Generate summary statistics

### 2. Query the Database (Command Line)

```bash
python3 query_mdrm_database.py
```

This displays various sample queries and statistics about the MDRM data.

### 3. Web Interface

```bash
python3 mdrm_web_explorer.py
```

Then visit http://localhost:51180 to use the web interface.

The web interface provides:
- Search functionality by item name, mnemonic, or item code
- Database statistics dashboard
- Detailed item information
- Responsive design for easy browsing

## Sample Queries

### Find all items related to assets:
```sql
SELECT mdrm_identifier, mnemonic, item_name 
FROM mdrm_data 
WHERE item_name LIKE '%ASSETS%';
```

### Get all items for a specific reporting form:
```sql
SELECT * FROM mdrm_data 
WHERE mnemonic = 'RCON' 
ORDER BY item_code;
```

### Find currently active items:
```sql
SELECT COUNT(*) FROM mdrm_data 
WHERE end_date > date('now');
```

### Get item type distribution:
```sql
SELECT item_type, COUNT(*) as count 
FROM mdrm_data 
GROUP BY item_type 
ORDER BY count DESC;
```

## Database Statistics

The database contains:
- **87,351** total records
- **847** unique mnemonics (reporting forms)
- **47,226** unique item codes
- **147** unique reporting forms
- **39,231** public items
- **48,119** confidential items

## Item Types

- **F** (Financial/reported): 75,500 items - Data submitted by reporters
- **D** (Derived): 9,006 items - Calculated from other variables
- **P** (Percentage): 978 items - Stored as percentage values
- **R** (Rate): 923 items - Stored as decimal values
- **S** (Structure): 909 items - Institutional descriptive data
- **J** (Projected): 35 items - Projected values

## Data Source

Data is sourced directly from the Federal Reserve Board:
- **Source URL**: https://www.federalreserve.gov/apps/mdrm/download_mdrm.htm
- **Documentation**: https://www.federalreserve.gov/data/mdrm.htm
- **Last Updated**: The database reflects the most current MDRM data available

## Requirements

- Python 3.6+
- pandas
- sqlite3 (included with Python)
- flask (for web interface)

## Installation

```bash
pip install pandas flask
```

## License

This project processes public data from the Federal Reserve. The MDRM data itself is in the public domain.
