import os
import subprocess
from pathlib import Path

import pytest

from codex_session_patcher import claude
from web.backend import api
from web.backend.main import app


def test_global_migration_preserves_user_content_and_backs_up_workspace():
    target = claude.claude_global_prompt_path()
    target.parent.mkdir(parents=True)
    original = b"# My preferences\r\nKeep my formatting.\r\n"
    target.write_bytes(original)
    workspace = Path.home() / '.claude-ctf-workspace' / '.claude' / 'CLAUDE.md'
    workspace.parent.mkdir(parents=True)
    local_prompt = claude.ensure_claude_marker('# Existing Claude prompt')
    workspace.write_bytes(local_prompt.encode('utf-8'))

    success, message = claude.ClaudeGlobalConfigInstaller().install()
    assert success, message
    assert target.read_bytes().endswith(original)
    assert claude.read_claude_global_prompt() == local_prompt
    assert not workspace.exists()
    assert len(list(workspace.parent.glob('CLAUDE.md.*.bak'))) == 1
    assert claude.claude_workspace_status()['claude_global_installed'] is True


def test_global_update_and_uninstall_preserve_unrelated_instructions():
    target = claude.claude_global_prompt_path()
    target.parent.mkdir(parents=True)
    original = b'Personal instructions without a final newline'
    target.write_bytes(original)
    installer = claude.ClaudeGlobalConfigInstaller()
    assert installer.install('# First prompt')[0]
    assert installer.install('# Updated prompt')[0]
    before = target.read_bytes()
    assert installer.install('# Updated prompt')[0]
    assert target.read_bytes() == before
    assert target.read_text(encoding='utf-8').count(claude.GLOBAL_START) == 1
    assert installer.uninstall()[0]
    assert target.read_bytes() == original


def test_uninstall_does_not_adopt_unmanaged_or_legacy_global_content():
    target = claude.claude_global_prompt_path()
    target.parent.mkdir(parents=True)
    original = b'<!-- managed-by: codex-session-patcher:ctf -->\nUser-owned global content'
    target.write_bytes(original)
    assert claude.ClaudeGlobalConfigInstaller().uninstall()[0]
    assert target.read_bytes() == original


def test_malformed_global_section_is_not_overwritten():
    target = claude.claude_global_prompt_path()
    target.parent.mkdir(parents=True)
    original = claude.GLOBAL_START + '\nIncomplete section'
    target.write_text(original, encoding='utf-8')
    assert claude.ClaudeGlobalConfigInstaller().install('# New prompt')[0] is False
    assert target.read_text(encoding='utf-8') == original


def test_failed_global_write_preserves_existing_file(monkeypatch):
    target = claude.claude_global_prompt_path()
    target.parent.mkdir(parents=True)
    target.write_bytes(b'Personal preferences')

    def fail_write(*args, **kwargs):
        raise PermissionError('simulated failure')

    monkeypatch.setattr(claude, 'atomic_write_text', fail_write)
    assert claude.ClaudeGlobalConfigInstaller().install('# New prompt')[0] is False
    assert target.read_bytes() == b'Personal preferences'


def test_claude_global_installer_rejects_codex_directory(monkeypatch):
    protected = Path.home() / '.codex'
    monkeypatch.setenv('CLAUDE_CONFIG_DIR', str(protected))
    with pytest.raises(ValueError, match='Codex'):
        claude.ClaudeGlobalConfigInstaller()
    assert not protected.exists()


def test_cli_rewrite_uses_the_global_prompt(monkeypatch):
    from codex_session_patcher import cli
    from web.backend import prompt_rewriter

    assert claude.ClaudeGlobalConfigInstaller().install('# My global instructions')[0]
    monkeypatch.setattr(cli, 'load_config', lambda: {'ai_endpoint':'http://example.invalid', 'ai_model':'test'})
    captured = {}

    async def rewrite(*args, **kwargs):
        captured.update(kwargs)
        return 'Test rewrite', 'test'

    monkeypatch.setattr(prompt_rewriter, 'rewrite_prompt', rewrite)
    assert cli.handle_rewrite('Test request') == 0
    assert captured['ctf_prompt'] == claude.read_claude_global_prompt()


def test_global_prompt_api_updates_only_managed_section(monkeypatch, asgi_client_factory):
    target = claude.claude_global_prompt_path()
    target.parent.mkdir(parents=True)
    original = b'My own instructions\r\n'
    target.write_bytes(original)
    assert claude.ClaudeGlobalConfigInstaller().install('# First prompt')[0]
    monkeypatch.setattr(api, '_CTF_PROMPT_PATHS', {'claude_code': str(target)})
    client = asgi_client_factory(app)
    result = client.get('/api/ctf/prompt/claude_code').json()
    assert '# First prompt' in result['prompt']
    assert 'My own instructions' not in result['prompt']
    assert client.post('/api/ctf/prompt/claude_code', json={'prompt':'# Updated prompt'}).json()['success']
    assert target.read_bytes().endswith(original)
    assert '# Updated prompt' in claude.read_claude_global_prompt()
    assert client.post('/api/ctf/claude/uninstall').json()['success']
    assert target.read_bytes() == original


@pytest.mark.skipif(os.name != 'nt', reason='Windows launcher')
def test_claude_launcher_preserves_current_project(tmp_path, monkeypatch):
    target = claude.claude_global_prompt_path()
    target.parent.mkdir(parents=True)
    target.write_text('Global instructions', encoding='utf-8')
    prefix = tmp_path / 'fake-cli'
    prefix.mkdir()
    (prefix / 'npm.cmd').write_bytes(('@echo off\r\necho ' + str(prefix) + '\r\n').encode())
    (prefix / 'claude.cmd').write_bytes(b'@echo off\r\necho CWD=%CD%\r\nexit /b 0\r\n')
    monkeypatch.setenv('PATH', str(prefix) + os.pathsep + os.environ['PATH'])
    project = tmp_path / 'project with spaces'
    project.mkdir()
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'start-claude.ps1'
    result = subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],cwd=project,capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert 'CWD=' + str(project) in result.stdout
