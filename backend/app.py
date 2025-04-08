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
with open(json_file_path, 'r') as file:
    stocks_data = json.load(file)
stocks_df = pd.DataFrame(stocks_data)

# Initialize app
app = Flask(__name__)
CORS(app)

# Global variables
rejected_tickers = set()

def filter_by_risk(df, risk):
    if risk <= 3:
        return df[(df['Beta Value'] < 0.9)]
    elif risk <= 7:
        return df[(df['Beta Value'] >= 0.9) & (df['Beta Value'] <= 1.2)]
    else:
        return df[(df['Beta Value'] > 1.2) & (df['Type'] == 'Stock')]

def svd_sector_match(df, sector):
    combined = df['Details'].fillna('') + " " + df['Sector'].fillna('') + " " + df['Industry'].fillna('')
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
    risk = int(request.args.get('risk', 5))
    sector = request.args.get('sector', 'No Preference')
    amount = float(request.args.get('amount', 1000))

    df = filter_by_risk(stocks_df, risk)

    if sector.lower() != 'no preference':
        df = svd_sector_match(df, sector)
    else:
        df = df.sample(frac=1)

    # Remove rejected
    df = df[~df['Ticker Symbol'].isin(rejected_tickers)]

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

    return jsonify([rec1, rec2])

@app.route('/reject')
def reject():
    ticker = request.args.get('ticker')
    rejected_tickers.add(ticker)
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
