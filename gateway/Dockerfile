FROM python:3.13-slim

WORKDIR /app

COPY shared/ ./shared/
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e ./shared/

COPY gateway/app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
