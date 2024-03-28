FROM python:3.9-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy the application code into the container
COPY app /app/
COPY requirements.txt /app/requirements.txt

WORKDIR /app

# Install dependencies
RUN pip install --upgrade wheel setuptools pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

EXPOSE 5001

# Run the Flask application with Gunicorn
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:5001"]