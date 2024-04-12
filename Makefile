lint:
	pylint --max-line-length=120 app/*.py

test:
	pytest

build:
	docker build -t sentiment-analysis:latest .

run:
	docker run --name sentiment-analysis --rm -p 5001:5001 sentiment-analysis:latest