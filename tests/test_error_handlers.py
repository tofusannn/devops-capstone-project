"""Unit tests for JSON error responses."""
from unittest import TestCase

from service import app
from service.common.error_handlers import internal_server_error


class TestErrorHandlers(TestCase):
    """The API formats unexpected server errors as JSON."""

    def test_internal_server_error(self):
        with app.app_context():
            response, status = internal_server_error(RuntimeError("test failure"))
        self.assertEqual(status, 500)
        payload = response.get_json()
        self.assertEqual(payload["status"], 500)
        self.assertEqual(payload["error"], "Internal Server Error")
        self.assertIn("test failure", payload["message"])
