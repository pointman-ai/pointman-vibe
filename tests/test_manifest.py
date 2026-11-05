"""Offline contract checks. These never execute Vibe or call Mistral."""
import json
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ManifestContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = tomllib.loads((ROOT / "extension.toml").read_text())
        cls.client = cls.manifest["client"]

    def test_extension(self):
        ext = self.manifest["extension"]
        self.assertEqual(ext["id"], "vibe")
        self.assertEqual(ext["name"], "Mistral Vibe")
        self.assertEqual(ext["version"], "0.1.0")
        self.assertEqual(ext["node"], ">=0.4.15")
        self.assertEqual(ext["publisher"], "aurelio")

    def test_install_and_protocol(self):
        self.assertEqual(self.client["protocol"], "vibe-stream")
        self.assertEqual(self.client["install"], {"from": "pypi", "package": "mistral-vibe"})
        self.assertEqual(self.client["binaries"], ["vibe"])

    def test_headless_streaming_run(self):
        run = self.client["run"]
        self.assertEqual(run["prompt"], "arg")
        self.assertEqual(run["args"][:7], ["-p", "{prompt}", "--output", "streaming", "--output-dir", "{home}/.vibe/run", "--trust"])
        for slot in ("{session}", "{model}", "{permissions}", "{add_dirs}"):
            self.assertIn(slot, run["args"])
        self.assertNotIn("--continue", run["args"])
        self.assertNotIn("-c", run["args"])
        self.assertEqual(run["resume"], ["--resume", "{value}"])
        self.assertNotIn("new_session", run)
        self.assertEqual(run["model"], ["--model", "{value}"])
        self.assertEqual(run["add_dir"], ["--add-dir", "{value}"])

    def test_home_isolation(self):
        self.assertEqual(self.client["home_env"], "HOME")
        self.assertEqual(self.client["run"]["env"], {"VIBE_HOME": "{home}/.vibe"})
        self.assertEqual(self.client["instructions"], {"via": "file", "file": ".vibe/AGENTS.md"})
        mcp = self.client["mcp"]
        self.assertEqual((mcp["via"], mcp["file"], mcp["key"]), ("config-file", ".vibe/config.toml", "mcp_servers"))
        self.assertEqual(mcp["settings"], {"enable_auto_update": False, "enable_update_checks": False})

    def test_only_supported_modes(self):
        modes = self.client["run"]["permissions"]
        self.assertEqual(set(modes), {"default", "auto"})
        self.assertEqual(modes["default"], ["--agent", "auto-approve"])
        self.assertEqual(modes["auto"], ["--agent", "auto-approve"])

    def test_limit_words(self):
        words = self.client["limits"]["words"]
        for word in ("rate limit", "too many requests", "quota exceeded"):
            self.assertIn(word, words)

    def test_one_vault_form_supplies_every_agents_run(self):
        self.assertEqual(self.client["api_keys"], ["MISTRAL_API_KEY"])
        self.assertEqual(self.client["key"], {"secret": "vibe.key", "env": "MISTRAL_API_KEY"})
        self.assertEqual(self.client["sign_in"], {"how": "/vibe add"})
        self.assertEqual(self.manifest["permissions"]["secrets"], ["vibe.key"])
        (cred,) = self.manifest["credentials"]
        self.assertEqual((cred["id"], cred["item"], cred["value"]), ("key", "vibe.key", r"\S{8,512}"))
        (cmd,) = self.manifest["commands"]
        self.assertEqual((cmd["kind"], cmd["slash"], cmd["form"]), ("vibe.add", "add", cred["id"]))
        self.assertEqual(cmd["params"], {"type": "object", "properties": {}, "additionalProperties": False})


class NativeFixture(unittest.TestCase):
    """tests/fixtures/native.jsonl is a captured `vibe -p --output streaming` run."""

    @classmethod
    def setUpClass(cls):
        cls.lines = (ROOT / "tests/fixtures/native.jsonl").read_text().splitlines()
        cls.entries = [json.loads(line) for line in cls.lines]

    def test_every_line_is_json_with_a_session_id(self):
        self.assertTrue(self.lines)
        for n, line in enumerate(self.lines, 1):
            with self.subTest(line=n):
                entry = json.loads(line)
                self.assertIsInstance(entry, dict)
                self.assertIsInstance(entry.get("sessionId"), str)
                self.assertTrue(entry["sessionId"])

    def test_one_session_and_turn(self):
        self.assertEqual(len({e["sessionId"] for e in self.entries}), 1)
        self.assertEqual(len({e["turnId"] for e in self.entries}), 1)

    def test_resumed_turn_with_a_bash_tool_call(self):
        self.assertEqual((self.entries[0]["type"], self.entries[0]["role"]), ("message", "user"))
        (effect,) = [e for e in self.entries if e["type"] == "effect"]
        self.assertEqual(effect["detail"]["toolName"], "file_system.bash")
        self.assertEqual(effect["detail"]["input"], {"command": "echo hi"})
        self.assertEqual(effect["state"]["status"], "completed")
        replies = [e for e in self.entries if e["type"] == "message" and e["role"] == "assistant"]
        self.assertEqual(replies[-1]["content"], [{"type": "text", "text": "walnut\nIt printed: hi"}])


if __name__ == "__main__":
    unittest.main()
