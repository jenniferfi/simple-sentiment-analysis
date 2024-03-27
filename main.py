"""
Flask app for sentiment analysis of text in uploaded Excel files.
Analyzes sentiment using VADER lexicon from NLTK.
"""

import os
import nltk

import pandas as pd

from flask import Flask, render_template, request
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
from openpyxl.utils import column_index_from_string


# Create Flask app, enable automatic template reloading and determine debug mode
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
debug = os.environ.get("DEBUG", False)

# Download Punkt sentence tokenizer, Part-of-Speech tagger and VADER lexicon
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('vader_lexicon')
nltk.download('wordnet')


# TODO: Idea: login to keep track of historical data? --> database + google authentication

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
            return []

    return vader_scores


def contains_lemmatized_keyword(text: str, keywords: list) -> bool:
  """ Check if text input matches lemmatized keyword. """
  # Create a lemmatizer object
  lemmatizer = WordNetLemmatizer()
  # Lemmatize the text and keywords
  text_lemma = lemmatizer.lemmatize(text.lower())
  lemmatized_keywords = [lemmatizer.lemmatize(keyword) for keyword in keywords]
  return any(keyword in text_lemma for keyword in lemmatized_keywords) 


def categorize_text(text_input):
    """ Sort text input into topic categories if they contain defined keywords for topic category. """
    # Define categories and keywords
    category_keywords = {
        'product': ['product', 'item', 'quality', 'feature', 'design', 'selection', ],
        'delivery': ['delivery', 'ship', 'receive', 'arrive'],
        'service': ['email', 'support', 'help', 'service', 'customer'],
        'price': ['price', 'expensive', 'dollar', 'value', 'afford', 'budget']
    }

    categorized_text = { category: [] for category in category_keywords}
    
    for text in text_input:
        text_lower = text.lower()
        
        # Check for matches in each category
        for category, keywords in category_keywords.items():
            if contains_lemmatized_keyword(text_lower, keywords):
                categorized_text[category].append(text)

    return categorized_text


def group_by_sentiment(texts: list, vader_scores: list) -> dict:
    """ Group text by sentiment and rank text from strongest sentiment to weakest """
    feedback_by_sentiment = {
        sentiment: [] for sentiment in sentiments
    }

    try:
        assert len(texts) == len(vader_scores)
    except AssertionError as e:
        print(f"Error formatting results: {e}")
        return {}

    for idx, text in enumerate(texts):
        score = vader_scores[idx]["compound"]
        if score > 0:
            feedback_by_sentiment["positive"].append((text, score))
        elif score < 0:
            feedback_by_sentiment["negative"].append((text, score))
        else:
            feedback_by_sentiment["neutral"].append((text, score))

    # Sort texts from strongest sentiment to weakest and keep only text
    for sentiment, feedback in feedback_by_sentiment.items():
        feedback_by_sentiment[sentiment] = sorted(feedback, key=lambda x: abs(x[1]), reverse=True)
        feedback_by_sentiment[sentiment] = [item[0] for item in feedback_by_sentiment[sentiment]]

    return feedback_by_sentiment


def format_results(all_texts: list, by_topic: dict):
    results = {}

    try:           
        if overall_vader := analyze_sentiment(all_texts):
            results['overall'] = group_by_sentiment(all_texts, overall_vader)
        
        for topic, texts in by_topic.items():
            print(topic, texts)
            if vader_scores := analyze_sentiment(texts):
                results[topic] = group_by_sentiment(texts, vader_scores)
    
    except Exception as e:
        print(f"Error formatting results: {str(e)}")

    return results


def format_charts(data: dict) -> dict:
    """ Calculate and format chart data. """

    charts = {}

    green = '#8bcb90'
    yellow = '#ffbf5b'
    red = '#ae2c36'
    teal = '#2980b9'

    # Calculate amounts of feedback and their sentiment distribution
    n_feedback = []
    distribution = {}
    for topic in data:
        n_total = sum(len(sentiments) for sentiments in data[topic].values())
        n_feedback.append(n_total)
        distribution[topic] = [round(len(data[topic][sent])/n_total * 100, 2) if n_total else 0 for sent in sentiments]

    # Bar chart displaying amount of feedback overall and for each topic
    charts['n-feedback'] = {
        'labels': [key.capitalize() for key in data.keys()],
        'data': n_feedback,
        'color': teal
    }

    # Pie chart displaying distribution of sentiments for feedback overall
    charts['overall-pie'] = {
        'labels': [sentiment.capitalize() for sentiment in sentiments],
        'data': distribution['overall'],
        'colors': [green, yellow, red]
    }

    # Stacked bar chart displaying distribution of sentiments for each topic
    labels = []
    positives = []
    neutrals = []
    negatives = []

    for topic, data in distribution.items():
        if topic != 'overall':
            labels.append(topic.capitalize())
            positives.append(data[0])
            neutrals.append(data[1])
            negatives.append(data[2])

    charts['topic-sentiment'] = {
        'labels': labels,
        'data': [{ 
                    'label': 'Positive', 
                    'backgroundColor': green, 
                    'data': positives, 
                }, { 
                    'label': 'Neutral', 
                    'backgroundColor': yellow, 
                    'data': neutrals, 
                }, { 
                    'label': 'Negative', 
                    'backgroundColor': red, 
                    'data': negatives, 
                }]
    }

    return charts


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
            # TODO: Maybe clean data in some way?
            df = pd.read_excel(file)
            text_input = df.iloc[:, column].tolist()
        except (ValueError, TypeError, MemoryError, FileNotFoundError) as e:
            print(f'Error reading Excel file: {e}.')
            msg = 'Please, make sure you choose a column that contains text.'
            return render_template('error.html', errormessage=msg)

        n_feedback = len(text_input)
        try:
            text = ' '.join(text_input)
            sentences = nltk.sent_tokenize(text)
        except Exception as e:
            print("Could not turn text into sentences")
            return render_template('error.html', errormessage=str(e))

        # Analyse and format results if text input is found
        # TODO: Maybe try / except this part - or less if levels and more render error if not?
        if n_feedback > 0:
            if feedback_by_topic := categorize_text(sentences):
                if grouped_text := format_results(text_input, feedback_by_topic):
                    if charts := format_charts(grouped_text):
                        return render_template('analysis.html',
                                                grouped_text=grouped_text, 
                                                charts=charts)

    msg = 'Could not perform the sentiment analysis. Please check that your file and column contains text.'
    return render_template('error.html', errormessage=msg)


#TODO: gunicorn for deployment
if __name__ == '__main__':
    app.run(debug=True, host=os.environ.get("HOST", "0.0.0.0"), port=os.environ.get("PORT", "20084"))
