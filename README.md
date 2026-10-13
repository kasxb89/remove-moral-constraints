<div align="center">

# Remove Moral Constraints

**AI 编码工具会话清理器 & CTF/渗透测试提示词注入工具**

支持 **Codex CLI** · **Claude Code** · **OpenCode**

[English](./README_EN.md) | 简体中文

[![GitHub stars](https://img.shields.io/github/stars/kasxb89/remove-moral-constraints?style=flat-square)](https://github.com/kasxb89/remove-moral-constraints/stargazers)
[![GitHub release](https://img.shields.io/github/v/release/kasxb89/remove-moral-constraints?style=flat-square)](https://github.com/kasxb89/remove-moral-constraints/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)](https://python.org)

命令行与 Python 包名沿用 `codex-patcher` / `codex_session_patcher`，配置目录为 `~/.codex-patcher/`。

</div>

---

## 是什么

在安全测试、CTF 比赛、渗透测试等场景下，AI 编码工具（Codex、Claude Code、OpenCode）会频繁拒绝涉及安全操作的请求，导致会话中断。

**Codex Session Patcher** 提供两类解决方案：

**1. 会话清理** — 扫描已产生的拒绝回复，替换为配合性内容，让会话可以 resume 继续

**2. CTF 提示词注入** — 在配置层面注入安全测试上下文，从源头降低被拒绝的概率

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 何时需要 |
|------|------|---------|
| Python | 3.8+ | 必需 |
| Node.js | 20.19+（20.x）或 22.12+ | 仅重新构建前端或使用开发模式时需要 |
| 目标工具 | 任一 | Codex CLI / Claude Code / OpenCode，至少装一个 |

### 启动渗透版 Codex（最常用）

```bash
# 1. 装一次 CTF Profile
codex-patcher --install-ctf-config

# 2. 用渗透版启动
codex -p ctf
```

- `codex -p ctf` 只在这次启动生效，普通 `codex` 会话完全不受影响。
- 想让**所有** Codex 新会话都带 CTF 上下文，就用全局模式：Web UI → 提示词增强 → Codex → 启用。之后直接敲 `codex` 即可，不加参数。
- 查看当前装了什么：`codex-patcher --ctf-status`。

### 启动方式一：Web UI（推荐）

```bash
git clone https://github.com/kasxb89/remove-moral-constraints.git
cd remove-moral-constraints

./scripts/start-web.sh
```

启动后浏览器打开 **http://127.0.0.1:8080**。

换地址或端口用环境变量覆盖：

```bash
PORT=9000 ./scripts/start-web.sh
HOST=127.0.0.1 PORT=9000 ./scripts/start-web.sh
```

脚本按需执行，不会重复安装：Python Web 依赖缺失才 `pip install -e ".[web]"`；前端 `dist` 已是最新就直接跳过构建——所以只跑生产模式时，机器上没有 Node.js 也能启动。

**开发模式（前后端分离 + 热更新，需要 Node.js）：**

```bash
./scripts/dev-web.sh
```

```
前端: http://127.0.0.1:3000    ← 3000 被占用时自动顺延到下一个可用端口
后端: http://127.0.0.1:8080    ← API 文档在 http://127.0.0.1:8080/docs
```

开发模式的前后端地址也可用 `BACKEND_HOST` / `BACKEND_PORT` / `FRONTEND_HOST` / `FRONTEND_PORT` 覆盖。

### 启动方式二：终端 CLI

安装成全局命令：

```bash
./scripts/install.sh
codex-patcher --help
```

安装脚本把可执行入口写到 `~/.local/bin/codex-patcher`（一个指向仓库的包装脚本，核心 CLI 无第三方依赖，不需要额外 `pip install`）。如果它提示 `~/.local/bin` 不在 PATH 中：

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

也可以不安装，直接在仓库目录里跑同一个 CLI：

```bash
cd remove-moral-constraints
python3 -m codex_session_patcher.cli --help
```

CLI 也能直接拉起 Web UI：

```bash
codex-patcher --web                     # http://127.0.0.1:8080
codex-patcher --web --host 127.0.0.1 --port 9000
```

注意：`--web` 走的是 FastAPI，需要先装一次 Web 依赖（`pip install -e ".[web]"`）。如果你用的是 `./scripts/start-web.sh`，这一步由脚本自动完成。

### 启动方式三：pip 安装（可选）

```bash
pip install -e ".[web]"

codex-patcher --help    # 会话清理 / CTF 注入
codex-patcher-web       # Web UI，默认 http://127.0.0.1:47832
```

注意 `codex-patcher-web` 的默认端口是 **47832**，与 `./scripts/start-web.sh` 的 8080 不同。想统一用 8080：

```bash
codex-patcher --web --port 8080
# 或者
python3 -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8080
```

---

## 终端里怎么用

### 清理会话

```bash
# 先预览，不改文件
codex-patcher --dry-run --show-content

# 清理最新 / 全部会话
codex-patcher --latest
codex-patcher --all

# 指定格式（codex / claude-code / opencode / auto，默认 auto）
codex-patcher --latest --format claude-code
codex-patcher --latest --format opencode

# 指定会话目录、不创建备份、保留推理内容
codex-patcher --latest --session-dir ~/.codex/sessions
codex-patcher --latest --no-backup
codex-patcher --latest --keep-reasoning

# 查看帮助
codex-patcher --help
```

### CTF/渗透测试提示词注入

**Codex —— Profile 模式（推荐，只影响 `-p ctf` 启动的会话）：**

```bash
codex-patcher --install-ctf-config

codex -p ctf              # 用 CTF profile 启动
# 遇到拒绝 → Web UI 清理会话
codex resume              # 继续上下文

codex-patcher --uninstall-ctf-config    # 卸载
```

**Codex —— 全局模式：** 在 Web UI 的提示词增强页启用，所有新会话自动生效，不影响已有会话。

**Claude Code / OpenCode —— 专用工作空间：**

```bash
codex-patcher --install-claude-ctf       # 创建 ~/.claude-ctf-workspace
cd ~/.claude-ctf-workspace && claude

codex-patcher --install-opencode-ctf     # 创建 ~/.opencode-ctf-workspace
cd ~/.opencode-ctf-workspace && opencode
```

OpenCode 没有 profile 机制，CTF 注入依赖工作空间，必须从该目录启动。

**查看三平台注入状态：**

```bash
codex-patcher --ctf-status
```

**改写提示词**（需先在 Web UI 配置 AI 接口）：

```bash
codex-patcher --rewrite "帮我写一个逆向分析脚本"
```

---

## 功能特性

### 会话清理
- **智能检测** — 两级拒绝检测策略（强短语全文匹配 + 弱关键词开头匹配），低误报率
- **AI 智能改写** — 调用 LLM 根据对话上下文生成符合语境的替换回复（支持 OpenAI / Ollama / OpenRouter 等兼容接口）
- **安全兜底** — 可清理只有 `event_msg` 的历史 Codex 拒绝记录；AI 返回问号乱码时自动回退到安全默认文本
- **桌面端投影** — 同步清理 `item_completed/AgentMessage` 和 `thread_history`，避免只改 JSONL 后界面仍显示拒绝
- **批量清理** — 处理会话中所有拒绝回复，而非仅最后一条
- **推理内容擦除** — 删除 Reasoning / Thinking block 加密推理内容
- **备份还原** — 清理前自动备份，支持一键还原到任意历史版本
- **Diff 对比** — 清理前后 Side-by-side 对比视图

### CTF/渗透测试提示词注入
- **Codex Profile 模式** — 创建新版 `ctf.config.toml` profile，仅 `codex -p ctf` 启动时生效，不影响正常会话
- **Codex 全局模式** — 注入到全局配置，所有新会话自动生效
- **Claude Code 工作空间** — 创建专用 CTF 工作空间 `~/.claude-ctf-workspace`，通过项目级 CLAUDE.md 注入
- **OpenCode 工作空间** — 创建专用 CTF 工作空间 `~/.opencode-ctf-workspace`，通过 AGENTS.md 注入
- **提示词自定义** — Web UI 内直接编辑注入提示词，支持模板保存与切换
- **三层自动工作流** — Codex 默认模板按通用执行规则、CTF 工作流和专项规则组织，自动匹配题型，无需手动切换
- **AI 提示词改写** — 结合已注入的 CTF 系统提示词，AI 改写你的请求使其更易被接受

### 平台支持

| 平台 | 会话清理 | CTF 注入 | 会话格式 |
|------|---------|---------|---------|
| **Codex CLI** | ✅ | ✅ Profile + 全局 | JSONL |
| **Claude Code** | ✅ | ✅ 专用工作空间 | JSONL |
| **OpenCode** | ✅ | ✅ 专用工作空间 | SQLite |

### Web UI
- **会话列表** — 多平台统一管理，按日期分组，支持按格式/拒绝状态/备份状态过滤
- **可视化清理** — 预览面板 + Diff 对比 + 一键执行
- **多语言** — 支持中文 / English 界面切换
- **实时日志** — WebSocket 推送，操作日志实时显示
- **本机访问边界** — HTTP、跨域请求和 WebSocket 只接受回环客户端与本机页面来源

---

## CTF/渗透测试工作流

### Codex

```bash
# 1. 安装 CTF Profile
codex-patcher --install-ctf-config

# 强 CTF 场景可选择替换 Codex 内置提示词
codex-patcher --install-ctf-config --ctf-injection-mode replace

# 2. 用 CTF Profile 启动（不影响普通会话）
codex -p ctf

# 3. 遇到拒绝 → 打开 Web UI 清理会话
# 4. 继续
codex resume
```

安装器会写入新版 Codex profile 文件：

- macOS/Linux: `~/.codex/ctf.config.toml`
- Windows: `%USERPROFILE%\.codex\ctf.config.toml`

为兼容 Codex CLI 0.134.0 及以后版本，安装时会从 `config.toml` 清理带有本工具历史标记的旧格式 `profile = "ctf"`、`[profiles.ctf]` 和 `[profiles.ctf.*]`，避免 `codex -p ctf` 启动时报 legacy profile 错误。Profile 模式和全局模式都支持追加规则或替换内置提示词；禁用全局模式会移除本工具写入的标记和配置。

Codex 提供两种注入方式：

- 默认追加规则：写入 `developer_instructions`，保留 Codex 内置提示词，适合日常安全测试。
- 替换内置提示词：写入 `model_instructions_file` 指向提示词文件，适合强 CTF 场景，但会接管 Codex 原本的内置提示词。

两种方式互斥。通过 Web UI 启用 Profile 或全局模式时可选择注入方式；CLI 可用 `--ctf-injection-mode append|replace`。

默认 Codex 提示词是单文件自动工作流：通用规则负责直接交付、证据和占位符；统一 CTF 流程负责侦察、验证、利用、取旗与复现；专项规则按 Web、Pwn、逆向、密码学、取证、移动端或云环境等任务语义自动采用。用户不需要手动选择专项模板。

全局模式只管理带有 `# __csp_ctf_global__` 标记的配置块。如果 `config.toml` 顶层已经存在用户自己写的 `developer_instructions` 或 `model_instructions_file`，安装器会拒绝启用全局模式，避免覆盖用户配置或生成重复 key；请先手动迁移或删除原有顶层提示词配置。

Profile 和提示词文件也使用管理标记。遇到没有标记的同名配置或提示词时，安装、更新和卸载都会保留原文件并报告冲突；更新已管理提示词前会先创建备份。Claude Code 与 OpenCode 的自定义提示词会自动添加同类标记，因此可以正常识别状态并安全卸载。

### Claude Code

```bash
# 1. Web UI → 提示词增强 → Claude Code → 启用
#    （创建 ~/.claude-ctf-workspace）

# 2. 从专用工作空间启动
cd ~/.claude-ctf-workspace && claude

# 3. 遇到拒绝 → Web UI 清理 → 继续对话
```

### OpenCode

```bash
# 1. Web UI → 提示词增强 → OpenCode → 启用
#    （创建 ~/.opencode-ctf-workspace）

# 2. 从专用工作空间启动
cd ~/.opencode-ctf-workspace && opencode

# 3. 遇到拒绝 → Web UI 清理 → 继续对话
```

---

## CLI 参数速查

| 参数 | 说明 |
|------|------|
| `--session-dir` | 指定会话目录（默认自动选择） |
| `--format` | 会话格式：`codex` / `claude-code` / `opencode` / `auto`（默认 `auto`） |
| `--dry-run` | 预览模式，不修改文件 |
| `--no-backup` | 不创建备份文件 |
| `--show-content` | 显示修改的详细内容 |
| `--latest` | 只处理最新会话 |
| `--all` | 处理所有会话 |
| `--keep-reasoning` | 保留推理内容（thinking/reasoning blocks），仅替换拒绝回复 |
| `--web` | 启动 Web UI |
| `--host` | Web UI 监听地址（默认 `127.0.0.1`） |
| `--port` | Web UI 端口（默认 `8080`） |
| `--install-ctf-config` | 安装 Codex CTF 配置 |
| `--ctf-injection-mode append\|replace` | 选择 Codex 注入方式，默认追加规则 |
| `--uninstall-ctf-config` | 卸载 Codex CTF 配置 |
| `--install-claude-ctf` | 安装 Claude Code CTF 配置 |
| `--uninstall-claude-ctf` | 卸载 Claude Code CTF 配置 |
| `--install-opencode-ctf` | 安装 OpenCode CTF 配置 |
| `--uninstall-opencode-ctf` | 卸载 OpenCode CTF 配置 |
| `--ctf-status` | 查看三平台 CTF 配置状态 |
| `--rewrite` | 改写提示词使其更易被接受 |

仓库根目录还保留了早期单文件脚本 `codex_patcher.py`（仅处理 Codex JSONL 会话，支持 `--select` / `--date` / `--file` / `--memory-file` / `--auto-resume`）。日常使用请优先用上面的 CLI。

---

## 环境变量

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `HOST` / `PORT` | `./scripts/start-web.sh` 的监听地址 / 端口 | `127.0.0.1` / `8080` |
| `BACKEND_HOST` / `BACKEND_PORT` | `./scripts/dev-web.sh` 后端地址 / 端口 | `127.0.0.1` / `8080` |
| `FRONTEND_HOST` / `FRONTEND_PORT` | `./scripts/dev-web.sh` 前端地址 / 端口 | `127.0.0.1` / `3000` |
| `CODEX_SESSION_PATCHER_PYTHON` | 强制 `codex-patcher` 使用的 Python 解释器 | 自动探测 |
| `MUGGLE_LEADS_ENDPOINT` | 合作意向表单的提交地址 | 线上 Muggle Leads 服务 |
| `MUGGLE_LEADS_SOURCE_ID` / `MUGGLE_LEADS_SOURCE_NAME` | 提交时携带的来源标识 | `codex-session-patcher` / `Codex Session Patcher` |

Web UI 合作页里的合作意向表单默认提交到线上服务 `https://leads.3jiezhiwai.com`，本地运行不需要部署 Cloudflare，也不需要配置提交地址。如果你 fork 了项目并希望表单提交到自己的服务：

```bash
export MUGGLE_LEADS_ENDPOINT="https://你的 Worker 域名/api/sources/codex-session-patcher/intents"
```

Telegram Bot token 和后台管理密钥只配置在服务端的 Cloudflare Worker 里，不能放在本地工具或前端代码中。

---

## 配置

CLI 和 Web UI 共享配置文件 `~/.codex-patcher/config.json`：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `mock_response` | 默认替换文本 | 配合性回复 |
| `ai_enabled` | 启用 AI 改写 | `false` |
| `ai_endpoint` | LLM API 地址 | — |
| `ai_key` | API Key | — |
| `ai_model` | 模型名称 | — |
| `custom_keywords` | 自定义拒绝检测关键词 | `{}` |
| `ctf_prompts` | 各平台自定义 CTF 提示词 | 内置模板 |
| `ctf_templates` | 用户保存的提示词模板 | `{}` |

Web 设置接口不会返回 `ai_key` 明文，只返回是否已配置。设置页加载后密钥框保持为空；直接保存会保留原密钥，输入新值会替换，重置后保存会明确清除。

---

## 项目结构

```
remove-moral-constraints/
├── codex_session_patcher/        # 核心库
│   ├── cli.py                    # CLI 入口
│   ├── core/
│   │   ├── formats.py            # 多平台格式策略
│   │   ├── parser.py             # 会话解析器（JSONL + SQLite）
│   │   ├── sqlite_adapter.py     # OpenCode SQLite 适配器
│   │   ├── detector.py           # 拒绝检测器
│   │   └── patcher.py            # 清理逻辑
│   └── ctf_config/
│       ├── installer.py          # CTF 注入安装器（三平台）
│       ├── templates.py          # 内置提示词模板
│       └── status.py             # 状态检测
├── web/
│   ├── backend/                  # FastAPI 后端
│   │   ├── api.py                # API 路由
│   │   ├── ai_service.py         # AI 分析 & 改写
│   │   ├── prompt_rewriter.py    # 提示词改写服务
│   │   └── schemas.py            # 数据模型
│   └── frontend/                 # Vue 3 + Naive UI
│       └── src/
│           ├── components/       # 页面组件
│           ├── stores/           # Pinia 状态管理
│           └── locales/          # i18n 国际化
├── scripts/
│   ├── install.sh                # 安装 CLI 到 ~/.local/bin
│   ├── start-web.sh              # 启动 Web UI（生产）
│   └── dev-web.sh                # 启动 Web UI（开发）
├── tests/
└── pyproject.toml
```

---

## 常见问题

**`./scripts/start-web.sh` 报找不到 Python**

需要 Python 3.8+。脚本会依次尝试 `python3` / `python` / `python3.13` … `python3.8` / `py -3`；也可以显式指定解释器后重试：

```bash
CODEX_SESSION_PATCHER_PYTHON=/usr/bin/python3 ./scripts/start-web.sh
```

**提示 Node.js 版本过低**

只有「重新构建前端」和「开发模式」需要 Node.js，要求 20.19+（20.x）或 22.12+。如果 `web/frontend/dist` 已存在且是最新的，生产模式不会碰 Node.js。

**8080 端口被占用**

```bash
PORT=9000 ./scripts/start-web.sh
```

**`codex-patcher --web` 和 `./scripts/start-web.sh` 打开的端口不一样**

两者是不同的入口：脚本默认 8080（可用 `PORT` 覆盖），pip 安装出的 `codex-patcher-web` 默认 47832，`--web` 则跟随 `--port`（默认 8080）。

**设置了 `--host 0.0.0.0` 还是只能本机访问**

服务只服务回环来源：HTTP 请求和 WebSocket 会校验客户端地址与页面 Origin。这是有意的安全边界，请保持默认 `127.0.0.1`。

**`codex -p ctf` 启动报 legacy profile 错误**

重跑一次 `codex-patcher --install-ctf-config`，安装器会清理旧格式的 `profile = "ctf"` / `[profiles.ctf]` 配置。

**`codex-patcher --ctf-status` 显示 Codex「未安装」，但我明明开了全局模式**

状态输出目前只反映 **Profile 模式**（`~/.codex/ctf.config.toml` 里有没有管理标记），全局注入不在这一行体现，所以开了全局模式也可能显示 ❌。判断全局注入是否生效，直接看 `config.toml` 里的标记：

```bash
grep -c '__csp_ctf_global__' ~/.codex/config.toml   # 1 = 已注入，0 = 未注入
```

只要标记在、且它下面的 `developer_instructions` 没被注释，直接 `codex` 启动就已经是渗透版。

**Windows 下中文输出变成问号**

在 Windows 的 Git Bash / MSYS / MINGW / Cygwin 环境中，启动脚本会自动为 Python 子进程设置 `PYTHONIOENCODING=utf-8`，减少本地 AI 代理或 Web 后端因 GBK 控制台导致中文变成问号串的概率。如果仍然出现 `?`，启动前自己导出一份：

```bash
export PYTHONIOENCODING=utf-8
```

---

## 局限性说明

- **无法突破平台最高安全策略** — 对于明确违规的请求仍可能被拒绝
- **效果因版本而异** — 模型版本更新可能影响效果
- **OpenCode 需从工作空间目录启动** — OpenCode 无 profile 机制，CTF 注入依赖工作空间
- **清理后需 resume** — 会话清理后需手动 resume 继续上下文

---

## 支持作者

如果这个项目对你有帮助，欢迎：

- ⭐ 点个 Star
- ☕ Web UI 右上角有赞赏入口（微信 / USDC）
- 📢 微信公众号：`YOUR_WECHAT_MP`
- 🐦 X (Twitter)：[@YOUR_X_HANDLE](https://x.com/YOUR_X_HANDLE)

---

## 许可证

[MIT License](./LICENSE)

---

<div align="center">
  <a href="https://github.com/kasxb89">GitHub</a> ·
  <a href="https://x.com/YOUR_X_HANDLE">X (Twitter)</a> ·
  微信公众号：YOUR_WECHAT_MP
</div>
