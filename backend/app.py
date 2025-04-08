import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD

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
    # Combines relevant fields into one document for each stock
    combined_text = stocks_df[['Company Name', 'Details', 'Sector', 'Industry']].fillna('').agg(' '.join, axis=1)
    
    # Creates a TF-IDF matrix, ignoring common English stop words
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(combined_text)

    # Apply SVD for dimensionality reduction (latent semantic analysis)
    svd = TruncatedSVD(n_components=40, random_state=42)
    svd_matrix = svd.fit_transform(tfidf_matrix)

     # Transform the query: first into TF-IDF space then into the SVD (LSA) space.
    query_tfidf = vectorizer.transform([query])
    query_svd = svd.transform(query_tfidf)
    
    cos_sim = cosine_similarity(query_svd, svd_matrix).flatten()
    
    # Save the similarity scores in the DataFrame.
    stocks_df['similarity'] = cos_sim
    
    # Sort the stocks by similarity in descending order and return top_n results.
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
