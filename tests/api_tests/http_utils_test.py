import unittest
from unittest.mock import MagicMock

from api.http_utils import get_client_ip


def _make_request(*, cf_ip=None, xff=None, client_host="172.22.0.3"):
    request = MagicMock()
    request.headers = {}
    if cf_ip is not None:
        request.headers["cf-connecting-ip"] = cf_ip
    if xff is not None:
        request.headers["x-forwarded-for"] = xff
    if client_host is None:
        request.client = None
    else:
        request.client = MagicMock()
        request.client.host = client_host
    return request


class TestGetClientIp(unittest.TestCase):
    def test_prefers_cf_connecting_ip_over_request_client(self):
        req = _make_request(cf_ip="203.0.113.42", client_host="162.158.1.1")
        self.assertEqual(get_client_ip(req), "203.0.113.42")

    def test_prefers_cf_connecting_ip_over_xff(self):
        req = _make_request(
            cf_ip="203.0.113.42", xff="162.158.1.1, 1.2.3.4", client_host=None
        )
        self.assertEqual(get_client_ip(req), "203.0.113.42")

    def test_falls_back_to_request_client_when_no_cf_header(self):
        req = _make_request(client_host="203.0.113.42")
        self.assertEqual(get_client_ip(req), "203.0.113.42")

    def test_falls_back_to_xff_when_no_cf_header_and_no_client(self):
        req = _make_request(xff="203.0.113.42, 162.158.1.1", client_host=None)
        self.assertEqual(get_client_ip(req), "203.0.113.42")

    def test_xff_picks_first_entry_in_chain(self):
        req = _make_request(xff="203.0.113.42, 162.158.1.1", client_host=None)
        self.assertEqual(get_client_ip(req), "203.0.113.42")

    def test_xff_strips_whitespace(self):
        req = _make_request(xff="  203.0.113.42  ,  162.158.1.1  ", client_host=None)
        self.assertEqual(get_client_ip(req), "203.0.113.42")

    def test_cf_empty_string_falls_through(self):
        req = _make_request(cf_ip="", client_host="203.0.113.42")
        self.assertEqual(get_client_ip(req), "203.0.113.42")

    def test_returns_none_when_nothing_available(self):
        req = _make_request(client_host=None)
        self.assertIsNone(get_client_ip(req))
