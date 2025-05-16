import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from functools import lru_cache

@lru_cache(maxsize=100)
def fetch_article_content(url):
    """Fetch and extract article content using BeautifulSoup"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return "Content not available"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to extract the article content
        # First, remove script and style elements
        for script in soup(['script', 'style']):
            script.extract()
            
        # Extract text from paragraphs (most common for articles)
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text().strip() for p in paragraphs[:3]])
        
        # If no paragraphs found, try to get the main content
        if not content:
            content = soup.get_text()[:500]
            
        return content.strip()[:500] + "..." if len(content) > 500 else content
    except Exception as e:
        return f"Error fetching content: {str(e)[:100]}"

def fetch_top_hn_articles(limit=20, hydrate=False):
    """Fetch top Hacker News articles with optional content hydration"""
    top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:limit]
    articles = []

    for item_id in top_ids:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
        if item and 'title' in item and 'url' in item:
            article = {
                'id': item['id'],
                'title': item['title'],
                'url': item.get('url', 'N/A'),
                'score': item.get('score', 0),
                'time': item.get('time', 0),
                'author': item.get('by', 'unknown'),
                'comments_count': item.get('descendants', 0)
            }
            
            # Hydrate content if requested
            if hydrate and 'url' in item and item['url']:
                article['content'] = fetch_article_content(item['url'])
            else:
                article['content'] = ""
                
            articles.append(article)

    return pd.DataFrame(articles)

def get_article_by_id(article_id):
    """Fetch a specific article by ID"""
    try:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{article_id}.json").json()
        if item and 'title' in item:
            article = {
                'id': item['id'],
                'title': item['title'],
                'url': item.get('url', 'N/A'),
                'score': item.get('score', 0),
                'time': item.get('time', 0),
                'author': item.get('by', 'unknown'),
                'comments_count': item.get('descendants', 0)
            }
            
            if 'url' in item and item['url']:
                article['content'] = fetch_article_content(item['url'])
            else:
                article['content'] = ""
                
            return article
        return None
    except:
        return None
