import re
from textblob import TextBlob
from news_processor import scrape_article_content
from utils import handle_errors

@handle_errors
def analyze_sentiment(text: str) -> float:
    clean = re.sub(r'[^\w\s]', '', text.lower())
    blob = TextBlob(clean)
    return blob.sentiment.polarity

def batch_analyze(articles: list[dict]) -> list[dict]:
    updated = []
    for article in articles:
        content = scrape_article_content(article['link'])
        if content:
            article['content'] = content
            sentiment = analyze_sentiment(content)
            article['sentiment'] = float(sentiment) if sentiment is not None else 0.0
        else:
            article['sentiment'] = 0.0
        updated.append(article)
    return updated
