import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "odoo_xmlrpc.py"
SPEC = importlib.util.spec_from_file_location("odoo_xmlrpc", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class OdooXmlRpcInputTest(unittest.TestCase):
    def test_parsers_accept_expected_cli_values(self):
        self.assertEqual(MODULE.parse_domain("[['state', '=', 'draft']]"), [["state", "=", "draft"]])
        self.assertEqual(MODULE.parse_fields("name, state"), ["name", "state"])
        self.assertEqual(MODULE.parse_ids("2, 7"), [2, 7])

    def test_domain_parser_rejects_code(self):
        with self.assertRaises(ValueError):
            MODULE.parse_domain("__import__('os').system('true')")

    def test_public_http_is_rejected_but_local_development_is_allowed(self):
        with self.assertRaises(ValueError):
            MODULE.validate_url("http://odoo.example.test")
        self.assertEqual(MODULE.validate_url("http://127.0.0.1:8069"), "http://127.0.0.1:8069")
        self.assertEqual(MODULE.validate_url("https://odoo.example.test/"), "https://odoo.example.test")

    def test_api_key_prefers_cli_value_and_supports_environment_value(self):
        self.assertEqual(MODULE.resolve_api_key(None, "environment-secret"), "environment-secret")
        self.assertEqual(MODULE.resolve_api_key("cli-secret", "environment-secret"), "cli-secret")


if __name__ == "__main__":
    unittest.main()
