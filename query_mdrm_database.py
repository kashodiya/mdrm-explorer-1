
#!/usr/bin/env python3
"""
MDRM Database Query Tool

This script demonstrates how to query the MDRM SQLite database
and provides examples of useful queries for exploring the data.
"""

import sqlite3
import pandas as pd
from datetime import datetime

def connect_to_database():
    """Connect to the MDRM SQLite database."""
    try:
        conn = sqlite3.connect('mdrm_database.db')
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def run_query(conn, query, description=""):
    """Run a SQL query and display results."""
    if description:
        print(f"\n{description}")
        print("-" * len(description))
    
    try:
        df = pd.read_sql_query(query, conn)
        print(df.to_string(index=False))
        return df
    except Exception as e:
        print(f"Error running query: {e}")
        return None

def main():
    """Main function to demonstrate database queries."""
    print("MDRM Database Query Tool")
    print("=" * 50)
    
    conn = connect_to_database()
    if not conn:
        return
    
    # Query 1: Database summary statistics
    run_query(conn, 
              "SELECT * FROM mdrm_summary ORDER BY statistic_name;",
              "Database Summary Statistics")
    
    # Query 2: Sample of MDRM data
    run_query(conn, 
              "SELECT mdrm_identifier, mnemonic, item_code, item_name, item_type FROM mdrm_data LIMIT 10;",
              "Sample MDRM Data Records")
    
    # Query 3: Unique mnemonics (reporting forms)
    run_query(conn, 
              "SELECT DISTINCT mnemonic, COUNT(*) as item_count FROM mdrm_data GROUP BY mnemonic ORDER BY item_count DESC LIMIT 15;",
              "Top 15 Mnemonics by Item Count")
    
    # Query 4: Item types distribution
    run_query(conn, 
              """SELECT 
                 item_type,
                 CASE 
                   WHEN item_type = 'F' THEN 'Financial/reported'
                   WHEN item_type = 'S' THEN 'Structure'
                   WHEN item_type = 'D' THEN 'Derived'
                   WHEN item_type = 'R' THEN 'Rate'
                   WHEN item_type = 'P' THEN 'Percentage'
                   WHEN item_type = 'E' THEN 'Examination/supervision'
                   WHEN item_type = 'J' THEN 'Projected'
                   ELSE 'Unknown'
                 END as type_description,
                 COUNT(*) as count
                 FROM mdrm_data 
                 WHERE item_type IS NOT NULL AND item_type != ''
                 GROUP BY item_type 
                 ORDER BY count DESC;""",
              "Item Types Distribution")
    
    # Query 5: Assets-related items
    run_query(conn, 
              """SELECT mdrm_identifier, mnemonic, item_name, item_type 
                 FROM mdrm_data 
                 WHERE item_name LIKE '%ASSETS%' 
                 ORDER BY mnemonic, item_name 
                 LIMIT 10;""",
              "Sample Assets-Related Items")
    
    # Query 6: Currently active vs expired items
    run_query(conn, 
              """SELECT 
                 CASE 
                   WHEN end_date > date('now') THEN 'Active'
                   ELSE 'Expired'
                 END as status,
                 COUNT(*) as count
                 FROM mdrm_data 
                 GROUP BY status;""",
              "Active vs Expired Items")
    
    # Query 7: Confidential vs Public items
    run_query(conn, 
              """SELECT 
                 CASE 
                   WHEN confidentiality = 'Y' THEN 'Confidential'
                   WHEN confidentiality = 'N' THEN 'Public'
                   ELSE 'Unknown'
                 END as confidentiality_status,
                 COUNT(*) as count
                 FROM mdrm_data 
                 GROUP BY confidentiality_status;""",
              "Confidentiality Distribution")
    
    # Query 8: Recent items (started in last 5 years)
    run_query(conn, 
              """SELECT mdrm_identifier, mnemonic, item_name, start_date
                 FROM mdrm_data 
                 WHERE start_date >= date('now', '-5 years')
                 ORDER BY start_date DESC 
                 LIMIT 10;""",
              "Recently Added Items (Last 5 Years)")
    
    conn.close()
    print("\n" + "=" * 50)
    print("Query demonstration completed!")

if __name__ == "__main__":
    main()

