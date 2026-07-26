import hashlib
import json
import logging
import re
import time
import urllib.parse
from datetime import datetime, timezone
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api.config import API_CONFIG
from api.http_utils import (
    ERROR_MAX_LENGTH,
    IP_MAX_LENGTH,
    PATH_MAX_LENGTH,
    QUERY_KEY_MAX_CHARS,
    QUERY_MAX_RAW_BYTES,
    QUERY_VALUE_MAX_CHARS,
    REQUEST_ID_HEADER,
    ROUTE_TEMPLATE_MAX_LENGTH,
    USER_AGENT_MAX_LENGTH,
    get_client_ip,
)
from api.models import ApiAudit
from ironforgedcore.database import db

logger = logging.getLogger(__name__)

QUERY_KEY_RE = re.compile(r"^[A-Za-z0-9_\-\.]{1,128}$")
QUERY_KEY_DENYLIST = frozenset({"__proto__", "constructor", "prototype"})
QUERY_TOO_LARGE_SENTINEL = "query_too_large"
QUERY_PARSE_FAILED_SENTINEL = "query_parse_failed"
QUERY_TRUNCATED_SENTINEL = "query_truncated"


def _sanitize_key(k: str) -> str:
    if QUERY_KEY_RE.match(k) and k not in QUERY_KEY_DENYLIST and not k.startswith("__"):
        return k[:QUERY_KEY_MAX_CHARS]
    h = hashlib.sha256(k.encode("utf-8")).hexdigest()[:6]
    return f"__invalid_key_{h}__"


def _sanitize_value(v: str) -> str:
    if len(v) > QUERY_VALUE_MAX_CHARS:
        return v[: QUERY_VALUE_MAX_CHARS - 3] + "..."
    return v


def _serialize_size(d: dict) -> int:
    return len(json.dumps(d, ensure_ascii=False, sort_keys=True))


def sanitize_query_params(
    raw_query: str | None,
) -> tuple[dict | None, str | None]:
    if not raw_query:
        return None, None
    if len(raw_query) > QUERY_MAX_RAW_BYTES:
        logger.warning(
            "Query string exceeds %d bytes, dropping query_params",
            QUERY_MAX_RAW_BYTES,
        )
        return None, QUERY_TOO_LARGE_SENTINEL
    try:
        parsed = urllib.parse.parse_qs(raw_query, keep_blank_values=True)
    except (ValueError, UnicodeDecodeError):
        logger.warning("Failed to parse query string, dropping")
        return None, QUERY_PARSE_FAILED_SENTINEL
    cleaned = {
        _sanitize_key(k): [_sanitize_value(v) for v in vs] for k, vs in parsed.items()
    }
    if _serialize_size(cleaned) <= QUERY_MAX_RAW_BYTES:
        return cleaned, None
    truncated: dict = {}
    for k, vs in cleaned.items():
        candidate = {**truncated, k: vs}
        if _serialize_size(candidate) > QUERY_MAX_RAW_BYTES:
            break
        truncated = candidate
    logger.warning(
        "Sanitized query_params exceeded %d bytes, truncated",
        QUERY_MAX_RAW_BYTES,
    )
    return truncated, QUERY_TRUNCATED_SENTINEL


async def write_audit_row(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_ms: int,
    client_ip: str | None,
    user_agent: str | None,
    request_id: str,
    consumer_id: int | None,
    consumer_name: str | None,
    consumer_perms: list[str] | None,
    required_perm: str | None,
    error: str | None,
    query_params: dict | None,
    route_template: str | None,
    response_bytes: int | None,
    cache_hit: bool | None,
    api_version: str | None,
) -> None:
    try:
        async with db.get_session() as session:
            session.add(
                ApiAudit(
                    timestamp=datetime.now(tz=timezone.utc),
                    request_id=request_id,
                    consumer_id=consumer_id,
                    consumer_name=consumer_name,
                    consumer_perms=consumer_perms,
                    required_perm=required_perm,
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    client_ip=client_ip[:IP_MAX_LENGTH] if client_ip else None,
                    user_agent=user_agent,
                    error=error,
                    query_params=query_params,
                    route_template=route_template,
                    response_bytes=response_bytes,
                    cache_hit=cache_hit,
                    api_version=api_version,
                )
            )
            await session.commit()
    except Exception:
        logger.exception("Failed to write api audit row")


class ApiAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        error_message: str | None = None
        status_code = 500
        response: Response | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        except Exception as exc:
            error_message = str(exc)[:ERROR_MAX_LENGTH]
            logger.exception("Request failed in audit middleware")
            raise
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            path = request.url.path[:PATH_MAX_LENGTH]
            method = request.method
            client_ip = get_client_ip(request)
            user_agent = (request.headers.get("user-agent") or "")[
                :USER_AGENT_MAX_LENGTH
            ]
            consumer = getattr(request.state, "consumer", None)
            required_perm = getattr(request.state, "required_perm", None)

            consumer_id = consumer["id"] if consumer is not None else None
            consumer_name = consumer["name"] if consumer is not None else None
            consumer_perms = list(consumer["perms"]) if consumer is not None else None

            query_params, query_flag = sanitize_query_params(request.url.query)
            if query_flag is not None:
                if error_message is None:
                    error_message = query_flag
                else:
                    error_message = f"{error_message};{query_flag}"

            route = request.scope.get("route")
            route_template = getattr(route, "path", None) if route is not None else None
            if route_template is None:
                route_template = path
            route_template = route_template[:ROUTE_TEMPLATE_MAX_LENGTH]

            response_bytes: int | None = None
            if response is not None:
                body = getattr(response, "body", None)
                if isinstance(body, (bytes, bytearray)):
                    response_bytes = len(body)
                else:
                    content_length = response.headers.get("content-length")
                    if content_length is not None:
                        try:
                            response_bytes = int(content_length)
                        except ValueError:
                            response_bytes = None
            cache_hit = getattr(request.state, "cache_hit", None)
            api_version = API_CONFIG.api_version

            await write_audit_row(
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=user_agent,
                request_id=request_id,
                consumer_id=consumer_id,
                consumer_name=consumer_name,
                consumer_perms=consumer_perms,
                required_perm=required_perm,
                error=error_message,
                query_params=query_params,
                route_template=route_template,
                response_bytes=response_bytes,
                cache_hit=cache_hit,
                api_version=api_version,
            )
