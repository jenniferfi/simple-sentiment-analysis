# Simple sentiment analysis app
Upload your Excel file containing textual feedback, product reviews etc., and get a simple sentiment analysis for the text.
The text is categorized into predefined topics using WordNetLemmatizer from NLTK.
The sentiment analysis uses VADER lexicon from NLTK.
The application itself is built with Flask.

Test the application f.ex. with the included .xlsx file.

Testing the application with the included Excel file, the analysis page looks like this.
![Screenshot of analysis page](app/static/images/app.png?raw=true)

## Local development 

### Create environment for Python

Install Python virtual environment (venv) in local folder that is ignored by git:

```bash
mkdir -p local
python3 -m venv local/venv
source local/venv/bin/activate
```

### Install required packages

```bash
# Upgrade installation tools first
pip install --upgrade setuptools pip wheel
pip install -r requirements.txt
```

### Run flask application in development mode
```bash
DEBUG=True python app/main.py
```
### Environmental variables
- DEBUG: optional to turn on Flask debug mode, hot loading, automatic rendering of templates
- PORT: optional, default is 5001
- HOST: optional default is 0.0.0.0

### Lint python files 
```bash
make lint
```

### Test python files
```bash
make test
```

## Deployment process
Build a Docker image of the application
```bash
make build
```
Run application locally in Docker container
```bash
make run
```
Instead of `make run`, you might want to tag and push your Docker image to a cloud platform like GCP.