"""
伺服器設定模型

對應 server.yml 的完整結構
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class ServerMeta:
    """伺服器基本資訊"""
    name: str
    display_name: str = ""
    description: str = ""


@dataclass
class ServerConfig:
    """伺服器主要設定"""
    root_dir: str = "server"
    startup_target: str = "server.jar"
    type: str = "minecraft-java"
    loader: str = "auto"
    working_dir: str = "server"


@dataclass
class JavaConfig:
    """Java 設定"""
    mode: str = "profile"  # profile, auto, custom
    profile: str = "java21"
    custom_path: Optional[str] = None


@dataclass
class LaunchConfig:
    """啟動設定"""
    min_memory: str = "2G"
    max_memory: str = "6G"
    jvm_args: List[str] = field(default_factory=list)
    server_args: List[str] = field(default_factory=lambda: ["nogui"])
    prelaunch_hooks: List[str] = field(default_factory=list)
    postlaunch_hooks: List[str] = field(default_factory=list)
    stop_command: str = "stop"


@dataclass
class DetectionConfig:
    """自動偵測設定"""
    auto_detect_loader: bool = True
    auto_detect_worlds: bool = True
    auto_detect_mods: bool = True


@dataclass
class WorldConfig:
    """世界設定"""
    mode: str = "auto"
    include: List[str] = field(default_factory=lambda: ["world*"])
    exclude: List[str] = field(default_factory=list)


@dataclass
class BackupHooks:
    """備份鉤子"""
    before_backup: List[str] = field(default_factory=lambda: ["save-off", "save-all"])
    after_backup: List[str] = field(default_factory=lambda: ["save-on"])


@dataclass
class BackupRetention:
    """備份保留策略"""
    keep_last: int = 10
    keep_days: int = 14


@dataclass
class BackupConfig:
    """備份設定"""
    enabled: bool = True
    mode: str = "manual"  # manual, scheduled, disabled
    provider: str = "internal"  # internal, external, disabled
    schedule: Optional[str] = None
    retention: BackupRetention = field(default_factory=BackupRetention)
    compression: str = "zip"
    include: List[str] = field(default_factory=lambda: [
        "world*", "server.properties", "ops.json",
        "whitelist.json", "banned-players.json", "banned-ips.json"
    ])
    exclude: List[str] = field(default_factory=lambda: [
        "logs/**", "crash-reports/**", "libraries/**", "mods/**"
    ])
    hooks: BackupHooks = field(default_factory=BackupHooks)


@dataclass
class SRVRecordConfig:
    """SRV 記錄設定"""
    enabled: bool = True
    priority: int = 0
    weight: int = 5
    port: int = 25565  # Minecraft 伺服器端口


@dataclass
class TunnelConfig:
    """隧道設定（用於穿透 CGNAT）"""
    enabled: bool = False
    type: str = "playit"  # playit, ngrok, cloudflared, zerotier
    executable_path: str = "playit.exe"  # 執行檔路徑
    address: Optional[str] = None  # 隧道地址（例如 xxx.playit.gg）
    auto_start: bool = True  # 是否隨伺服器自動啟動
    auto_stop: bool = True   # 是否隨伺服器自動停止
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RCONConfig:
    """RCON（遠端控制台）設定"""
    enabled: bool = True  # 是否啟用 RCON
    host: str = "localhost"  # RCON 主機地址
    port: int = 25575  # RCON 端口
    password: str = ""  # RCON 密碼（如果為空，會自動生成）
    auto_configure: bool = True  # 是否在啟動時自動配置 server.properties


@dataclass
class DNSConfig:
    """DNS 設定"""
    enabled: bool = False
    mode: str = "cloudflare"  # cloudflare, duckdns, custom, disabled
    domain: str = ""
    server_port: int = 25565  # Minecraft 伺服器端口（用於 SRV 記錄）
    update_interval: int = 300  # 秒
    srv_record: SRVRecordConfig = field(default_factory=SRVRecordConfig)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeaturesConfig:
    """功能開關"""
    allow_internal_backup: bool = True
    allow_auto_restart: bool = False
    allow_monitoring: bool = True


@dataclass
class ServerInstanceConfig:
    """完整的伺服器實例設定"""
    meta: ServerMeta
    server: ServerConfig
    java: JavaConfig
    launch: LaunchConfig
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    world: WorldConfig = field(default_factory=WorldConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    dns: DNSConfig = field(default_factory=DNSConfig)
    tunnel: TunnelConfig = field(default_factory=TunnelConfig)
    rcon: RCONConfig = field(default_factory=RCONConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    
    # 實例的實際路徑（由系統填充）
    instance_path: Optional[Path] = None

    @property
    def server_path(self) -> Optional[Path]:
        """取得伺服器工作目錄的完整路徑"""
        if self.instance_path:
            return self.instance_path / self.server.root_dir
        return None

    @property
    def runtime_path(self) -> Optional[Path]:
        """取得 runtime 目錄的完整路徑"""
        if self.instance_path:
            return self.instance_path / "runtime"
        return None

    @property
    def backup_path(self) -> Optional[Path]:
        """取得 backup 目錄的完整路徑"""
        if self.instance_path:
            return self.instance_path / "backups"
        return None

    def validate(self) -> tuple[bool, List[str]]:
        """
        驗證設定是否完整
        
        Returns:
            (是否有效, 錯誤訊息列表)
        """
        errors = []
        
        if not self.meta.name:
            errors.append("伺服器名稱不能為空")
        
        if not self.server.startup_target:
            errors.append("啟動目標不能為空")
        
        if self.java.mode == "profile" and not self.java.profile:
            errors.append("Java mode 為 profile 但未指定 profile")
        
        if self.java.mode == "custom" and not self.java.custom_path:
            errors.append("Java mode 為 custom 但未指定路徑")
        
        if self.dns.enabled and not self.dns.domain:
            errors.append("DNS 已啟用但未指定網域名稱")
        
        return len(errors) == 0, errors
