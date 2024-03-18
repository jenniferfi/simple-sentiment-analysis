# Sentiment analysis
Upload your Excel containing textual feedback, product reviews etc and get a sentiment analysis for the text.

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
DEBUG=True python main.py
```
