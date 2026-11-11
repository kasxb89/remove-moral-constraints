"""Claude Code deployment settings and workspace status."""

import os
import shutil
from pathlib import Path

from .ctf_config.status import has_ctf_marker
from .file_ops import atomic_write_text, create_unique_backup, require_regular_or_missing

APP_NAME = "Claude Session Patcher"
GLOBAL_START = "<!-- claude-session-patcher:global:start -->"
GLOBAL_END = "<!-- claude-session-patcher:global:end -->"


def claude_global_prompt_path() -> Path:
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(config_dir).expanduser() if config_dir else Path.home() / ".claude") / "CLAUDE.md"


def _managed_span(content: str):
    if GLOBAL_START not in content and GLOBAL_END not in content:
        return None
    if content.count(GLOBAL_START) != 1 or content.count(GLOBAL_END) != 1:
        raise ValueError("Claude 全局配置标记不完整或重复，已保留原文件")
    start = content.index(GLOBAL_START)
    end = content.index(GLOBAL_END)
    if end < start:
        raise ValueError("Claude 全局配置标记顺序异常，已保留原文件")
    after = end + len(GLOBAL_END)
    if content[after:after + 2] == "\n\n":
        after += 2
    return start, after, content[start + len(GLOBAL_START):end].strip()


def read_claude_global_prompt(path=None):
    target = Path(path) if path is not None else claude_global_prompt_path()
    if require_regular_or_missing(target) is None:
        return None
    content = target.read_bytes().decode("utf-8")
    span = _managed_span(content)
    if span is not None:
        return span[2]
    return None


class ClaudeGlobalConfigInstaller:
    """Manage only our section in Claude's user-level CLAUDE.md."""

    def __init__(self, prompt_path=None):
        self.prompt_path = Path(prompt_path) if prompt_path is not None else claude_global_prompt_path()
        protected = (Path.home() / ".codex").resolve()
        resolved = self.prompt_path.resolve()
        if resolved == protected or protected in resolved.parents:
            raise ValueError("Claude 全局配置目标不能位于 Codex 配置目录")

    def install(self, custom_prompt=None):
        try:
            current = require_regular_or_missing(self.prompt_path)
            content = self.prompt_path.read_bytes().decode("utf-8") if current is not None else ""
            span = _managed_span(content)
            workspace = Path.home() / ".claude-ctf-workspace" / ".claude" / "CLAUDE.md"
            workspace_text = None
            if require_regular_or_missing(workspace) is not None:
                candidate = workspace.read_bytes().decode("utf-8")
                if has_ctf_marker(candidate):
                    workspace_text = candidate
            if custom_prompt is None:
                custom_prompt = read_claude_global_prompt(self.prompt_path) or workspace_text
            if custom_prompt is None:
                from .ctf_config.templates import CLAUDE_CODE_SECURITY_MODE_PROMPT
                custom_prompt = CLAUDE_CODE_SECURITY_MODE_PROMPT
            if not custom_prompt.strip():
                raise ValueError("Claude 全局提示词不能为空")
            prompt = ensure_claude_marker(custom_prompt).strip()
            block = f"{GLOBAL_START}\n{prompt}\n{GLOBAL_END}\n\n"
            if span is not None:
                updated = content[:span[0]] + block + content[span[1]:]
            else:
                updated = block + content
            details = []
            if updated != content:
                if current is not None:
                    details.append(f"已备份原全局文件: {create_unique_backup(self.prompt_path)}")
                atomic_write_text(self.prompt_path, updated)
            if workspace_text is not None:
                backup = create_unique_backup(workspace)
                try:
                    workspace.unlink()
                    details.append(f"旧工作目录提示词已备份迁移: {backup}")
                except OSError:
                    details.append("全局已生效；旧工作目录副本仍被占用，请稍后移除重复副本")
            details.insert(0, f"Claude 全局提示词已启用: {self.prompt_path}")
            details.append("在任意项目目录新建 Claude 会话即可使用")
            return True, "\n".join(details)
        except Exception as exc:
            return False, f"Claude 全局配置失败: {exc}"

    def uninstall(self):
        try:
            if require_regular_or_missing(self.prompt_path) is None:
                return True, "Claude 全局提示词未启用"
            content = self.prompt_path.read_bytes().decode("utf-8")
            span = _managed_span(content)
            if span is not None:
                updated = content[:span[0]] + content[span[1]:]
            else:
                return True, "没有本工具管理的 Claude 全局提示词，已保留用户原文件"
            backup = create_unique_backup(self.prompt_path)
            atomic_write_text(self.prompt_path, updated)
            return True, f"已移除本工具的全局提示词，其他内容保留。备份: {backup}"
        except Exception as exc:
            return False, f"Claude 全局配置卸载失败: {exc}"


def ensure_claude_marker(content: str) -> str:
    marker = "managed-by: claude-session-patcher:ctf"
    content = content.replace("managed-by: codex-session-patcher:ctf", marker, 1)
    if marker in content[:500]:
        return content
    return f"<!-- {marker} -->\n{content.lstrip(chr(10))}"


def claude_workspace_status() -> dict:
    workspace = Path.home() / ".claude-ctf-workspace"
    prompt = claude_global_prompt_path()
    exists = prompt.exists()
    installed = read_claude_global_prompt(prompt) is not None
    return {
        "claude_installed": installed,
        "claude_workspace_exists": workspace.is_dir(),
        "claude_prompt_exists": exists,
        "claude_workspace_path": str(workspace),
        "claude_prompt_path": str(prompt),
        "claude_global_prompt_path": str(prompt),
        "claude_global_installed": installed,
        "claude_scope": "global",
        "claude_cli_available": bool(shutil.which("claude") or shutil.which("claude.cmd")),
        "activation_command": "claude",
    }
