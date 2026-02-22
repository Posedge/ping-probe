FROM python:3-slim AS base

RUN pip install pipenv

WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --ignore-pipfile --dev

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser
COPY pingprobe/ ./pingprobe/

# Run tests
COPY tests/ ./tests/
RUN pytest


# Runtime image
FROM base AS application
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "pingprobe"]
