import re
from datetime import datetime

import nltk
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

from src.utils import logger

from typing import Any, cast

try:
    from src.config import MIN_WORDS_FOR_ANALYSIS
except ImportError:
    MIN_WORDS_FOR_ANALYSIS = 5


def _ensure_nltk_resource(path, name):
    try:
        nltk.data.find(path)
    except LookupError:
        nltk.download(name, quiet=True)


_ensure_nltk_resource("sentiment/vader_lexicon", "vader_lexicon")
_ensure_nltk_resource("tokenizers/punkt", "punkt")
_ensure_nltk_resource("corpora/stopwords", "stopwords")


class SentimentAnalyzer:
    # Class-level shared resources to avoid recreating for each instance
    _stopwords = None
    _lexicon_loaded = False

    def __init__(self):
        self.sid = SentimentIntensityAnalyzer()

        # Reuse stopwords across instances
        if SentimentAnalyzer._stopwords is None:
            SentimentAnalyzer._stopwords = frozenset(nltk.corpus.stopwords.words("english"))
        self.stopwords = SentimentAnalyzer._stopwords
        self.positive_phrases = {
            "breakout": 1.5,
            "surge": 1.5,
            "soar": 1.5,
            "rally": 1.5,
            "jump": 1.3,
            "outperform": 1.3,
            "upgrade": 1.4,
            "beat": 1.3,
            "growth": 1.2,
            "gain": 1.2,
            "positive": 1.2,
            "strong": 1.2,
            "increase": 1.1,
            "rise": 1.1,
            "higher": 1.1,
            "improve": 1.0,
            "improving": 1.0,
            "progress": 1.0,
            "potential": 0.9,
            "opportunity": 0.9,
            "recovery": 0.9,
            "momentum": 0.9,
            "bullish": 1.3,
            "optimistic": 1.1,
            "exceed": 1.2,
            "upside": 1.1,
            "profit": 1.1,
            "profitable": 1.1,
            "dividend": 0.8,
            "buy": 1.2,
            "strong buy": 1.5,
            "overweight": 1.2,
        }
        self.negative_phrases = {
            "plunge": -1.5,
            "tumble": -1.5,
            "crash": -2.0,
            "collapse": -2.0,
            "plummet": -1.8,
            "downgrade": -1.4,
            "miss": -1.3,
            "loss": -1.3,
            "decline": -1.2,
            "drop": -1.2,
            "negative": -1.2,
            "weak": -1.1,
            "decrease": -1.1,
            "fall": -1.1,
            "lower": -1.1,
            "concern": -0.9,
            "risk": -0.9,
            "volatile": -1.0,
            "uncertainty": -1.0,
            "pressure": -0.9,
            "slowdown": -1.1,
            "declining": -1.1,
            "bearish": -1.3,
            "pessimistic": -1.1,
            "underperform": -1.3,
            "sell": -1.5,
            "short": -1.2,
            "downturn": -1.2,
            "recession": -1.3,
            "bankrupt": -2.0,
            "default": -1.8,
            "overvalued": -1.1,
            "bubble": -1.4,
            "correction": -1.2,
            "volatility": -0.8,
        }

    def _preprocess_text(self, text):
        if not text:
            return ""
        # Compile regex patterns once (these are already at module level in practice)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip().lower()
        # Use list comprehension with optimized filtering
        words = [w for w in text.split() if len(w) > 2 and w not in self.stopwords]
        return " ".join(words)

    def _has_enough_content(self, cleaned_text):
        words = [w for w in cleaned_text.split() if w not in self.stopwords and len(w) > 2]
        return len(words) >= int(MIN_WORDS_FOR_ANALYSIS)

    def _neutral_result(self):
        return {
            "compound": 0.0,
            "sentiment": "neutral",
            "confidence": 0.0,
            "keywords_found": [],
            "vader_score": 0.0,
            "textblob_score": 0.0,
            "word_count": 0,
        }

    def analyze_sentiment(self, text):
        if not isinstance(text, str):
            return self._neutral_result()

        cleaned = self._preprocess_text(text)
        if not cleaned:
            return self._neutral_result()

        words = cleaned.split()
        word_count = len(words)
        is_short = not self._has_enough_content(cleaned)

        # Optimize phrase matching - combine positive and negative phrases
        keyword_score = 0.0
        matched_keywords = []

        # Check positive phrases first
        for phrase, weight in self.positive_phrases.items():
            if phrase in cleaned:
                keyword_score += weight
                matched_keywords.append(phrase)

        # Check negative phrases
        for phrase, weight in self.negative_phrases.items():
            if phrase in cleaned:
                keyword_score += weight
                matched_keywords.append(phrase)

        vader_scores = self.sid.polarity_scores(cleaned)
        vader_compound = float(vader_scores.get("compound", 0.0))
        blob = TextBlob(cleaned)
        sent = cast(Any, blob.sentiment)
        blob_score = float(getattr(sent, "polarity", 0.0))

        # Optimize calculations - reduce temporary variables
        keyword_weight = min(1.0, len(matched_keywords) * 0.2)
        base_score = vader_compound * (1.0 - keyword_weight)
        adjusted_score = base_score + (keyword_score * 0.1 * keyword_weight)
        adjusted_score = (adjusted_score + 0.3 * blob_score) / 1.3

        compound = max(-1.0, min(1.0, adjusted_score))

        # Calculate confidence
        length_conf = min(1.0, word_count / 50.0)
        keyword_conf = min(1.0, len(matched_keywords) * 0.3)
        confidence = max(0.1, (length_conf + keyword_conf) / 2.0)
        if is_short:
            confidence = min(confidence, 0.6)

        # Determine label with optimized conditionals
        if compound >= 0.15:
            label = "strongly_positive"
        elif compound >= 0.05:
            label = "positive"
        elif compound <= -0.15:
            label = "strongly_negative"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "compound": compound,
            "sentiment": label,
            "confidence": confidence,
            "keywords_found": matched_keywords,
            "vader_score": vader_compound,
            "textblob_score": blob_score,
            "word_count": word_count,
        }


def _extract_text_from_record(record):
    for key in ("content", "summary", "description", "title"):
        val = record.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def batch_analyze(items):
    # Create analyzer once and reuse for entire batch
    analyzer = SentimentAnalyzer()

    if isinstance(items, pd.DataFrame):
        df = items.copy()
        text_col = None
        for cand in ("content", "summary", "description", "title"):
            if cand in df.columns:
                text_col = cand
                break
        if text_col is None:
            df["sentiment"] = 0.0
            df["sentiment_label"] = "neutral"
            df["sentiment_confidence"] = 0.0
            return df

        # Batch process all texts at once
        sentiments = [analyzer.analyze_sentiment(text) for text in df[text_col].astype(str)]

        # Use vectorized assignment instead of list comprehensions
        df["sentiment"] = [s["compound"] for s in sentiments]
        df["sentiment_label"] = [s["sentiment"] for s in sentiments]
        df["sentiment_confidence"] = [s["confidence"] for s in sentiments]
        df["vader_score"] = [s["vader_score"] for s in sentiments]
        df["textblob_score"] = [s["textblob_score"] for s in sentiments]
        df["word_count"] = [s["word_count"] for s in sentiments]
        return df

    # Optimize dict processing - pre-allocate results list
    results = []
    timestamp = datetime.utcnow().isoformat()  # Calculate once

    for rec in items:
        if not isinstance(rec, dict):
            continue
        text = _extract_text_from_record(rec)
        if not text:
            continue
        try:
            s = analyzer.analyze_sentiment(text)
        except Exception as e:
            logger.error("Error analyzing article: %s", e)
            continue

        # Optimize dict creation - avoid intermediate dict
        enriched = {**rec,
            "sentiment": float(s["compound"]),
            "sentiment_label": s["sentiment"],
            "sentiment_confidence": float(s["confidence"]),
            "sentiment_keywords": s.get("keywords_found", []),
            "vader_score": float(s["vader_score"]),
            "textblob_score": float(s["textblob_score"]),
            "word_count": int(s["word_count"]),
            "analysis_timestamp": timestamp,
        }
        results.append(enriched)

    # Use sorted() with key parameter for efficiency
    results.sort(key=lambda x: x.get("sentiment", 0.0), reverse=True)
    return results
