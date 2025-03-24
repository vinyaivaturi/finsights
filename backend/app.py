import json
import os
import pandas as pd
from flask import Flask, render_template, request
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

# def stocks_search(query, top_n=10):
#     # Combine relevant fields into one document for each stock.
#     combined_text = stocks_df[['Company Name', 'Details', 'Sector', 'Industry']].fillna('').agg(' '.join, axis=1)
    
#     # Create a TF-IDF matrix, ignoring common English stop words.
#     vectorizer = TfidfVectorizer(stop_words='english')
#     tfidf_matrix = vectorizer.fit_transform(combined_text)
    
#     # Transform the query into the TF-IDF space.
#     query_tfidf = vectorizer.transform([query])
    
#     # Compute cosine similarity between the query and each stock's text.
#     cos_sim = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
#     stocks_df['similarity'] = cos_sim
    
#     # Sort stocks by similarity (highest first) and return the top N as JSON.
#     results_df = stocks_df.sort_values(by='similarity', ascending=False).head(top_n)
#     return results_df.to_json(orient='records')

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
