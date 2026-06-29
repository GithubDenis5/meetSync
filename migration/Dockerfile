FROM python:3.13-slim

WORKDIR /app

# Copy shared module (has all models + pyproject.toml with deps)
COPY shared/ ./shared/

# Copy alembic config and migrations
COPY alembic.ini .
COPY alembic/ ./alembic/

# Install dependencies
RUN pip install --no-cache-dir psycopg2-binary
RUN pip install --no-cache-dir -e ./shared/

# Wait for postgres and run migrations
COPY scripts/wait-for-pg.py /usr/local/bin/wait-for-pg.py
RUN chmod +x /usr/local/bin/wait-for-pg.py

CMD wait-for-pg.py && \
    SQLALCHEMY_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB" \
    alembic -c alembic.ini upgrade head
