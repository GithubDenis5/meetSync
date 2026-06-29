FROM python:3.13-slim

WORKDIR /app

# Copy shared module (has all models + pyproject.toml with deps)
COPY shared/ ./shared/

# Copy alembic config and migrations
COPY alembic.ini .
COPY alembic/ ./alembic/

# Install shared module (includes all dependencies)
RUN pip install --no-cache-dir -e ./shared/

# Run migrations on container start
CMD ["alembic", "upgrade", "head"]
