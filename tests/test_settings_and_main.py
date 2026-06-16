import runpy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from talk_debt.settings import AppSettings, SettingsStore


class SettingsStoreTests(unittest.TestCase):
    def test_load_defaults_when_file_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            store = SettingsStore(path)

            loaded = store.load()

            self.assertEqual(loaded, AppSettings())

    def test_load_defaults_when_json_invalid(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text("{invalid-json", encoding="utf-8")
            store = SettingsStore(path)

            loaded = store.load()

            self.assertEqual(loaded, AppSettings())

    def test_load_normalizes_duration_and_booleans(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text(
                """
                {
                  "duration_seconds": 0,
                  "window_x": 15,
                  "window_y": 30,
                  "mode": "compact",
                  "click_through": 1,
                  "always_on_top": 0
                }
                """,
                encoding="utf-8",
            )
            store = SettingsStore(path)

            loaded = store.load()

            self.assertEqual(loaded.duration_seconds, 1)
            self.assertEqual(loaded.window_x, 15)
            self.assertEqual(loaded.window_y, 30)
            self.assertEqual(loaded.mode, "compact")
            self.assertTrue(loaded.click_through)
            self.assertFalse(loaded.always_on_top)

    def test_save_writes_json(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            store = SettingsStore(path)
            expected = AppSettings(
                duration_seconds=300,
                window_x=100,
                window_y=200,
                mode="screen_share",
                click_through=True,
                always_on_top=False,
            )

            store.save(expected)
            loaded = store.load()

            self.assertEqual(loaded, expected)


class MainEntrypointTests(unittest.TestCase):
    def test_main_module_calls_app_main(self) -> None:
        with patch("talk_debt.app.main", return_value=7) as mocked_main:
            with self.assertRaises(SystemExit) as ctx:
                runpy.run_module("talk_debt.__main__", run_name="__main__")

        mocked_main.assert_called_once_with()
        self.assertEqual(ctx.exception.code, 7)


if __name__ == "__main__":
    unittest.main()
