FROM python:3.13-slim

WORKDIR /app

COPY shared/ ./shared/
COPY recommendation-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e ./shared/

COPY recommendation-service/app/ ./app/

EXPOSE 8007

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
