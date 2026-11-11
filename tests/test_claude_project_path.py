from codex_session_patcher.core.formats import decode_claude_project_path


def test_preserves_plain_path():
    assert decode_claude_project_path("/plain/path") == "/plain/path"


def test_decodes_existing_hyphenated_directory(tmp_path):
    project = tmp_path / "codex-session-patcher"
    project.mkdir()

    encoded = str(project).replace("/", "-")

    assert decode_claude_project_path(encoded) == str(project)


def test_falls_back_when_path_does_not_exist():
    encoded = "-this-encoded-path-does-not-exist-xyz"

    assert decode_claude_project_path(encoded) == "/this/encoded/path/does/not/exist/xyz"
