"""Exercise the installed stdio server with an isolated, empty data directory."""
import argparse
import asyncio
import os
import sys
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def data(result):
    value = result.structured_content
    if not isinstance(value, dict) or not value.get("ok"):
        raise RuntimeError("Tool failed: " + str(value.get("status") if isinstance(value, dict) else "invalid_response"))
    return value


async def verify(live):
    with tempfile.TemporaryDirectory(prefix="shu-huyou-check-") as home:
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "shu_huyou_mcp"],
            env={**os.environ, "SHU_HUYOU_HOME": home},
        )
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                listing = await session.list_tools()
                names = {t.name for t in listing.tools}
                assert names == {"get_shu_huyou_info", "search_huyou_posts", "get_huyou_post"}, names
                info = data(await session.call_tool("get_shu_huyou_info", {}))
                assert info["circle_id"] == "826522127825056896"
                empty = data(await session.call_tool("search_huyou_posts", {
                    "query": "test", "keywords": ["test"], "local": True,
                }))
                assert empty["items"] == []
                print("MCP_HANDSHAKE=PASS\nTOOLS=3\nOFFLINE_CHECK=PASS", flush=True)
                if live:
                    found = data(await session.call_tool("search_huyou_posts", {
                        "query": "考试", "keywords": ["考试"], "limit": 2, "pages": 1,
                    }))
                    assert found["items"], "No posts returned by public search"
                    assert all(str(p["circle_id"]) == info["circle_id"] for p in found["items"])
                    post = data(await session.call_tool("get_huyou_post", {
                        "target": found["items"][0]["feed_id"], "comment_limit": 3, "reply_limit": 2,
                    }))
                    assert str(post["item"]["circle_id"]) == info["circle_id"]
                    assert isinstance(post["item"]["discussion"]["comments"], list)
                    print("LIVE_SEARCH=PASS\nLIVE_DETAIL=PASS", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Also query the public Huyou service")
    asyncio.run(verify(parser.parse_args().live))
