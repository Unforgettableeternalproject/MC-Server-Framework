"""
伺服器實例掃描器

負責掃描 servers/ 目錄下的所有伺服器實例
"""

from pathlib import Path
from typing import List, Optional
from ..models.server_config import ServerInstanceConfig
from ..utils.yaml_loader import load_server_config


class ServerScanner:
    """伺服器掃描器"""
    
    def __init__(self, servers_root: Path):
        """
        初始化掃描器
        
        Args:
            servers_root: servers 根目錄
        """
        self.servers_root = servers_root
    
    def scan_all(self) -> List[ServerInstanceConfig]:
        """
        掃描所有伺服器實例
        
        Returns:
            有效實例的設定列表
        """
        if not self.servers_root.exists():
            print(f"警告: servers 目錄不存在 - {self.servers_root}")
            return []
        
        instances = []
        
        # 掃描所有子目錄
        for item in self.servers_root.iterdir():
            if not item.is_dir():
                continue
            
            # 嘗試載入此實例
            config = self.load_instance(item)
            if config:
                instances.append(config)
        
        return instances
    
    def load_instance(self, instance_path: Path) -> Optional[ServerInstanceConfig]:
        """
        載入單個實例
        
        Args:
            instance_path: 實例目錄
        
        Returns:
            實例設定，失敗時回傳 None
        """
        # 檢查是否有 server.yml
        config_file = instance_path / "server.yml"
        
        if not config_file.exists():
            print(f"略過 {instance_path.name}: 沒有 server.yml")
            return None
        
        # 載入設定
        config = load_server_config(instance_path)
        if not config:
            print(f"略過 {instance_path.name}: 無法載入設定")
            return None
        
        # 驗證設定
        is_valid, errors = config.validate()
        if not is_valid:
            print(f"警告: {instance_path.name} 設定有誤:")
            for error in errors:
                print(f"  - {error}")
        
        return config
    
    def find_instance(self, server_name: str) -> Optional[Path]:
        """
        尋找指定名稱的實例目錄
        
        Args:
            server_name: 伺服器名稱
        
        Returns:
            實例目錄路徑，找不到時回傳 None
        """
        instance_path = self.servers_root / server_name
        
        if instance_path.exists() and instance_path.is_dir():
            return instance_path
        
        return None
    
    def is_valid_instance(self, instance_path: Path) -> bool:
        """
        檢查目錄是否為有效的實例
        
        Args:
            instance_path: 實例目錄
        
        Returns:
            是否有效
        """
        # 必須有 server.yml
        config_file = instance_path / "server.yml"
        if not config_file.exists():
            return False
        
        # 必須有 server/ 目錄
        server_dir = instance_path / "server"
        if not server_dir.exists():
            return False
        
        return True
    
    def detect_server_jar(self, instance_path: Path) -> Optional[str]:
        """
        偵測伺服器 JAR 檔案
        
        Args:
            instance_path: 實例目錄
        
        Returns:
            JAR 檔案名稱，找不到時回傳 None
        """
        server_dir = instance_path / "server"
        if not server_dir.exists():
            return None
        
        # 常見的伺服器 JAR 名稱
        common_names = [
            "server.jar",
            "minecraft_server.jar",
            "paper.jar",
            "purpur.jar",
            "spigot.jar",
            "fabric-server-launch.jar"
        ]
        
        # 先檢查常見名稱
        for name in common_names:
            jar_file = server_dir / name
            if jar_file.exists():
                return name
        
        # 尋找 forge 或 neoforge JAR
        for jar_file in server_dir.glob("*.jar"):
            jar_name = jar_file.name.lower()
            if "forge" in jar_name or "neoforge" in jar_name:
                return jar_file.name
        
        # 如果只有一個 JAR 檔，就用它
        jar_files = list(server_dir.glob("*.jar"))
        if len(jar_files) == 1:
            return jar_files[0].name
        
        return None
    
    def list_instances(self) -> List[str]:
        """
        列出所有實例名稱
        
        Returns:
            實例名稱列表
        """
        if not self.servers_root.exists():
            return []
        
        names = []
        for item in self.servers_root.iterdir():
            if item.is_dir() and self.is_valid_instance(item):
                names.append(item.name)
        
        return sorted(names)
