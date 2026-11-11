# Claude Session Patcher

Claude Code 专用的本机会话管理工具，提供会话列表、内容搜索、清理预览、差异对比、备份恢复和 用户级全局提示词配置。

本地版本：**1.5.1+claude.1**。基于 [remove-moral-constraints](https://github.com/kasxb89/remove-moral-constraints) 改造。

## Windows 启动

安装完成后，重新打开 CMD 或 PowerShell：

```powershell
claude-patcher-web
```

浏览器访问 http://127.0.0.1:8080。也可双击项目目录中的 `start-web.cmd`，双击 `stop-web.cmd` 停止管理服务。

## 启动 Claude Code

```powershell
# 只需配置一次
claude-patcher --install-config

# 在任意项目目录启动
claude
```

`claude-ctf` 保留当前项目目录，使用现有 Claude Code 登录/API 设置，并在启动进程中采用 Windows 已启用的 HTTP/HTTPS 代理。

全局提示词保存在 `%USERPROFILE%\.claude\CLAUDE.md`，会在所有项目的新会话中加载。工具只管理其中带边界标记的部分，保留用户原有全局内容；旧专用目录的提示词已备份迁移。首次运行按 Claude Code 提示完成主题选择和登录。

提示词会作为 Claude 的上下文加载；本工具不修改官方客户端或模型，也不保证消除拒答。

## 命令行

```powershell
claude-patcher --help
claude-patcher --status
claude-patcher --dry-run --latest --show-content
claude-patcher --latest
claude-patcher --all
claude-patcher --latest --keep-reasoning
```

不带参数时显示帮助。会话默认从 `~/.claude/projects` 发现；`--format auto` 也只处理 Claude Code。可用 `--session-dir` 指定 Claude 会话副本目录。

实际清理默认先创建唯一时间戳备份。建议先预览差异、选择内容，再执行清理。完成后回到原项目目录，用 `claude --continue` 继续。

## 网页功能

- 会话：仅显示 Claude Code，按项目、时间和处理状态过滤。
- 提示词：管理 Claude 全局配置、编辑提示词、保存和切换模板。
- 预览与恢复：查看差异，默认备份，按备份还原。
- 可选 AI 改写：在设置页配置兼容 OpenAI Chat Completions 的接口和模型。

AI 改写接口在本工具设置页独立配置；Claude Code 自身的登录与模型配置继续由 Claude Code 管理。

## 配置与边界

应用设置文件：`~/.claude-patcher/config.json`。升级时会迁移旧应用设置，并保留原文件。

服务仅供本机访问，HTTP、CORS 和 WebSocket 保持回环来源校验。设置接口不返回 API 密钥明文。

Windows 原子替换遇到短暂占用时最多重试 5 次，累计等待 3.1 秒；等待期间若原文件变化，会停止写入并提示刷新。持续占用时先退出相关 Claude 进程再清理。

## 从源码安装

需要 Python 3.8+；重新构建前端需要 Node.js 20.19+ 或 22.12+。

```powershell
python -m venv .venv
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m pip install -e ".[web]"
npm.cmd --prefix web/frontend ci
npm.cmd --prefix web/frontend run build
```

Windows 用户可将项目的 `bin` 目录加入 Path，重新打开终端后使用 `claude-patcher`、`claude-patcher-web` 和 `claude-ctf`。
