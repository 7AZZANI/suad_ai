FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Install core deps by default for a fast, reliable image.
# Swap to requirements.txt for the full provider stack.
COPY requirements-core.txt requirements.txt ./
RUN pip install -r requirements-core.txt

COPY backend ./backend
COPY alembic.ini ./

WORKDIR /app/backend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
