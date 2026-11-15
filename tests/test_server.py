import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import shu_huyou_mcp as mod


class FakeApp:
    def __init__(self, runtime):
        self.runtime = runtime

    def huyou_search(self, *args):
        return {"ok": True, "circle_id": args[2], "items": []}

    def huyou_post(self, *args):
        return {"ok": True, "item": {"circle_id": "another-circle", "body": "DO NOT EXPOSE"}}


class ServerTests(unittest.IsolatedAsyncioTestCase):
    async def call(self, server, name, args):
        result = await server.call_tool(name, args)
        return result.structured_content

    async def test_circle_scope_and_wrong_circle_redaction(self):
        with patch.object(mod, "App", FakeApp):
            server = mod.build_server()
            found = await self.call(server, "search_huyou_posts", {"query": "example"})
            self.assertEqual(found["circle_id"], mod.SHU_CIRCLE_ID)
            rejected = await self.call(server, "get_huyou_post", {"target": "123"})
            self.assertEqual(rejected["status"], "wrong_circle")
            self.assertNotIn("DO NOT EXPOSE", str(rejected))

    async def test_exception_does_not_leak_internal_data(self):
        class BrokenApp(FakeApp):
            def huyou_search(self, *args):
                raise RuntimeError("synthetic-private-error")
        with patch.object(mod, "App", BrokenApp):
            result = await self.call(mod.build_server(), "search_huyou_posts", {"query": "example"})
            self.assertEqual(result["status"], "operation_failed")
            self.assertNotIn("synthetic-private-error", str(result))

    async def test_runtime_is_explicit_and_isolated(self):
        homes = []
        class CaptureApp(FakeApp):
            def __init__(self, runtime):
                homes.append(runtime.home)
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(mod, "App", CaptureApp), patch.dict(os.environ, {
                "SHU_HUYOU_HOME": directory, "STU_MCP_HOME": directory + "-unused",
            }):
                mod.build_server()
            self.assertEqual(homes[0], Path(directory).resolve())
        with patch.object(mod, "App", CaptureApp), patch.dict(os.environ, {"SHU_HUYOU_HOME": ""}):
            mod.build_server()
        self.assertIn("shu-huyou-mcp", str(homes[1]))


if __name__ == "__main__":
    unittest.main()
