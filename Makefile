web:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=term-missing
