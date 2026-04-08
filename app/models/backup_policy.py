"""
備份策略模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from enum import Enum


class BackupMode(Enum):
    """備份模式"""
    MANUAL = "manual"  # 手動備份
    SCHEDULED = "scheduled"  # 排程備份
    DISABLED = "disabled"  # 停用


class BackupProvider(Enum):
    """備份提供者"""
    INTERNAL = "internal"  # 由框架執行
    EXTERNAL = "external"  # 外部備份系統
    DISABLED = "disabled"  # 不備份


class BackupStatus(Enum):
    """備份狀態"""
    PENDING = "pending"  # 待執行
    RUNNING = "running"  # 執行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失敗
    SKIPPED = "skipped"  # 跳過


@dataclass
class BackupPolicy:
    """備份策略"""
    enabled: bool = True
    mode: BackupMode = BackupMode.MANUAL
    provider: BackupProvider = BackupProvider.INTERNAL
    keep_last: int = 10  # 保留最近 N 個備份
    keep_days: int = 14  # 保留最近 N 天的備份
    compression: str = "zip"
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    
    def should_backup(self) -> bool:
        """判斷是否應該執行備份"""
        if not self.enabled:
            return False
        if self.provider == BackupProvider.DISABLED:
            return False
        if self.provider == BackupProvider.EXTERNAL:
            return False  # 外部備份，不由框架處理
        return True
    
    def get_backup_filename(self, server_name: str, timestamp: Optional[datetime] = None) -> str:
        """
        產生備份檔案名稱
        
        Args:
            server_name: 伺服器名稱
            timestamp: 時間戳記，預設為現在
        
        Returns:
            備份檔案名稱，如 "server-name_2024-01-15_14-30-00.zip"
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        time_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        ext = self.compression if self.compression else "zip"
        return f"{server_name}_{time_str}.{ext}"


@dataclass
class BackupRecord:
    """備份記錄"""
    server_name: str
    backup_file: Path
    created_at: datetime
    status: BackupStatus
    size_bytes: int = 0
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    
    def is_success(self) -> bool:
        """是否備份成功"""
        return self.status == BackupStatus.SUCCESS
    
    def get_size_mb(self) -> float:
        """取得檔案大小（MB）"""
        return self.size_bytes / (1024 * 1024)
    
    def should_keep(self, policy: BackupPolicy, now: Optional[datetime] = None) -> bool:
        """
        根據策略判斷是否應該保留此備份
        
        Args:
            policy: 備份策略
            now: 現在時間，預設為當前時間
        
        Returns:
            是否應該保留
        """
        if now is None:
            now = datetime.now()
        
        # 計算備份的天數
        age_days = (now - self.created_at).days
        
        # 如果在保留天數內，則保留
        if age_days <= policy.keep_days:
            return True
        
        return False
