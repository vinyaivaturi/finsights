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
    stocks_data = json.load(file)

# Create DataFrames
stocks_df = pd.DataFrame(stocks_data)

app = Flask(__name__)
CORS(app)

def stocks_search(query):
    query = query.lower()
    mask = (
        stocks_df["Company Name"].str.lower().str.contains(query, na=False) |
        stocks_df["Details"].str.lower().str.contains(query, na=False) |
        stocks_df["Sector"].str.lower().str.contains(query, na=False) |
        stocks_df["Industry"].str.lower().str.contains(query, na=False)
    )
    matches = stocks_df[mask]
    return matches.to_json(orient='records')

@app.route("/")
def home():
    return render_template('base.html', title="Stock Data Search")

@app.route("/search")
def search_api():
    q = request.args.get("q", "")
    return stocks_search(q)

if 'DB_NAME' not in os.environ:
    app.run(debug=True, host="0.0.0.0", port=5000)
