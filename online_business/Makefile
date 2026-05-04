.PHONY: install dev test lint

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --port 8000

test:
	cd online_business && pytest tests/ -v

lint:
	flake8 app/ tests/ --max-line-length=120
