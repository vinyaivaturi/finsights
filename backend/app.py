import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Set ROOT_PATH if needed.
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# Get current directory and load the JSON file.
current_directory = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(current_directory, 'init.json')
with open(json_file_path, 'r') as file:
    stocks_data = json.load(file)

# Create a DataFrame from the JSON data.
stocks_df = pd.DataFrame(stocks_data)

app = Flask(__name__)
CORS(app)

def stocks_search(query, top_n=10):
    combined_text = stocks_df[['Company Name', 'Details', 'Sector', 'Industry']].fillna('').agg(' '.join, axis=1)
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(combined_text)
    query_tfidf = vectorizer.transform([query])
    cos_sim = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
    stocks_df['similarity'] = cos_sim
    results_df = stocks_df.sort_values(by='similarity', ascending=False).head(top_n)
    return results_df.to_json(orient='records')

@app.route("/")
def home():
    return render_template('base.html', title="Stock Data Search")

@app.route("/search")
def search_api():
    q = request.args.get("q", "")
    return stocks_search(q)

if 'DB_NAME' not in os.environ:
    app.run(debug=True, host="0.0.0.0", port=5000)
