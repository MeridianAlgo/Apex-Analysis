import re
from typing import List, Dict, Any, Tuple
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from datetime import datetime
from pathlib import Path
from src.news_processor import scrape_article_content
from src.utils import handle_errors, logger
from src.config import MIN_WORDS_FOR_ANALYSIS

# Download required NLTK data
nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

class SentimentAnalyzer:
    def __init__(self):
        self.sid = SentimentIntensityAnalyzer()
        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        
        # Enhanced sentiment keywords with weights
        self.positive_phrases = {
            # Strong positive
            'breakout': 1.5, 'surge': 1.5, 'soar': 1.5, 'rally': 1.5, 'jump': 1.3,
            'outperform': 1.4, 'upgrade': 1.4, 'beat': 1.3, 'growth': 1.2, 'gain': 1.2,
            'positive': 1.2, 'strong': 1.2, 'increase': 1.1, 'rise': 1.1, 'higher': 1.1,
            # Moderate positive
            'improve': 1.0, 'improving': 1.0, 'progress': 1.0, 'potential': 0.9,
            'opportunity': 0.9, 'recovery': 0.9, 'momentum': 0.9, 'strengthen': 0.9,
            'bullish': 1.3, 'optimistic': 1.1, 'exceed': 1.2, 'outperform': 1.3,
            'upside': 1.1, 'profit': 1.1, 'profitable': 1.1, 'dividend': 0.8,
            'buy': 1.2, 'strong buy': 1.5, 'outperform': 1.3, 'overweight': 1.2
        }
        
        self.negative_phrases = {
            # Strong negative
            'plunge': -1.5, 'tumble': -1.5, 'crash': -2.0, 'collapse': -2.0, 'plummet': -1.8,
            'downgrade': -1.4, 'miss': -1.3, 'loss': -1.3, 'decline': -1.2, 'drop': -1.2,
            'negative': -1.2, 'weak': -1.1, 'decrease': -1.1, 'fall': -1.1, 'lower': -1.1,
            # Moderate negative
            'concern': -0.9, 'risk': -0.9, 'volatile': -1.0, 'uncertainty': -1.0,
            'pressure': -0.9, 'slowdown': -1.1, 'declining': -1.1, 'bearish': -1.3,
            'pessimistic': -1.1, 'underperform': -1.3, 'sell': -1.5, 'short': -1.2,
            'downturn': -1.2, 'recession': -1.3, 'bankrupt': -2.0, 'default': -1.8,
            'overvalued': -1.1, 'bubble': -1.4, 'correction': -1.2, 'volatility': -0.8
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis."""
        if not text:
            return ""
            
        # Remove HTML tags, URLs, and special characters
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip().lower()
        
        # Remove stopwords and short words
        words = [word for word in text.split() 
                if word not in self.stopwords and len(word) > 2]
        return ' '.join(words)
    
    def _is_meaningful_text(self, text: str) -> bool:
        """Check if text has enough meaningful content for analysis."""
        words = [w for w in text.split() if w not in self.stopwords and len(w) > 2]
        return len(words) >= MIN_WORDS_FOR_ANALYSIS
    
    @handle_errors
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment using multiple methods and return a comprehensive result.
        Enhanced with financial keywords and phrase matching.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dict containing sentiment scores from different methods
        """
        if not text or not isinstance(text, str) or len(text.strip()) < 10:
            return {
                'compound': 0.0,
                'sentiment': 'neutral',
                'confidence': 0.0,
                'keywords_found': []
            }
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text.lower())
        words = cleaned_text.split()
        
        # Initialize scores
        keyword_score = 0
        matched_keywords = []
        
        # Check for positive and negative phrases
        for phrase, weight in {**self.positive_phrases, **self.negative_phrases}.items():
            if phrase in cleaned_text:
                keyword_score += weight
                matched_keywords.append(phrase)
        
        # Get VADER sentiment
        vader_scores = self.sid.polarity_scores(cleaned_text)
        
        # Get TextBlob sentiment
        blob = TextBlob(cleaned_text)
        
        # Combine scores with emphasis on keywords
        keyword_weight = min(1.0, len(matched_keywords) * 0.2)  # Cap keyword influence
        base_score = vader_scores['compound'] * (1 - keyword_weight)
        adjusted_score = base_score + (keyword_score * 0.1 * keyword_weight)
        
        # Normalize to [-1, 1] range
        compound_score = max(-1.0, min(1.0, adjusted_score))
        
        # Calculate confidence based on text length and keyword matches
        length_confidence = min(1.0, len(words) / 50.0)  # More text = more confident
        keyword_confidence = min(1.0, len(matched_keywords) * 0.3)  # More keywords = more confident
        confidence = max(0.1, (length_confidence + keyword_confidence) / 2)
        
        # Determine sentiment
        if compound_score >= 0.15:
            sentiment = 'strongly_positive'
        elif compound_score >= 0.05:
            sentiment = 'positive'
        elif compound_score <= -0.15:
            sentiment = 'strongly_negative'
        elif compound_score <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'compound': compound_score,
            'sentiment': sentiment,
            'confidence': confidence,
            'keywords_found': matched_keywords,
            'vader_score': vader_scores['compound'],
            'textblob_score': blob.sentiment.polarity,
            'word_count': len(words)
        }

def batch_analyze(articles: List[Dict]) -> List[Dict]:
    if not articles:
        return []
        
    analyzer = SentimentAnalyzer()
    updated = []
    
    for article in articles:
        if not article or not isinstance(article, dict):
            continue
            
        try:
            # Get content from article, fallback to title if content is not available
            content = article.get('content', '')
            if not content and 'title' in article:
                content = article['title']
            
            if not content:
                continue
                
            # Analyze the article content
            sentiment = analyzer.analyze_sentiment(content)
            
            # Add detailed sentiment data to article
            article.update({
                'sentiment': float(sentiment['compound']),
                'sentiment_label': sentiment['sentiment'],
                'sentiment_confidence': float(sentiment['confidence']),
                'sentiment_keywords': sentiment.get('keywords_found', []),
                'vader_score': float(sentiment.get('vader_score', 0)),
                'textblob_score': float(sentiment.get('textblob_score', 0)),
                'word_count': int(sentiment.get('word_count', 0)),
                'analysis_timestamp': datetime.now().isoformat()
            })
            
            updated.append(article)
            
        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            continue
    
    # Sort articles by sentiment score (most positive first)
    return sorted(updated, key=lambda x: x.get('sentiment', 0), reverse=True)
