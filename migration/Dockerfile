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

# Copy wait script
COPY scripts/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Shell form CMD so Dockerfile escaping works correctly
CMD wait-for-it.sh $POSTGRES_HOST:$POSTGRES_PORT -t 60 && \
    SQLALCHEMY_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB \
    alembic -c alembic.ini upgrade head
