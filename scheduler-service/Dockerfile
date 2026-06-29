FROM python:3.13-slim

WORKDIR /app

COPY shared/ ./shared/
COPY scheduler-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e ./shared/

COPY scheduler-service/app/ ./app/

EXPOSE 8010

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
