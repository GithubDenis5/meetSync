FROM python:3.13-slim

WORKDIR /app

COPY shared/ ./shared/
COPY voting-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e ./shared/

COPY voting-service/app/ ./app/

EXPOSE 8006

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
