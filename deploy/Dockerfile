FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY pyproject.toml /app/
RUN pip install poetry && poetry install --no-interaction --no-ansi

COPY controller /app/controller
COPY config /app/config
COPY tools /app/tools

EXPOSE 8080

CMD ["uvicorn", "controller.app:app", "--host", "0.0.0.0", "--port", "8080"]
