"""
子程序管理工具
"""

import subprocess
import psutil
from pathlib import Path
from typing import Optional, List
import signal
import sys


def is_process_running(pid: int) -> bool:
    """
    檢查程序是否正在運行
    
    Args:
        pid: 程序 ID
    
    Returns:
        是否正在運行
    """
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def kill_process(pid: int, force: bool = False) -> bool:
    """
    終止程序
    
    Args:
        pid: 程序 ID
        force: 是否強制終止
    
    Returns:
        是否成功
    """
    try:
        process = psutil.Process(pid)
        
        if force:
            process.kill()  # SIGKILL
        else:
            process.terminate()  # SIGTERM
        
        # 等待程序結束
        process.wait(timeout=10)
        return True
    except psutil.NoSuchProcess:
        return True  # 程序已不存在
    except psutil.TimeoutExpired:
        # 如果不是強制模式，嘗試強制終止
        if not force:
            return kill_process(pid, force=True)
        return False
    except Exception as e:
        print(f"錯誤: 終止程序失敗 (PID {pid}) - {e}")
        return False


def start_process(
    command: List[str],
    cwd: Path,
    stdout_file: Optional[Path] = None,
    stderr_file: Optional[Path] = None,
    attach: bool = False
) -> Optional[subprocess.Popen]:
    """
    啟動子程序
    
    Args:
        command: 指令列表
        cwd: 工作目錄
        stdout_file: 標準輸出重定向檔案
        stderr_file: 標準錯誤重定向檔案
        attach: 是否附加到終端（顯示即時輸出）
    
    Returns:
        Popen 物件，失敗時回傳 None
    """
    try:
        # 準備輸出串流
        stdout = None
        stderr = None
        creation_flags = 0
        
        if attach:
            # 附加模式：直接輸出到終端，不隱藏視窗
            stdout = None  # 讓它輸出到當前終端
            stderr = None
        else:
            # 背景模式：重定向到檔案，隱藏視窗
            if stdout_file:
                stdout = open(stdout_file, 'w', encoding='utf-8')
            
            if stderr_file:
                stderr = open(stderr_file, 'w', encoding='utf-8')
            elif stdout_file:
                stderr = subprocess.STDOUT
            
            # Windows 特殊設定：避免開啟新視窗
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NO_WINDOW
        
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=stdout if stdout else None,
            stderr=stderr if stderr else None,
            stdin=subprocess.PIPE,
            creationflags=creation_flags
        )
        
        return process
    
    except Exception as e:
        print(f"錯誤: 啟動程序失敗 - {e}")
        return None


def send_command(process: subprocess.Popen, command: str) -> bool:
    """
    向程序發送指令（透過 stdin）
    
    Args:
        process: 程序物件
        command: 指令
    
    Returns:
        是否成功
    """
    try:
        if process.stdin:
            process.stdin.write(f"{command}\n".encode('utf-8'))
            process.stdin.flush()
            return True
        return False
    except Exception as e:
        print(f"錯誤: 發送指令失敗 - {e}")
        return False


def get_process_info(pid: int) -> Optional[dict]:
    """
    取得程序資訊
    
    Args:
        pid: 程序 ID
    
    Returns:
        程序資訊字典，失敗時回傳 None
    """
    try:
        process = psutil.Process(pid)
        
        return {
            'pid': pid,
            'name': process.name(),
            'status': process.status(),
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / (1024 * 1024),
            'create_time': process.create_time()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None
