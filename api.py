from flask import Flask, jsonify, request
import json
from feed import fetch_top_hn_articles, get_article_by_id
from recommender import HackerNewsRecommender
import pandas as pd

app = Flask(__name__)

# Create a recommender instance
recommender = HackerNewsRecommender()

# Cache for articles
article_cache = {}
last_fetch_time = 0

def get_articles(force_refresh=False):
    """Get articles with caching"""
    import time
    global article_cache, last_fetch_time
    current_time = time.time()
    
    # Refresh cache if it's empty, or if it's older than 15 minutes, or if forced
    if not article_cache or (current_time - last_fetch_time > 900) or force_refresh:
        article_cache = fetch_top_hn_articles(limit=50, hydrate=True)
        last_fetch_time = current_time
        
    return article_cache

@app.route('/api/articles', methods=['GET'])
def get_all_articles():
    """Get all articles, optionally with hydrated content"""
    hydrate = request.args.get('hydrate', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 30))
    
    # Get articles
    df = fetch_top_hn_articles(limit=limit, hydrate=hydrate)
    
    # Convert to JSON
    return jsonify({
        'status': 'success',
        'count': len(df),
        'articles': df.to_dict('records')
    })

@app.route('/api/article/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """Get a specific article with hydrated content"""
    article = get_article_by_id(article_id)
    
    if article:
        return jsonify({
            'status': 'success',
            'article': article
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Article {article_id} not found'
        }), 404

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get recommendations based on liked articles"""
    # Get request data
    data = request.json
    liked_ids = data.get('liked_ids', [])
    limit = data.get('limit', 5)
    
    if not liked_ids:
        return jsonify({
            'status': 'error',
            'message': 'No liked articles provided'
        }), 400
    
    # Get articles
    df = get_articles()
    
    # Get recommendations
    recommended_ids = recommender.get_recommendations(df, liked_ids, top_n=limit)
    recommended_articles = df[df['id'].isin(recommended_ids)].to_dict('records')
    
    return jsonify({
        'status': 'success',
        'count': len(recommended_articles),
        'recommendations': recommended_articles
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 