"""
RCON (Remote Console) 管理器
用於與 Minecraft 伺服器進行遠端命令交互
"""
import socket
import struct
import time
from typing import Optional, Tuple
from pathlib import Path


class RCONError(Exception):
    """RCON 相關錯誤"""
    pass


class RCONManager:
    """管理與 Minecraft 伺服器的 RCON 連接"""
    
    # RCON 封包類型
    PACKET_LOGIN = 3
    PACKET_COMMAND = 2
    PACKET_RESPONSE = 0
    
    def __init__(self, host: str = "localhost", port: int = 25575, password: str = ""):
        """
        初始化 RCON 管理器
        
        Args:
            host: 伺服器主機地址
            port: RCON 端口
            password: RCON 密碼
        """
        self.host = host
        self.port = port
        self.password = password
        self.sock: Optional[socket.socket] = None
        self.request_id = 0
    
    def connect(self, timeout: float = 5.0) -> bool:
        """
        連接到 RCON 伺服器
        
        Args:
            timeout: 連接超時時間（秒）
            
        Returns:
            連接是否成功
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect((self.host, self.port))
            
            # 發送認證請求
            response = self._send_packet(self.PACKET_LOGIN, self.password)
            if response is None:
                raise RCONError("認證失敗：無回應")
            
            packet_type, request_id, payload = response
            if request_id == -1:
                raise RCONError("認證失敗：密碼錯誤")
            
            return True
            
        except socket.timeout:
            raise RCONError("連接超時")
        except ConnectionRefusedError:
            raise RCONError("連接被拒絕，請檢查伺服器是否啟用 RCON")
        except Exception as e:
            raise RCONError(f"連接失敗: {str(e)}")
    
    def disconnect(self):
        """斷開 RCON 連接"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            finally:
                self.sock = None
    
    def send_command(self, command: str) -> str:
        """
        發送命令到伺服器
        
        Args:
            command: 要執行的命令（不需要包含 /）
            
        Returns:
            伺服器回應
        """
        if not self.sock:
            raise RCONError("未連接到伺服器")
        
        try:
            response = self._send_packet(self.PACKET_COMMAND, command)
            if response is None:
                raise RCONError("無回應")
            
            packet_type, request_id, payload = response
            return payload.strip()
            
        except socket.timeout:
            raise RCONError("命令執行超時")
        except Exception as e:
            raise RCONError(f"命令執行失敗: {str(e)}")
    
    def _send_packet(self, packet_type: int, payload: str) -> Optional[Tuple[int, int, str]]:
        """
        發送 RCON 封包
        
        Args:
            packet_type: 封包類型
            payload: 封包內容
            
        Returns:
            (回應類型, 請求ID, 回應內容) 或 None
        """
        if not self.sock:
            return None
        
        self.request_id += 1
        request_id = self.request_id
        
        # 編碼 payload
        payload_bytes = payload.encode('utf-8')
        
        # 構建封包：請求ID(4) + 類型(4) + payload + null(1) + null(1)
        packet_size = 4 + 4 + len(payload_bytes) + 2
        packet = struct.pack('<iii', packet_size, request_id, packet_type)
        packet += payload_bytes
        packet += b'\x00\x00'
        
        # 發送封包
        self.sock.sendall(packet)
        
        # 接收回應
        return self._receive_packet()
    
    def _receive_packet(self) -> Optional[Tuple[int, int, str]]:
        """
        接收 RCON 封包
        
        Returns:
            (封包類型, 請求ID, 內容) 或 None
        """
        if not self.sock:
            return None
        
        # 讀取封包大小（4 bytes）
        size_data = self._recv_exactly(4)
        if not size_data:
            return None
        
        packet_size = struct.unpack('<i', size_data)[0]
        
        # 讀取封包內容
        packet_data = self._recv_exactly(packet_size)
        if not packet_data:
            return None
        
        # 解析封包：請求ID(4) + 類型(4) + payload + null(1) + null(1)
        request_id = struct.unpack('<i', packet_data[0:4])[0]
        packet_type = struct.unpack('<i', packet_data[4:8])[0]
        payload = packet_data[8:-2].decode('utf-8', errors='ignore')
        
        return (packet_type, request_id, payload)
    
    def _recv_exactly(self, size: int) -> bytes:
        """
        接收指定大小的數據
        
        Args:
            size: 要接收的字節數
            
        Returns:
            接收到的數據
        """
        if not self.sock:
            return b''
        
        data = b''
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                return b''
            data += chunk
        
        return data
    
    def __enter__(self):
        """上下文管理器：進入"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：退出"""
        self.disconnect()


def enable_rcon_in_properties(properties_file: Path, password: str = "", port: int = 25575) -> bool:
    """
    在 server.properties 中啟用 RCON
    
    Args:
        properties_file: server.properties 文件路徑
        password: RCON 密碼（如果為空，會生成隨機密碼）
        port: RCON 端口
        
    Returns:
        是否成功修改
    """
    import secrets
    import string
    
    if not properties_file.exists():
        return False
    
    # 如果沒有提供密碼，生成隨機密碼
    if not password:
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(16))
    
    # 讀取現有內容
    lines = properties_file.read_text(encoding='utf-8').splitlines()
    
    # 修改 RCON 相關設定
    modified_lines = []
    found_enable = False
    found_password = False
    found_port = False
    
    for line in lines:
        if line.startswith('enable-rcon='):
            modified_lines.append('enable-rcon=true')
            found_enable = True
        elif line.startswith('rcon.password='):
            modified_lines.append(f'rcon.password={password}')
            found_password = True
        elif line.startswith('rcon.port='):
            modified_lines.append(f'rcon.port={port}')
            found_port = True
        else:
            modified_lines.append(line)
    
    # 如果沒有找到相關設定，添加它們
    if not found_enable:
        modified_lines.append('enable-rcon=true')
    if not found_password:
        modified_lines.append(f'rcon.password={password}')
    if not found_port:
        modified_lines.append(f'rcon.port={port}')
    
    # 寫回文件
    properties_file.write_text('\n'.join(modified_lines) + '\n', encoding='utf-8')
    
    return True


def get_rcon_config_from_properties(properties_file: Path) -> Optional[dict]:
    """
    從 server.properties 讀取 RCON 配置
    
    Args:
        properties_file: server.properties 文件路徑
        
    Returns:
        包含 enabled, password, port 的字典，或 None
    """
    if not properties_file.exists():
        return None
    
    config = {
        'enabled': False,
        'password': '',
        'port': 25575
    }
    
    lines = properties_file.read_text(encoding='utf-8').splitlines()
    
    for line in lines:
        line = line.strip()
        if line.startswith('enable-rcon='):
            value = line.split('=', 1)[1].strip().lower()
            config['enabled'] = value == 'true'
        elif line.startswith('rcon.password='):
            config['password'] = line.split('=', 1)[1].strip()
        elif line.startswith('rcon.port='):
            try:
                config['port'] = int(line.split('=', 1)[1].strip())
            except:
                pass
    
    return config
