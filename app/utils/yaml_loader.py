"""
YAML 設定檔載入工具
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from ..models.server_config import (
    ServerInstanceConfig, ServerMeta, ServerConfig, JavaConfig,
    LaunchConfig, DetectionConfig, WorldConfig, BackupConfig,
    DNSConfig, FeaturesConfig, BackupHooks, BackupRetention, SRVRecordConfig
)
from ..models.java_profile import JavaRegistry, JavaProfile


def load_yaml(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    載入 YAML 檔案
    
    Args:
        file_path: YAML 檔案路徑
    
    Returns:
        解析後的字典，失敗時回傳 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"錯誤: 解析 YAML 失敗 - {e}")
        return None
    except Exception as e:
        print(f"錯誤: 讀取檔案失敗 - {e}")
        return None


def save_yaml(data: Dict[str, Any], file_path: Path) -> bool:
    """
    儲存 YAML 檔案
    
    Args:
        data: 要儲存的資料
        file_path: 目標檔案路徑
    
    Returns:
        是否成功
    """
    try:
        # 確保目錄存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, indent=2)
        return True
    except Exception as e:
        print(f"錯誤: 儲存 YAML 失敗 - {e}")
        return False


def load_server_config(instance_path: Path) -> Optional[ServerInstanceConfig]:
    """
    載入伺服器實例設定
    
    Args:
        instance_path: 實例目錄路徑
    
    Returns:
        ServerInstanceConfig 物件，失敗時回傳 None
    """
    config_file = instance_path / "server.yml"
    
    if not config_file.exists():
        print(f"警告: {instance_path.name} 沒有 server.yml")
        return None
    
    data = load_yaml(config_file)
    if not data:
        return None
    
    try:
        # 解析各個區塊
        meta = ServerMeta(**data.get('meta', {}))
        server = ServerConfig(**data.get('server', {}))
        java = JavaConfig(**data.get('java', {}))
        launch = LaunchConfig(**data.get('launch', {}))
        detection = DetectionConfig(**data.get('detection', {}))
        world = WorldConfig(**data.get('world', {}))
        
        # 備份設定（較複雜）
        backup_data = data.get('backup', {})
        retention_data = backup_data.get('retention', {})
        hooks_data = backup_data.get('hooks', {})
        
        retention = BackupRetention(**retention_data)
        hooks = BackupHooks(**hooks_data)
        backup_data['retention'] = retention
        backup_data['hooks'] = hooks
        backup = BackupConfig(**backup_data)
        
        # DNS 設定
        dns_data = data.get('dns', {})
        srv_data = dns_data.get('srv_record', {})
        srv_record = SRVRecordConfig(**srv_data)
        dns_data['srv_record'] = srv_record
        dns = DNSConfig(**dns_data)
        
        # 功能開關
        features = FeaturesConfig(**data.get('features', {}))
        
        # 建立完整設定
        config = ServerInstanceConfig(
            meta=meta,
            server=server,
            java=java,
            launch=launch,
            detection=detection,
            world=world,
            backup=backup,
            dns=dns,
            features=features,
            instance_path=instance_path
        )
        
        return config
    
    except Exception as e:
        print(f"錯誤: 解析 server.yml 失敗 - {e}")
        return None


def load_java_registry(config_path: Path) -> Optional[JavaRegistry]:
    """
    載入 Java Registry
    
    Args:
        config_path: java_registry.yml 的路徑
    
    Returns:
        JavaRegistry 物件，失敗時回傳 None
    """
    if not config_path.exists():
        print(f"警告: 找不到 {config_path}")
        return JavaRegistry(profiles={})
    
    data = load_yaml(config_path)
    if not data:
        return JavaRegistry(profiles={})
    
    try:
        profiles_data = data.get('profiles', {})
        profiles = {}
        
        for name, profile_data in profiles_data.items():
            profile = JavaProfile(
                name=name,
                path=profile_data.get('path', ''),
                version=profile_data.get('version', ''),
                description=profile_data.get('description', '')
            )
            profiles[name] = profile
        
        return JavaRegistry(profiles=profiles)
    
    except Exception as e:
        print(f"錯誤: 解析 Java Registry 失敗 - {e}")
        return JavaRegistry(profiles={})


def create_default_server_config(server_name: str, instance_path: Path) -> bool:
    """
    建立預設的 server.yml
    
    Args:
        server_name: 伺服器名稱
        instance_path: 實例目錄路徑
    
    Returns:
        是否成功
    """
    default_config = {
        'meta': {
            'name': server_name,
            'display_name': server_name.replace('_', ' ').title(),
            'description': 'Minecraft Server'
        },
        'server': {
            'root_dir': 'server',
            'startup_target': 'server.jar',
            'type': 'minecraft-java',
            'loader': 'auto',
            'working_dir': 'server'
        },
        'java': {
            'mode': 'profile',
            'profile': 'java21'
        },
        'launch': {
            'min_memory': '2G',
            'max_memory': '6G',
            'jvm_args': [],
            'server_args': ['nogui'],
            'prelaunch_hooks': [],
            'postlaunch_hooks': [],
            'stop_command': 'stop'
        },
        'detection': {
            'auto_detect_loader': True,
            'auto_detect_worlds': True,
            'auto_detect_mods': True
        },
        'world': {
            'mode': 'auto',
            'include': ['world*'],
            'exclude': []
        },
        'backup': {
            'enabled': True,
            'mode': 'manual',
            'provider': 'internal',
            'schedule': None,
            'retention': {
                'keep_last': 10,
                'keep_days': 14
            },
            'compression': 'zip',
            'include': [
                'world*', 'server.properties', 'ops.json',
                'whitelist.json', 'banned-players.json', 'banned-ips.json'
            ],
            'exclude': [
                'logs/**', 'crash-reports/**', 'libraries/**', 'mods/**'
            ],
            'hooks': {
                'before_backup': ['save-off', 'save-all'],
                'after_backup': ['save-on']
            }
        },
        'dns': {
            'enabled': False,
            'mode': 'cloudflare',
            'domain': '',
            'update_interval': 300,
            'srv_record': {
                'enabled': True,
                'priority': 0,
                'weight': 5
            },
            'config': {}
        },
        'features': {
            'allow_internal_backup': True,
            'allow_auto_restart': False,
            'allow_monitoring': True
        }
    }
    
    config_file = instance_path / "server.yml"
    return save_yaml(default_config, config_file)
