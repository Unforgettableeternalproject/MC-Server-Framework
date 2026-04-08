"""
伺服器啟動器

負責啟動、停止和管理 Minecraft 伺服器程序
"""

from pathlib import Path
from typing import Optional, List
import subprocess
from datetime import datetime
import json

from ..models.server_config import ServerInstanceConfig
from ..models.instance_status import InstanceStatus, ServerState
from ..core.path_resolver import PathResolver
from ..core.java_resolver import JavaResolver
from ..utils.process import start_process, send_command, is_process_running, kill_process
import re


class ServerLauncher:
    """伺服器啟動器"""
    
    def __init__(self, config: ServerInstanceConfig, java_resolver: JavaResolver):
        """
        初始化啟動器
        
        Args:
            config: 伺服器設定
            java_resolver: Java 解析器
        """
        self.config = config
        self.java_resolver = java_resolver
        self.paths = PathResolver(config)
        self.process: Optional[subprocess.Popen] = None
        self.status = InstanceStatus(server_name=config.meta.name)
    
    def _check_server_properties(self) -> dict:
        """
        檢查 server.properties 配置
        
        Returns:
            配置信息字典
        """
        result = {
            'exists': False,
            'server_ip': None,
            'server_port': None,
            'online_mode': None,
            'max_players': None,
            'motd': None,
            'warnings': []
        }
        
        props_file = self.paths.get_server_properties()
        if not props_file.exists():
            result['warnings'].append('server.properties 不存在（首次啟動會自動生成）')
            return result
        
        result['exists'] = True
        
        try:
            with open(props_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 解析關鍵設定
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('#') or '=' not in line:
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'server-ip':
                        result['server_ip'] = value if value else '(all interfaces)'
                    elif key == 'server-port':
                        result['server_port'] = value
                    elif key == 'online-mode':
                        result['online_mode'] = value
                    elif key == 'max-players':
                        result['max_players'] = value
                    elif key == 'motd':
                        result['motd'] = value
                
                # 檢查警告
                if result['server_ip'] and result['server_ip'] not in ['(all interfaces)', '0.0.0.0', '']:
                    if result['server_ip'].startswith('127.') or result['server_ip'] == 'localhost':
                        result['warnings'].append(f"server-ip 設定為 {result['server_ip']}，將無法從外部連接")
                        result['warnings'].append('建議設定為 0.0.0.0 或留空以接受外部連接')
                
                if result['server_port'] and result['server_port'] != str(self.config.dns.server_port):
                    result['warnings'].append(f"server.properties 中的端口 ({result['server_port']}) 與 server.yml 設定 ({self.config.dns.server_port}) 不一致")
        
        except Exception as e:
            result['warnings'].append(f'讀取 server.properties 失敗: {e}')
        
        return result
    
    def build_command(self) -> Optional[List[str]]:
        """
        建立啟動指令
        
        Returns:
            指令列表，失敗時回傳 None
        """
        # 解析 Java 路徑
        java_path = self.java_resolver.resolve_java_path(self.config.java.profile)
        if not java_path:
            print(f"錯誤: 無法解析 Java profile '{self.config.java.profile}'")
            return None
        
        # 建立指令
        command = [str(java_path)]
        
        # 檢查是否為 Forge 特殊啟動模式（1.17+ 新版 Forge）
        is_forge_special = (
            self.config.server.loader.lower() == "forge" and 
            (self.config.server.startup_target == "FORGE_SPECIAL" or 
             any("@libraries" in arg for arg in self.config.launch.jvm_args))
        )
        
        if is_forge_special:
            # Forge 1.17+ 特殊啟動方式
            # 不添加 -Xms/-Xmx，因為它們在 @user_jvm_args.txt 中
            print("偵測到 Forge 1.17+ 啟動模式")
            
            # 添加所有 JVM 參數（包含 @user_jvm_args.txt 和 @win_args.txt）
            command.extend(self.config.launch.jvm_args)
            
            # 添加伺服器參數（如 nogui）
            command.extend(self.config.launch.server_args)
        else:
            # 傳統啟動方式（-jar）
            # 記憶體設定
            command.append(f"-Xms{self.config.launch.min_memory}")
            command.append(f"-Xmx{self.config.launch.max_memory}")
            
            # JVM 參數
            command.extend(self.config.launch.jvm_args)
            
            # JAR 檔案
            command.extend(["-jar", self.config.server.startup_target])
            
            # 伺服器參數
            command.extend(self.config.launch.server_args)
        
        return command
    
    def start(self, attach: bool = False) -> bool:
        """
        啟動伺服器
        
        Args:
            attach: 是否附加到終端（顯示即時日誌）
        
        Returns:
            是否成功
        """
        # 檢查是否已在運行
        if self.is_running():
            print(f"伺服器 {self.config.meta.name} 已在運行")
            return False
        
        # 驗證路徑
        is_valid, errors = self.paths.validate_paths()
        if not is_valid:
            print(f"路徑驗證失敗:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        # 確保目錄存在
        self.paths.ensure_directories()
        
        # 建立指令
        command = self.build_command()
        if not command:
            return False
        
        # 準備日誌檔案
        log_file = self.paths.get_session_log() if not attach else None
        
        print(f"啟動指令: {' '.join(command)}")
        print(f"工作目錄: {self.paths.get_server_root()}")
        
        # 檢查 server.properties 配置
        print("\n" + "="*60)
        print("伺服器網絡配置檢查")
        print("="*60)
        
        props_info = self._check_server_properties()
        if props_info['exists']:
            print(f"server-ip: {props_info['server_ip'] or '(未設定，默認 all interfaces)'}")
            print(f"server-port: {props_info['server_port'] or '25565'}")
            print(f"online-mode: {props_info['online_mode']}")
            print(f"max-players: {props_info['max_players']}")
            
            if props_info['warnings']:
                print("\n⚠️  配置警告:")
                for warning in props_info['warnings']:
                    print(f"  • {warning}")
            else:
                print("\n✓ 網絡配置正確，可接受外部連接")
        else:
            print("server.properties 不存在（首次啟動會自動生成）")
        
        print("="*60 + "\n")
        
        # DNS 連線測試（如果啟用）
        if self.config.dns.enabled:
            from ..core.dns_manager import DNSManager
            from ..utils.yaml_loader import load_global_config
            
            print("\n" + "="*60)
            print("DNS 連線測試")
            print("="*60)
            
            global_config = load_global_config()
            dns_mgr = DNSManager(self.config, global_config)
            test_result = dns_mgr.test_connection()
            
            print(f"狀態: {'✓ 啟用' if test_result['enabled'] else '✗ 停用'}")
            print(f"模式: {test_result['mode']}")
            print(f"網域: {test_result['domain']}")
            print(f"當前 IP: {test_result['current_ip'] or '無法檢測'}")
            print(f"伺服器端口: {self.config.dns.server_port}")
            
            if test_result['mode'].lower() == 'cloudflare':
                api_token = self.config.dns.config.get('api_token', '')
                zone_id = self.config.dns.config.get('zone_id', '')
                print(f"API Token: {'✓ 已設定 (' + api_token[:8] + '...' + api_token[-4:] + ')' if api_token else '✗ 未設定'}")
                print(f"Zone ID: {'✓ 已設定 (' + zone_id[:8] + '...)' if zone_id else '✗ 未設定'}")
                print(f"SRV 記錄: {'✓ 啟用' if self.config.dns.srv_record.enabled else '✗ 停用'}")
            
            if test_result['errors']:
                print("\n⚠️  發現問題:")
                for error in test_result['errors']:
                    print(f"  • {error}")
            
            if test_result['success']:
                print("\n✓ DNS 配置正確，將執行更新...")
                if dns_mgr.update_dns(force=True):
                    print(f"✓ DNS 更新成功: {test_result['domain']} -> {test_result['current_ip']}")
                    print(f"\n🌐 玩家連接方式:")
                    print(f"  直接連接: {test_result['domain']}")
                    if self.config.dns.srv_record.enabled:
                        print(f"  (SRV 記錄已啟用，玩家可以直接使用域名，無需輸入端口)")
                    else:
                        port = props_info.get('server_port', '25565')
                        if port != '25565':
                            print(f"  非標準端口: {test_result['domain']}:{port}")
                    print(f"  或使用 IP: {test_result['current_ip']}:{props_info.get('server_port', '25565')}")
                else:
                    print("✗ DNS 更新失敗，請檢查上方錯誤訊息")
            else:
                print("\n✗ DNS 配置有誤，請修正後重試")
            
            print("="*60 + "\n")
        
        if attach:
            print(f"[附加模式] 伺服器日誌將顯示在下方，按 Ctrl+C 可停止伺服器\n")
            print("="*60)
        
        # 啟動程序
        self.process = start_process(
            command=command,
            cwd=self.paths.get_server_root(),
            stdout_file=log_file,
            attach=attach
        )
        
        if not self.process:
            self.status.update_state(ServerState.ERROR, "無法啟動程序")
            return False
        
        # 儲存 PID
        pid = self.process.pid
        self._save_pid(pid)
        
        # 更新狀態
        self.status.pid = pid
        self.status.update_state(ServerState.STARTING)
        
        if not attach:
            print(f"伺服器已啟動 (PID: {pid})")
            print(f"日誌檔案: {log_file}")
            self.status.update_state(ServerState.RUNNING)
        else:
            # 附加模式：等待程序結束
            try:
                self.process.wait()
            except KeyboardInterrupt:
                print("\n\n" + "="*60)
                print("偵測到 Ctrl+C，正在停止伺服器...")
                self.stop()
            finally:
                print(f"\n伺服器已停止")
        
        return True
    
    def stop(self, timeout: int = 30) -> bool:
        """
        停止伺服器
        
        Args:
            timeout: 逾時秒數
        
        Returns:
            是否成功
        """
        if not self.is_running():
            print(f"伺服器 {self.config.meta.name} 未運行")
            return False
        
        self.status.update_state(ServerState.STOPPING)
        
        # 透過指令停止
        if self.process:
            stop_cmd = self.config.launch.stop_command
            print(f"發送停止指令: {stop_cmd}")
            send_command(self.process, stop_cmd)
            
            # 等待程序結束
            try:
                self.process.wait(timeout=timeout)
                self.status.update_state(ServerState.STOPPED)
                self._remove_pid()
                print("伺服器已正常停止")
                return True
            except subprocess.TimeoutExpired:
                print(f"警告: 伺服器未在 {timeout} 秒內停止，嘗試強制終止")
        
        # 強制終止
        if self.status.pid:
            if kill_process(self.status.pid, force=True):
                self.status.update_state(ServerState.STOPPED)
                self._remove_pid()
                print("伺服器已強制停止")
                return True
        
        self.status.update_state(ServerState.ERROR, "無法停止伺服器")
        return False
    
    def restart(self) -> bool:
        """
        重啟伺服器
        
        Returns:
            是否成功
        """
        print(f"重啟伺服器 {self.config.meta.name}")
        
        if self.is_running():
            if not self.stop():
                return False
        
        return self.start()
    
    def is_running(self) -> bool:
        """
        檢查伺服器是否正在運行
        
        Returns:
            是否運行中
        """
        # 從 PID 檔案讀取
        pid = self._load_pid()
        if pid:
            if is_process_running(pid):
                self.status.pid = pid
                self.status.update_state(ServerState.RUNNING)
                return True
        
        self.status.update_state(ServerState.STOPPED)
        return False
    
    def get_status(self) -> InstanceStatus:
        """
        取得伺服器狀態
        
        Returns:
            實例狀態
        """
        # 更新運行狀態
        self.is_running()
        
        # 更新路徑資訊
        self.status.instance_path = self.config.instance_path
        
        return self.status
    
    def _save_pid(self, pid: int):
        """儲存 PID 到檔案"""
        pid_file = self.paths.get_pid_file()
        try:
            data = {
                "pid": pid,
                "started_at": datetime.now().isoformat(),
                "server_name": self.config.meta.name
            }
            with open(pid_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"警告: 無法儲存 PID - {e}")
    
    def _load_pid(self) -> Optional[int]:
        """從檔案載入 PID"""
        pid_file = self.paths.get_pid_file()
        if not pid_file.exists():
            return None
        
        try:
            with open(pid_file, 'r') as f:
                data = json.load(f)
                return data.get("pid")
        except Exception:
            return None
    
    def _remove_pid(self):
        """移除 PID 檔案"""
        pid_file = self.paths.get_pid_file()
        try:
            if pid_file.exists():
                pid_file.unlink()
        except Exception as e:
            print(f"警告: 無法移除 PID 檔案 - {e}")
