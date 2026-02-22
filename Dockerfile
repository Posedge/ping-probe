FROM python:3-slim AS base

RUN pip install pipenv

WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --ignore-pipfile --dev

# Run as non-root user
ARG USER=1000
USER ${USER}
COPY pingprobe/ ./pingprobe/

# Run tests
COPY tests/ ./tests/
RUN pytest


# Runtime image
FROM base AS application
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "pingprobe"]
