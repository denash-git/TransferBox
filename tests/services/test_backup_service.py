import pytest
import os
import zipfile
from core.system.executor import MockSystemExecutor
from core.services.backup_service import BackupService


def test_backup_creation_and_listing(tmp_path):
    mock_exec = MockSystemExecutor()
    backup_dir = tmp_path / "backups"
    cfg1 = tmp_path / "instance.env"
    cfg1.write_text("DOMAIN=test.com\n", encoding="utf-8")
    cfg2 = tmp_path / "users.json"
    cfg2.write_text("[]\n", encoding="utf-8")

    service = BackupService(mock_exec, backup_dir=str(backup_dir))

    # 1. Create standard backup
    ok, path = service.create_backup(files=[str(cfg1), str(cfg2)])
    assert ok is True
    assert os.path.exists(path)
    assert "transferbox_backup_" in path

    # 2. Create pre-update backup
    ok2, path2 = service.create_backup(is_pre_update=True, version="4.0.0", files=[str(cfg1)])
    assert ok2 is True
    assert "pre_update_v4.0.0" in path2

    # 3. List backups
    backups = service.list_backups()
    assert len(backups) == 2
    assert any(b["is_pre_update"] for b in backups)


def test_backup_restore(tmp_path):
    mock_exec = MockSystemExecutor()
    backup_dir = tmp_path / "backups"
    cfg = tmp_path / "instance.env"
    cfg.write_text("RESTORED_KEY=123\n", encoding="utf-8")

    service = BackupService(mock_exec, backup_dir=str(backup_dir))
    ok, zip_path = service.create_backup(files=[str(cfg)])
    assert ok is True

    # Test restore
    ok_restore, msg = service.restore_backup(zip_path, extract_to_root=False)
    assert ok_restore is True
