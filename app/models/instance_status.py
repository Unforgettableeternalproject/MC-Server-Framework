"""
伺服器實例狀態模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from pathlib import Path


class ServerState(Enum):
    """伺服器狀態"""
    UNKNOWN = "unknown"  # 未知
    STOPPED = "stopped"  # 已停止
    STARTING = "starting"  # 啟動中
    RUNNING = "running"  # 運行中
    STOPPING = "stopping"  # 停止中
    CRASHED = "crashed"  # 已崩潰
    ERROR = "error"  # 錯誤


@dataclass
class InstanceStatus:
    """伺服器實例狀態"""
    server_name: str
    state: ServerState = ServerState.UNKNOWN
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # 基本資訊
    java_version: Optional[str] = None
    server_version: Optional[str] = None
    loader_type: Optional[str] = None
    
    # 路徑資訊
    instance_path: Optional[Path] = None
    
    # DNS 狀態
    dns_enabled: bool = False
    dns_last_update: Optional[datetime] = None
    dns_current_ip: Optional[str] = None
    dns_status: Optional[str] = None
    
    def is_running(self) -> bool:
        """是否正在運行"""
        return self.state == ServerState.RUNNING
    
    def is_stopped(self) -> bool:
        """是否已停止"""
        return self.state == ServerState.STOPPED
    
    def can_start(self) -> bool:
        """是否可以啟動"""
        return self.state in [ServerState.STOPPED, ServerState.CRASHED, ServerState.ERROR]
    
    def can_stop(self) -> bool:
        """是否可以停止"""
        return self.state in [ServerState.RUNNING, ServerState.STARTING]
    
    def get_uptime_seconds(self) -> Optional[float]:
        """
        取得運行時間（秒）
        
        Returns:
            運行時間，如果未運行則回傳 None
        """
        if not self.is_running() or not self.started_at:
            return None
        return (datetime.now() - self.started_at).total_seconds()
    
    def get_uptime_string(self) -> str:
        """
        取得運行時間的人類可讀字串
        
        Returns:
            如 "2h 15m 30s" 或 "已停止"
        """
        uptime = self.get_uptime_seconds()
        if uptime is None:
            return "已停止"
        
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def update_state(self, new_state: ServerState, error: Optional[str] = None):
        """
        更新狀態
        
        Args:
            new_state: 新狀態
            error: 錯誤訊息（可選）
        """
        self.state = new_state
        self.last_check = datetime.now()
        
        if error:
            self.error_message = error
        
        # 根據狀態更新時間戳記
        if new_state == ServerState.RUNNING and not self.started_at:
            self.started_at = datetime.now()
        elif new_state == ServerState.STOPPED:
            self.stopped_at = datetime.now()
            self.started_at = None
            self.pid = None


@dataclass
class DNSStatus:
    """DNS 狀態"""
    enabled: bool = False
    domain: str = ""
    current_ip: Optional[str] = None
    last_update: Optional[datetime] = None
    last_check: Optional[datetime] = None
    update_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    
    def is_healthy(self) -> bool:
        """DNS 服務是否健康"""
        if not self.enabled:
            return True
        return self.error_count == 0 or (self.last_update is not None)
    
    def get_status_text(self) -> str:
        """取得狀態文字"""
        if not self.enabled:
            return "已停用"
        if not self.current_ip:
            return "未設定"
        if self.last_error:
            return f"錯誤: {self.last_error}"
        if self.last_update:
            return f"正常 (IP: {self.current_ip})"
        return "未知"
