# builder: compile all prod wheels
FROM python:3.13-alpine AS builder

RUN apk add --no-cache \
    mariadb-dev \
    gcc \
    musl-dev \
    pkgconf \
    libffi-dev

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
 && find /install -name '__pycache__' -exec rm -rf {} + 2>/dev/null; \
    find /install -name '*.dist-info' -exec rm -rf {} + 2>/dev/null; \
    find /install -name '*.egg-info' -exec rm -rf {} + 2>/dev/null; \
    rm -rf /install/lib/python3.13/site-packages/pip

# runner: clean Alpine + mariadb-connector-c + apiuser, shared by prod images
FROM python:3.13-alpine AS runner

RUN apk add --no-cache mariadb-connector-c

RUN adduser -D apiuser
RUN mkdir /app && chown apiuser:apiuser /app
WORKDIR /app

USER apiuser

# api-prod: api only
FROM runner AS api-prod

COPY --from=builder /install /usr/local
COPY --chown=apiuser:apiuser api ./api

CMD ["python", "-m", "api.main"]

# dev: builder + dev dependencies + full copy for self-contained dev
FROM builder AS dev

RUN adduser -D apiuser
RUN mkdir /app && chown apiuser:apiuser /app
WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=apiuser:apiuser . .

USER apiuser

# api-dev: dev deps + uvicorn auto-reload for the API service
FROM dev AS api-dev

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
