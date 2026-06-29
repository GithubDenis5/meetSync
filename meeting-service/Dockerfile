FROM python:3.13-slim

WORKDIR /app

COPY shared/ ./shared/
COPY meeting-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e ./shared/

COPY meeting-service/app/ ./app/

EXPOSE 8011

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8011"]
