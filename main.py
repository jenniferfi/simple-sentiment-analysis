"""
Flask app for sentiment analysis of text in uploaded Excel files.
Analyzes sentiment using VADER lexicon from NLTK.
"""

import os
import nltk

import pandas as pd

from flask import Flask, render_template, request
from nltk.sentiment import SentimentIntensityAnalyzer
from openpyxl.utils import column_index_from_string


# Create Flask app, enable automatic template reloading and determine debug mode
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
debug = os.environ.get("DEBUG", False)

# Download Punkt sentence tokenizer, Part-of-Speech tagger and VADER lexicon
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('vader_lexicon')

analyzer = SentimentIntensityAnalyzer()

# TODO: Development idea: keywords on topics

def analyze_sentiment(texts: list) -> list:
    """ Analyze text input with nltk. """
    vader_scores = []
    for text in texts:
        try:
            scores = analyzer.polarity_scores(text)
            vader_scores.append(scores)
        except (TypeError, ValueError) as e:
            print(f"Error analyzing sentiment for text '{text}': {e}")
            return []
    return vader_scores


def format_results(texts, vader_scores) -> dict:
    """ Group text by sentiment and calculate share of positive, negative and neutral feedback. """
    sentiments = ["positive", "neutral", "negative"]
    analysis = { sentiment: {"texts": [], "share": 0} for sentiment in sentiments}

    try:
        assert len(texts) == len(vader_scores)
    except AssertionError as e:
        print(f"Error formatting results: {e}")
        return {}

    for idx, text in enumerate(texts):
        score = vader_scores[idx]["compound"]
        if score > 0:
            analysis["positive"]["texts"].append(text)
        elif score < 0:
            analysis["negative"]["texts"].append(text)
        else:
            analysis["neutral"]["texts"].append(text)

    for sentiment in sentiments:
        analysis[sentiment]["share"] = round(len(analysis[sentiment]["texts"])/len(texts) * 100)

    return analysis


@app.route('/')
def index():
    """ Serve index page uploading function. """
    return render_template('index.html')


@app.route('/analyze-sentiment', methods=['POST'])
def process_file():
    """ Process uploaded text and serve analysis to user. """
    if request.method == 'POST':
        # Check that file is provided
        if 'file' not in request.files:
            return render_template('error.html', errormessage='No "file" in request.')

        file = request.files['file']

        if not file or file.filename == '':
            return render_template('error.html', errormessage='Please provide a file to analyze.')

        # Check that column input is letters and transform to column index
        col_input = request.form['column-input']
        col_input = ''.join(char.upper() for char in col_input if char.isalpha())
        column = column_index_from_string(col_input)-1

        # Read uploaded file and transform content of chosen column to list
        try:
            df = pd.read_excel(file)
            text_input = df.iloc[:, column].tolist()
        except (ValueError, TypeError, MemoryError, FileNotFoundError) as e:
            print(f'Error reading Excel file: {e}.')
            msg = 'Please, make sure you choose a column that contains text.'
            return render_template('error.html', errormessage=msg)

        # Analyse and format results if text input is found
        if len(text_input) > 0:
            if sentiment_scores := analyze_sentiment(text_input):
                if analysis := format_results(text_input, sentiment_scores):
                    return render_template('analysis.html', analysis=analysis)

    msg = 'Could not perform the sentiment analysis. Please check that your file and column contains text.'
    return render_template('error.html', errormessage=msg)


if __name__ == '__main__':
    app.run(debug=True, host=os.environ.get("HOST", "0.0.0.0"), port=os.environ.get("PORT", "20084"))
