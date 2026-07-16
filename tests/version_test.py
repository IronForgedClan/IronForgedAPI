import importlib
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch


def _read_pyproject_version() -> str:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)["project"]["version"]


class TestApiPackageVersion(unittest.TestCase):
    def test_api_version_is_non_empty_string(self):
        import api

        self.assertIsInstance(api.__version__, str)
        self.assertGreater(len(api.__version__), 0)

    def test_api_version_matches_pyproject(self):
        import api

        expected = _read_pyproject_version()
        self.assertEqual(api.__version__, expected)

    def test_api_falls_back_to_pyproject_when_not_installed(self):
        import api

        original = api.__version__
        expected = _read_pyproject_version()
        with patch(
            "importlib.metadata.version",
            side_effect=importlib.metadata.PackageNotFoundError("ironforgedapi"),
        ):
            reloaded = importlib.reload(api)

        try:
            self.assertEqual(reloaded.__version__, expected)
        finally:
            reloaded.__version__ = original


if __name__ == "__main__":
    unittest.main()
