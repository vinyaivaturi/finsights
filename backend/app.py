import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
import pandas as pd

# ROOT_PATH for linking with all your files. 
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..",os.curdir))

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Specify the path to the JSON file relative to the current script
json_file_path = os.path.join(current_directory, 'init.json')

# Assuming your JSON data is stored in a file named 'init.json'
with open(json_file_path, 'r') as file:
    data = json.load(file)

app = Flask(__name__)
CORS(app)

# Sample search using json with pandas
# def json_search(query):
#     query = query.lower()
#     matches = []
#     matches = sectors_df[sectors_df['sector'].str.lower().str.contains(query, na=False)]
#     matches_filtered = matches[['sector', 'weight']]
#     matches_filtered_json = matches_filtered.to_json(orient='records')
#     return matches_filtered_json

# Search function to retrieve sectors - added by vinya
# def sector_search(etf, query):
#     query = query.lower()
#     if etf not in data:
#         return json.dumps({"error": "ETF not found"})
    
#     sectors_df = pd.DataFrame(data[etf].get('sectors', []))
#     matches = sectors_df[sectors_df['sector'].str.lower().str.contains(query, na=False)]
#     return matches[['sector', 'weight']].to_json(orient='records')

# def holdings_search(etf, query):
#     query = query.lower()
#     if etf not in data:
#         return json.dumps({"error": "ETF not found"})
    
#     holdings_df = pd.DataFrame(data[etf].get('holdings', []))
#     matches = holdings_df[
#         (holdings_df['symbol'].str.lower().str.contains(query, na=False)) | 
#         (holdings_df['description'].str.lower().str.contains(query, na=False))
#     ]
#     return matches[['symbol', 'description', 'weight']].to_json(orient='records')

# adding temporarily
# Function to get sector data across all ETFs
@app.route("/sectors", methods=["GET"])
def get_sectors():
    query = request.args.get("sector", "").lower()
    results = []

    for etf, etf_data in data.items():
        sectors = etf_data.get("sectors", [])
        matches = [
            {"etf": etf, "sector": s["sector"], "weight": s["weight"]}
            for s in sectors if query in s["sector"].lower()
        ]
        results.extend(matches)
    
    return jsonify(results)

# Function to get holdings data across all ETFs
@app.route("/holdings", methods=["GET"])
def get_holdings():
    query = request.args.get("holding", "").lower()
    results = []

    for etf, etf_data in data.items():
        holdings = etf_data.get("holdings", [])
        matches = [
            {"etf": etf, "symbol": h["symbol"], "description": h["description"], "weight": h["weight"]}
            for h in holdings if query in h["symbol"].lower() or query in h["description"].lower()
        ]
        results.extend(matches)

    return jsonify(results)

@app.route("/")
def home():
    return render_template('base.html',title="sample html")

@app.route("/sectors")
def sectors_search():
    etf = request.args.get("etf", "").upper()
    text = request.args.get("sector", "")
    return sector_search(etf, text)

@app.route("/holdings")
def holdings_search_api():
    etf = request.args.get("etf", "").upper()
    text = request.args.get("holding", "")
    return holdings_search(etf, text)

if 'DB_NAME' not in os.environ:
    app.run(debug=True,host="0.0.0.0",port=5000)