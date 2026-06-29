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

# Copy helper scripts
COPY scripts/wait-for-pg.py /usr/local/bin/wait-for-pg.py
COPY scripts/run-migrations.py /usr/local/bin/run-migrations.py
RUN chmod +x /usr/local/bin/wait-for-pg.py /usr/local/bin/run-migrations.py

CMD wait-for-pg.py && run-migrations.py
