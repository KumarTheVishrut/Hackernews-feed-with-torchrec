import torch
import torchrec
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from torchrec.sparse.jagged_tensor import KeyedJaggedTensor
from torchrec.models.dlrm import DLRM, DLRMTrain

class HackerNewsRecommender:
    def __init__(self, embedding_dim=64, hidden_layers=(256, 128, 64)):
        self.embedding_dim = embedding_dim
        self.hidden_layers = hidden_layers
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.word_to_idx = {}  # Vocabulary mapping
        self.next_word_idx = 1  # Start from 1, 0 is for padding
        self.article_embeddings = {}  # Cache for article embeddings
        
    def initialize_model(self, vocab_size):
        """Initialize the TorchRec DLRM model"""
        sparse_arch = {"features": {"title_words": {"cardinality": vocab_size, "embedding_dim": self.embedding_dim}}}
        dense_arch = [self.embedding_dim * 2]  # For the article score and time features
        over_arch = list(self.hidden_layers) + [1]  # Output layer with 1 neuron
        
        self.model = DLRM(
            sparse_arch=sparse_arch,
            dense_arch=dense_arch,
            over_arch=over_arch,
        ).to(self.device)
            
    def _tokenize_text(self, text: str) -> List[int]:
        """Convert text to token IDs"""
        words = text.lower().split()
        token_ids = []
        
        for word in words:
            if word not in self.word_to_idx:
                self.word_to_idx[word] = self.next_word_idx
                self.next_word_idx += 1
            token_ids.append(self.word_to_idx[word])
            
        return token_ids
    
    def _prepare_batch(self, articles_df: pd.DataFrame) -> Tuple[KeyedJaggedTensor, torch.Tensor]:
        """Prepare a batch of articles for inference"""
        # Process sparse features (article titles)
        keys = []
        values = []
        lengths = []
        
        for _, row in articles_df.iterrows():
            title_tokens = self._tokenize_text(row['title'])
            keys.append("title_words")
            values.extend(title_tokens)
            lengths.append(len(title_tokens))
        
        sparse_features = KeyedJaggedTensor(
            keys=keys,
            values=torch.tensor(values, dtype=torch.int32).to(self.device),
            lengths=torch.tensor(lengths, dtype=torch.int32).to(self.device),
        )
        
        # Process dense features (score and time)
        dense_features = torch.tensor(
            articles_df[['score', 'time']].values, 
            dtype=torch.float32
        ).to(self.device)
        
        return sparse_features, dense_features
    
    def get_article_embeddings(self, articles_df: pd.DataFrame) -> Dict[int, np.ndarray]:
        """Get embeddings for articles using the model"""
        # Initialize model if not already done
        if self.model is None:
            vocab_size = len(self.word_to_idx) + 1  # +1 for padding
            if vocab_size < 100:  # Ensure minimum vocabulary size
                vocab_size = 100
            self.initialize_model(vocab_size)
        
        # Get embeddings for each article
        article_embeddings = {}
        with torch.no_grad():
            sparse_features, dense_features = self._prepare_batch(articles_df)
            # Use the model's first layers to get embeddings
            embeddings = self.model.sparse.forward(sparse_features)
            
            # Combine with dense features
            for i, article_id in enumerate(articles_df['id']):
                # Combine sparse and dense features
                article_embeddings[article_id] = embeddings.values().cpu().numpy()
        
        return article_embeddings
    
    def get_recommendations(self, articles_df: pd.DataFrame, liked_ids: List[int], top_n: int = 5) -> List[int]:
        """Get recommendations based on liked articles"""
        if not liked_ids:
            # If no likes, return top articles by score
            return articles_df.sort_values('score', ascending=False).head(top_n)['id'].tolist()
        
        # Get embeddings for all articles
        all_embeddings = self.get_article_embeddings(articles_df)
        
        # Calculate similarity between liked articles and other articles
        liked_embeddings = np.mean([all_embeddings[article_id] for article_id in liked_ids 
                                   if article_id in all_embeddings], axis=0)
        
        # Filter out already liked articles
        candidate_articles = articles_df[~articles_df['id'].isin(liked_ids)]
        
        # Calculate similarities to candidate articles
        similarities = {}
        for _, row in candidate_articles.iterrows():
            article_id = row['id']
            if article_id in all_embeddings:
                # Cosine similarity
                similarity = np.dot(liked_embeddings, all_embeddings[article_id]) / (
                    np.linalg.norm(liked_embeddings) * np.linalg.norm(all_embeddings[article_id])
                )
                similarities[article_id] = similarity
        
        # Sort by similarity and return top N
        recommended_ids = sorted(similarities.keys(), key=lambda k: similarities[k], reverse=True)[:top_n]
        return recommended_ids 