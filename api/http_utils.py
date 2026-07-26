from fastapi import Request

REQUEST_ID_HEADER = "X-Request-ID"
PATH_MAX_LENGTH = 512
ERROR_MAX_LENGTH = 512
USER_AGENT_MAX_LENGTH = 512
IP_MAX_LENGTH = 64
QUERY_MAX_RAW_BYTES = 4096
QUERY_VALUE_MAX_CHARS = 1024
QUERY_KEY_MAX_CHARS = 128
RESPONSE_BYTES_MAX = 2**31 - 1
ROUTE_TEMPLATE_MAX_LENGTH = 256
API_VERSION_MAX_LENGTH = 32


def get_client_ip(request: Request) -> str | None:
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip
    if request.client is not None:
        return request.client.host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return None
