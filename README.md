# Better Hacker News Feed with TorchRec

This is an enhanced Hacker News feed application that uses TorchRec for advanced recommendation capabilities and content hydration for a better reading experience.

## Features

- Content hydration: Article summaries are extracted from the original articles
- TorchRec-based recommendations: Uses deep learning to provide better article recommendations
- Dual interfaces:
  - Streamlit web UI for interactive browsing
  - Flask API for programmatic access
- Docker support for easy deployment

## Architecture

The application consists of these main components:

1. `feed.py`: Fetches and hydrates content from Hacker News API
2. `recommender.py`: TorchRec-based recommendation engine
3. `app.py`: Streamlit web UI
4. `api.py`: Flask REST API
5. Docker configuration for containerization

## Running the Application

### Using Docker (Recommended)

The easiest way to run the application is using Docker Compose:

```bash
docker-compose up
```

This will build and start the application. The Streamlit UI will be available at http://localhost:8501 and the API at http://localhost:5000.

### Manual Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Start the Flask API:

```bash
python api.py
```

3. In a separate terminal, start the Streamlit UI:

```bash
streamlit run app.py
```

## API Endpoints

The application provides the following API endpoints:

- `GET /api/articles?hydrate=true&limit=30`: Get a list of articles
- `GET /api/article/{article_id}`: Get a specific article with hydrated content
- `POST /api/recommendations`: Get recommendations based on liked articles
  - Request body: `{"liked_ids": [123, 456], "limit": 5}`

## How the Recommender Works

The application uses TorchRec's DLRM (Deep Learning Recommendation Model) to generate embeddings for articles based on their titles and metadata. These embeddings are then used to find similar articles based on the user's liked articles.

The recommendation engine factors in:
- Article content
- Article scores
- User preferences based on liked articles

## Environment Variables

- None required, but you can customize the application using environment variables in the docker-compose.yml file. 