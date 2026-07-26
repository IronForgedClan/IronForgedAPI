import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.helpers import create_mock_db_session


def _patch_audit_db():
    mock_db = patch("api.audit.db").start()
    mock_session = create_mock_db_session()
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_db.get_session.return_value = mock_ctx
    unittest.TestCase.addCleanup = lambda self, f=None: None
    return mock_session


def _audit_row(mock_session):
    from api.audit import ApiAudit

    added = [c.args[0] for c in mock_session.add.call_args_list]
    rows = [a for a in added if isinstance(a, ApiAudit)]
    assert len(rows) == 1, f"expected 1 audit row, got {len(rows)}"
    return rows[0]


class TestQueryParams(unittest.TestCase):
    def setUp(self):
        from api.audit import ApiAuditMiddleware

        self.app = FastAPI()
        self.app.add_middleware(ApiAuditMiddleware)

        @self.app.get("/items")
        async def items():
            return {"ok": True}

        self.client = TestClient(self.app, raise_server_exceptions=False)
        self._cleanup = patch.stopall

    def tearDown(self):
        patch.stopall()

    def test_writes_query_params_as_json(self):
        from api.audit import ApiAudit

        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            self.client.get("/items?filter=booster&limit=10")

            row = _audit_row(mock_session)
            self.assertEqual(row.query_params, {"filter": ["booster"], "limit": ["10"]})
            self.assertIsInstance(row.query_params, dict)

    def test_drops_query_params_when_raw_query_exceeds_4kb(self):
        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            big = "a" * 5000
            self.client.get(f"/items?p={big}")

            row = _audit_row(mock_session)
            self.assertIsNone(row.query_params)
            self.assertEqual(row.error, "query_too_large")

    def test_truncates_individual_param_values_to_1kb(self):
        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            big = "x" * 3000
            self.client.get(f"/items?p={big}")

            row = _audit_row(mock_session)
            self.assertIsNotNone(row.query_params)
            value = row.query_params["p"][0]
            self.assertLessEqual(len(value), 1024)
            self.assertTrue(value.endswith("..."))

    def test_replaces_invalid_query_keys(self):
        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            self.client.get("/items?__proto__=bar&valid=ok&a-b.c_1=x")

            row = _audit_row(mock_session)
            self.assertIn("valid", row.query_params)
            self.assertIn("a-b.c_1", row.query_params)
            proto_keys = [k for k in row.query_params if k.startswith("__invalid_key_")]
            self.assertEqual(len(proto_keys), 1)
            self.assertEqual(len(proto_keys[0]), len("__invalid_key_xxxxxx__"))

    def test_caps_serialized_json_size(self):
        from api.audit import QUERY_MAX_RAW_BYTES

        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            params = "&".join(f"k{i}=v{i}" for i in range(400))
            self.client.get(f"/items?{params}")

            row = _audit_row(mock_session)
            self.assertIsNotNone(row.query_params)
            serialized = json.dumps(row.query_params, sort_keys=True)
            self.assertLessEqual(len(serialized), QUERY_MAX_RAW_BYTES)
            self.assertIn("query_truncated", row.error or "")

    def test_preserves_unicode_values(self):
        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            self.client.get("/items?q=%F0%9F%A6%80h%C3%A9llo")

            row = _audit_row(mock_session)
            self.assertEqual(row.query_params["q"], ["🦀héllo"])

    def test_does_not_redact_query_param_values(self):
        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            self.client.get("/items?token=abc&api_key=xyz&password=hunter2")

            row = _audit_row(mock_session)
            self.assertEqual(row.query_params["token"], ["abc"])
            self.assertEqual(row.query_params["api_key"], ["xyz"])
            self.assertEqual(row.query_params["password"], ["hunter2"])


class TestRouteTemplate(unittest.TestCase):
    def test_writes_route_template_for_path_params(self):
        from api.audit import ApiAuditMiddleware

        app = FastAPI()
        app.add_middleware(ApiAuditMiddleware)

        @app.get("/items/{item_id}")
        async def item(item_id: str):
            return {"id": item_id}

        client = TestClient(app, raise_server_exceptions=False)

        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            client.get("/items/123")

            row = _audit_row(mock_session)
            self.assertEqual(row.route_template, "/items/{item_id}")
            self.assertEqual(row.path, "/items/123")

    def test_route_template_falls_back_to_path_when_no_route(self):
        from api.audit import ApiAuditMiddleware

        app = FastAPI()
        app.add_middleware(ApiAuditMiddleware)

        @app.get("/ok")
        async def ok():
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)

        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            client.get("/ok")
            row = _audit_row(mock_session)
            self.assertEqual(row.route_template, "/ok")
            self.assertEqual(row.path, "/ok")


class TestResponseBytes(unittest.TestCase):
    def test_writes_response_bytes_for_json_response(self):
        from api.audit import ApiAuditMiddleware

        app = FastAPI()
        app.add_middleware(ApiAuditMiddleware)

        @app.get("/data")
        async def data():
            return {"x": "y"}

        client = TestClient(app, raise_server_exceptions=False)

        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            client.get("/data")
            row = _audit_row(mock_session)
            self.assertIsNotNone(row.response_bytes)
            self.assertGreater(row.response_bytes, 0)


class TestCacheHit(unittest.TestCase):
    def _build_app(self):
        from api.audit import ApiAuditMiddleware
        from api.deps import get_current_consumer, get_db_session
        from api.errors import install_error_handlers

        app = FastAPI()
        app.add_middleware(ApiAuditMiddleware)
        install_error_handlers(app)
        return app

    def _override_deps(self, app):
        from api.deps import get_current_consumer, get_db_session
        from api.models import ApiConsumer
        from api.permissions import PERM
        from api.perm import requires_perm
        from api.rate_limit import rate_limit
        from tests.api_tests.helpers import make_consumer

        session = AsyncMock()
        consumer = make_consumer(perms=[PERM.SCORES_READ.value])

        async def override_db():
            yield session

        async def override_consumer():
            return consumer

        app.dependency_overrides[get_db_session] = override_db
        app.dependency_overrides[get_current_consumer] = override_consumer

    def test_writes_cache_hit_true_when_cache_populated(self):
        from api.routers.scores import router

        app = self._build_app()
        app.include_router(router)
        self._override_deps(app)

        from ironforgedcore.cache.score_cache import SCORE_CACHE
        from ironforgedcore.models.score import ScoreBreakdown

        breakdown = ScoreBreakdown(skills=[], clues=[], raids=[], bosses=[])

        async def fake_service(self_or_http=None, *args, **kwargs):
            return breakdown

        from unittest.mock import AsyncMock as _AM

        with patch("api.audit.db") as mock_db, patch(
            "ironforgedcore.cache.score_cache.SCORE_CACHE.get",
            new_callable=_AM,
            return_value=breakdown,
        ) as mock_get, patch(
            "ironforgedcore.services.score_service.get_score_service"
        ) as mock_get_service:
            mock_get_service.return_value.get_player_score = AsyncMock(
                return_value=breakdown
            )

            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            client = TestClient(app, raise_server_exceptions=False)
            response = client.get(
                "/score/zezima", headers={"Authorization": "Bearer x"}
            )

            self.assertEqual(response.status_code, 200)
            row = _audit_row(mock_session)
            self.assertIs(row.cache_hit, True)

    def test_writes_cache_hit_false_on_bypass(self):
        from api.routers.scores import router
        from ironforgedcore.models.score import ScoreBreakdown

        breakdown = ScoreBreakdown(skills=[], clues=[], raids=[], bosses=[])

        app = self._build_app()
        app.include_router(router)
        self._override_deps(app)

        with patch("api.audit.db") as mock_db, patch(
            "ironforgedcore.services.score_service.get_score_service"
        ) as mock_get_service:
            mock_get_service.return_value.get_player_score = AsyncMock(
                return_value=breakdown
            )

            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            client = TestClient(app, raise_server_exceptions=False)
            response = client.get(
                "/score/zezima?bypass_cache=true",
                headers={"Authorization": "Bearer x"},
            )

            self.assertEqual(response.status_code, 200)
            row = _audit_row(mock_session)
            self.assertIs(row.cache_hit, False)


class TestApiVersion(unittest.TestCase):
    def test_writes_api_version_from_config(self):
        from api.audit import ApiAuditMiddleware

        app = FastAPI()
        app.add_middleware(ApiAuditMiddleware)

        @app.get("/v")
        async def v():
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)

        with patch("api.audit.db") as mock_db:
            mock_session = create_mock_db_session()
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_db.get_session.return_value = mock_ctx

            client.get("/v")
            row = _audit_row(mock_session)
            from api.config import API_CONFIG

            self.assertEqual(row.api_version, API_CONFIG.api_version)


class TestSanitizeQueryParamsUnit(unittest.TestCase):
    def test_empty_returns_none(self):
        from api.audit import sanitize_query_params

        self.assertEqual(sanitize_query_params(None), (None, None))
        self.assertEqual(sanitize_query_params(""), (None, None))

    def test_parse_failed_returns_sentinel(self):
        from unittest.mock import patch

        from api.audit import sanitize_query_params

        with patch("urllib.parse.parse_qs", side_effect=ValueError("nope")):
            result, flag = sanitize_query_params("a=b")
        self.assertEqual(result, None)
        self.assertEqual(flag, "query_parse_failed")
