FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    mecab libmecab-dev mecab-ipadic-utf8 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY api/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY py/ py/
COPY crf/ crf/
COPY api/ api/

ENV PORT=8080
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT"]
