
#!/usr/bin/env python3
"""
MDRM Web Explorer

A simple Flask web application to explore the MDRM (Micro Data Reference Manual) database.
Provides search functionality and data browsing capabilities.
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect('mdrm_database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Main page with search interface."""
    return render_template('index.html')

@app.route('/api/search')
def search():
    """API endpoint for searching MDRM data."""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'item_name')
    limit = int(request.args.get('limit', 50))
    
    conn = get_db_connection()
    
    if not query:
        # Return recent items if no query
        sql = """
        SELECT mdrm_identifier, mnemonic, item_code, item_name, item_type, 
               confidentiality, start_date, end_date
        FROM mdrm_data 
        ORDER BY start_date DESC 
        LIMIT ?
        """
        results = conn.execute(sql, (limit,)).fetchall()
    else:
        # Search based on type
        if search_type == 'item_name':
            sql = """
            SELECT mdrm_identifier, mnemonic, item_code, item_name, item_type, 
                   confidentiality, start_date, end_date
            FROM mdrm_data 
            WHERE item_name LIKE ? 
            ORDER BY item_name 
            LIMIT ?
            """
            results = conn.execute(sql, (f'%{query}%', limit)).fetchall()
        elif search_type == 'mnemonic':
            sql = """
            SELECT mdrm_identifier, mnemonic, item_code, item_name, item_type, 
                   confidentiality, start_date, end_date
            FROM mdrm_data 
            WHERE mnemonic LIKE ? 
            ORDER BY item_name 
            LIMIT ?
            """
            results = conn.execute(sql, (f'%{query}%', limit)).fetchall()
        elif search_type == 'item_code':
            sql = """
            SELECT mdrm_identifier, mnemonic, item_code, item_name, item_type, 
                   confidentiality, start_date, end_date
            FROM mdrm_data 
            WHERE item_code LIKE ? 
            ORDER BY mnemonic, item_name 
            LIMIT ?
            """
            results = conn.execute(sql, (f'%{query}%', limit)).fetchall()
        else:
            results = []
    
    conn.close()
    
    # Convert to list of dictionaries
    data = []
    for row in results:
        data.append({
            'mdrm_identifier': row['mdrm_identifier'],
            'mnemonic': row['mnemonic'],
            'item_code': row['item_code'],
            'item_name': row['item_name'],
            'item_type': row['item_type'],
            'confidentiality': row['confidentiality'],
            'start_date': row['start_date'],
            'end_date': row['end_date']
        })
    
    return jsonify(data)

@app.route('/api/details/<mdrm_id>')
def get_details(mdrm_id):
    """Get detailed information for a specific MDRM item."""
    conn = get_db_connection()
    
    sql = """
    SELECT * FROM mdrm_data 
    WHERE mdrm_identifier = ?
    """
    
    result = conn.execute(sql, (mdrm_id,)).fetchone()
    conn.close()
    
    if result:
        return jsonify(dict(result))
    else:
        return jsonify({'error': 'Item not found'}), 404

@app.route('/api/stats')
def get_stats():
    """Get database statistics."""
    conn = get_db_connection()
    
    # Get summary statistics
    stats = {}
    summary_results = conn.execute("SELECT * FROM mdrm_summary").fetchall()
    for row in summary_results:
        stats[row['statistic_name']] = row['statistic_value']
    
    # Get top mnemonics
    top_mnemonics = conn.execute("""
        SELECT mnemonic, COUNT(*) as count 
        FROM mdrm_data 
        GROUP BY mnemonic 
        ORDER BY count DESC 
        LIMIT 10
    """).fetchall()
    
    stats['top_mnemonics'] = [dict(row) for row in top_mnemonics]
    
    conn.close()
    return jsonify(stats)

# Create templates directory and HTML template
def create_templates():
    """Create the HTML template for the web interface."""
    os.makedirs('templates', exist_ok=True)
    
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MDRM Explorer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .search-container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        select, button {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #2980b9;
        }
        .results-container {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .results-header {
            background-color: #34495e;
            color: white;
            padding: 15px;
            border-radius: 8px 8px 0 0;
        }
        .results-table {
            width: 100%;
            border-collapse: collapse;
        }
        .results-table th, .results-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .results-table th {
            background-color: #ecf0f1;
            font-weight: bold;
        }
        .results-table tr:hover {
            background-color: #f8f9fa;
        }
        .item-type {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .type-F { background-color: #e8f5e8; color: #2d5a2d; }
        .type-S { background-color: #e8f0ff; color: #1a4480; }
        .type-D { background-color: #fff3e0; color: #8b4513; }
        .type-R { background-color: #ffeaea; color: #8b0000; }
        .type-P { background-color: #f0e8ff; color: #4b0082; }
        .confidential { color: #e74c3c; font-weight: bold; }
        .public { color: #27ae60; font-weight: bold; }
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .stat-label {
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 5px;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
        }
        .no-results {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>MDRM Explorer</h1>
        <p>Micro Data Reference Manual - Federal Reserve Banking Data Dictionary</p>
    </div>

    <div id="stats-container" class="stats-container">
        <!-- Stats will be loaded here -->
    </div>

    <div class="search-container">
        <h3>Search MDRM Data</h3>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Enter search term..." />
            <select id="searchType">
                <option value="item_name">Item Name</option>
                <option value="mnemonic">Mnemonic</option>
                <option value="item_code">Item Code</option>
            </select>
            <button onclick="performSearch()">Search</button>
            <button onclick="loadRecentItems()">Show Recent</button>
        </div>
        <p><strong>Examples:</strong> Search for "ASSETS", "RCON", "2170", etc.</p>
    </div>

    <div class="results-container">
        <div class="results-header">
            <h3 id="resultsTitle">Search Results</h3>
        </div>
        <div id="resultsContent">
            <div class="loading">Loading recent items...</div>
        </div>
    </div>

    <script>
        // Load statistics on page load
        window.onload = function() {
            loadStats();
            loadRecentItems();
        };

        // Allow Enter key to trigger search
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });

        function loadStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    const statsContainer = document.getElementById('stats-container');
                    statsContainer.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-number">${data.total_records}</div>
                            <div class="stat-label">Total Records</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${data.unique_mnemonics}</div>
                            <div class="stat-label">Unique Mnemonics</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${data.unique_item_codes}</div>
                            <div class="stat-label">Unique Item Codes</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${data.public_items}</div>
                            <div class="stat-label">Public Items</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${data.confidential_items}</div>
                            <div class="stat-label">Confidential Items</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${data.unique_reporting_forms}</div>
                            <div class="stat-label">Reporting Forms</div>
                        </div>
                    `;
                })
                .catch(error => {
                    console.error('Error loading stats:', error);
                });
        }

        function performSearch() {
            const query = document.getElementById('searchInput').value;
            const searchType = document.getElementById('searchType').value;
            
            document.getElementById('resultsContent').innerHTML = '<div class="loading">Searching...</div>';
            document.getElementById('resultsTitle').textContent = `Search Results for "${query}"`;
            
            const url = `/api/search?q=${encodeURIComponent(query)}&type=${searchType}&limit=100`;
            
            fetch(url)
                .then(response => response.json())
                .then(data => displayResults(data))
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('resultsContent').innerHTML = '<div class="no-results">Error loading results</div>';
                });
        }

        function loadRecentItems() {
            document.getElementById('resultsContent').innerHTML = '<div class="loading">Loading recent items...</div>';
            document.getElementById('resultsTitle').textContent = 'Recent Items';
            
            fetch('/api/search?limit=50')
                .then(response => response.json())
                .then(data => displayResults(data))
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('resultsContent').innerHTML = '<div class="no-results">Error loading results</div>';
                });
        }

        function displayResults(data) {
            const resultsContent = document.getElementById('resultsContent');
            
            if (data.length === 0) {
                resultsContent.innerHTML = '<div class="no-results">No results found</div>';
                return;
            }
            
            let html = `
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>MDRM ID</th>
                            <th>Mnemonic</th>
                            <th>Item Code</th>
                            <th>Item Name</th>
                            <th>Type</th>
                            <th>Confidentiality</th>
                            <th>Start Date</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.forEach(item => {
                const typeClass = `type-${item.item_type}`;
                const confClass = item.confidentiality === 'Y' ? 'confidential' : 'public';
                const confText = item.confidentiality === 'Y' ? 'Confidential' : 'Public';
                
                html += `
                    <tr onclick="showDetails('${item.mdrm_identifier}')" style="cursor: pointer;">
                        <td><strong>${item.mdrm_identifier}</strong></td>
                        <td>${item.mnemonic}</td>
                        <td>${item.item_code}</td>
                        <td>${item.item_name}</td>
                        <td><span class="item-type ${typeClass}">${item.item_type}</span></td>
                        <td><span class="${confClass}">${confText}</span></td>
                        <td>${item.start_date ? new Date(item.start_date).toLocaleDateString() : 'N/A'}</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table>';
            resultsContent.innerHTML = html;
        }

        function showDetails(mdrm_id) {
            fetch(`/api/details/${mdrm_id}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('Error loading details: ' + data.error);
                        return;
                    }
                    
                    const description = data.description || 'No description available';
                    const seriesGlossary = data.series_glossary || 'No series glossary available';
                    
                    alert(`MDRM ID: ${data.mdrm_identifier}\\n\\nItem Name: ${data.item_name}\\n\\nDescription: ${description}\\n\\nSeries Glossary: ${seriesGlossary}`);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error loading item details');
                });
        }
    </script>
</body>
</html>
    '''
    
    with open('templates/index.html', 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    # Create templates
    create_templates()
    
    # Check if database exists
    if not os.path.exists('mdrm_database.db'):
        print("Error: mdrm_database.db not found!")
        print("Please run create_mdrm_database.py first to create the database.")
        exit(1)
    
    print("Starting MDRM Web Explorer...")
    print("Access the application at: http://localhost:51180")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=51180, debug=True)

