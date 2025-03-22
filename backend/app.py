import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
import pandas as pd

# ROOT_PATH for linking with all your files.
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(current_directory, 'init.json')

# Load JSON data
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Combine sectors and holdings across all ETFs
sectors_list = []
holdings_list = []

for etf, etf_data in data.items():
    for sector in etf_data.get("sectors", []):
        sector["ETF"] = etf  # Add ETF name to the sector
        sectors_list.append(sector)
    for holding in etf_data.get("holdings", []):
        holding["ETF"] = etf  # Add ETF name to the holding
        holdings_list.append(holding)

# Create DataFrames
sectors_df = pd.DataFrame(sectors_list)
holdings_df = pd.DataFrame(holdings_list)

app = Flask(__name__)
CORS(app)

def sector_search(query):
    query = query.lower()
    matches = sectors_df[sectors_df['sector'].str.lower().str.contains(query, na=False)]
    return matches[['ETF', 'sector', 'weight']].to_json(orient='records')

def holdings_search(query):
    query = query.lower()
    matches = holdings_df[
        (holdings_df['symbol'].str.lower().str.contains(query, na=False)) | 
        (holdings_df['description'].str.lower().str.contains(query, na=False))
    ]
    return matches[['ETF', 'symbol', 'description', 'details', 'weight']].to_json(orient='records')

@app.route("/")
def home():
    return render_template('base.html', title="ETF Data Search")

@app.route("/sectors")
def sectors_search():
    text = request.args.get("sector", "")
    return sector_search(text)

@app.route("/holdings")
def holdings_search_api():
    text = request.args.get("holding", "")
    return holdings_search(text)

if 'DB_NAME' not in os.environ:
    app.run(debug=True, host="0.0.0.0", port=5000)
