FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin looplet

COPY pyproject.toml README.md ./
COPY looplet ./looplet

RUN pip install --no-cache-dir .

RUN mkdir -p /app/data && chown -R looplet:looplet /app/data

USER looplet

CMD ["python", "-m", "looplet"]

