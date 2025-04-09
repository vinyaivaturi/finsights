import json
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import random

#print("DEBUG: Current working directory:", os.getcwd())
#print("DEBUG: List of files:", os.listdir(os.getcwd()))

# Load Data
current_directory = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(current_directory, 'init.json')
#print(f"DEBUG: Attempting to load JSON from {json_file_path}")

# Safely load JSON
try:
    with open(json_file_path, 'r') as file:
        stocks_data = json.load(file)
    #print(f"DEBUG: Loaded init.json successfully. Number of records: {len(stocks_data)}")
except Exception as e:
    #print("ERROR: Failed to load init.json:", e)
    stocks_data = []

stocks_df = pd.DataFrame(stocks_data)

# Create DataFrame
try:
    stocks_df = pd.DataFrame(stocks_data)
    print(f"DEBUG: Created DataFrame. Columns are: {stocks_df.columns.tolist()}")
except Exception as e:
    print("ERROR: Failed to create DataFrame from JSON:", e)

# Fill missing Beta Values with a safe default
if 'Beta Value' not in stocks_df.columns:
    print("WARNING: 'Beta Value' column missing. Adding default Beta = 1.0")
    stocks_df['Beta Value'] = 1.0
else:
    stocks_df['Beta Value'] = stocks_df['Beta Value'].fillna(1.0)

print("DEBUG: executed Beta block")

# Fill other critical missing fields
stocks_df['Sector'] = stocks_df['Sector'].fillna('Unknown')
stocks_df['Details'] = stocks_df['Details'].fillna('')
stocks_df['Industry'] = stocks_df['Industry'].fillna('')
stocks_df['Type'] = stocks_df['Type'].fillna('Stock')

print("DEBUG: filled missing fields if any")

# Initialize app
app = Flask(__name__)
CORS(app)

rejected_tickers = set()

def filter_by_risk(df, risk):
    print(f"DEBUG: Filtering stocks by risk level: {risk}")
    
    if risk <= 3:
        return df[(df['Beta Value'] < 0.9)]
    elif risk <= 7:
        return df[(df['Beta Value'] >= 0.9) & (df['Beta Value'] <= 1.2)]
    else:
        return df[(df['Beta Value'] > 1.2) & (df['Type'] == 'Stock')]

def svd_sector_match(df, sector):
    print(f"DEBUG: Running SVD + TF-IDF for sector matching: {sector}")
    combined = df['Details'] + " " + df['Sector'] + " " + df['Industry']
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(combined)
    svd = TruncatedSVD(n_components=40, random_state=42)
    svd_matrix = svd.fit_transform(tfidf_matrix)
    query_vec = vectorizer.transform([sector])
    query_svd = svd.transform(query_vec)
    similarities = cosine_similarity(query_svd, svd_matrix).flatten()
    df = df.copy() 
    df['similarity'] = similarities
    return df.sort_values(by='similarity', ascending=False)

@app.route('/')
def home():
    print("DEBUG: Serving Home Page")
    return render_template('base.html')

@app.route('/search')
def search():
    try:
        risk = int(request.args.get('risk', 5))
        sector = request.args.get('sector', 'No Preference')
        amount = float(request.args.get('amount', 1000))
        print(f"DEBUG: Received search request with risk={risk}, sector={sector}, amount={amount}")

        df = filter_by_risk(stocks_df, risk)

        if sector.lower() != 'no preference':
            df = svd_sector_match(df, sector)
        else:
            df = df.sample(frac=1)

        df = df[~df['Ticker Symbol'].isin(rejected_tickers)]

        if df.empty:
            return jsonify({"message": "No matching investments found."})  # Clean response

        selected = df.head(5)

        rec1 = []
        rec2 = []

        equal_investment = amount / len(selected)
        total_beta = sum(selected['Beta Value'])

        for _, row in selected.iterrows():
            weighted_investment = (row['Beta Value'] / total_beta) * amount
            info = row.to_dict()
            info['Investment'] = equal_investment
            rec1.append(info)

            info2 = row.to_dict()
            info2['Investment'] = weighted_investment
            rec2.append(info2)

        print("DEBUG: Successfully generated 2 recommendation sets.")
        return jsonify([rec1, rec2])
    
    except Exception as e:
        print("Error during search:", e)
        return jsonify({"message": "Error processing request."})

@app.route('/reject')
def reject():
    ticker = request.args.get('ticker')
    rejected_tickers.add(ticker)
    print(f"DEBUG: Ticker rejected: {ticker}")
    return '', 204

if __name__ == '__main__':
    print("DEBUG: Starting Flask app on port 5000...")
    app.run(debug=True)