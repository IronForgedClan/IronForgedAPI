<h1 align="center">Iron Forged API</h1>
<p align="center">
<img alt="API (latest)" src="https://img.shields.io/ghcr/v/IronForgedClan/IronForgedApi/ironforgedapi/latest?label=api%20%28latest%29&sort=semver">
<img alt="API (staging)" src="https://img.shields.io/ghcr/v/IronForgedClan/IronForgedApi/ironforgedapi/staging?label=api%20%28staging%29&sort=semver&include_prereleases">
<a href="https://github.com/IronForgedClan/IronForgedApi/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/IronForgedClan/IronForgedApi"></a>
<a href="https://github.com/psf/black"><img alt="Code style: Black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

API for the Iron Forged Old School RuneScape clan.

## Endpoints

| Method | Path                                       | Required perm              |
| ------ | ------------------------------------------ | -------------------------- |
| GET    | `/health`                                  | _none (public)_            |
| GET    | `/members`                                 | `members:list`             |
| GET    | `/members/{member_id}`                     | `members:read`             |
| GET    | `/members/{member_id}/ingots`              | `ingots:read`              |
| GET    | `/members/{member_id}/ingots/transactions` | `ingots:read:transactions` |
| GET    | `/score/{rsn}`                             | `scores:read`              |
| GET    | `/score/{rsn}/breakdown`                   | `scores:read`              |
| GET    | `/score/{rsn}/history`                     | `scores:read:history`      |

## Authentication

Every request to a private endpoint needs a `Bearer` token in the
`Authorization` header:

```sh
curl -H "Authorization: Bearer <token>" http://localhost:8080/members
```

## Permissions

Permissions are `resource:action` strings, stored as a JSON array on each
consumer.

| Perm                       | Grants access to                               |
| -------------------------- | ---------------------------------------------- |
| `members:list`             | `GET /members`                                 |
| `members:read`             | `GET /members/{member_id}`                     |
| `ingots:read`              | `GET /members/{member_id}/ingots`              |
| `ingots:read:transactions` | `GET /members/{member_id}/ingots/transactions` |
| `scores:read`              | `GET /score/{rsn}`                             |
| `scores:read`              | `GET /score/{rsn}/breakdown`                   |
| `scores:read:history`      | `GET /score/{rsn}/history`                     |

## Responses

Success:

```json
{
    "data": {},
    "meta": {
        "request_id": "8f3a2c1b-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
        "timestamp": "2026-07-12T14:23:11.123456+00:00"
    }
}
```

Error:

```json
{
    "error": {
        "code": "not_found",
        "message": "No member with id=123456789012345678"
    },
    "meta": {
        "request_id": "8f3a2c1b-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
        "timestamp": "2026-07-12T14:23:11.123456+00:00"
    }
}
```

`code` is a stable string. `message` is human-readable and can change.

| Status | `code`               | When                                               |
| ------ | -------------------- | -------------------------------------------------- |
| 400    | `bad_request`        | Bad path or query params.                          |
| 401    | `unauthorized`       | Missing, malformed, or revoked token.              |
| 403    | `forbidden`          | Token is valid but missing the required perm.      |
| 404    | `not_found`          | Member, player, or hiscores record does not exist. |
| 405    | `method_not_allowed` | Method not supported for the given path.           |
| 422    | `validation_error`   | Request validation failed.                         |
| 429    | `rate_limited`       | Per-consumer per-minute limit exceeded.            |
| 500    | `internal_error`     | Unhandled server-side exception.                   |

Every response also carries an `X-Request-ID` header with the same value as
`meta.request_id`. If having issues, share this ID to help with debugging.

## Rate limiting

Per-consumer per-route limit, 30 requests per minute by default. 429 responses
use the standard response envelope and include a `Retry-After` header.

## Endpoints

### GET /health

Pings the database.

Required perm: none

Response 200:

```json
{
    "data": {
        "status": "ok",
        "db": "ok",
        "version": "1.0.0",
        "environment": "prod"
    },
    "meta": { "request_id": "...", "timestamp": "..." }
}
```

Returns 503 with `"status": "degraded"` and `"db": "error"` when the database is
unreachable.

---

### GET /members

Paginated member list. Default filter returns active members only.

Required perm: `members:list`

| Name     | Type   | Default  | Constraints                                              |
| -------- | ------ | -------- | -------------------------------------------------------- |
| `limit`  | int    | `100`    | 1-500                                                    |
| `offset` | int    | `0`      | >= 0                                                     |
| `role`   | string | _none_   | A `ROLE` enum value, e.g. `Member`, `Staff`, `Owner`     |
| `rank`   | string | _none_   | A `RANK` enum value, e.g. `Iron`, `Dragon`, `Myth`       |
| `filter` | string | `active` | `active`, `booster`, `prospect`, `blacklisted`, `banned` |

Response 200:

```json
{
    "data": {
        "members": [
            {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "discord_id": 123456789012345678,
                "nickname": "Zezima",
                "role": "Member",
                "rank": "Dragon",
                "joined_date": "2024-01-15T00:00:00+00:00",
                "is_booster": false,
                "is_prospect": false,
                "is_blacklisted": false,
                "is_banned": false
            }
        ],
        "total": 142,
        "limit": 100,
        "offset": 0
    },
    "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

### GET /members/{member_id}

Single member by Discord id or internal UUID. Numeric path values match against
`discord_id`; non-numeric values match against the internal UUID.

Required perm: `members:read`

Response 200:

```json
{
    "data": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "discord_id": 123456789012345678,
        "nickname": "Zezima",
        "role": "Member",
        "rank": "Dragon",
        "joined_date": "2024-01-15T00:00:00+00:00",
        "is_booster": false,
        "is_prospect": false,
        "is_blacklisted": false,
        "is_banned": false
    },
    "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

### GET /members/{member_id}/ingots

Current ingot balance. `member_id` is a Discord id or internal UUID.

Required perm: `ingots:read`

Response 200:

```json
{
    "data": { "nickname": "Zezima", "ingots": 4200 },
    "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

### GET /members/{member_id}/ingots/transactions

Recent add/remove ingot transactions, newest first. `member_id` is a Discord id
or UUID.

Required perm: `ingots:read:transactions`

| Name    | Type | Default | Constraints                                           |
| ------- | ---- | ------- | ----------------------------------------------------- |
| `days`  | int  | _none_  | 1-365. Filter to transactions within the last N days. |
| `limit` | int  | `50`    | 1-500                                                 |

Response 200:

```json
{
    "data": {
        "transactions": [
            {
                "id": 98765,
                "change_type": "ADD_INGOTS",
                "previous_value": "4000",
                "new_value": "4200",
                "comment": "Payroll",
                "admin": {
                    "id": "f0e1d2c3-b4a5-9687-6543-210fedcba987",
                    "discord_id": 111222333444555666,
                    "nickname": "BossMan"
                },
                "timestamp": "2026-07-01T06:00:00+00:00"
            },
            {
                "id": 98760,
                "change_type": "REMOVE_INGOTS",
                "previous_value": "4050",
                "new_value": "4000",
                "comment": "Bought raffle tickets",
                "admin": null,
                "timestamp": "2026-06-15T18:42:11+00:00"
            }
        ]
    },
    "meta": { "request_id": "...", "timestamp": "..." }
}
```

`admin` is `null` when the changelog row has no `admin_id`. This typically means
the change was initiated by the bot (think automated payroll). When populated,
it is a `MemberRef` (internal UUID, Discord id, nickname).

---

### GET /score/{rsn}

Compute score and rank for a player. For full breakdown, see
`GET /score/{rsn}/breakdown`.

Required perm: `scores:read`

| Name  | Type   | Description                                           |
| ----- | ------ | ----------------------------------------------------- |
| `rsn` | string | RuneScape name. 1-12 characters. `400` outside range. |

| Name           | Type | Default | Description                                            |
| -------------- | ---- | ------- | ------------------------------------------------------ |
| `bypass_cache` | bool | `false` | Skip the score cache and force a fresh hiscores fetch. |

Response 200:

```json
{
    "data": {
        "player_name": "Zezima",
        "total_points": 12345,
        "rank": "Rune"
    },
    "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

### GET /score/{rsn}/breakdown

OSRS hiscores breakdown converted to clan points.

Required perm: `scores:read`

| Name  | Type   | Description                                           |
| ----- | ------ | ----------------------------------------------------- |
| `rsn` | string | RuneScape name. 1-12 characters. `400` outside range. |

| Name           | Type | Default | Description                                            |
| -------------- | ---- | ------- | ------------------------------------------------------ |
| `bypass_cache` | bool | `false` | Skip the score cache and force a fresh hiscores fetch. |

Response 200:

```json
{
    "data": {
        "player_name": "Zezima",
        "rank": "Rune",
        "skills": [
            {
                "name": "Attack",
                "display_name": null,
                "display_order": 1,
                "emoji_key": "Attack",
                "level": 99,
                "xp": 13034431,
                "points": 152
            }
        ],
        "clues": [
            {
                "name": "Clue Scrolls (beginner)",
                "display_name": "Beginner",
                "display_order": 1,
                "emoji_key": "Beginner_Clue",
                "kc": 42,
                "points": 4
            }
        ],
        "raids": [
            {
                "name": "Chambers of Xeric",
                "display_name": null,
                "display_order": 1,
                "emoji_key": "Chambers_of_Xeric",
                "kc": 75,
                "points": 75
            }
        ],
        "bosses": [
            {
                "name": "Zulrah",
                "display_name": null,
                "display_order": 200,
                "emoji_key": "Zulrah",
                "kc": 1200,
                "points": 600
            }
        ],
        "total_points": 12345
    },
    "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

### GET /score/{rsn}/history

Historical score snapshots for a registered member, looked up at multiple
periods. The player must be a clan member.

Required perm: `scores:read:history`

`rsn` is a osrs name (see `GET /score/{rsn}`).

| Name   | Type   | Default     | Constraints                                                               |
| ------ | ------ | ----------- | ------------------------------------------------------------------------- |
| `days` | string | `"7,30,90"` | Comma-separated day windows. Each value 1-365. `400` if any value is bad. |

For each requested period, the endpoint returns the single nearest snapshot
within ~3 days of the target date. If no qualifying snapshot exists, `score` is
`null`.

Response 200:

```json
{
    "data": {
        "discord_id": 123456789012345678,
        "entries": [
            { "period_days": 7, "score": 11800, "snapshot_date": null },
            { "period_days": 30, "score": 10500, "snapshot_date": null },
            { "period_days": 90, "score": 9000, "snapshot_date": null }
        ]
    },
    "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

## Setup

1. Set the API port in `.env`: `API_PORT=8080`.
2. Run migrations: `make migrate`.
3. Create a consumer: `make api-consumer-interactive`. The CLI prints a fresh
   bearer token once. Copy it.
4. Hit an endpoint:

   ```sh
   curl -H "Authorization: Bearer iron_<token>" http://localhost:8080/members
   ```

## Configuration

| Env var             | Default     | Description                                                            |
| ------------------- | ----------- | ---------------------------------------------------------------------- |
| `API_HOST`          | `0.0.0.0`   | Bind address.                                                          |
| `API_PORT`          | `8080`      | Listen port.                                                           |
| `API_TRUSTED_HOSTS` | `127.0.0.1` | Comma-separated trusted reverse-proxy IPs for X-Forwarded-For parsing. |
| `API_CORS_ORIGINS`  | (empty)     | Comma-separated allowed CORS origins.                                  |
| `API_RATE_LIMIT`    | `30`        | Per-route per-consumer per-minute. `0` disables.                       |

## Bruno collection

A [Bruno](https://www.usebruno.com/) collection lives in `api/bruno/`.
