FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p ml_models

ENV FLASK_ENV=production
EXPOSE 5000

CMD ["gunicorn", "app:create_app()", "--workers", "2", "--bind", "0.0.0.0:5000", "--timeout", "120"]
