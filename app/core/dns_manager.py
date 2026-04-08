"""
DNS 管理器

負責管理動態 DNS 更新，支援 Cloudflare 和 DuckDNS
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json
import requests
import time
import threading

from ..models.server_config import ServerInstanceConfig, DNSConfig
from ..models.instance_status import DNSStatus
from ..core.path_resolver import PathResolver


class DNSManager:
    """DNS 管理器"""
    
    def __init__(self, config: ServerInstanceConfig, global_config: Optional[Dict[str, Any]] = None):
        """
        初始化 DNS 管理器
        
        Args:
            config: 伺服器設定
            global_config: 全域配置（從 app.yml 載入）
        """
        self.config = config
        self.dns_config: DNSConfig = config.dns
        self.global_config = global_config or {}
        self.paths = PathResolver(config)
        self.status = DNSStatus(
            enabled=self.dns_config.enabled,
            domain=self.dns_config.domain
        )
        self._load_state()
        self._update_thread: Optional[threading.Thread] = None
        self._stop_thread = False
        
        # 從全域配置讀取 API 憑證作為後備
        self._merge_global_config()
    
    def _merge_global_config(self):
        """合併全域配置到 DNS 配置（server.yml 優先）"""
        if not self.global_config:
            return
        
        dns_global = self.global_config.get('dns', {})
        mode = self.dns_config.mode.lower()
        
        # 如果 server.yml 沒有配置 API 憑證，從全域配置讀取
        if mode == 'cloudflare':
            cloudflare_global = dns_global.get('cloudflare', {})
            if not self.dns_config.config.get('api_token'):
                api_token = cloudflare_global.get('api_token')
                if api_token:
                    self.dns_config.config['api_token'] = api_token
            
            if not self.dns_config.config.get('zone_id'):
                zone_id = cloudflare_global.get('zone_id')
                if zone_id:
                    self.dns_config.config['zone_id'] = zone_id
        
        elif mode == 'duckdns':
            duckdns_global = dns_global.get('duckdns', {})
            if not self.dns_config.config.get('token'):
                token = duckdns_global.get('token')
                if token:
                    self.dns_config.config['token'] = token
    
    def is_enabled(self) -> bool:
        """檢查 DNS 功能是否啟用"""
        return self.dns_config.enabled and self.dns_config.domain
    
    def get_current_ip(self) -> Optional[str]:
        """
        取得當前公網 IP
        
        Returns:
            IP 位址，失敗時回傳 None
        """
        try:
            # 使用多個服務確保可靠性
            services = [
                "https://api.ipify.org",
                "https://ifconfig.me/ip",
                "https://icanhazip.com"
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        if self._is_valid_ip(ip):
                            return ip
                except Exception:
                    continue
            
            return None
        
        except Exception as e:
            print(f"錯誤: 無法取得公網 IP - {e}")
            return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """驗證 IP 位址格式"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def update_dns(self, force: bool = False) -> bool:
        """
        更新 DNS 記錄
        
        Args:
            force: 是否強制更新（即使 IP 未變更）
        
        Returns:
            是否成功
        """
        if not self.is_enabled():
            print("DNS 功能未啟用")
            return False
        
        # 取得當前 IP
        current_ip = self.get_current_ip()
        if not current_ip:
            self.status.last_error = "無法取得公網 IP"
            self.status.error_count += 1
            return False
        
        # 檢查 IP 是否變更
        if not force and current_ip == self.status.current_ip:
            print(f"IP 未變更 ({current_ip})")
            return True
        
        print(f"偵測到 IP 變更: {self.status.current_ip} -> {current_ip}")
        
        # 根據模式更新 DNS
        mode = self.dns_config.mode.lower()
        success = False
        
        if mode == "cloudflare":
            success = self._update_cloudflare(current_ip)
        elif mode == "duckdns":
            success = self._update_duckdns(current_ip)
        else:
            print(f"錯誤: 不支援的 DNS 模式 '{mode}'")
            return False
        
        # 更新狀態
        if success:
            self.status.current_ip = current_ip
            self.status.last_update = datetime.now()
            self.status.update_count += 1
            self.status.last_error = None
            print(f"DNS 更新成功: {self.dns_config.domain} -> {current_ip}")
        else:
            self.status.error_count += 1
        
        self.status.last_check = datetime.now()
        self._save_state()
        
        return success
    
    def _update_cloudflare(self, ip: str) -> bool:
        """
        更新 Cloudflare DNS 記錄
        
        Args:
            ip: 新的 IP 位址
        
        Returns:
            是否成功
        """
        try:
            api_token = self.dns_config.config.get("api_token")
            zone_id = self.dns_config.config.get("zone_id")
            
            if not api_token or not zone_id:
                self.status.last_error = "缺少 Cloudflare API Token 或 Zone ID"
                print(f"錯誤: {self.status.last_error}")
                return False
            
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            # 取得網域名稱
            domain = self.dns_config.domain
            
            # 尋找現有的 A 記錄
            list_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
            params = {"name": domain, "type": "A"}
            
            response = requests.get(list_url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                self.status.last_error = f"Cloudflare API 錯誤: {response.status_code}"
                print(f"錯誤: {self.status.last_error}")
                return False
            
            data = response.json()
            records = data.get("result", [])
            
            # 更新或建立 A 記錄
            if records:
                # 更新現有記錄
                record_id = records[0]["id"]
                update_url = f"{list_url}/{record_id}"
                
                payload = {
                    "type": "A",
                    "name": domain,
                    "content": ip,
                    "ttl": 300,
                    "proxied": False
                }
                
                response = requests.put(update_url, headers=headers, json=payload, timeout=10)
            else:
                # 建立新記錄
                payload = {
                    "type": "A",
                    "name": domain,
                    "content": ip,
                    "ttl": 300,
                    "proxied": False
                }
                
                response = requests.post(list_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code not in [200, 201]:
                self.status.last_error = f"更新 A 記錄失敗: {response.status_code}"
                print(f"錯誤: {self.status.last_error}")
                return False
            
            # 更新 SRV 記錄（如果啟用）
            if self.dns_config.srv_record.enabled:
                self._update_cloudflare_srv(zone_id, headers, domain, ip)
            
            return True
        
        except Exception as e:
            self.status.last_error = f"Cloudflare 更新失敗: {str(e)}"
            print(f"錯誤: {self.status.last_error}")
            return False
    
    def _update_cloudflare_srv(self, zone_id: str, headers: Dict, domain: str, ip: str) -> bool:
        """更新 Cloudflare SRV 記錄（用於 Minecraft）"""
        try:
            list_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
            
            # Minecraft SRV 記錄格式: _minecraft._tcp.domain.com
            srv_name = f"_minecraft._tcp.{domain}"
            
            # 尋找現有的 SRV 記錄
            params = {"name": srv_name, "type": "SRV"}
            response = requests.get(list_url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            records = data.get("result", [])
            
            # 取得自訂端口（優先使用 srv_record.port，否則使用 server_port）
            port = self.dns_config.srv_record.port if hasattr(self.dns_config.srv_record, 'port') and self.dns_config.srv_record.port else self.dns_config.server_port
            
            # SRV 記錄資料
            srv_data = {
                "type": "SRV",
                "name": srv_name,
                "data": {
                    "service": "_minecraft",
                    "proto": "_tcp",
                    "name": domain,
                    "priority": self.dns_config.srv_record.priority,
                    "weight": self.dns_config.srv_record.weight,
                    "port": port,
                    "target": domain
                }
            }
            
            if records:
                # 更新現有記錄
                record_id = records[0]["id"]
                update_url = f"{list_url}/{record_id}"
                response = requests.put(update_url, headers=headers, json=srv_data, timeout=10)
            else:
                # 建立新記錄
                response = requests.post(list_url, headers=headers, json=srv_data, timeout=10)
            
            return response.status_code in [200, 201]
        
        except Exception as e:
            print(f"警告: SRV 記錄更新失敗 - {e}")
            return False
    
    def _update_duckdns(self, ip: str) -> bool:
        """
        更新 DuckDNS 記錄
        
        Args:
            ip: 新的 IP 位址
        
        Returns:
            是否成功
        """
        try:
            token = self.dns_config.config.get("token")
            if not token:
                self.status.last_error = "缺少 DuckDNS Token"
                print(f"錯誤: {self.status.last_error}")
                return False
            
            # 從完整網域取得子網域名稱（假設格式為 subdomain.duckdns.org）
            domain_parts = self.dns_config.domain.split('.')
            subdomain = domain_parts[0] if domain_parts else self.dns_config.domain
            
            url = f"https://www.duckdns.org/update"
            params = {
                "domains": subdomain,
                "token": token,
                "ip": ip
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200 and response.text.strip() == "OK":
                return True
            else:
                self.status.last_error = f"DuckDNS 回應: {response.text}"
                print(f"錯誤: {self.status.last_error}")
                return False
        
        except Exception as e:
            self.status.last_error = f"DuckDNS 更新失敗: {str(e)}"
            print(f"錯誤: {self.status.last_error}")
            return False
    
    def start_auto_update(self):
        """啟動自動更新背景服務"""
        if not self.is_enabled():
            print("DNS 功能未啟用")
            return
        
        if self._update_thread and self._update_thread.is_alive():
            print("DNS 自動更新已在運行")
            return
        
        self._stop_thread = False
        self._update_thread = threading.Thread(target=self._auto_update_loop, daemon=True)
        self._update_thread.start()
        print(f"DNS 自動更新已啟動（間隔: {self.dns_config.update_interval} 秒）")
    
    def stop_auto_update(self):
        """停止自動更新背景服務"""
        self._stop_thread = True
        if self._update_thread:
            self._update_thread.join(timeout=5)
        print("DNS 自動更新已停止")
    
    def _auto_update_loop(self):
        """自動更新迴圈（背景執行）"""
        while not self._stop_thread:
            try:
                self.update_dns()
            except Exception as e:
                print(f"DNS 自動更新錯誤: {e}")
            
            # 等待指定間隔
            for _ in range(self.dns_config.update_interval):
                if self._stop_thread:
                    break
                time.sleep(1)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        測試 DNS 連線和配置
        
        Returns:
            測試結果字典
        """
        result = {
            'success': False,
            'enabled': self.dns_config.enabled,
            'mode': self.dns_config.mode,
            'domain': self.dns_config.domain,
            'current_ip': None,
            'has_credentials': False,
            'api_test': False,
            'errors': []
        }
        
        if not self.is_enabled():
            result['errors'].append('DNS 功能未啟用')
            return result
        
        # 測試 IP 檢測
        current_ip = self.get_current_ip()
        result['current_ip'] = current_ip
        if not current_ip:
            result['errors'].append('無法檢測公網 IP')
            return result
        
        # 檢查憑證
        mode = self.dns_config.mode.lower()
        if mode == 'cloudflare':
            api_token = self.dns_config.config.get('api_token')
            zone_id = self.dns_config.config.get('zone_id')
            
            if not api_token:
                result['errors'].append('缺少 Cloudflare API Token')
            if not zone_id:
                result['errors'].append('缺少 Cloudflare Zone ID')
            
            result['has_credentials'] = bool(api_token and zone_id)
            
            # 測試 API 連線
            if result['has_credentials']:
                try:
                    headers = {
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json"
                    }
                    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        result['api_test'] = True
                        result['success'] = True
                    else:
                        result['errors'].append(f'Cloudflare API 錯誤: HTTP {response.status_code}')
                        if response.status_code == 401:
                            result['errors'].append('API Token 無效或已過期')
                        elif response.status_code == 403:
                            result['errors'].append('API Token 權限不足')
                except Exception as e:
                    result['errors'].append(f'API 連線失敗: {str(e)}')
        
        elif mode == 'duckdns':
            token = self.dns_config.config.get('token')
            result['has_credentials'] = bool(token)
            
            if not token:
                result['errors'].append('缺少 DuckDNS Token')
            else:
                result['api_test'] = True
                result['success'] = True
        
        return result
    
    def get_status(self) -> DNSStatus:
        """取得 DNS 狀態"""
        self.status.last_check = datetime.now()
        return self.status
    
    def _save_state(self):
        """儲存 DNS 狀態到檔案"""
        try:
            state_file = self.paths.get_dns_state_file()
            state_file.parent.mkdir(exist_ok=True)
            
            state = {
                "domain": self.status.domain,
                "current_ip": self.status.current_ip,
                "last_update": self.status.last_update.isoformat() if self.status.last_update else None,
                "last_check": self.status.last_check.isoformat() if self.status.last_check else None,
                "update_count": self.status.update_count,
                "error_count": self.status.error_count,
                "last_error": self.status.last_error
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        
        except Exception as e:
            print(f"警告: 無法儲存 DNS 狀態 - {e}")
    
    def _load_state(self):
        """從檔案載入 DNS 狀態"""
        try:
            state_file = self.paths.get_dns_state_file()
            if not state_file.exists():
                return
            
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            self.status.current_ip = state.get("current_ip")
            self.status.update_count = state.get("update_count", 0)
            self.status.error_count = state.get("error_count", 0)
            self.status.last_error = state.get("last_error")
            
            if state.get("last_update"):
                self.status.last_update = datetime.fromisoformat(state["last_update"])
            if state.get("last_check"):
                self.status.last_check = datetime.fromisoformat(state["last_check"])
        
        except Exception as e:
            print(f"警告: 無法載入 DNS 狀態 - {e}")
