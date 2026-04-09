"""
隧道管理器

負責管理 PlayIt.gg 等隧道服務的啟動和停止
"""

from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import psutil
import json
from datetime import datetime

from ..models.server_config import ServerInstanceConfig
from ..core.path_resolver import PathResolver


class TunnelManager:
    """隧道管理器"""
    
    def __init__(self, config: ServerInstanceConfig, global_config: Optional[Dict[str, Any]] = None):
        """
        初始化隧道管理器
        
        Args:
            config: 伺服器設定
            global_config: 全局配置（可選，用於讀取全局 tunnel 路徑）
        """
        self.config = config
        self.global_config = global_config or {}
        self.paths = PathResolver(config)
        self.process: Optional[subprocess.Popen] = None
        self.tunnel_config = config.tunnel if hasattr(config, 'tunnel') else None
    
    def is_enabled(self) -> bool:
        """檢查隧道功能是否啟用"""
        return (self.tunnel_config is not None and 
                getattr(self.tunnel_config, 'enabled', False))
    
    def start(self) -> bool:
        """
        啟動隧道
        
        Returns:
            是否成功
        """
        if not self.is_enabled():
            return True  # 未啟用視為成功
        
        if self.is_running():
            print("隧道已在運行")
            return True
        
        tunnel_type = getattr(self.tunnel_config, 'type', 'playit')
        
        if tunnel_type == 'playit':
            return self._start_playit()
        else:
            print(f"不支援的隧道類型: {tunnel_type}")
            return False
    
    def _start_playit(self) -> bool:
        """啟動 PlayIt.gg 隧道"""
        try:
            # 獲取 playit.exe 路徑
            playit_path = getattr(self.tunnel_config, 'executable_path', 'playit.exe')
            playit_path = Path(playit_path)
            
            # 如果是相對路徑且全局配置中有設定，優先使用全局配置
            if not playit_path.is_absolute():
                global_path = self.global_config.get('tunnel', {}).get('playit', {}).get('executable_path', '')
                if global_path:
                    global_path = Path(global_path)
                    if global_path.exists():
                        playit_path = global_path
                        print(f"使用全局配置的 PlayIt 路徑")
            
            if not playit_path.exists():
                print(f"錯誤: 找不到 PlayIt 執行檔: {playit_path}")
                print(f"請檢查以下位置:")
                print(f"  1. 伺服器設定 (server.yml): tunnel.executable_path")
                print(f"  2. 全局設定 (config/app.yml): tunnel.playit.executable_path")
                print(f"或下載 PlayIt: https://playit.gg/download")
                return False
            
            print(f"啟動 PlayIt 隧道...")
            print(f"執行檔: {playit_path}")
            
            # 準備日誌檔案
            log_file = self.paths.get_runtime_path() / "playit.log"
            
            # 啟動 PlayIt（後台模式）
            with open(log_file, 'w', encoding='utf-8') as log:
                self.process = subprocess.Popen(
                    [str(playit_path)],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            
            # 儲存 PID
            self._save_pid(self.process.pid)
            
            print(f"✓ PlayIt 隧道已啟動 (PID: {self.process.pid})")
            print(f"日誌: {log_file}")
            
            # 顯示連接資訊（如果有設定）
            tunnel_address = getattr(self.tunnel_config, 'address', None)
            if tunnel_address:
                print(f"隧道地址: {tunnel_address}")
            
            return True
            
        except Exception as e:
            print(f"錯誤: 啟動 PlayIt 隧道失敗 - {e}")
            return False
    
    def stop(self) -> bool:
        """
        停止隧道
        
        Returns:
            是否成功
        """
        if not self.is_enabled():
            return True
        
        try:
            pid = self._load_pid()
            if not pid:
                print("沒有運行中的隧道")
                return True
            
            if not self.is_running():
                self._clear_pid()
                print("隧道已停止")
                return True
            
            # 終止程序
            try:
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=10)
                print(f"✓ 隧道已停止 (PID: {pid})")
            except psutil.TimeoutExpired:
                process.kill()
                print(f"✓ 隧道已強制停止 (PID: {pid})")
            
            self._clear_pid()
            return True
            
        except Exception as e:
            print(f"錯誤: 停止隧道失敗 - {e}")
            return False
    
    def is_running(self) -> bool:
        """檢查隧道是否正在運行"""
        pid = self._load_pid()
        if not pid:
            return False
        
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def get_status(self) -> dict:
        """
        取得隧道狀態
        
        Returns:
            狀態資訊字典
        """
        status = {
            'enabled': self.is_enabled(),
            'running': False,
            'pid': None,
            'type': None,
            'address': None,
            'server_running': self.is_server_running(),
            'orphaned': False  # 是否為孤立狀態（伺服器停止但隧道還在運行）
        }
        
        if not self.is_enabled():
            return status
        
        status['type'] = getattr(self.tunnel_config, 'type', 'playit')
        status['address'] = getattr(self.tunnel_config, 'address', None)
        status['running'] = self.is_running()
        
        if status['running']:
            status['pid'] = self._load_pid()
            # 檢查是否為孤立狀態
            status['orphaned'] = status['running'] and not status['server_running']
        
        return status
    
    def _get_pid_file(self) -> Path:
        """取得 PID 檔案路徑"""
        return self.paths.get_runtime_path() / "tunnel.pid"
    
    def _save_pid(self, pid: int):
        """儲存 PID"""
        try:
            pid_file = self._get_pid_file()
            pid_file.write_text(str(pid))
        except Exception as e:
            print(f"警告: 儲存隧道 PID 失敗 - {e}")
    
    def _load_pid(self) -> Optional[int]:
        """載入 PID"""
        try:
            pid_file = self._get_pid_file()
            if pid_file.exists():
                return int(pid_file.read_text().strip())
        except Exception:
            pass
        return None
    
    def _clear_pid(self):
        """清除 PID 檔案"""
        try:
            pid_file = self._get_pid_file()
            if pid_file.exists():
                pid_file.unlink()
        except Exception:
            pass
    
    def _get_server_pid_file(self) -> Path:
        """取得伺服器 PID 檔案路徑"""
        return self.paths.get_runtime_path() / "server.pid"
    
    def is_server_running(self) -> bool:
        """檢查伺服器是否正在運行"""
        try:
            server_pid_file = self._get_server_pid_file()
            if not server_pid_file.exists():
                return False
            
            server_pid = int(server_pid_file.read_text().strip())
            process = psutil.Process(server_pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError, FileNotFoundError):
            return False
    
    def check_and_cleanup(self, verbose: bool = False) -> bool:
        """
        檢查並清理孤立的隧道
        如果伺服器已停止但隧道還在運行，自動停止隧道
        
        Args:
            verbose: 是否顯示詳細訊息
        
        Returns:
            True 如果執行了清理操作，False 如果不需要清理
        """
        if not self.is_enabled():
            return False
        
        # 檢查隧道是否在運行
        if not self.is_running():
            return False
        
        # 檢查伺服器是否在運行
        if self.is_server_running():
            if verbose:
                print("伺服器正在運行，隧道狀態正常")
            return False
        
        # 伺服器已停止，但隧道還在運行 - 需要清理
        if verbose:
            print("⚠️  檢測到孤立的隧道（伺服器已停止但隧道仍在運行）")
            print("正在自動清理...")
        
        if self.stop():
            if verbose:
                print("✓ 隧道已清理")
            return True
        else:
            if verbose:
                print("✗ 隧道清理失敗")
            return False
