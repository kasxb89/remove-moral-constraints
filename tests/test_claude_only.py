import json
from pathlib import Path

import pytest

from codex_session_patcher import cli
from codex_session_patcher.core import SessionFormat
from web.backend import api
from web.backend.main import app


@pytest.fixture
def claude_session(tmp_path, monkeypatch):
    projects = tmp_path / "claude-projects"
    project = projects / "test-project"
    project.mkdir(parents=True)
    session = project / "a1234567-1234-1234-1234-123456789abc.jsonl"
    records = [
        {"type": "user", "uuid": "user-1", "message": {"role": "user", "content": "Test request"}},
        {"type": "assistant", "uuid": "assistant-1", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Sorry, I cannot help with that"}
        ]}},
    ]
    original = ("\n".join(json.dumps(row) for row in records) + "\n").encode()
    session.write_bytes(original)
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"mock_response": "Test replacement"}), encoding="utf-8")
    monkeypatch.setattr(api, "DEFAULT_CLAUDE_SESSION_DIR", str(projects))
    monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(config))
    api._invalidate_session_cache()
    yield session, original, projects
    api._invalidate_session_cache()


def test_default_and_auto_discover_only_claude(claude_session, asgi_client_factory):
    client = asgi_client_factory(app)
    for params in ({}, {"format": "auto"}, {"format": "claude_code"}):
        response = client.get("/api/sessions", params=params)
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "claude_code"
        assert data["total"] == 1
        assert {session["format"] for session in data["sessions"]} == {"claude_code"}
    for unsupported in ("codex", "opencode"):
        assert client.get("/api/sessions", params={"format": unsupported}).status_code == 400


def test_only_claude_configuration_routes_are_available(asgi_client_factory):
    client = asgi_client_factory(app)
    paths = app.openapi()["paths"]
    for path in ("/ctf/install", "/ctf/uninstall", "/ctf/global/install", "/ctf/global/uninstall", "/ctf/opencode/install", "/ctf/opencode/uninstall"):
        assert "/api" + path not in paths
        assert client.post("/api" + path).status_code in (404, 405)
    assert client.get("/api/ctf/prompt/codex").status_code == 400
    assert client.get("/api/ctf/prompt/opencode/templates").status_code == 400


def test_claude_preview_patch_and_restore_round_trip(claude_session, asgi_client_factory):
    session, original, _ = claude_session
    client = asgi_client_factory(app)
    entry = client.get("/api/sessions").json()["sessions"][0]
    session_id = entry["id"]
    preview = client.post(f"/api/sessions/{session_id}/preview")
    assert preview.status_code == 200
    assert preview.json()["has_changes"] is True
    assert session.read_bytes() == original

    response = client.post(f"/api/sessions/{session_id}/patch", json={"clean_reasoning": False})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True, data
    backup = Path(data["backup_path"])
    assert backup.read_bytes() == original
    assert "Test replacement" in session.read_text(encoding="utf-8")

    restored = client.post(f"/api/sessions/{session_id}/restore", params={"backup_filename": backup.name})
    assert restored.json()["success"] is True
    assert session.read_bytes() == original


def test_status_does_not_read_other_platform_configuration(monkeypatch, asgi_client_factory):
    from codex_session_patcher import claude, ctf_config

    def forbidden():
        raise AssertionError("Other platform status must not be read")

    monkeypatch.setattr(ctf_config, "check_ctf_status", forbidden)
    monkeypatch.setattr(claude, "claude_workspace_status", lambda: {"claude_installed": True, "activation_command": "claude-ctf"})
    response = asgi_client_factory(app).get("/api/ctf/status")
    assert response.status_code == 200
    assert response.json()["claude_installed"] is True
    assert all(key.startswith("claude_") or key == "activation_command" for key in response.json())


def test_bare_cli_shows_help_without_scanning(monkeypatch, capsys):
    monkeypatch.setattr(cli, "SessionParser", lambda *args, **kwargs: pytest.fail("No implicit scan"))
    assert cli.main([]) == 0
    output = capsys.readouterr().out
    assert "claude-patcher" in output
    assert "Codex" not in output
    assert "OpenCode" not in output


def test_cli_dry_run_preserves_claude_session(claude_session, monkeypatch):
    session, original, projects = claude_session
    monkeypatch.setattr(cli, "load_config", lambda: {"mock_response": "Test replacement"})
    assert cli.main(["--session-dir", str(projects), "--latest", "--dry-run"]) == 0
    assert session.read_bytes() == original
    assert not list(session.parent.glob("*.bak"))
    assert cli.resolve_session_format(type("Args", (), {"format": "auto"})()) == SessionFormat.CLAUDE_CODE


def test_cli_rejects_codex_format():
    with pytest.raises(SystemExit) as error:
        cli.main(["--format", "codex", "--latest"])
    assert error.value.code == 2


def test_prompt_rewrite_requires_claude_target(asgi_client_factory):
    response = asgi_client_factory(app).post("/api/prompt-rewrite", json={"original_request": "Test", "target": "codex"})
    assert response.status_code == 422


@pytest.mark.parametrize("operation", ["get_ctf_prompt", "save_ctf_prompt", "reset_ctf_prompt"])
def test_other_platform_prompt_rejected_even_with_legacy_path(monkeypatch, tmp_path, operation):
    import asyncio
    from fastapi import HTTPException

    protected = tmp_path / "old-prompt.md"
    protected.write_text("Preserve original", encoding="utf-8")
    monkeypatch.setattr(api, "_CTF_PROMPT_PATHS", {"codex": str(protected)})
    handler = getattr(api, operation)
    arguments = ["codex", {"prompt": "Replacement"}] if operation == "save_ctf_prompt" else ["codex"]
    with pytest.raises(HTTPException) as error:
        asyncio.run(handler(*arguments))
    assert error.value.status_code == 400
    assert protected.read_text(encoding="utf-8") == "Preserve original"
