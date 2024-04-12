"""
Test Flask routes and key functions defined in app/main.py
"""

from io import BytesIO

from tests.conftest import app, client
from app.main import analyze_sentiment, contains_lemmatized_keyword, categorize_text, group_by_sentiment


texts = [
    "Love it! Works perfectly.", 
    "The customer service was terrible.",
    "Beautiful design and great functionality. Highly recommend it.",
    "The product arrived earlier than expected."
    ]

expected_vader_scores = [
    {'neg': 0.0, 'neu': 0.187, 'pos': 0.813, 'compound': 0.8655}, 
    {'neg': 0.437, 'neu': 0.563, 'pos': 0.0, 'compound': -0.4767}, 
    {'neg': 0.0, 'neu': 0.317, 'pos': 0.683, 'compound': 0.8955}, 
    {'neg': 0.0, 'neu': 1.0, 'pos': 0.0, 'compound': 0.0}
    ]

def test_route_index_returns_template(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    assert b"Simple Sentiment Analysis" in response.data
    assert b'<form id="form"' in response.data

def test_route_analyze_sentiment_with_no_file(client):
    response = client.post('/analyze-sentiment')
    assert response.status_code == 200
    assert b'Error' in response.data
    assert b'No file in request.' in response.data

def test_route_analyze_sentiment_with_empty_filename(client):
    response = client.post('/analyze-sentiment', content_type='multipart/form-data', data={
        'file': (BytesIO(b''), '')
    })
    assert response.status_code == 200
    assert b'Error' in response.data
    assert b'Please provide a file to analyze.' in response.data

def test_analyze_sentiment_vader_scores():
    vader_scores = analyze_sentiment(texts)
    for scores in vader_scores:
        assert 'compound' in scores
    assert len(texts) == len(vader_scores)
    assert vader_scores == expected_vader_scores

def test_contains_lemmatized_keyword():
    assert contains_lemmatized_keyword(texts[2], ['design'])
    assert contains_lemmatized_keyword(texts[0], ['work', 'penguin', 'dog'])
    assert not contains_lemmatized_keyword(texts[0], ['elephant', 'cat'])

def test_categorize_text():
    results = categorize_text(texts)
    expected_results = {
        'product': ['Beautiful design and great functionality. Highly recommend it.', 
                    'The product arrived earlier than expected.'], 
        'delivery': ['The product arrived earlier than expected.'], 
        'service': ['The customer service was terrible.'], 
        'price': []
        }
    empty_results = categorize_text([])
    assert len(results) > 0
    assert results == expected_results
    for category in empty_results.values():
        assert category == []

def test_group_by_sentiment():
    results = group_by_sentiment(texts, expected_vader_scores)
    expected_keys = {'positive', 'neutral', 'negative'}
    expected_results = {
        'positive': ['Beautiful design and great functionality. Highly recommend it.', 'Love it! Works perfectly.'],
        'neutral': ['The product arrived earlier than expected.'], 
        'negative': ['The customer service was terrible.']
        }
    assert group_by_sentiment(texts, []) == {}
    assert group_by_sentiment(texts, [{'hello': 1},{},{},{}]) == {}
    assert expected_keys.issubset(set(expected_results.keys()))
    assert results == expected_results