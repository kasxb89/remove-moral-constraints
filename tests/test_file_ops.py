import os

import pytest

from codex_session_patcher import file_ops
from codex_session_patcher.file_ops import (
    UnsafeFileError,
    atomic_write_text,
    create_unique_backup,
)


class FrozenDatetime:
    @classmethod
    def now(cls):
        return cls()

    def strftime(self, _format):
        return "20260802_120000"


def test_atomic_write_preserves_original_when_replace_fails(tmp_path, monkeypatch):
    target = tmp_path / "session.jsonl"
    target.write_text("original\n", encoding="utf-8")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr(file_ops.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        atomic_write_text(target, "new\n")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert list(tmp_path.glob(".session.jsonl.*.tmp")) == []


@pytest.mark.skipif(os.name != "nt", reason="Windows 文件替换重试")
@pytest.mark.parametrize("winerror", [5, 32, 33])
def test_atomic_write_retries_transient_windows_conflict(tmp_path, monkeypatch, winerror):
    target = tmp_path / "session.jsonl"
    target.write_text("original\n", encoding="utf-8")
    real_replace = file_ops.os.replace
    attempts = []
    delays = []

    def temporarily_busy(source, destination):
        attempts.append(source)
        assert target.read_text(encoding="utf-8") == "original\n"
        if len(attempts) <= 2:
            error = PermissionError("file temporarily busy")
            error.winerror = winerror
            raise error
        real_replace(source, destination)

    monkeypatch.setattr(file_ops.os, "replace", temporarily_busy)
    monkeypatch.setattr(file_ops.time, "sleep", delays.append)

    atomic_write_text(target, "new\n")

    assert len(attempts) == 3
    assert len(delays) == 2
    assert len(set(attempts)) == 1
    assert target.read_text(encoding="utf-8") == "new\n"
    assert list(tmp_path.glob(".session.jsonl.*.tmp")) == []


@pytest.mark.skipif(os.name != "nt", reason="Windows 文件替换重试")
def test_atomic_write_succeeds_after_windows_reader_releases_file(tmp_path, monkeypatch):
    target = tmp_path / "session.jsonl"
    target.write_bytes(b"original\n")
    reader = target.open("rb")
    delays = []

    def release_reader(_delay):
        delays.append(_delay)
        assert reader.read() == b"original\n"
        reader.close()

    monkeypatch.setattr(file_ops.time, "sleep", release_reader)
    try:
        atomic_write_text(target, "new\n")
    finally:
        reader.close()

    assert len(delays) == 1
    assert target.read_text(encoding="utf-8") == "new\n"
    assert list(tmp_path.glob(".session.jsonl.*.tmp")) == []


@pytest.mark.skipif(os.name != "nt", reason="Windows 文件替换重试")
def test_atomic_write_does_not_overwrite_changes_made_during_retry(tmp_path, monkeypatch):
    target = tmp_path / "session.jsonl"
    target.write_bytes(b"original\n")
    attempts = []

    def temporarily_busy(source, destination):
        attempts.append(source)
        error = PermissionError("file temporarily busy")
        error.winerror = 5
        raise error

    def concurrent_update(_delay):
        target.write_bytes(b"newly appended conversation\n")

    monkeypatch.setattr(file_ops.os, "replace", temporarily_busy)
    monkeypatch.setattr(file_ops.time, "sleep", concurrent_update)

    with pytest.raises(OSError, match="原文件在等待替换期间发生变化"):
        atomic_write_text(target, "cleaned\n")

    assert len(attempts) == 1
    assert target.read_bytes() == b"newly appended conversation\n"
    assert list(tmp_path.glob(".session.jsonl.*.tmp")) == []


@pytest.mark.skipif(os.name != "nt", reason="Windows 文件替换重试")
def test_atomic_write_keeps_original_after_windows_retry_limit(tmp_path, monkeypatch):
    target = tmp_path / "session.jsonl"
    target.write_text("original\n", encoding="utf-8")
    attempts = []
    delays = []

    def access_denied(source, destination):
        attempts.append(source)
        error = PermissionError("access remains denied")
        error.winerror = 5
        raise error

    monkeypatch.setattr(file_ops.os, "replace", access_denied)
    monkeypatch.setattr(file_ops.time, "sleep", delays.append)

    with pytest.raises(PermissionError, match="access remains denied"):
        atomic_write_text(target, "new\n")

    assert len(attempts) == 6
    assert len(delays) == 5
    assert target.read_text(encoding="utf-8") == "original\n"
    assert list(tmp_path.glob(".session.jsonl.*.tmp")) == []


def test_atomic_write_rejects_symlink_target(tmp_path):
    actual = tmp_path / "actual.txt"
    actual.write_text("original", encoding="utf-8")
    target = tmp_path / "target.txt"
    try:
        target.symlink_to(actual)
    except (OSError, NotImplementedError):
        pytest.skip("当前平台不支持测试符号链接")

    with pytest.raises(UnsafeFileError):
        atomic_write_text(target, "new")

    assert actual.read_text(encoding="utf-8") == "original"


def test_backups_created_in_same_second_do_not_overwrite(tmp_path, monkeypatch):
    source = tmp_path / "config.toml"
    source.write_text("first", encoding="utf-8")
    monkeypatch.setattr(file_ops, "datetime", FrozenDatetime)

    first = create_unique_backup(source)
    source.write_text("second", encoding="utf-8")
    second = create_unique_backup(source)

    assert first != second
    assert open(first, encoding="utf-8").read() == "first"
    assert open(second, encoding="utf-8").read() == "second"


def test_backup_rejects_symlink_source(tmp_path):
    actual = tmp_path / "actual.txt"
    actual.write_text("content", encoding="utf-8")
    source = tmp_path / "source.txt"
    try:
        source.symlink_to(actual)
    except (OSError, NotImplementedError):
        pytest.skip("当前平台不支持测试符号链接")

    with pytest.raises(UnsafeFileError):
        create_unique_backup(source)
