FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY youtube_shortcut_helper.py .

ENV PORT=8787
EXPOSE 8787

CMD ["sh", "-c", "uvicorn youtube_shortcut_helper:app --host 0.0.0.0 --port ${PORT}"]
