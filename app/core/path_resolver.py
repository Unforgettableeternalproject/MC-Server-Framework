"""
路徑解析器

提供統一的路徑存取介面
"""

from pathlib import Path
from typing import List
from ..models.server_config import ServerInstanceConfig


class PathResolver:
    """路徑解析器"""
    
    def __init__(self, config: ServerInstanceConfig):
        """
        初始化路徑解析器
        
        Args:
            config: 伺服器實例設定
        """
        self.config = config
        self.instance_path = config.instance_path
    
    def get_server_root(self) -> Path:
        """取得伺服器工作目錄（server/）"""
        return self.instance_path / self.config.server.root_dir
    
    def get_runtime_path(self) -> Path:
        """取得 runtime 目錄"""
        return self.instance_path / "runtime"
    
    def get_backup_path(self) -> Path:
        """取得 backup 目錄"""
        return self.instance_path / "backups"
    
    def get_temp_path(self) -> Path:
        """取得 temp 目錄"""
        return self.instance_path / "temp"
    
    def get_startup_jar(self) -> Path:
        """取得啟動 JAR 檔案路徑"""
        server_root = self.get_server_root()
        return server_root / self.config.server.startup_target
    
    def get_world_paths(self) -> List[Path]:
        """
        取得世界資料夾路徑列表
        
        Returns:
            世界目錄列表
        """
        server_root = self.get_server_root()
        world_paths = []
        
        # 標準世界名稱
        standard_worlds = ["world", "world_nether", "world_the_end"]
        
        for world_name in standard_worlds:
            world_path = server_root / world_name
            if world_path.exists() and world_path.is_dir():
                world_paths.append(world_path)
        
        # 自訂世界樣式
        if self.config.world.mode == "auto":
            for pattern in self.config.world.include:
                for world_path in server_root.glob(pattern):
                    if world_path.is_dir() and world_path not in world_paths:
                        # 檢查是否被排除
                        should_exclude = False
                        for exclude_pattern in self.config.world.exclude:
                            if world_path.match(exclude_pattern):
                                should_exclude = True
                                break
                        
                        if not should_exclude:
                            world_paths.append(world_path)
        
        return world_paths
    
    def get_mods_path(self) -> Path:
        """取得 mods 目錄"""
        return self.get_server_root() / "mods"
    
    def get_config_path(self) -> Path:
        """取得 config 目錄"""
        return self.get_server_root() / "config"
    
    def get_logs_path(self) -> Path:
        """取得 logs 目錄"""
        return self.get_server_root() / "logs"
    
    def get_libraries_path(self) -> Path:
        """取得 libraries 目錄"""
        return self.get_server_root() / "libraries"
    
    def get_crash_reports_path(self) -> Path:
        """取得 crash-reports 目錄"""
        return self.get_server_root() / "crash-reports"
    
    def get_server_properties(self) -> Path:
        """取得 server.properties 檔案路徑"""
        return self.get_server_root() / "server.properties"
    
    def get_eula_file(self) -> Path:
        """取得 eula.txt 檔案路徑"""
        return self.get_server_root() / "eula.txt"
    
    def get_pid_file(self) -> Path:
        """取得 PID 檔案路徑"""
        return self.get_runtime_path() / "pid.txt"
    
    def get_session_log(self) -> Path:
        """取得 session log 檔案路徑"""
        return self.get_runtime_path() / "session.log"
    
    def get_dns_state_file(self) -> Path:
        """取得 DNS 狀態檔案路徑"""
        return self.get_runtime_path() / "dns_state.json"
    
    def ensure_directories(self) -> bool:
        """
        確保所有必要目錄存在
        
        Returns:
            是否成功
        """
        try:
            directories = [
                self.get_server_root(),
                self.get_runtime_path(),
                self.get_backup_path(),
                self.get_temp_path()
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
            
            return True
        except Exception as e:
            print(f"錯誤: 建立目錄失敗 - {e}")
            return False
    
    def validate_paths(self) -> tuple[bool, List[str]]:
        """
        驗證必要路徑是否存在
        
        Returns:
            (是否有效, 錯誤訊息列表)
        """
        errors = []
        
        if not self.instance_path.exists():
            errors.append(f"實例目錄不存在: {self.instance_path}")
        
        if not self.get_server_root().exists():
            errors.append(f"伺服器目錄不存在: {self.get_server_root()}")
        
        # 檢查啟動目標（跳過 Forge 特殊模式）
        is_forge_special = (
            self.config.server.loader.lower() == "forge" and 
            self.config.server.startup_target == "FORGE_SPECIAL"
        )
        
        if not is_forge_special:
            startup_jar = self.get_startup_jar()
            if not startup_jar.exists():
                errors.append(f"啟動 JAR 不存在: {startup_jar}")
        else:
            # Forge 特殊模式：檢查必要的目錄和檔案
            libraries_dir = self.get_server_root() / "libraries"
            if not libraries_dir.exists():
                errors.append(f"Forge libraries 目錄不存在: {libraries_dir}")
            
            user_jvm_args = self.get_server_root() / "user_jvm_args.txt"
            if not user_jvm_args.exists():
                errors.append(f"Forge 設定檔不存在: {user_jvm_args}")
        
        return len(errors) == 0, errors
