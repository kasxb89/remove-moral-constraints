# -*- coding: utf-8 -*-
"""Command line tools for Claude Code sessions."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

from .claude import APP_NAME, claude_workspace_status
from .config import ConfigError, DEFAULT_CONFIG_FILE, load_config as load_shared_config
from .core import RefusalDetector, SessionFormat, SessionParser, MOCK_RESPONSE, clean_session_jsonl
from .core.patcher import save_session_jsonl
from .file_ops import create_unique_backup
from .output import safe_print

print = safe_print


def load_config():
    try:
        return load_shared_config(DEFAULT_CONFIG_FILE)
    except ConfigError as exc:
        print(f"配置读取失败，将使用默认设置: {exc}", file=sys.stderr)
        return {}


def handle_ctf_status():
    status = claude_workspace_status()
    print(APP_NAME)
    print(f"Claude Code CLI: {'已安装' if status['claude_cli_available'] else '未检测到'}")
    print(f"提示词配置: {'已启用' if status['claude_installed'] else '未启用'}")
    print("生效范围: Claude Code 用户级全局（全部项目）")
    print(f"CLAUDE.md: {status['claude_prompt_path']}")
    print(f"启动命令: {status['activation_command']}")


def handle_claude_ctf_install():
    from .claude import ClaudeGlobalConfigInstaller
    success, message = ClaudeGlobalConfigInstaller().install()
    print(message)
    return 0 if success else 1


def handle_claude_ctf_uninstall():
    from .claude import ClaudeGlobalConfigInstaller
    success, message = ClaudeGlobalConfigInstaller().uninstall()
    print(message)
    return 0 if success else 1


def handle_rewrite(original_request: str):
    config = load_config()
    if not config.get('ai_endpoint') or not config.get('ai_model'):
        print('请先在 claude-patcher-web 的设置页配置 AI 接口和模型。')
        return 1
    try:
        from web.backend.prompt_rewriter import rewrite_prompt
        from .ctf_config.templates import CLAUDE_CODE_SECURITY_MODE_PROMPT
        from .claude import read_claude_global_prompt
        rewritten, strategy = asyncio.run(rewrite_prompt(
            original_request, config['ai_endpoint'], config.get('ai_key', ''),
            config['ai_model'], target='claude_code', ctf_prompt=read_claude_global_prompt() or CLAUDE_CODE_SECURITY_MODE_PROMPT,
        ))
        print(f'改写结果 ({strategy}):')
        print(rewritten)
        return 0
    except Exception as exc:
        print(f'改写失败: {exc}', file=sys.stderr)
        return 1


def resolve_session_format(args) -> SessionFormat:
    if getattr(args, 'format', 'claude-code') not in ('auto', 'claude-code', 'claude_code'):
        raise ValueError('此版本仅支持 Claude Code 会话')
    return SessionFormat.CLAUDE_CODE


def _print_changes_summary(changes, show_content=False):
    print(f'  检测到 {len(changes)} 处修改')
    if show_content:
        for change in changes:
            print(f'    第 {change.line_num} 行 [{change.change_type}]: {change.original_content or ""}')


def main(argv=None):
    parser = argparse.ArgumentParser(prog='claude-patcher', description='Claude Code 会话预览、清理、备份和提示词配置')
    parser.add_argument('--session-dir', default=None, help='Claude 会话目录，默认 ~/.claude/projects')
    parser.add_argument('--format', choices=['claude-code', 'claude_code', 'auto'], default='claude-code', help='仅支持 Claude Code；auto 也按 Claude 格式处理')
    parser.add_argument('--dry-run', action='store_true', help='预览差异，不修改文件')
    parser.add_argument('--show-content', action='store_true', help='显示差异原文')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--latest', action='store_true', help='处理最新 Claude 会话')
    selection.add_argument('--all', action='store_true', help='处理全部 Claude 会话')
    parser.add_argument('--no-backup', action='store_true', help='不创建备份')
    parser.add_argument('--keep-reasoning', action='store_true', help='保留 thinking 内容')
    parser.add_argument('--status', '--ctf-status', dest='ctf_status', action='store_true', help='查看 Claude CLI 和全局提示词状态')
    parser.add_argument('--install-config', '--install-claude-ctf', dest='install_config', action='store_true', help='安装 Claude 全局提示词配置')
    parser.add_argument('--uninstall-config', '--uninstall-claude-ctf', dest='uninstall_config', action='store_true', help='卸载本工具管理的 Claude 全局提示词配置')
    parser.add_argument('--rewrite', metavar='REQUEST', help='使用已配置的 AI 接口改写请求')
    parser.add_argument('--web', action='store_true', help='启动网页管理界面')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args(argv)

    if args.ctf_status:
        handle_ctf_status()
        return 0
    if args.install_config:
        return handle_claude_ctf_install()
    if args.uninstall_config:
        return handle_claude_ctf_uninstall()
    if args.rewrite:
        return handle_rewrite(args.rewrite)
    if args.web:
        from web.backend.main import run_server
        run_server(host=args.host, port=args.port)
        return 0
    if not (args.latest or args.all or args.dry_run):
        parser.print_help()
        return 0

    session_dir = os.path.expanduser(args.session_dir or '~/.claude/projects')
    session_parser = SessionParser(session_dir, session_format=resolve_session_format(args))
    sessions = session_parser.list_sessions()
    if not args.all:
        sessions = sessions[:1]
    if not sessions:
        print(f'未找到 Claude 会话: {session_dir}')
        print('运行 claude-ctf，完成一次对话后再刷新。')
        return 0

    config = load_config()
    detector = RefusalDetector(config.get('custom_keywords'))
    modified_count = 0
    failed_count = 0
    for session in sessions:
        print(f'Claude 会话: {session.session_id}')
        try:
            lines = session_parser.parse_session_jsonl(session.path)
            if not any(line.get('type') in ('assistant', 'user') and isinstance(line.get('message'), dict) for line in lines):
                print('  跳过：不是可识别的 Claude Code 会话')
                continue
            cleaned, modified, changes = clean_session_jsonl(
                lines, detector, show_content=args.show_content,
                mock_response=config.get('mock_response', MOCK_RESPONSE),
                session_format=SessionFormat.CLAUDE_CODE,
                clean_reasoning=not args.keep_reasoning,
            )
            if not modified:
                print('  无需修改')
                continue
            _print_changes_summary(changes, args.show_content)
            if args.dry_run:
                print('  预览完成，未修改文件')
                continue
            if not args.no_backup:
                print(f'  备份: {create_unique_backup(session.path)}')
            save_session_jsonl(cleaned, session.path)
            modified_count += 1
            print('  已保存')
        except Exception as exc:
            failed_count += 1
            print(f'  处理失败: {exc}', file=sys.stderr)
    print(f'完成: {len(sessions)} 个 Claude 会话，修改 {modified_count} 个，失败 {failed_count} 个')
    return 1 if failed_count else 0


if __name__ == '__main__':
    sys.exit(main())
