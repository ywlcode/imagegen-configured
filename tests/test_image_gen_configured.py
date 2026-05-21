import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "image_gen_configured.py"
spec = importlib.util.spec_from_file_location("image_gen_configured", MODULE_PATH)
image_gen_configured = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(image_gen_configured)


class OpenAICustomHeadersTests(unittest.TestCase):
    def test_injects_non_blocked_user_agent_when_missing(self):
        env = {}

        image_gen_configured._ensure_openai_custom_headers(env)

        self.assertEqual(env["OPENAI_CUSTOM_HEADERS"], "User-Agent: CodexImagegen/1.0")

    def test_preserves_existing_headers_and_adds_user_agent(self):
        env = {"OPENAI_CUSTOM_HEADERS": "X-Test: 1"}

        image_gen_configured._ensure_openai_custom_headers(env)

        self.assertEqual(
            env["OPENAI_CUSTOM_HEADERS"],
            "X-Test: 1\nUser-Agent: CodexImagegen/1.0",
        )

    def test_respects_explicit_user_agent(self):
        env = {"OPENAI_CUSTOM_HEADERS": "User-Agent: CustomClient/2.0"}

        image_gen_configured._ensure_openai_custom_headers(env)

        self.assertEqual(env["OPENAI_CUSTOM_HEADERS"], "User-Agent: CustomClient/2.0")


if __name__ == "__main__":
    unittest.main()
