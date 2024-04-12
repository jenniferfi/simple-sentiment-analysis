"""
Flask app for sentiment analysis of text in uploaded Excel files.
Categorizes text into topics using WordNetLemmatizer from NLTK.
Analyzes sentiment using VADER lexicon from NLTK.
"""

import os
import nltk

import pandas as pd

from flask import Flask, render_template, request
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
from openpyxl.utils import column_index_from_string


# Create Flask app, determine debug mode and enable automatic template reloading in debug mode
app = Flask(__name__)
debug = os.environ.get("DEBUG", False)
app.config['TEMPLATES_AUTO_RELOAD'] = debug

# Download Punkt sentence tokenizer, Part-of-Speech tagger, VADER lexicon and Wordnet corpus
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('vader_lexicon')
nltk.download('wordnet')

sentiments = ["positive", "neutral", "negative"]

def analyze_sentiment(texts: list) -> list:
    """ Calculate vader scores for text input. """
    analyzer = SentimentIntensityAnalyzer()
    vader_scores = []

    for text in texts:
        try:
            scores = analyzer.polarity_scores(text)
            vader_scores.append(scores)
        except (TypeError, ValueError) as e:
            print(f"Error analyzing sentiment for text '{text}': {e}")

    return vader_scores


def contains_lemmatized_keyword(text: str, keywords: list) -> bool:
    """ Check if text input matches any of the given keywords. """
    try:
        lemmatizer = WordNetLemmatizer()
        text_lemma = lemmatizer.lemmatize(text.lower())
        lemmatized_keywords = [lemmatizer.lemmatize(keyword) for keyword in keywords]
        return any(keyword in text_lemma for keyword in lemmatized_keywords)
    except LookupError:
        return False


def categorize_text(texts: list) -> dict:
    """ Sort text input into topic categories if they contain defined keywords for topic. """

    # Define categories and keywords
    topic_keywords = {
        'product': ['product', 'item', 'quality', 'feature', 'design', 'selection'],
        'delivery': ['delivery', 'ship', 'receive', 'arrive'],
        'service': ['email', 'support', 'help', 'service', 'customer'],
        'price': ['price', 'expensive', 'dollar', 'value', 'afford', 'budget']
    }

    texts_by_topic = { topic: [] for topic in topic_keywords}

    for text in texts:
        text_lower = text.lower()

        # Check for matches in each category
        for topic, keywords in topic_keywords.items():
            if contains_lemmatized_keyword(text_lower, keywords):
                texts_by_topic[topic].append(text)

    return texts_by_topic


def group_by_sentiment(texts: list, vader_scores: list) -> dict:
    """ Group text by sentiment and rank text from strongest sentiment to weakest """
    feedback_by_sentiment = {
        sentiment: [] for sentiment in sentiments
    }

    try:
        assert len(texts) > 0
        assert len(texts) == len(vader_scores)
    except AssertionError:
        print("Error grouping text by sentiment: number of texts and vader scores do not match")
        return {}

    try:
        for idx, text in enumerate(texts):
            score = vader_scores[idx]["compound"]
            if score > 0:
                feedback_by_sentiment["positive"].append((text, score))
            elif score < 0:
                feedback_by_sentiment["negative"].append((text, score))
            else:
                feedback_by_sentiment["neutral"].append((text, score))
    except (IndexError, KeyError, TypeError) as e:
        print(f"Error grouping text by sentiment: {e}")
        return {}

    # Sort texts from strongest sentiment to weakest and keep only text
    for sentiment, feedback in feedback_by_sentiment.items():
        feedback_by_sentiment[sentiment] = sorted(feedback, key=lambda x: abs(x[1]), reverse=True)
        feedback_by_sentiment[sentiment] = [item[0] for item in feedback_by_sentiment[sentiment]]

    return feedback_by_sentiment


def format_results(all_texts: list, by_topic: dict) -> dict:
    """ Compile results grouped by topic and sentiment. """
    results = {}

    try:
        if overall_vader := analyze_sentiment(all_texts):
            results['overall'] = group_by_sentiment(all_texts, overall_vader)

        for topic, texts in by_topic.items():
            if vader_scores := analyze_sentiment(texts):
                results[topic] = group_by_sentiment(texts, vader_scores)

    except (TypeError, KeyError) as e:
        print(f"Error formatting results: {str(e)}")

    return results


def format_charts(data: dict) -> dict:
    """ Calculate and format chart data. """
    charts = {}

    green = '#8bcb90'
    yellow = '#ffbf5b'
    red = '#ae2c36'
    teal = '#2980b9'

    # Calculate feedback sentiment distribution
    distribution = {}
    for topic in data:
        try:
            n_total = sum(len(sentiments) for sentiments in data[topic].values())
            percentages = [round(len(data[topic][sent])/n_total * 100, 2) if n_total else 0 for sent in sentiments]
            distribution[topic] = percentages
        except (KeyError, ZeroDivisionError) as e:
            print(f"Error calculating distribution of sentiments for topic '{topic}': {e}")
            continue

    # Bar chart displaying amount of feedback overall and for each topic
    charts['n-feedback'] = {
        'labels': [key.capitalize() for key in data.keys()],
        'data': [sum(len(sentiments) for sentiments in data[topic].values()) for topic in data],
        'color': teal
    }

    # Pie chart displaying distribution of sentiments for feedback overall
    try:
        charts['overall-pie'] = {
            'labels': [sentiment.capitalize() for sentiment in sentiments],
            'data': distribution['overall'],
            'colors': [green, yellow, red]
        }
    except KeyError:
        charts['overall-pie'] = {}

    # Stacked bar chart displaying distribution of sentiments for each topic
    charts['topic-sentiment'] = {
        'labels': [topic.capitalize() for topic in distribution if topic != 'overall'],
        'data': [{ 
                    'label': 'Positive', 
                    'backgroundColor': green, 
                    'data': [percent[0] for topic, percent in distribution.items() if topic != 'overall'], 
                }, {
                    'label': 'Neutral', 
                    'backgroundColor': yellow, 
                    'data': [percent[1] for topic, percent in distribution.items() if topic != 'overall'], 
                }, {
                    'label': 'Negative', 
                    'backgroundColor': red, 
                    'data': [percent[2] for topic, percent in distribution.items() if topic != 'overall'], 
                }]
    }

    return charts


@app.route('/')
def index():
    """ Serve index page uploading function. """
    return render_template('index.html')


@app.route('/analyze-sentiment', methods=['POST'])
def process_file():
    """ Handle form data, process text from Excel file and serve analysis or error page to user. """
    if request.method == 'POST':
        # Check that file is provided
        if 'file' not in request.files:
            return render_template('error.html', errormessage='No file in request.')

        file = request.files['file']

        if not file or file.filename == '':
            return render_template('error.html', errormessage='Please provide a file to analyze.')

        # Check that column input is letters and transform to column index
        col_input = request.form['column-input']
        col_input = ''.join(char.upper() for char in col_input if char.isalpha())
        column = column_index_from_string(col_input)-1

        try:
            # Read uploaded file and transform content of chosen column to list
            df = pd.read_excel(file)
            text_input = df.iloc[:, column].dropna().tolist() # Remove empty cells

            n_feedback = len(text_input)
            if not n_feedback:
                msg = 'Please, check that your chosen column contains text.'
                return render_template('error.html', errormessage=msg)

            # Transform feedback into individual sentences
            text = ' '.join(text_input)
            sentences = nltk.sent_tokenize(text)

            # Analyse and format results
            feedback_by_topic = categorize_text(sentences)
            grouped_text = format_results(text_input, feedback_by_topic)
            if not grouped_text:
                msg = 'Could not perform analysis. Please check that chosen column contains text.'
                return render_template('error.html', errormessage=msg)

            charts = format_charts(grouped_text) # Missing charts are handled in front

            return render_template('analysis.html', grouped_text=grouped_text, charts=charts)

        except (MemoryError, FileNotFoundError) as e:
            print(f'Error in processing user input (likely reading Excel file): {e}.')
        except (UnicodeDecodeError, ValueError, TypeError, ) as e:
            print(f'Error processing textual feedback {e}.')
        except (ModuleNotFoundError, LookupError) as e:
            print(f"Error processing user input (likely in transforming feedback using nltk): {e}")

    msg = "Could not perform analysis. Please make sure that chosen file and column contains text."
    return render_template('error.html', errormessage='Could not perform analysis.')


if __name__ == '__main__':
    app.run(debug=debug, host=os.environ.get("HOST", "0.0.0.0"), port=os.environ.get("PORT", "5001"))
