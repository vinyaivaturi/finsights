# import json
# import os
# from flask import Flask, render_template, request
# from flask_cors import CORS
# from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
# import pandas as pd

# # ROOT_PATH for linking with all your files. 
# # Feel free to use a config.py or settings.py with a global export variable
# os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..",os.curdir))

# # Get the directory of the current script
# current_directory = os.path.dirname(os.path.abspath(__file__))

# # Specify the path to the JSON file relative to the current script
# json_file_path = os.path.join(current_directory, 'init.json')

# # Assuming your JSON data is stored in a file named 'init.json'
# with open(json_file_path, 'r') as file:
#     data = json.load(file)

# if 'sectors' not in data:
#     raise ValueError("Expected 'sectors' field in JSON data")

# sectors_df = pd.DataFrame(data['sectors'])
# print(sectors_df.head())
# holdings_df = pd.DataFrame(data.get('holdings', []))

# app = Flask(__name__)
# CORS(app)

# # Sample search using json with pandas
# # def json_search(query):
# #     query = query.lower()
# #     matches = []
# #     matches = sectors_df[sectors_df['sector'].str.lower().str.contains(query, na=False)]
# #     matches_filtered = matches[['sector', 'weight']]
# #     matches_filtered_json = matches_filtered.to_json(orient='records')
# #     return matches_filtered_json

# # Search function to retrieve sectors - added by vinya
# def sector_search(query):
#     query = query.lower()
#     matches = sectors_df[sectors_df['sector'].str.lower().str.contains(query, na=False)]
#     matches_filtered = matches[['sector', 'weight']]
#     return matches_filtered.to_json(orient='records')

# def holdings_search(query):
#     query = query.lower()
#     matches = holdings_df[
#         (holdings_df['symbol'].str.lower().str.contains(query, na=False)) | 
#         (holdings_df['description'].str.lower().str.contains(query, na=False))
#     ]
#     return matches[['symbol', 'description', 'weight']].to_json(orient='records')

# @app.route("/")
# def home():
#     return render_template('base.html',title="sample html")

# @app.route("/sectors")
# def sectors_search():
#     text = request.args.get("sector", "")
#     return sector_search(text)

# @app.route("/holdings")
# def holdings_search_api():
#     text = request.args.get("holding", "")
#     return holdings_search(text)
    
# if 'DB_NAME' not in os.environ:
#     app.run(debug=True,host="0.0.0.0",port=5000)

import json
import os
import re
import numpy as np
from collections import Counter, defaultdict
from flask import Flask, render_template, request
from flask_cors import CORS
import pandas as pd

# ROOT_PATH for linking with all your files. 
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Specify the path to the JSON file relative to the current script
json_file_path = os.path.join(current_directory, 'init.json')

# Load the JSON data
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Create a DataFrame for sectors and holdings
sectors_df = pd.DataFrame(data['sectors'])
holdings_df = pd.DataFrame(data.get('holdings', []))

# Define stopwords (can be adjusted based on your requirements)
STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'when', 
    'where', 'how', 'of', 'to', 'in', 'for', 'with', 'by', 'about', 'against', 
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 
    'from', 'up', 'down', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 
    'once', 'here', 'there', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 
    'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
}

# Preprocess and tokenize the description text
def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'<.*?>', ' ', text)  # Remove HTML tags if present
    text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
    text = re.sub(r'\d+', ' ', text)  # Remove numbers
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text

def tokenize(text):
    words = text.split()
    return {word for word in words if word not in STOPWORDS and len(word) > 1}

# Tokenize holdings descriptions
holdings_tokens = []
def initialize_holdings_tokens():
    global holdings_tokens, holdings_df
    holdings_df['processed_description'] = holdings_df['description'].apply(preprocess_text)
    holdings_tokens = [tokenize(desc) for desc in holdings_df['processed_description']]
    print(f"Tokenized {len(holdings_df)} holdings")

# Jaccard Similarity
def jaccard_similarity(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union != 0 else 0.0

# Search function to find correlated holdings
def holdings_search(query, top_n=10):
    if not holdings_tokens or not query:
        return '[]'
    try:
        # Preprocess the query and tokenize it
        processed_query = preprocess_text(query)
        query_tokens = tokenize(processed_query)
        
        # Calculate Jaccard similarity between the query and each holding
        similarity_scores = []
        for idx, holding_token_set in enumerate(holdings_tokens):
            score = jaccard_similarity(query_tokens, holding_token_set)
            similarity_scores.append(score)
        
        # Add similarity scores to results
        holdings_df['similarity_score'] = similarity_scores
        top_results = holdings_df.sort_values('similarity_score', ascending=False).head(top_n)
        
        # Return top correlated holdings
        return top_results[['symbol', 'description', 'weight', 'similarity_score']].to_json(orient='records')
    except Exception as e:
        print(f"Error in holdings_search: {str(e)}")
        return json.dumps({"error": str(e)})

# Flask App setup
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template('base.html', title="Stock Search")

@app.route("/holdings", methods=['GET'])
def holdings_search_api():
    query = request.args.get("holding", "")
    return holdings_search(query)

if __name__ == '__main__':
    initialize_holdings_tokens()  # Preprocess the tokens before running the app
    app.run(debug=True, host="0.0.0.0", port=5000)
