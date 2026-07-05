FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 looplet \
    && useradd --uid 10001 --gid looplet --create-home --shell /usr/sbin/nologin looplet

COPY pyproject.toml README.md ./
COPY looplet ./looplet

RUN pip install --no-cache-dir .

RUN mkdir -p /app/data && chown -R looplet:looplet /app/data

USER looplet

CMD ["python", "-m", "looplet"]
