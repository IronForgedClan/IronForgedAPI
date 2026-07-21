# builder: install prod wheels into the default location (/usr/local)
FROM python:3.13-alpine AS builder

RUN apk add --no-cache \
    mariadb-dev \
    gcc \
    musl-dev \
    pkgconf \
    libffi-dev \
    git

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /build

COPY api ./api
RUN pip install --no-cache-dir ./api \
 && find /usr/local -name '__pycache__' -exec rm -rf {} + 2>/dev/null; \
    find /usr/local -name '*.egg-info' -exec rm -rf {} + 2>/dev/null; \
    rm -rf /usr/local/lib/python3.13/site-packages/pip

# runner: clean Alpine + mariadb-connector-c + apiuser, shared by prod images
FROM python:3.13-alpine AS runner

RUN apk add --no-cache mariadb-connector-c

RUN adduser -D apiuser
RUN mkdir /app && chown apiuser:apiuser /app
WORKDIR /app

USER apiuser

# api-prod: api only
FROM runner AS api-prod

COPY --from=builder /usr/local /usr/local
COPY --chown=apiuser:apiuser api ./api
COPY --chown=apiuser:apiuser scripts ./scripts

CMD ["python", "-m", "api.main"]

# dev: full copy for self-contained dev
FROM builder AS dev

RUN adduser -D apiuser
RUN mkdir /app && chown apiuser:apiuser /app
WORKDIR /app

COPY --chown=apiuser:apiuser . .

USER apiuser

# api-dev: uvicorn auto-reload for the API service
FROM dev AS api-dev

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
