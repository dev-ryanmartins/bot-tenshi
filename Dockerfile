FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    ENABLE_SITE=1 \
    SITE_HOST=0.0.0.0

WORKDIR /app

COPY requirements.txt ./requirements.txt
COPY artifacts/tenshi-bot/requirements.txt ./artifacts/tenshi-bot/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
