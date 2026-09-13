"""Runtime secret delivery regressions; all material below is invalid test data."""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "secret_files_under_test", ROOT / "apps/api/app/secret_files.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SecretFileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "secret"
        self.path.write_text("invalid-local-fixture\n")
        self.path.chmod(0o400)

    def test_file_value_is_read_without_environment_materialization(self):
        with patch.dict(os.environ, {"EXAMPLE_FILE": str(self.path)}, clear=True):
            self.assertEqual(MODULE.environment_secret("EXAMPLE"), "invalid-local-fixture")
            self.assertNotIn("EXAMPLE", os.environ)

    def test_inline_and_file_conflict(self):
        with patch.dict(
            os.environ, {"EXAMPLE": "inline", "EXAMPLE_FILE": str(self.path)}, clear=True
        ):
            with self.assertRaisesRegex(ValueError, "only one"):
                MODULE.environment_secret("EXAMPLE")

    def test_missing_file_has_no_inline_fallback(self):
        self.path.unlink()
        with patch.dict(os.environ, {"EXAMPLE_FILE": str(self.path)}, clear=True):
            with self.assertRaises(ValueError):
                MODULE.environment_secret("EXAMPLE", "fallback")

    def test_unsafe_files_are_rejected(self):
        for mode in (0o644, 0o440, 0o700):
            with self.subTest(mode=mode):
                self.path.chmod(mode)
                with self.assertRaises(ValueError):
                    MODULE.read_secret_file(str(self.path), "EXAMPLE")
        self.path.unlink()
        self.path.mkdir()
        with self.assertRaises(ValueError):
            MODULE.read_secret_file(str(self.path), "EXAMPLE")

    def test_world_readable_file_outside_compose_is_rejected(self):
        self.path.chmod(0o444)
        with self.assertRaises(ValueError):
            MODULE.read_secret_file(str(self.path), "EXAMPLE")

    def test_link_and_fifo_are_rejected(self):
        link = self.path.with_name("link")
        link.symlink_to(self.path)
        with self.assertRaises(ValueError):
            MODULE.read_secret_file(str(link), "EXAMPLE")
        pipe = self.path.with_name("pipe")
        os.mkfifo(pipe, 0o600)
        with self.assertRaises(ValueError):
            MODULE.read_secret_file(str(pipe), "EXAMPLE")

    def test_empty_binary_and_oversized_values_are_rejected_without_contents(self):
        for data in (b" ", b"\xffinvalid-local-fixture", b"a\x00b", b"x" * 65537):
            self.path.chmod(0o600)
            self.path.write_bytes(data)
            with self.assertRaises(ValueError) as caught:
                MODULE.read_secret_file(str(self.path), "EXAMPLE")
            self.assertNotIn("invalid-local-fixture", str(caught.exception))

    def test_rotated_file_is_read_on_next_load(self):
        replacement = self.path.with_name("replacement")
        replacement.write_text("rotated-fixture")
        replacement.chmod(0o400)
        replacement.replace(self.path)
        self.assertEqual(MODULE.read_secret_file(str(self.path), "EXAMPLE"), "rotated-fixture")

    def test_settings_resolve_declared_file_without_exposing_value_in_repr(self):
        from app.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(app_env="test", _env_file=None, database_url_file=str(self.path))
            self.assertEqual(settings.database_url, "invalid-local-fixture")
            self.assertNotIn("invalid-local-fixture", repr(settings))
            with self.assertRaises(ValueError):
                Settings(app_env="test", _env_file=None, database_url="inline", database_url_file=str(self.path))

    def test_file_environment_uses_application_prefix(self):
        from app.config import Settings

        with patch.dict(os.environ, {"DATABASE_URL_FILE": str(self.path)}, clear=True):
            settings = Settings(app_env="test", _env_file=None)
            self.assertEqual(settings.database_url, "invalid-local-fixture")


class OdooCredentialBoundaryTests(unittest.TestCase):
    def test_direct_odoo_configuration_is_rejected_before_reading_files(self):
        from app.config import Settings

        for values in (
            {"odoo_enabled": True},
            {"odoo_api_key": "invalid-odoo-fixture"},
            {"odoo_api_key_file": "/missing/odoo-key"},
        ):
            with self.subTest(values=values), patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ValueError, "Direct Odoo credentials"):
                    Settings(app_env="test", _env_file=None, **values)

    def test_odoo_environment_credentials_are_rejected(self):
        from app.config import Settings

        for key in ("ODOO_API_KEY", "ODOO_API_KEY_FILE"):
            with self.subTest(key=key), patch.dict(os.environ, {key: "invalid-fixture"}, clear=True):
                with self.assertRaisesRegex(ValueError, "Direct Odoo credentials"):
                    Settings(app_env="test", _env_file=None)

    def test_secret_contract_does_not_provision_odoo_credentials(self):
        import json

        contract = json.loads((ROOT / "openbao-secret-consumer.v1.json").read_text())
        self.assertFalse(any(b["setting"].startswith("ODOO_") for b in contract["bindings"]))


if __name__ == "__main__":
    unittest.main()
