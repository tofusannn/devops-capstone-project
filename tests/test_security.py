"""Checks for the security headers and browser CORS preflight policy."""
from unittest import TestCase

from service import app


class TestSecurityHeaders(TestCase):
    """Security headers are present without breaking local HTTP API calls."""

    def setUp(self):
        self.client = app.test_client()

    def test_security_headers_on_get(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertIn("default-src", response.headers.get("Content-Security-Policy", ""))

    def test_cors_preflight(self):
        response = self.client.options(
            "/accounts",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "https://example.com")
        self.assertIn("POST", response.headers.get("Access-Control-Allow-Methods", ""))
