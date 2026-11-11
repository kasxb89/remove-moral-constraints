import asyncio
from pathlib import Path
import sys

import pytest
from httpx import ASGITransport, AsyncClient


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class ASGITestClient:
    """通过 HTTPX ASGI 传输层同步调用应用，避免依赖 TestClient 适配层。"""

    def __init__(self, app, host="127.0.0.1"):
        self.app = app
        self.host = host

    def request(self, method, path, **kwargs):
        async def send_request():
            transport = ASGITransport(
                app=self.app,
                client=(self.host, 50000),
            )
            async with AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send_request())

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def options(self, path, **kwargs):
        return self.request("OPTIONS", path, **kwargs)


@pytest.fixture
def asgi_client_factory():
    return ASGITestClient


@pytest.fixture(autouse=True)
def isolated_user_directories(tmp_path, monkeypatch):
    """Never let tests discover or write the real Windows/POSIX user profile."""
    home = tmp_path / "isolated-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)

    from codex_session_patcher import cli, config
    from codex_session_patcher.ctf_config import installer, status
    from web.backend import api

    claude_workspace = str(home / ".claude-ctf-workspace")
    opencode_workspace = str(home / ".opencode-ctf-workspace")
    for module in (installer, status):
        monkeypatch.setattr(module, "DEFAULT_CLAUDE_CTF_WORKSPACE", claude_workspace)
        monkeypatch.setattr(module, "DEFAULT_OPENCODE_CTF_WORKSPACE", opencode_workspace)
    configuration = str(home / ".claude-patcher" / "config.json")
    for module in (cli, config, api):
        monkeypatch.setattr(module, "DEFAULT_CONFIG_FILE", configuration)
    monkeypatch.setattr(api, "DEFAULT_CLAUDE_SESSION_DIR", str(home / ".claude" / "projects"))
    monkeypatch.setattr(api, "_CTF_PROMPT_PATHS", {
        "claude_code": str(home / ".claude-ctf-workspace" / ".claude" / "CLAUDE.md")
    })
    api._invalidate_session_cache()
    yield
    api._invalidate_session_cache()
