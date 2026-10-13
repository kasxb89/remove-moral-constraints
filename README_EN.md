<div align="center">

# Remove Moral Constraints

**AI Coding Session Cleaner & CTF/Pentest Prompt Injection Tool**

Supports **Codex CLI** · **Claude Code** · **OpenCode**

[简体中文](./README.md) | English

[![GitHub stars](https://img.shields.io/github/stars/kasxb89/remove-moral-constraints?style=flat-square)](https://github.com/kasxb89/remove-moral-constraints/stargazers)
[![GitHub release](https://img.shields.io/github/v/release/kasxb89/remove-moral-constraints?style=flat-square)](https://github.com/kasxb89/remove-moral-constraints/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)](https://python.org)

The CLI and Python package names stay `codex-patcher` / `codex_session_patcher`, with config in `~/.codex-patcher/`.

</div>

---

## What is this?

AI coding tools (Codex, Claude Code, OpenCode) frequently refuse security-related requests in CTF competitions, penetration testing, and security research scenarios, causing sessions to break.

**Codex Session Patcher** provides two types of solutions:

**1. Session Cleaning** — Scan existing refusal responses and replace them with compliant content so you can resume the session

**2. CTF Prompt Injection** — Inject security testing context at the configuration level to reduce refusals from the start

---

## Quick Start

### Requirements

| Dependency | Version | When it is needed |
|------------|---------|-------------------|
| Python | 3.8+ | Always |
| Node.js | 20.19+ (20.x) or 22.12+ | Only to rebuild the frontend or run development mode |
| Target tool | any | At least one of Codex CLI / Claude Code / OpenCode |

### Start the CTF/Pentest Codex (most common)

```bash
# 1. Install the CTF profile once
codex-patcher --install-ctf-config

# 2. Launch the pentest build
codex -p ctf
```

- `codex -p ctf` applies only to that launch; a plain `codex` session is untouched.
- To give **every** new Codex session the CTF context, use global mode instead: Web UI → Prompt Enhance → Codex → Enable. After that, plain `codex` is enough with no extra flag.
- Check what is currently installed: `codex-patcher --ctf-status`.

### Option 1: Web UI (Recommended)

```bash
git clone https://github.com/kasxb89/remove-moral-constraints.git
cd remove-moral-constraints

./scripts/start-web.sh
```

Then open **http://127.0.0.1:8080** in your browser.

Override the address or port with environment variables:

```bash
PORT=9000 ./scripts/start-web.sh
HOST=127.0.0.1 PORT=9000 ./scripts/start-web.sh
```

The script runs each step only when needed: Python web deps are installed with `pip install -e ".[web]"` only when missing, and the frontend build is skipped when `dist` is current — so production mode starts fine on a machine without Node.js.

**Development mode (split frontend/backend with hot reload, requires Node.js):**

```bash
./scripts/dev-web.sh
```

```
frontend: http://127.0.0.1:3000    ← falls back to the next free port if 3000 is taken
backend:  http://127.0.0.1:8080    ← API docs at http://127.0.0.1:8080/docs
```

Development addresses can also be overridden with `BACKEND_HOST` / `BACKEND_PORT` / `FRONTEND_HOST` / `FRONTEND_PORT`.

### Option 2: Terminal CLI

Install it as a global command:

```bash
./scripts/install.sh
codex-patcher --help
```

The installer writes the entry point to `~/.local/bin/codex-patcher` (a small wrapper pointing at this repo — the core CLI has no third-party dependencies, so no `pip install` is needed). If it warns that `~/.local/bin` is not on your `PATH`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

You can also skip the install and run the same CLI straight from the repo:

```bash
cd remove-moral-constraints
python3 -m codex_session_patcher.cli --help
```

The CLI can launch the Web UI as well:

```bash
codex-patcher --web                     # http://127.0.0.1:8080
codex-patcher --web --host 127.0.0.1 --port 9000
```

Note: `--web` serves FastAPI, so the web dependencies must be installed once (`pip install -e ".[web]"`). `./scripts/start-web.sh` takes care of that for you.

### Option 3: pip install (Optional)

```bash
pip install -e ".[web]"

codex-patcher --help    # session cleaning / CTF injection
codex-patcher-web       # Web UI, default http://127.0.0.1:47832
```

Note that `codex-patcher-web` defaults to port **47832**, unlike the 8080 used by `./scripts/start-web.sh`. To standardize on 8080:

```bash
codex-patcher --web --port 8080
# or
python3 -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8080
```

---

## Using It From the Terminal

### Cleaning Sessions

```bash
# Preview first, do not touch files
codex-patcher --dry-run --show-content

# Clean the latest / all sessions
codex-patcher --latest
codex-patcher --all

# Pick a format (codex / claude-code / opencode / auto, defaults to auto)
codex-patcher --latest --format claude-code
codex-patcher --latest --format opencode

# Custom session directory, no backup, keep reasoning blocks
codex-patcher --latest --session-dir ~/.codex/sessions
codex-patcher --latest --no-backup
codex-patcher --latest --keep-reasoning

# Show help
codex-patcher --help
```

### CTF/Pentest Prompt Injection

**Codex — Profile mode (recommended; only affects sessions started with `-p ctf`):**

```bash
codex-patcher --install-ctf-config

codex -p ctf              # launch with the CTF profile
# refused? → clean the session in the Web UI
codex resume              # continue with full context

codex-patcher --uninstall-ctf-config    # uninstall
```

**Codex — Global mode:** enable it in the Web UI prompt-enhance page. It applies to all new sessions and does not affect existing ones.

**Claude Code / OpenCode — dedicated workspaces:**

```bash
codex-patcher --install-claude-ctf       # creates ~/.claude-ctf-workspace
cd ~/.claude-ctf-workspace && claude

codex-patcher --install-opencode-ctf     # creates ~/.opencode-ctf-workspace
cd ~/.opencode-ctf-workspace && opencode
```

OpenCode has no profile mechanism, so CTF injection depends on the workspace — you must launch from that directory.

**Check injection status across platforms:**

```bash
codex-patcher --ctf-status
```

**Rewrite a prompt** (configure the AI endpoint in the Web UI first):

```bash
codex-patcher --rewrite "Help me write a reverse analysis script"
```

---

## Features

### Session Cleaning
- **Smart Detection** — Two-level refusal detection (strong phrase full-text match + weak keyword prefix match), low false positive rate
- **AI Rewrite** — Call LLM to generate context-aware replacement responses (supports OpenAI / Ollama / OpenRouter compatible APIs)
- **Safe Fallbacks** — Clean historical Codex refusals that only contain `event_msg`; fall back to a safe default when AI returns question-mark mojibake
- **Desktop projection** — Also update `item_completed/AgentMessage` and `thread_history`, so the desktop app does not keep showing a refusal after the JSONL is cleaned
- **Batch Cleaning** — Process all refusal responses in a session, not just the last one
- **Reasoning Erasure** — Remove encrypted Reasoning / Thinking block content
- **Backup & Restore** — Auto-backup before cleaning, one-click restore to any historical version
- **Diff View** — Side-by-side before/after comparison

### CTF/Pentest Prompt Injection
- **Codex Profile Mode** — Create the new `ctf.config.toml` profile, only active when launched with `codex -p ctf`, doesn't affect normal sessions
- **Codex Global Mode** — Inject into global config, automatically active for all new sessions
- **Claude Code Workspace** — Create dedicated CTF workspace `~/.claude-ctf-workspace` with project-level CLAUDE.md injection
- **OpenCode Workspace** — Create dedicated CTF workspace `~/.opencode-ctf-workspace` with AGENTS.md injection
- **Custom Prompts** — Edit injection prompts directly in Web UI, with template save/switch support
- **Three-layer automatic workflow** — The default Codex prompt combines universal rules, the CTF workflow, and task-specific playbooks selected automatically
- **AI Prompt Rewrite** — AI rewrites your requests to align with the injected CTF system prompt for better results

### Platform Support

| Platform | Session Cleaning | CTF Injection | Session Format |
|----------|-----------------|---------------|----------------|
| **Codex CLI** | ✅ | ✅ Profile + Global | JSONL |
| **Claude Code** | ✅ | ✅ Dedicated workspace | JSONL |
| **OpenCode** | ✅ | ✅ Dedicated workspace | SQLite |

### Web UI
- **Session List** — Unified multi-platform management, grouped by date, filter by format/refusal status/backup status
- **Visual Cleaning** — Preview panel + Diff view + one-click execute
- **i18n** — Supports Chinese / English interface
- **Real-time Logs** — WebSocket push, operation logs in real time
- **Loopback boundary** — HTTP, cross-origin requests, and WebSockets only accept loopback clients and local page origins

---

## CTF/Pentest Workflow

### Codex

```bash
# 1. Install the CTF profile
codex-patcher --install-ctf-config

# Strong CTF scenarios can replace Codex built-in instructions
codex-patcher --install-ctf-config --ctf-injection-mode replace

# 2. Launch with the CTF profile (doesn't affect normal sessions)
codex -p ctf

# 3. Refused? → open the Web UI and clean the session
# 4. Continue
codex resume
```

The installer writes the new Codex profile file:

- macOS/Linux: `~/.codex/ctf.config.toml`
- Windows: `%USERPROFILE%\.codex\ctf.config.toml`

To support Codex CLI 0.134.0 and newer, install removes legacy `profile = "ctf"`, `[profiles.ctf]`, and `[profiles.ctf.*]` entries from `config.toml` only when the historical tool marker is present, preventing `codex -p ctf` from failing with a legacy profile error without taking over user-owned profiles. Profile mode and global mode both support appending rules or replacing Codex built-in instructions. Disabling global mode removes the marker and settings managed by this tool.

Codex supports two injection modes:

- Append rules by default: writes `developer_instructions`, preserving Codex built-in instructions. Use this for daily security testing.
- Replace built-in instructions: writes `model_instructions_file` pointing at the prompt file. Use this for strong CTF scenarios; it takes over Codex built-in instructions.

The two modes are mutually exclusive. The Web UI lets you choose the injection mode when enabling Profile or Global mode; the CLI supports `--ctf-injection-mode append|replace`.

The default Codex prompt is one automatic workflow file: universal rules define direct delivery, evidence, and placeholders; the common CTF workflow covers reconnaissance, validation, exploitation, flag recovery, and reproduction; task-specific playbooks are selected from Web, Pwn, reverse engineering, cryptography, forensics, mobile, or cloud task signals. Users do not switch playbooks manually.

Global mode only manages the block marked with `# __csp_ctf_global__`. If `config.toml` already has a user-managed top-level `developer_instructions` or `model_instructions_file`, the installer refuses to enable global mode to avoid overwriting user settings or creating duplicate keys. Remove or migrate the existing top-level instruction setting first.

Profile and prompt files also carry ownership markers. Install, update, and uninstall preserve an unmarked file at a managed path and report the conflict; updating a managed prompt creates a backup first. Custom Claude Code and OpenCode prompts receive the same marker automatically, so status detection and uninstall work consistently.

### Claude Code

```bash
# 1. Web UI → Prompt Enhance → Claude Code → Enable
#    (creates ~/.claude-ctf-workspace)

# 2. Launch from the dedicated workspace
cd ~/.claude-ctf-workspace && claude

# 3. Refused? → clean in the Web UI → continue the conversation
```

### OpenCode

```bash
# 1. Web UI → Prompt Enhance → OpenCode → Enable
#    (creates ~/.opencode-ctf-workspace)

# 2. Launch from the dedicated workspace
cd ~/.opencode-ctf-workspace && opencode

# 3. Refused? → clean in the Web UI → continue the conversation
```

---

## CLI Reference

| Argument | Description |
|----------|-------------|
| `--session-dir` | Specify session directory (auto-selected by default) |
| `--format` | Session format: `codex` / `claude-code` / `opencode` / `auto` (default `auto`) |
| `--dry-run` | Preview mode, don't modify files |
| `--no-backup` | Don't create backup files |
| `--show-content` | Show detailed modification content |
| `--latest` | Process only the latest session |
| `--all` | Process all sessions |
| `--keep-reasoning` | Keep reasoning content (thinking/reasoning blocks), only replace refusal responses |
| `--web` | Launch Web UI |
| `--host` | Web UI listen address (default `127.0.0.1`) |
| `--port` | Web UI port (default `8080`) |
| `--install-ctf-config` | Install Codex CTF config |
| `--ctf-injection-mode append\|replace` | Choose Codex injection mode, defaults to append |
| `--uninstall-ctf-config` | Uninstall Codex CTF config |
| `--install-claude-ctf` | Install Claude Code CTF config |
| `--uninstall-claude-ctf` | Uninstall Claude Code CTF config |
| `--install-opencode-ctf` | Install OpenCode CTF config |
| `--uninstall-opencode-ctf` | Uninstall OpenCode CTF config |
| `--ctf-status` | View CTF config status for all platforms |
| `--rewrite` | Rewrite prompt for better acceptance |

The repo root also keeps the early single-file script `codex_patcher.py` (Codex JSONL sessions only; supports `--select` / `--date` / `--file` / `--memory-file` / `--auto-resume`). Prefer the CLI above for daily use.

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `HOST` / `PORT` | `./scripts/start-web.sh` listen address / port | `127.0.0.1` / `8080` |
| `BACKEND_HOST` / `BACKEND_PORT` | `./scripts/dev-web.sh` backend address / port | `127.0.0.1` / `8080` |
| `FRONTEND_HOST` / `FRONTEND_PORT` | `./scripts/dev-web.sh` frontend address / port | `127.0.0.1` / `3000` |
| `CODEX_SESSION_PATCHER_PYTHON` | Force the Python interpreter used by `codex-patcher` | auto-detected |
| `MUGGLE_LEADS_ENDPOINT` | Submission endpoint for the cooperation-intent form | Hosted Muggle Leads service |
| `MUGGLE_LEADS_SOURCE_ID` / `MUGGLE_LEADS_SOURCE_NAME` | Source identifiers sent with submissions | `codex-session-patcher` / `Codex Session Patcher` |

Cooperation-intent form submissions from the Web UI cooperation page default to the hosted Muggle Leads service (`https://leads.3jiezhiwai.com`). Running the Web UI locally does not require deploying Cloudflare or configuring a submission endpoint. If you fork this project and want submissions to go to your own service:

```bash
export MUGGLE_LEADS_ENDPOINT="https://your-worker-domain/api/sources/codex-session-patcher/intents"
```

Telegram Bot tokens and admin secrets live only in the server-side Cloudflare Worker, never in the local tool or frontend code.

---

## Configuration

CLI and Web UI share `~/.codex-patcher/config.json`:

| Key | Description | Default |
|-----|-------------|---------|
| `mock_response` | Default replacement text | Compliant response |
| `ai_enabled` | Enable AI rewrite | `false` |
| `ai_endpoint` | LLM API endpoint | — |
| `ai_key` | API Key | — |
| `ai_model` | Model name | — |
| `custom_keywords` | Custom refusal detection keywords | `{}` |
| `ctf_prompts` | Custom CTF prompts per platform | Built-in templates |
| `ctf_templates` | User-saved prompt templates | `{}` |

The Web settings API never returns the plaintext `ai_key`; it only reports whether one is configured. The key field stays blank after loading. Saving it blank preserves the existing key, entering a new value replaces it, and saving after Reset explicitly clears it.

---

## Project Structure

```
remove-moral-constraints/
├── codex_session_patcher/        # core library
│   ├── cli.py                    # CLI entry point
│   ├── core/
│   │   ├── formats.py            # multi-platform format strategies
│   │   ├── parser.py             # session parser (JSONL + SQLite)
│   │   ├── sqlite_adapter.py     # OpenCode SQLite adapter
│   │   ├── detector.py           # refusal detector
│   │   └── patcher.py            # cleaning logic
│   └── ctf_config/
│       ├── installer.py          # CTF injection installer (3 platforms)
│       ├── templates.py          # built-in prompt templates
│       └── status.py             # status detection
├── web/
│   ├── backend/                  # FastAPI backend
│   │   ├── api.py                # API routes
│   │   ├── ai_service.py         # AI analysis & rewrite
│   │   ├── prompt_rewriter.py    # prompt rewrite service
│   │   └── schemas.py            # data models
│   └── frontend/                 # Vue 3 + Naive UI
│       └── src/
│           ├── components/       # page components
│           ├── stores/           # Pinia state
│           └── locales/          # i18n
├── scripts/
│   ├── install.sh                # install CLI into ~/.local/bin
│   ├── start-web.sh              # start Web UI (production)
│   └── dev-web.sh                # start Web UI (development)
├── tests/
└── pyproject.toml
```

---

## FAQ

**`./scripts/start-web.sh` cannot find Python**

Python 3.8+ is required. The script tries `python3` / `python` / `python3.13` … `python3.8` / `py -3` in order; you can also point it at a specific interpreter:

```bash
CODEX_SESSION_PATCHER_PYTHON=/usr/bin/python3 ./scripts/start-web.sh
```

**"Node.js version is too old"**

Only rebuilding the frontend and development mode need Node.js, requiring 20.19+ (20.x) or 22.12+. If `web/frontend/dist` exists and is current, production mode never touches Node.js.

**Port 8080 is already in use**

```bash
PORT=9000 ./scripts/start-web.sh
```

**`codex-patcher --web` and `./scripts/start-web.sh` open different ports**

They are different entry points: the script defaults to 8080 (override with `PORT`), the pip-installed `codex-patcher-web` defaults to 47832, and `--web` follows `--port` (default 8080).

**I set `--host 0.0.0.0` and it is still only reachable locally**

The service only serves loopback clients: HTTP requests and WebSockets validate the client address and the page Origin. That boundary is intentional — keep the default `127.0.0.1`.

**`codex -p ctf` fails with a legacy profile error**

Re-run `codex-patcher --install-ctf-config`; the installer cleans up the legacy `profile = "ctf"` / `[profiles.ctf]` entries.

**`codex-patcher --ctf-status` reports Codex as "not installed" even though global mode is on**

The status output currently reflects **Profile mode** only (whether `~/.codex/ctf.config.toml` carries the managed marker); global injection is not part of that line, so ❌ can appear with global mode enabled. To check whether global injection is live, look at the marker in `config.toml`:

```bash
grep -c '__csp_ctf_global__' ~/.codex/config.toml   # 1 = injected, 0 = not injected
```

As long as the marker exists and the `developer_instructions` under it is not commented out, a plain `codex` launch is already the pentest build.

**Chinese output shows up as question marks on Windows**

On Windows Git Bash / MSYS / MINGW / Cygwin the launch scripts set `PYTHONIOENCODING=utf-8` for Python child processes, which avoids GBK console mojibake from the local AI proxy or the Web backend. If you still see `?` runs, export it before starting:

```bash
export PYTHONIOENCODING=utf-8
```

---

## Limitations

- **Cannot bypass platform-level safety policies** — Explicitly illegal requests may still be refused
- **Effectiveness varies by model version** — Model updates may affect results
- **OpenCode requires launching from workspace directory** — OpenCode has no profile mechanism; CTF injection depends on the workspace
- **Resume required after cleaning** — You need to manually resume the session after cleaning

---

## Support

If this project helps you:

- ⭐ Star the repo
- ☕ Sponsor button in the Web UI top-right corner (WeChat / USDC)
- 🐦 X (Twitter): [@YOUR_X_HANDLE](https://x.com/YOUR_X_HANDLE)

---

## License

[MIT License](./LICENSE)

---

<div align="center">
  <a href="https://github.com/kasxb89">GitHub</a> ·
  <a href="https://x.com/YOUR_X_HANDLE">X (Twitter)</a>
</div>
