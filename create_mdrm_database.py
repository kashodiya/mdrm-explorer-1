#!/usr/bin/env python3
"""
MDRM Database Creator

This script processes the Federal Reserve's Micro Data Reference Manual (MDRM) CSV file
and creates a SQLite database for easier querying and analysis.

The MDRM is a catalog of micro and macro data collected from depository institutions
and other respondents, organized into reports or data series consisting primarily
of financial and structure data.
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os
import sys

def clean_csv_data():
    """Clean and prepare the MDRM CSV data for database insertion."""
    print("Reading MDRM CSV file...")
    
    # Read the CSV file, skipping the first line which just says "PUBLIC"
    try:
        df = pd.read_csv('MDRM_CSV.csv', skiprows=1, encoding='utf-8')
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        df = pd.read_csv('MDRM_CSV.csv', skiprows=1, encoding='latin-1')
    
    print(f"Loaded {len(df)} records from CSV file")
    print(f"Columns: {list(df.columns)}")
    
    # Clean column names (remove extra spaces and trailing commas)
    df.columns = df.columns.str.strip().str.rstrip(',')
    
    # Handle date columns
    date_columns = ['Start Date', 'End Date']
    for col in date_columns:
        if col in df.columns:
            # Convert dates to proper format
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Clean text fields - remove HTML entities and extra whitespace
    text_columns = ['Description', 'SeriesGlossary', 'Item Name']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('&#x0D;', '\n', regex=False)
            df[col] = df[col].str.replace('&amp;', '&', regex=False)
            df[col] = df[col].str.strip()
    
    # Create MDRM Identifier by combining Mnemonic and Item Code
    if 'Mnemonic' in df.columns and 'Item Code' in df.columns:
        df['MDRM_Identifier'] = df['Mnemonic'].astype(str) + df['Item Code'].astype(str)
    
    return df

def create_database(df):
    """Create SQLite database and insert the MDRM data."""
    db_name = 'mdrm_database.db'
    
    print(f"Creating SQLite database: {db_name}")
    
    # Remove existing database if it exists
    if os.path.exists(db_name):
        os.remove(db_name)
    
    # Create connection to SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Create the main MDRM table
    create_table_sql = """
    CREATE TABLE mdrm_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mdrm_identifier TEXT,
        mnemonic TEXT,
        item_code TEXT,
        start_date DATE,
        end_date DATE,
        item_name TEXT,
        confidentiality TEXT,
        item_type TEXT,
        reporting_form TEXT,
        description TEXT,
        series_glossary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    cursor.execute(create_table_sql)
    
    # Create indexes for better query performance
    indexes = [
        "CREATE INDEX idx_mdrm_identifier ON mdrm_data(mdrm_identifier);",
        "CREATE INDEX idx_mnemonic ON mdrm_data(mnemonic);",
        "CREATE INDEX idx_item_code ON mdrm_data(item_code);",
        "CREATE INDEX idx_item_name ON mdrm_data(item_name);",
        "CREATE INDEX idx_item_type ON mdrm_data(item_type);",
        "CREATE INDEX idx_reporting_form ON mdrm_data(reporting_form);",
        "CREATE INDEX idx_start_date ON mdrm_data(start_date);",
        "CREATE INDEX idx_end_date ON mdrm_data(end_date);"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    print("Database schema created successfully")
    
    # Insert data into the database
    print("Inserting data into database...")
    
    # Prepare data for insertion
    columns_mapping = {
        'MDRM_Identifier': 'mdrm_identifier',
        'Mnemonic': 'mnemonic', 
        'Item Code': 'item_code',
        'Start Date': 'start_date',
        'End Date': 'end_date',
        'Item Name': 'item_name',
        'Confidentiality': 'confidentiality',
        'ItemType': 'item_type',
        'Reporting Form': 'reporting_form',
        'Description': 'description',
        'SeriesGlossary': 'series_glossary'
    }
    
    # Select and rename columns
    df_clean = df.copy()
    for old_col, new_col in columns_mapping.items():
        if old_col in df_clean.columns:
            df_clean = df_clean.rename(columns={old_col: new_col})
    
    # Select only the columns we want to insert
    insert_columns = list(columns_mapping.values())
    df_insert = df_clean[insert_columns].copy()
    
    # Insert data using pandas to_sql method
    df_insert.to_sql('mdrm_data', conn, if_exists='append', index=False)
    
    # Get record count
    cursor.execute("SELECT COUNT(*) FROM mdrm_data")
    record_count = cursor.fetchone()[0]
    
    print(f"Successfully inserted {record_count} records into the database")
    
    # Create summary statistics table
    create_summary_stats(cursor)
    
    conn.commit()
    conn.close()
    
    return db_name

def create_summary_stats(cursor):
    """Create summary statistics about the MDRM data."""
    print("Creating summary statistics...")
    
    # Create summary table
    cursor.execute("""
    CREATE TABLE mdrm_summary (
        statistic_name TEXT PRIMARY KEY,
        statistic_value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Calculate and insert summary statistics
    stats_queries = [
        ("total_records", "SELECT COUNT(*) FROM mdrm_data"),
        ("unique_mnemonics", "SELECT COUNT(DISTINCT mnemonic) FROM mdrm_data"),
        ("unique_item_codes", "SELECT COUNT(DISTINCT item_code) FROM mdrm_data"),
        ("unique_reporting_forms", "SELECT COUNT(DISTINCT reporting_form) FROM mdrm_data WHERE reporting_form IS NOT NULL AND reporting_form != ''"),
        ("confidential_items", "SELECT COUNT(*) FROM mdrm_data WHERE confidentiality = 'Y'"),
        ("public_items", "SELECT COUNT(*) FROM mdrm_data WHERE confidentiality = 'N'"),
        ("active_items", "SELECT COUNT(*) FROM mdrm_data WHERE end_date > date('now')"),
        ("expired_items", "SELECT COUNT(*) FROM mdrm_data WHERE end_date <= date('now')")
    ]
    
    for stat_name, query in stats_queries:
        cursor.execute(query)
        result = cursor.fetchone()[0]
        cursor.execute("INSERT INTO mdrm_summary (statistic_name, statistic_value) VALUES (?, ?)", 
                      (stat_name, str(result)))
    
    # Item type distribution
    cursor.execute("""
    SELECT item_type, COUNT(*) 
    FROM mdrm_data 
    WHERE item_type IS NOT NULL AND item_type != ''
    GROUP BY item_type
    """)
    
    item_types = cursor.fetchall()
    for item_type, count in item_types:
        cursor.execute("INSERT INTO mdrm_summary (statistic_name, statistic_value) VALUES (?, ?)", 
                      (f"item_type_{item_type}", str(count)))

def main():
    """Main function to process MDRM data and create database."""
    print("MDRM Database Creator")
    print("=" * 50)
    
    # Check if CSV file exists
    if not os.path.exists('MDRM_CSV.csv'):
        print("Error: MDRM_CSV.csv file not found!")
        print("Please ensure the MDRM.zip file has been downloaded and extracted.")
        sys.exit(1)
    
    try:
        # Clean and process the CSV data
        df = clean_csv_data()
        
        # Create the SQLite database
        db_name = create_database(df)
        
        print("\n" + "=" * 50)
        print("Database creation completed successfully!")
        print(f"Database file: {db_name}")
        print(f"Total records processed: {len(df)}")
        
        # Display some sample queries
        print("\nSample queries you can run:")
        print("1. SELECT COUNT(*) FROM mdrm_data;")
        print("2. SELECT * FROM mdrm_summary;")
        print("3. SELECT DISTINCT mnemonic FROM mdrm_data LIMIT 10;")
        print("4. SELECT * FROM mdrm_data WHERE item_name LIKE '%ASSETS%' LIMIT 5;")
        
    except Exception as e:
        print(f"Error processing MDRM data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
