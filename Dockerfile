FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /code/backend/

EXPOSE 8000

CMD ["sh", "-c", "cd /code/backend && alembic upgrade head && cd /code && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
