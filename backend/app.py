import json
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import random

# Load Data
current_directory = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(current_directory, 'init.json')

# Safely load JSON
try:
    with open(json_file_path, 'r') as file:
        stocks_data = json.load(file)
except Exception as e:
    print("Error loading init.json:", e)
    stocks_data = []

stocks_df = pd.DataFrame(stocks_data)

# Fill missing Beta Values with a safe default (like 1.0)
if 'Beta Value' not in stocks_df.columns:
    stocks_df['Beta Value'] = 1.0
else:
    stocks_df['Beta Value'] = stocks_df['Beta Value'].fillna(1.0)

# Fill other critical missing fields
stocks_df['Sector'] = stocks_df['Sector'].fillna('Unknown')
stocks_df['Details'] = stocks_df['Details'].fillna('')
stocks_df['Industry'] = stocks_df['Industry'].fillna('')
stocks_df['Type'] = stocks_df['Type'].fillna('Stock')

# Initialize app
app = Flask(__name__)
CORS(app)

rejected_tickers = set()

def filter_by_risk(df, risk):
    if risk <= 3:
        return df[(df['Beta Value'] < 0.9)]
    elif risk <= 7:
        return df[(df['Beta Value'] >= 0.9) & (df['Beta Value'] <= 1.2)]
    else:
        return df[(df['Beta Value'] > 1.2) & (df['Type'] == 'Stock')]

def svd_sector_match(df, sector):
    combined = df['Details'] + " " + df['Sector'] + " " + df['Industry']
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(combined)

    svd = TruncatedSVD(n_components=40, random_state=42)
    svd_matrix = svd.fit_transform(tfidf_matrix)

    query_vec = vectorizer.transform([sector])
    query_svd = svd.transform(query_vec)

    similarities = cosine_similarity(query_svd, svd_matrix).flatten()
    df['similarity'] = similarities
    return df.sort_values(by='similarity', ascending=False)

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/search')
def search():
    try:
        risk = int(request.args.get('risk', 5))
        sector = request.args.get('sector', 'No Preference')
        amount = float(request.args.get('amount', 1000))

        df = filter_by_risk(stocks_df, risk)

        if sector.lower() != 'no preference':
            df = svd_sector_match(df, sector)
        else:
            df = df.sample(frac=1)

        df = df[~df['Ticker Symbol'].isin(rejected_tickers)]

        selected = df.head(5)

        rec1 = []
        rec2 = []

        if selected.empty:
            return jsonify([])

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

        return jsonify([rec1, rec2])
    
    except Exception as e:
        print("Error during search:", e)
        return jsonify([])

@app.route('/reject')
def reject():
    ticker = request.args.get('ticker')
    rejected_tickers.add(ticker)
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)