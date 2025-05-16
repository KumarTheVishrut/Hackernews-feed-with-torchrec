import streamlit as st
from feed import fetch_top_hn_articles
from recommender import HackerNewsRecommender
import requests
import time
import json
import pandas as pd

st.set_page_config(
    page_title="Hacker News Recommender",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API settings
API_URL = "http://localhost:5000"
STREAMLIT_MODE = "api"  # Can be 'api' or 'direct'

# Initialize recommender
@st.cache_resource
def get_recommender():
    return HackerNewsRecommender()

recommender = get_recommender()

st.title("Hacker News Recommender")
st.subheader("Powered by TorchRec")

# Sidebar for configuration
st.sidebar.header("Settings")
article_limit = st.sidebar.slider("Number of articles to fetch", 10, 100, 30)
hydrate_content = st.sidebar.checkbox("Hydrate article content", value=True)
mode = st.sidebar.radio("Processing mode", ["API", "Direct"], index=0)
STREAMLIT_MODE = mode.lower()
refresh_data = st.sidebar.button("Refresh Data")

# Cache articles
@st.cache_data(ttl=900, show_spinner=False)
def load_articles_direct(limit, hydrate, refresh=False):
    with st.spinner("Fetching articles..."):
        return fetch_top_hn_articles(limit=limit, hydrate=hydrate)

@st.cache_data(ttl=900, show_spinner=False)
def load_articles_api(limit, hydrate, refresh=False):
    with st.spinner("Fetching articles from API..."):
        try:
            response = requests.get(f"{API_URL}/api/articles?limit={limit}&hydrate={str(hydrate).lower()}")
            if response.status_code == 200:
                data = response.json()
                return pd.DataFrame(data['articles'])
            else:
                st.error(f"Failed to fetch articles from API: {response.status_code}")
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Error connecting to API: {str(e)}")
            # Fallback to direct mode
            return fetch_top_hn_articles(limit=limit, hydrate=hydrate)

# Get recommendations from API
def get_recommendations_api(liked_ids, limit=5):
    try:
        response = requests.post(f"{API_URL}/api/recommendations", 
                               json={"liked_ids": liked_ids, "limit": limit})
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data['recommendations'])
        else:
            st.error(f"Failed to get recommendations from API: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        # Fallback to direct mode
        return pd.DataFrame()

# Get articles based on the selected mode
if STREAMLIT_MODE == 'api':
    articles_df = load_articles_api(article_limit, hydrate_content, refresh=refresh_data)
else:
    articles_df = load_articles_direct(article_limit, hydrate_content, refresh=refresh_data)

# Session state to store liked articles
if 'liked_ids' not in st.session_state:
    st.session_state.liked_ids = []

# Two-column layout
left_col, right_col = st.columns([2, 1])

with right_col:
    st.header("Your Likes")
    if st.session_state.liked_ids:
        liked_df = articles_df[articles_df['id'].isin(st.session_state.liked_ids)]
        for _, row in liked_df.iterrows():
            with st.expander(f"{row['title']} (Score: {row['score']})", expanded=False):
                st.write(f"Author: {row['author']}")
                st.write(f"Comments: {row['comments_count']}")
                if hydrate_content and 'content' in row and row['content']:
                    st.write("Preview:")
                    st.write(row['content'])
                st.markdown(f"[Read more]({row['url']})")
                if st.button(f"Remove from likes 💔", key=f"remove_{row['id']}"):
                    st.session_state.liked_ids.remove(row['id'])
                    st.experimental_rerun()
    else:
        st.info("You haven't liked any articles yet.")
    
    # Recommendations
    st.header("Recommended for You")
    if st.session_state.liked_ids:
        with st.spinner("Generating recommendations..."):
            if STREAMLIT_MODE == 'api':
                recommended_df = get_recommendations_api(st.session_state.liked_ids)
            else:
                recommended_ids = recommender.get_recommendations(articles_df, st.session_state.liked_ids)
                recommended_df = articles_df[articles_df['id'].isin(recommended_ids)]
            
            if not recommended_df.empty:
                for _, row in recommended_df.iterrows():
                    with st.expander(f"{row['title']} (Score: {row['score']})", expanded=False):
                        st.write(f"Author: {row['author']}")
                        st.write(f"Comments: {row['comments_count']}")
                        if hydrate_content and 'content' in row and row['content']:
                            st.write("Preview:")
                            st.write(row['content'])
                        st.markdown(f"[Read more]({row['url']})")
                        
                        if row['id'] not in st.session_state.liked_ids:
                            if st.button(f"Like 👍", key=f"rec_like_{row['id']}"):
                                st.session_state.liked_ids.append(row['id'])
                                st.experimental_rerun()
            else:
                st.info("No strong recommendations yet. Like more articles!")
    else:
        st.info("Like some articles to get recommendations.")

with left_col:
    st.header("Browse Articles")
    
    # Filter options
    st.subheader("Filter Articles")
    col1, col2 = st.columns(2)
    with col1:
        min_score = st.number_input("Minimum score", 0, 1000, 0)
    with col2:
        search_term = st.text_input("Search in title")
    
    # Apply filters
    filtered_df = articles_df
    if min_score > 0:
        filtered_df = filtered_df[filtered_df['score'] >= min_score]
    if search_term:
        filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False)]
    
    # Display articles
    for _, row in filtered_df.iterrows():
        with st.expander(f"{row['title']} (Score: {row['score']})", expanded=False):
            st.write(f"Author: {row['author']}")
            st.write(f"Comments: {row['comments_count']}")
            if hydrate_content and 'content' in row and row['content']:
                st.write("Preview:")
                st.write(row['content'])
            st.markdown(f"[Read more]({row['url']})")
            
            if row['id'] not in st.session_state.liked_ids:
                if st.button(f"Like 👍", key=f"browse_like_{row['id']}"):
                    st.session_state.liked_ids.append(row['id'])
                    st.experimental_rerun()
            else:
                if st.button(f"Unlike 💔", key=f"browse_unlike_{row['id']}"):
                    st.session_state.liked_ids.remove(row['id'])
                    st.experimental_rerun()
