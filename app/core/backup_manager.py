"""
備份管理器

負責執行和管理伺服器備份
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
import json

from ..models.server_config import ServerInstanceConfig
from ..models.backup_policy import BackupPolicy, BackupRecord, BackupStatus, BackupMode, BackupProvider
from ..core.path_resolver import PathResolver
from ..core.launcher import ServerLauncher
from ..utils.archive import create_zip_archive, create_tar_archive
from ..utils.process import send_command
from ..utils.fs import get_file_size_mb


class BackupManager:
    """備份管理器"""
    
    def __init__(self, config: ServerInstanceConfig, launcher: Optional[ServerLauncher] = None):
        """
        初始化備份管理器
        
        Args:
            config: 伺服器設定
            launcher: 伺服器啟動器（用於發送備份鉤子指令）
        """
        self.config = config
        self.launcher = launcher
        self.paths = PathResolver(config)
        self.policy = self._create_policy_from_config()
    
    def _create_policy_from_config(self) -> BackupPolicy:
        """從設定建立備份策略"""
        backup_config = self.config.backup
        
        return BackupPolicy(
            enabled=backup_config.enabled,
            mode=BackupMode(backup_config.mode),
            provider=BackupProvider(backup_config.provider),
            keep_last=backup_config.retention.keep_last,
            keep_days=backup_config.retention.keep_days,
            compression=backup_config.compression,
            include_patterns=backup_config.include,
            exclude_patterns=backup_config.exclude
        )
    
    def should_backup(self) -> bool:
        """判斷是否應該執行備份"""
        return self.policy.should_backup()
    
    def create_backup(self) -> Optional[BackupRecord]:
        """
        建立備份
        
        Returns:
            備份記錄，失敗時回傳 None
        """
        if not self.should_backup():
            print(f"備份已停用或由外部管理")
            return None
        
        server_name = self.config.meta.name
        print(f"開始備份 {server_name}...")
        
        start_time = datetime.now()
        record = BackupRecord(
            server_name=server_name,
            backup_file=Path(),  # 暫時
            created_at=start_time,
            status=BackupStatus.RUNNING
        )
        
        try:
            # 執行 before_backup 鉤子
            if not self._run_hooks(self.config.backup.hooks.before_backup, "before_backup"):
                record.status = BackupStatus.FAILED
                record.error_message = "Before backup hooks 失敗"
                return record
            
            # 建立備份檔案
            backup_file = self._create_backup_archive()
            if not backup_file:
                record.status = BackupStatus.FAILED
                record.error_message = "建立備份檔案失敗"
                return record
            
            record.backup_file = backup_file
            record.size_bytes = int(backup_file.stat().st_size)
            
            # 執行 after_backup 鉤子
            self._run_hooks(self.config.backup.hooks.after_backup, "after_backup")
            
            # 成功
            end_time = datetime.now()
            record.status = BackupStatus.SUCCESS
            record.duration_seconds = (end_time - start_time).total_seconds()
            
            size_mb = record.get_size_mb()
            print(f"備份完成: {backup_file.name} ({size_mb:.2f} MB)")
            
            # 清理舊備份
            self.cleanup_old_backups()
            
            return record
        
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.error_message = str(e)
            print(f"備份失敗: {e}")
            return record
    
    def _create_backup_archive(self) -> Optional[Path]:
        """建立備份壓縮檔"""
        server_root = self.paths.get_server_root()
        backup_dir = self.paths.get_backup_path()
        backup_dir.mkdir(exist_ok=True)
        
        # 產生檔案名稱
        filename = self.policy.get_backup_filename(self.config.meta.name)
        backup_file = backup_dir / filename
        
        # 建立壓縮檔
        compression = self.policy.compression.lower()
        
        if compression == "zip":
            success = create_zip_archive(
                source_dir=server_root,
                output_file=backup_file,
                include_patterns=self.policy.include_patterns,
                exclude_patterns=self.policy.exclude_patterns
            )
        elif compression in ["tar", "tar.gz", "gz"]:
            success = create_tar_archive(
                source_dir=server_root,
                output_file=backup_file,
                include_patterns=self.policy.include_patterns,
                exclude_patterns=self.policy.exclude_patterns,
                compression="gz"
            )
        else:
            print(f"警告: 不支援的壓縮格式 '{compression}'，使用 zip")
            success = create_zip_archive(
                source_dir=server_root,
                output_file=backup_file,
                include_patterns=self.policy.include_patterns,
                exclude_patterns=self.policy.exclude_patterns
            )
        
        if success:
            return backup_file
        return None
    
    def _run_hooks(self, commands: List[str], hook_type: str) -> bool:
        """
        執行鉤子指令
        
        Args:
            commands: 指令列表
            hook_type: 鉤子類型
        
        Returns:
            是否全部成功
        """
        if not commands:
            return True
        
        if not self.launcher or not self.launcher.is_running():
            print(f"警告: 伺服器未運行，跳過 {hook_type} hooks")
            return True
        
        print(f"執行 {hook_type} hooks...")
        for cmd in commands:
            print(f"  > {cmd}")
            if not send_command(self.launcher.process, cmd):
                print(f"警告: 指令執行可能失敗: {cmd}")
        
        # 給伺服器一些時間處理指令
        import time
        time.sleep(2)
        
        return True
    
    def list_backups(self) -> List[Path]:
        """
        列出所有備份檔案
        
        Returns:
            備份檔案列表（依時間由新到舊）
        """
        backup_dir = self.paths.get_backup_path()
        if not backup_dir.exists():
            return []
        
        backups = []
        for file in backup_dir.iterdir():
            if file.is_file() and file.suffix in ['.zip', '.tar', '.gz']:
                backups.append(file)
        
        # 依修改時間排序（新到舊）
        backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return backups
    
    def cleanup_old_backups(self):
        """清理舊備份"""
        backups = self.list_backups()
        
        # 保留最近 N 個
        if len(backups) > self.policy.keep_last:
            old_backups = backups[self.policy.keep_last:]
            print(f"清理 {len(old_backups)} 個舊備份...")
            
            for backup_file in old_backups:
                try:
                    # 檢查是否應該保留（基於日期）
                    age_days = (datetime.now() - datetime.fromtimestamp(backup_file.stat().st_mtime)).days
                    if age_days <= self.policy.keep_days:
                        continue
                    
                    print(f"  刪除: {backup_file.name}")
                    backup_file.unlink()
                except Exception as e:
                    print(f"  警告: 無法刪除 {backup_file.name} - {e}")
    
    def get_backup_info(self, backup_file: Path) -> dict:
        """
        取得備份資訊
        
        Args:
            backup_file: 備份檔案
        
        Returns:
            備份資訊字典
        """
        stat = backup_file.stat()
        
        return {
            "name": backup_file.name,
            "path": str(backup_file),
            "size_mb": stat.st_size / (1024 * 1024),
            "created_at": datetime.fromtimestamp(stat.st_mtime),
            "age_days": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
        }
