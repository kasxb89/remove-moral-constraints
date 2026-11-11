# Claude Session Patcher

Local session management and global instruction configuration for Claude Code.

This Windows deployment uses Claude sessions from `~/.claude/projects` and user-level global instructions at `~/.claude/CLAUDE.md`.

Commands:

```text
claude-patcher --help
claude-patcher --status
claude-patcher --install-config
claude-patcher --dry-run --latest
claude-patcher --latest
claude-patcher-web
claude-ctf
```

The web interface is available at http://127.0.0.1:8080 and only accepts local clients. Session changes are previewable and create backups by default. Application settings are stored at `~/.claude-patcher/config.json`; existing Claude Code authentication and API settings remain managed by Claude Code.

See [the Chinese README](README.md) for the Windows deployment and development instructions.

Global instructions apply to new sessions in every project. Both `claude` and `claude-ctf` keep the current project directory. This tool preserves unrelated global instructions and does not change other coding agents.

Instructions are loaded as context. This tool does not modify the official Claude client or model, and cannot guarantee that refusals disappear.
